import gi
gi.require_version('Gtk', '3.0')

from utils import action_handler

import logging
import os

from headerbar import HeaderBar
from nihao.k8s import K8s

from gi.repository import Gio, Gtk
from jobs_view import JobsView

logging.basicConfig(level=os.environ.get("NIHAO_LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)


MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="job-menu">
    <section>
        <item>
            <attribute name="label">Describe</attribute>
            <attribute name="action">jobs.describe</attribute>
        </item>
        <item>
            <attribute name="label">Copy dir</attribute>
            <attribute name="action">jobs.yank</attribute>
        </item>
        <item>
            <attribute name="label">Kill</attribute>
            <attribute name="action">jobs.kill</attribute>
        </item>
    </section>
  </menu>
</interface>
"""


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

    setup_popover_menu(jobs_view)

    def describe_job():
        log.info(f"Describing jobs: {jobs_view.selected_jobs()}")

    describe_action = Gio.SimpleAction.new("describe", None)
    describe_action.connect("activate", action_handler(describe_job))
    action_group.add_action(describe_action)

    def yank_job():
        log.info(f"Copying directory of jobs: {jobs_view.selected_jobs()}")

    yank_action = Gio.SimpleAction.new("yank", None)
    yank_action.connect("activate", action_handler(yank_job))
    action_group.add_action(yank_action)

    def kill_job():
        log.info(f"Killing jobs: {jobs_view.selected_jobs()}")

    kill_action = Gio.SimpleAction.new("kill", None)
    kill_action.connect("activate", action_handler(kill_job))
    action_group.add_action(kill_action)

    window.show_all()

    return window


def setup_popover_menu(jobs_view: JobsView):
    builder = Gtk.Builder.new_from_string(MENU_XML, -1)
    menu = builder.get_object("job-menu")
    popover = Gtk.Popover.new_from_model(jobs_view, menu)
    popover.set_modal(True)

    def popup_right_click_menu(clicked_rect):
        popover.set_pointing_to(clicked_rect)
        popover.popup()

    jobs_view.add_right_click_handler(popup_right_click_menu)


class Application(Gtk.Application):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="com.tcl.nihao", **kwargs)
        self.window = None

    def _create_window(self):
        self.window = create_window()
        self.add_window(self.window)

        self.set_accels_for_action("jobs.update", ["<Control>r"])
        self.set_accels_for_action("jobs.search", ["<Control>f"])
        self.set_accels_for_action("jobs.describe", ["<Control>s"])
        self.set_accels_for_action("jobs.yank", ["<Control>y"])
        self.set_accels_for_action("jobs.kill", ["<Control>k"])
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
