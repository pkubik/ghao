from gi.repository import Gtk, Gio

from jobs_view import JobFilter
from utils import action_handler


def create_user_filter_checkbox(username: str, job_filter: JobFilter) -> Gtk.CheckButton:
    checkbox = Gtk.CheckButton(label="Filter by user")

    def filter_job(fields):
        return not checkbox.get_active() or username in fields.name

    job_filter.add_predicate(filter_job)

    def checkbox_toggled(_widget):
        job_filter.refresh()

    checkbox.connect("toggled", checkbox_toggled)
    checkbox.set_active(True)

    return checkbox


class SearchBox(Gtk.Entry):
    def __init__(self, job_filter: JobFilter):
        super().__init__(expand=True)
        self.set_placeholder_text("<Ctrl> + F")

        def filter_job(fields):
            words = self.get_text().split()
            return all(word in fields.name for word in words)

        job_filter.add_predicate(filter_job)

        def text_changed(_widget):
            job_filter.refresh()

        self.connect("changed", text_changed)


class HeaderBar(Gtk.HeaderBar):
    def __init__(self, title: str, username: str):
        super().__init__()
        self.set_show_close_button(True)
        self.set_vexpand(True)

        self.job_filter = JobFilter()

        title_text = Gtk.Label()
        title_text.set_markup(f'   <b>{title}</b>   ')
        self.entry = SearchBox(self.job_filter)
        self.set_custom_title(self.entry)

        self.pack_start(title_text)

        checkbox = create_user_filter_checkbox(username, self.job_filter)
        self.pack_end(checkbox)

    def setup_actions(self, action_group: Gio.ActionGroup):
        update_jobs_action = Gio.SimpleAction.new("search", None)
        update_jobs_action.connect("activate", action_handler(self.entry.grab_focus))
        action_group.add_action(update_jobs_action)
