from gi.repository import Gtk, Pango


class JobsView(Gtk.Bin):
    def __init__(self):
        super().__init__()
        self.filters = []

        self.list_store = Gtk.ListStore(str, str, str, str)

        def is_job_visible(model, iter, _):
            return all(f(model[iter]) for f in self.filters)

        self.job_filter = self.list_store.filter_new()
        self.job_filter.set_visible_func(is_job_visible)
        tree_view = Gtk.TreeView(model=Gtk.TreeModelSort(model=self.job_filter))
        self.add(tree_view)
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
