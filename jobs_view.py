import threading
import time
from dataclasses import dataclass
from typing import Callable

from gi.repository import GLib, Gio, Gtk, Pango
import logging

from nihao.k8s import K8s

from utils import action_handler

log = logging.getLogger(__name__)


@dataclass
class Job:
    priority: str
    name: str
    state: str
    node: str


class JobFilter:
    def __init__(self):
        self.visible_fns = []
        self.refresh_fns = []

    def is_visible(self, job: Job):
        return all(fn(job) for fn in self.visible_fns)

    def refresh(self):
        for fn in self.refresh_fns:
            fn()

    def add_predicate(self, fn: Callable):
        self.visible_fns.append(fn)


class JobsView(Gtk.Bin):
    def __init__(self, job_filter: JobFilter):
        super().__init__()
        self.filters = []

        self.list_store = Gtk.ListStore(str, str, str, str)

        def is_job_visible(model, iter, _):
            job = Job(*model[iter])
            return job_filter.is_visible(job)

        self.store_filter = self.list_store.filter_new()
        self.store_filter.set_visible_func(is_job_visible)

        job_filter.refresh_fns.append(self.update)

        self.tree_view = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.store_filter))
        for i, column_title in enumerate(["Priority", "Name", "State", "Node"]):
            renderer = Gtk.CellRendererText(single_paragraph_mode=True,
                                            ellipsize=Pango.EllipsizeMode.START,
                                            family='Monospace')
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            if i == 1:
                column.set_expand(True)
                column.set_min_width(320)
            else:
                column.set_min_width(80)
            self.tree_view.append_column(column)

        scroll_area = Gtk.ScrolledWindow()
        scroll_area.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_area.add(self.tree_view)
        self.add(scroll_area)

    def grab_focus(self):
        self.tree_view.grab_focus()

    def update(self, jobs_list: list = None):
        if jobs_list is not None:
            log.info("Updating jobs list...")
            jobs_dict = {j.name: j for j in jobs_list}

            for it in self.list_store:
                job = jobs_dict.pop(it[1], None)
                if job is None:
                    self.list_store.remove(it.iter)
                else:
                    self.list_store[it.iter] = [job.priority, job.name, job.phase, job.node]

            for job in jobs_dict.values():
                self.list_store.append([job.priority, job.name, job.phase, job.node])
        else:
            log.info("Refreshing jobs list...")

        self.store_filter.refilter()

        if len(self.list_store) > 0 and self.tree_view.get_selection().count_selected_rows() == 0:
            self.tree_view.get_selection().select_path(0)

    def setup_update_actions(self, k8s: K8s, action_group: Gio.SimpleActionGroup):
        def update_jobs():
            def fn():
                jobs_list = k8s.get_jobs_info()
                GLib.idle_add(lambda: self.update(jobs_list))

            threading.Thread(target=fn, daemon=True).start()

        def update_jobs_periodic_task():
            while True:
                jobs_list = k8s.get_jobs_info()
                GLib.idle_add(lambda: self.update(jobs_list))
                time.sleep(8.)

        update_jobs_action = Gio.SimpleAction.new("update", None)
        update_jobs_action.connect("activate", action_handler(update_jobs))

        action_group.add_action(update_jobs_action)
        threading.Thread(target=update_jobs_periodic_task, daemon=True).start()
