from gi.repository import Gtk

from jobs_view import JobsView


def create_user_filter_checkbox(username: str, jobs_view: JobsView) -> Gtk.CheckButton:
    # Filter object should be probably separated from the filter checkbox

    checkbox = Gtk.CheckButton(label="Filter by user")

    def checkbox_toggled(_widget):
        jobs_view.update()

    def filter_job(fields):
        return not checkbox.get_active() or username in fields[1]

    jobs_view.add_filter(filter_job)

    checkbox.connect("toggled", checkbox_toggled)
    checkbox.set_active(True)

    return checkbox


class SearchBox(Gtk.Entry):
    def __init__(self, jobs_view: JobsView):
        super().__init__(expand=True)
        self.set_placeholder_text("<Ctrl> + F")

        def text_changed(_widget):
            jobs_view.update()

        def filter_job(fields):
            words = self.get_text().split()
            return all(word in fields[1] for word in words)

        self.connect("changed", text_changed)
        jobs_view.add_filter(filter_job)


class HeaderBar(Gtk.HeaderBar):
    def __init__(self, title: str, username: str, jobs_view: JobsView):
        super().__init__()
        self.set_show_close_button(True)
        self.set_vexpand(True)

        title_text = Gtk.Label()
        title_text.set_markup(f'   <b>{title}</b>   ')
        entry = SearchBox(jobs_view)
        self.set_custom_title(entry)

        self.pack_start(title_text)

        # Note: dependency on JobsView is quite ridiculous and should be removed in the future
        checkbox = create_user_filter_checkbox(username, jobs_view)
        self.pack_end(checkbox)
