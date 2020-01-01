import os
import logging
import tempfile
import time
import threading
from contextlib import suppress
from pathlib import Path
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List, Callable

import plumbum as pb

from errors import GhaoRuntimeError
from jobs_view import JobsView

from gi.repository import GLib, Gio, Gtk, Gdk

from utils import action_handler, get_command_base

log = logging.getLogger(__name__)


class KubeCtl:
    def __init__(self):
        from nihao.k8s import K8s
        self.k8s = K8s(gather_pods_by_job=False)
        self.cmd = get_command_base('kubectl')

    def get_jobs(self):
        return self.k8s.get_jobs_info(jobdir=True)

    def describe_cmd(self, name: str, filename: str) -> Callable:
        return self.cmd["describe", "job", name] > filename

    def kill_cmd(self, name: str) -> Callable:
        return self.cmd["delete", "job", name]


class JobCtl:
    def __init__(self, fake=False):
        if fake:
            from fakectl import FakeKubeCtl
            self.kubectl = FakeKubeCtl()
        else:
            self.kubectl = KubeCtl()
        self._jobs_cache = []  # Used to run job specific commands by job name

    def update_jobs_view(self, jobs_view: JobsView):
        def fn():
            self._jobs_cache = self.kubectl.get_jobs()
            GLib.idle_add(lambda: jobs_view.update(self._jobs_cache))

        threading.Thread(target=fn, daemon=True).start()

    def setup_update_actions(self, jobs_view: JobsView, action_group: Gio.SimpleActionGroup):
        def update_jobs_periodic_task():
            while True:
                self._jobs_cache = self.kubectl.get_jobs()
                GLib.idle_add(lambda: jobs_view.update(self._jobs_cache))
                time.sleep(8.)

        update_jobs_action = Gio.SimpleAction.new("update", None)
        update_jobs_action.connect("activate", action_handler(lambda: self.update_jobs_view(jobs_view)))

        action_group.add_action(update_jobs_action)
        threading.Thread(target=update_jobs_periodic_task, daemon=True).start()

    def open_file_browsers(self, names: List[str]):
        items = [item for item in self._jobs_cache if item.name in names]
        jobs_without_dir = []

        for item in items:
            if item.directory:
                if not Path(item.directory).exists():
                    raise GhaoRuntimeError(f"Job directory not accessible! Are network drives mounted?")

                log.info(f"Opening file browser in {item.directory}")
                cmd = get_command_base('xdg-open')
                runner = cmd[item.directory]
                with suppress(pb.ProcessExecutionError):
                    runner.run_bg()
            else:
                jobs_without_dir.append(item)

        if len(jobs_without_dir) > 0:
            names_ul = '\n -'.join(job.name for job in jobs_without_dir)
            raise GhaoRuntimeError(f"There is no assigned directory to:\n{names_ul}")

    def yank_job_path(self, names: List[str]):
        if len(names) == 0:
            raise GhaoRuntimeError("Failed to copy job path - no job selected!")
        elif len(names) > 1:
            raise GhaoRuntimeError("Failed to copy job path - more than 1 job selected!")
        else:
            name = names[0]
            items = [item for item in self._jobs_cache if item.name == name]
            if len(items) == 0:
                raise GhaoRuntimeError("Failed to copy job path - job no longer exists!")
            item = items[0]

            if item.directory is None:
                raise GhaoRuntimeError(f"Failed to copy job path - no directory assigned to `{name}`!")

            directory = item.directory

            def fn():
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(directory, -1)

            GLib.idle_add(fn)

    def describe_jobs(self, names: List[str]):
        if len(names) == 0:
            return
        temp_dir = Path(tempfile.mkdtemp(prefix='nihao'))
        files = []
        for name in names:
            file = str(temp_dir / name) + '.txt'
            cmd = self.kubectl.describe_cmd(name, file)
            with suppress(pb.ProcessExecutionError):
                cmd()
            os.chmod(file, S_IREAD | S_IRGRP | S_IROTH)
            files.append(file)

        for file in files:
            editor = get_command_base("xdg-open")[file]
            with suppress(pb.ProcessExecutionError):
                editor.run_bg()

    def kill_jobs(self, names: List[str]):
        for name in names:
            cmd = self.kubectl.kill_cmd(name)
            with suppress(pb.ProcessExecutionError):
                cmd()
