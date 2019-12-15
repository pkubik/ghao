from nihao.k8s import K8s

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

k8s = K8s()
jobs_list = k8s.get_jobs_info()
username = 'lukasztreszczotko'


class NihaoWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Nihao | 你好")

        self.display_all = True

        self.set_default_size(640, 640)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.list_store = Gtk.ListStore(str, str, str, str)
        for job in jobs_list:
            self.list_store.append([job.priority, job.name, job.phase, job.node])

        self.language_filter = self.list_store.filter_new()
        self.language_filter.set_visible_func(self.is_job_visible)

        self.tree_view = Gtk.TreeView.new_with_model(Gtk.TreeModelSort(model=self.language_filter))
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
            self.tree_view.append_column(column)

        checkbox = Gtk.CheckButton(label="Display all")

        def checkbox_toggled(widget):
            self.display_all = widget.get_active()
            self.language_filter.refilter()

        checkbox.connect("toggled", checkbox_toggled)
        checkbox.set_active(True)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(False)
        self.add(self.grid)

        self.scroll_area = Gtk.ScrolledWindow()
        self.scroll_area.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll_area.set_vexpand(True)
        self.scroll_area.add(self.tree_view)
        self.grid.attach(self.scroll_area, 0, 0, 1, 1)

        self.grid.attach_next_to(checkbox, self.scroll_area, Gtk.PositionType.BOTTOM, 1, 1)

        self.show_all()

    def is_job_visible(self, model, iter, _):
        if self.display_all:
            return True
        else:
            return username in model[iter][1]


win = NihaoWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
