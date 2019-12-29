import os
import logging
import tempfile
import time
import threading
from contextlib import suppress
from pathlib import Path
from stat import S_IREAD, S_IRGRP, S_IROTH
from typing import List

import plumbum as pb

from errors import GhaoRuntimeError
from jobs_view import JobsView
from nihao.k8s import K8s

from gi.repository import GLib, Gio

from utils import action_handler


log = logging.getLogger(__name__)


def get_command_base(name: str):
    try:
        cmd = pb.local[name]
        return cmd
    except pb.CommandNotFound as e:
        log.error(f"{e.program} was not found.\n"
                  "Make sure that it's installed before using this tool.")
        raise GhaoRuntimeError(f"Command `{name}` not found.")


class KubeCtl:
    def __init__(self):
        self.k8s = K8s()
        self._jobs_cache = []  # Used to run job specific commands by job name

    def update_jobs_view(self, jobs_view: JobsView):
        def fn():
            self._jobs_cache = self.k8s.get_jobs_info(jobdir=True)
            GLib.idle_add(lambda: jobs_view.update(self._jobs_cache))

        threading.Thread(target=fn, daemon=True).start()

    def setup_update_actions(self, jobs_view: JobsView, action_group: Gio.SimpleActionGroup):
        def update_jobs_periodic_task():
            while True:
                self._jobs_cache = self.k8s.get_jobs_info(jobdir=True)
                GLib.idle_add(lambda: jobs_view.update(self._jobs_cache))
                time.sleep(8.)

        update_jobs_action = Gio.SimpleAction.new("update", None)
        update_jobs_action.connect("activate", action_handler(self.update_jobs_view))

        action_group.add_action(update_jobs_action)
        threading.Thread(target=update_jobs_periodic_task, daemon=True).start()

    def open_file_browsers(self, names: List[str]):
        items = [item for item in self._jobs_cache if item.name in names]
        jobs_without_dir = []

        for item in items:
            if item.directory:
                print(f"Opening file browser in {item.directory}")
                cmd = get_command_base('xdg-open')
                runner = cmd[item.directory]
                with suppress(pb.ProcessExecutionError):
                    runner.run_bg()
            else:
                jobs_without_dir.append(item)

        if len(jobs_without_dir) > 0:
            names_ul = '\n -'.join(job.name for job in jobs_without_dir)
            raise GhaoRuntimeError(f"There is no assigned directory to:\n{names_ul}")


def describe_jobs(names: List[str]):
    if len(names) == 0:
        return
    temp_dir = Path(tempfile.mkdtemp(prefix='nihao'))
    files = []
    for name in names:
        file = str(temp_dir / name) + '.txt'
        kubectl = get_command_base('kubectl')
        bash_runner = kubectl["describe", "job", name] > file
        with suppress(pb.ProcessExecutionError):
            bash_runner()
        os.chmod(file, S_IREAD | S_IRGRP | S_IROTH)
        files.append(file)

    editor = get_command_base("xdg-open").__getitem__(*files)
    with suppress(pb.ProcessExecutionError):
        editor.run_bg()


def yank_jobs(names: List[str]):
    # joined_names = " ".join(names)
    msg = "Yank jobs not implemented yet!"
    log.warning(msg)
    raise GhaoRuntimeError(msg)


def kill_jobs(names: List[str]):
    for name in names:
        kubectl = get_command_base('kubectl')
        bash_runner = kubectl["delete", "job", name]
        with suppress(pb.ProcessExecutionError):
            bash_runner.run_tee()
