from nihao.k8s import K8s

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango


class State:
    def __init__(self):
        self.k8s = K8s()
        self.jobs_list = self.k8s.get_jobs_info()
        self.username = 'lukasztreszczotko'
        self.is_filtered_by_user = True


def create_window():
    state = State()
    window = Gtk.Window(title="Nihao | 你好")

    window.set_default_size(640, 640)
    window.set_position(Gtk.WindowPosition.CENTER)

    jobs_view, job_filter = create_jobs_view(state)
    user_filter_checkbox = create_user_filter_checkbox(state, job_filter)
    layout = create_layout(jobs_view, user_filter_checkbox)

    window.add(layout)
    window.show_all()
    window.connect("destroy", Gtk.main_quit)

    return window


def create_layout(jobs_view: Gtk.TreeView, user_filter_checkbox: Gtk.CheckButton):
    grid = Gtk.Grid()
    grid.set_column_homogeneous(True)
    grid.set_row_homogeneous(False)

    scroll_area = Gtk.ScrolledWindow()
    scroll_area.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll_area.set_vexpand(True)
    scroll_area.add(jobs_view)
    grid.attach(scroll_area, 0, 0, 1, 1)

    grid.attach_next_to(user_filter_checkbox, scroll_area, Gtk.PositionType.BOTTOM, 1, 1)

    return grid


def create_user_filter_checkbox(state: State, job_filter: Gtk.TreeModelFilter) -> Gtk.CheckButton:
    checkbox = Gtk.CheckButton(label="Filter by user")

    def checkbox_toggled(widget):
        state.is_filtered_by_user = widget.get_active()
        job_filter.refilter()

    checkbox.connect("toggled", checkbox_toggled)
    checkbox.set_active(True)

    return checkbox


def create_jobs_view(state: State) -> (Gtk.TreeView, Gtk.TreeModelFilter):
    list_store = Gtk.ListStore(str, str, str, str)
    for job in state.jobs_list:
        list_store.append([job.priority, job.name, job.phase, job.node])

    def is_job_visible(model, iter, _):
        if state.is_filtered_by_user:
            return state.username in model[iter][1]
        else:
            return True

    job_filter = list_store.filter_new()
    job_filter.set_visible_func(is_job_visible)
    tree_view = Gtk.TreeView.new_with_model(Gtk.TreeModelSort(model=job_filter))
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
    return tree_view, job_filter


def main():
    _ = create_window()
    Gtk.main()


if __name__ == '__main__':
    main()
