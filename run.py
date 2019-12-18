from nihao.k8s import K8s

import threading
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Pango


class State:
    def __init__(self):
        self.k8s = K8s()
        self.username = 'lukasztreszczotko'
        self.is_filtered_by_user = True


def create_window(app: Gtk.Application):
    state = State()
    window = Gtk.ApplicationWindow(application=app, title="Nihao | 你好")
    window.insert_action_group("app", app)

    window.set_default_size(640, 640)
    window.set_position(Gtk.WindowPosition.CENTER)

    jobs_view = JobsView()
    user_filter_checkbox = create_user_filter_checkbox(state, jobs_view)
    layout = create_layout(jobs_view, user_filter_checkbox)

    jobs_view.update()

    window.add(layout)
    window.show_all()

    def update_jobs(jobs_list=None):
        print('Updating jobs')
        jobs_view.update(jobs_list)

    def update_jobs_task():
        while True:
            jobs_list = state.k8s.get_jobs_info()
            GLib.idle_add(update_jobs, jobs_list)
            time.sleep(5.0)

    update_jobs_action = Gio.SimpleAction.new("update_jobs", None)
    update_jobs_action.connect("activate", lambda obj, action: update_jobs())

    app.add_action(update_jobs_action)
    app.set_accels_for_action("app.update_jobs", ["<Control>r"])

    thread = threading.Thread(target=update_jobs_task)
    thread.daemon = True
    thread.start()

    return window


class JobsView(Gtk.TreeView):
    def __init__(self):
        self.filters = []

        self.list_store = Gtk.ListStore(str, str, str, str)

        def is_job_visible(model, iter, _):
            return all(f(model[iter]) for f in self.filters)

        self.job_filter = self.list_store.filter_new()
        self.job_filter.set_visible_func(is_job_visible)
        super().__init__(model=Gtk.TreeModelSort(model=self.job_filter))
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
            self.append_column(column)

    def update(self, jobs_list: list = None):
        if jobs_list is not None:
            jobs_dict = {j.name: j for j in jobs_list}

            for it in self.list_store:
                job = jobs_dict.pop(it[1], None)
                if job is None:
                    self.list_store.remove(it.iter)
                else:
                    self.list_store[it.iter] = [job.priority, job.name, job.phase, job.node]

            for job in jobs_dict.values():
                self.list_store.append([job.priority, job.name, job.phase, job.node])

        self.job_filter.refilter()

    def add_filter(self, filter_):
        self.filters.append(filter_)


def create_user_filter_checkbox(state: State, jobs_view: JobsView) -> Gtk.CheckButton:
    checkbox = Gtk.CheckButton(label="Filter by user")

    def checkbox_toggled(widget):
        state.is_filtered_by_user = widget.get_active()
        jobs_view.update()

    def filter_job(fields):
        return not state.is_filtered_by_user or state.username in fields[1]

    jobs_view.add_filter(filter_job)

    checkbox.connect("toggled", checkbox_toggled)
    checkbox.set_active(True)

    return checkbox


def create_layout(jobs_view: JobsView, user_filter_checkbox: Gtk.CheckButton):
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


class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.tcl.nihao", **kwargs)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.window = create_window(self)
        self.add_window(self.window)

    def do_activate(self):
        if not self.window:
            self.window = create_window(self)
            self.add_window(self.window)

        self.window.present()

    def on_quit(self, action, param):
        self.quit()


def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
