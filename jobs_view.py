import threading
import time

from gi.repository import GLib, Gio, Gtk, Pango
import logging

from nihao.k8s import K8s


log = logging.getLogger(__name__)


def action_handler(fn):
    def handler(_action, _params):
        return fn()
    return handler


class JobsView(Gtk.Bin):
    def __init__(self):
        super().__init__()
        self.filters = []

        self.list_store = Gtk.ListStore(str, str, str, str)

        def is_job_visible(model, iter, _):
            return all(f(model[iter]) for f in self.filters)

        self.job_filter = self.list_store.filter_new()
        self.job_filter.set_visible_func(is_job_visible)
        tree_view = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.job_filter))
        self.add(tree_view)
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
            tree_view.append_column(column)

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

        self.job_filter.refilter()

    def add_filter(self, filter_):
        self.filters.append(filter_)

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
                time.sleep(5.0)

        update_jobs_action = Gio.SimpleAction.new("update", None)
        update_jobs_action.connect("activate", action_handler(update_jobs))

        action_group.add_action(update_jobs_action)
        threading.Thread(target=update_jobs_periodic_task, daemon=True).start()
