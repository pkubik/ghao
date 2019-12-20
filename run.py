import gi
gi.require_version('Gtk', '3.0')

import logging
import os

from headerbar import HeaderBar
from nihao.k8s import K8s

from gi.repository import Gio, Gtk
from jobs_view import JobsView

logging.basicConfig(level=os.environ.get("NIHAO_LOGLEVEL", "INFO"))


class State:
    def __init__(self):
        self.k8s = K8s()
        self.username = 'maciek'
        self.is_filtered_by_user = True


def create_window():
    state = State()
    title = "Nihao | 你好"
    window = Gtk.ApplicationWindow(title=title)
    action_group = Gio.SimpleActionGroup()
    window.insert_action_group("jobs", action_group)

    window.set_default_size(640, 640)
    window.set_position(Gtk.WindowPosition.CENTER)

    jobs_view = JobsView()
    layout = create_main_layout(jobs_view)
    window.add(layout)

    header = HeaderBar(title, state.username, jobs_view)
    window.set_titlebar(header)

    jobs_view.setup_update_actions(state.k8s, action_group)

    window.show_all()

    return window


def create_main_layout(jobs_view: JobsView):
    scroll_area = Gtk.ScrolledWindow()
    scroll_area.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll_area.set_vexpand(True)
    scroll_area.add(jobs_view)

    return scroll_area


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
