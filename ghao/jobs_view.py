from dataclasses import dataclass
from typing import Callable, List

from gi.repository import Gtk, Gdk, Pango
import logging

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


def children_generator(store: Gtk.TreeStore, parent_iter: Gtk.TreeIter):
    child_iter = store.iter_children(parent_iter)
    while child_iter is not None:
        next_iter = store.iter_next(child_iter)  # get next iterator before yield to protect against item removal
        yield child_iter
        child_iter = next_iter


class JobsView(Gtk.Bin):
    def __init__(self, job_filter: JobFilter):
        super().__init__()
        self.filters = []

        self.tree_store = Gtk.TreeStore(str, str, str, str)

        def is_job_visible(model, iter, _):
            job = Job(*model[iter])
            return job_filter.is_visible(job)

        self.store_filter = self.tree_store.filter_new()
        self.store_filter.set_visible_func(is_job_visible)

        job_filter.refresh_fns.append(self.update)

        self.tree_view = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.store_filter))
        self.tree_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.tree_view.set_property("enable-grid-lines", True)
        self.tree_view.set_property("enable-tree-lines", True)
        self.tree_view.set_property("enable-search", False)
        for i, column_title in enumerate(["Priority", "Name", "State", "Node"]):
            renderer = Gtk.CellRendererText(single_paragraph_mode=True,
                                            ellipsize=Pango.EllipsizeMode.START,
                                            family='Monospace')
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            if i == 0:
                column.set_min_width(110)
            elif i == 1:
                column.set_expand(True)
                column.set_min_width(300)
            else:
                column.set_min_width(80)
            self.tree_view.append_column(column)

        scroll_area = Gtk.ScrolledWindow()
        scroll_area.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_area.add(self.tree_view)
        self.add(scroll_area)

    def grab_focus(self):
        self.tree_view.grab_focus()

    def update(self, jobs_list: List = None):
        if jobs_list is not None:
            log.info("Updating jobs list...")
            jobs_dict = {j.name: j for j in jobs_list}

            for it in self.tree_store:
                job = jobs_dict.pop(it[1], None)
                if job is None:
                    self.tree_store.remove(it.iter)
                else:
                    self.tree_store[it.iter] = [job.priority, job.name, job.phase, job.node]
                    pods_dict = {p.name: p for p in job.pods}
                    for child_iter in children_generator(self.tree_store, it.iter):
                        pod_name = self.tree_store[child_iter][1]
                        pod = pods_dict.pop(pod_name, None)
                        if pod is None:
                            self.tree_store.remove(child_iter)
                        else:
                            self.tree_store[child_iter] = [pod.priority, pod.name, pod.phase, pod.node]

                    for pod in pods_dict.values():
                        self.tree_store.append(it.iter, [pod.priority, pod.name, pod.phase, pod.node])

            for job in jobs_dict.values():
                piter = self.tree_store.append(None, [job.priority, job.name, job.phase, job.node])
                for pod in job.pods:
                    self.tree_store.append(piter, [pod.priority, pod.name, pod.phase, pod.node])
        else:
            log.info("Refreshing jobs list...")

        self.store_filter.refilter()

        if len(self.tree_store) > 0:
            selection = self.tree_view.get_selection()
            if selection.count_selected_rows() == 0:
                selection.select_path(0)

    def add_right_click_handler(self, fn):
        def button_press_handler(_view, event):
            # Unselect right-clicked row so it is selected again by the parent code
            # (to prevent unselecting by the parent code)
            if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
                path = self.tree_view.get_path_at_pos(event.x, event.y)[0]
                self.tree_view.get_selection().unselect_path(path)

        def button_release_handler(_view, event):
            if event.type == Gdk.EventType.BUTTON_RELEASE and event.button == 3:
                click_location = Gdk.Rectangle()
                click_location.x = event.x
                click_location.y = event.y + 24  # need some offset because the coordinates are shifted, dunno
                fn(click_location)

        self.tree_view.connect('button-press-event', button_press_handler)
        self.tree_view.connect('button-release-event', button_release_handler)

    def selected_jobs(self) -> List[Job]:
        selection = self.tree_view.get_selection()
        model, path_list = selection.get_selected_rows()
        return [Job(*model[model.get_iter(path)]) for path in path_list]
