import gi

from utils import action_handler

gi.require_version('Gtk', '3.0')

import logging
import os

from headerbar import HeaderBar
from nihao.k8s import K8s

from gi.repository import Gio, Gtk
from jobs_view import JobsView

logging.basicConfig(level=os.environ.get("NIHAO_LOGLEVEL", "INFO"))


def create_window():
    username = 'maciek'
    k8s = K8s()

    title = "Nihao | 你好"
    window = Gtk.ApplicationWindow(title=title)
    action_group = Gio.SimpleActionGroup()
    window.insert_action_group("jobs", action_group)

    window.set_default_size(640, 640)
    window.set_position(Gtk.WindowPosition.CENTER)

    header = HeaderBar(title, username)
    window.set_titlebar(header)
    header.setup_actions(action_group)

    jobs_view = JobsView(header.job_filter)
    window.add(jobs_view)
    jobs_view.grab_focus()
    jobs_view.setup_update_actions(k8s, action_group)

    focus_jobs_action = Gio.SimpleAction.new("focus", None)
    focus_jobs_action.connect("activate", action_handler(jobs_view.grab_focus))
    action_group.add_action(focus_jobs_action)

    window.show_all()

    return window


class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.tcl.nihao", **kwargs)
        self.window = None

    def _create_window(self):
        self.window = create_window()
        self.add_window(self.window)

        self.set_accels_for_action("jobs.update", ["<Control>r"])
        self.set_accels_for_action("jobs.search", ["<Control>f"])
        self.set_accels_for_action("jobs.focus", ["Escape"])

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
