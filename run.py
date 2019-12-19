import logging
import os

from nihao.k8s import K8s

import threading
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk
from jobs_view import JobsView

logging.basicConfig(level=os.environ.get("NIHAO_LOGLEVEL", "INFO"))


class State:
    def __init__(self):
        self.k8s = K8s()
        self.username = 'lukasztreszczotko'
        self.is_filtered_by_user = True


def create_window():
    state = State()
    window = Gtk.ApplicationWindow(title="Nihao | 你好")
    action_group = Gio.SimpleActionGroup()
    window.insert_action_group("jobs", action_group)

    window.set_default_size(640, 640)
    window.set_position(Gtk.WindowPosition.CENTER)

    jobs_view = JobsView()
    user_filter_checkbox = create_user_filter_checkbox(state, jobs_view)
    layout = create_layout(jobs_view, user_filter_checkbox)

    jobs_view.setup_update_actions(state.k8s, action_group)

    window.add(layout)
    window.show_all()

    return window


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

    def _create_window(self):
        self.window = create_window()
        self.add_window(self.window)

        self.set_accels_for_action("jobs.update", ["<Control>r"])

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self._create_window()

    def do_activate(self):
        if not self.window:
            self._create_window()

        self.window.present()

    def on_quit(self, action, param):
        self.quit()


def main():
    app = Application()
    app.run()


if __name__ == '__main__':
    main()
