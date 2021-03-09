from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .base import BaseRegSummaryView


class SimpleTable(BaseRegSummaryView):
    template = ViewPageTemplateFile('pt/simple-report-table.pt')
    show_header = False

    def __init__(self, context, request, rows, header=None, title=None,
                 align_right=True):
        super(SimpleTable, self).__init__(context, request)

        self.header = header
        self.title = title
        self.rows = rows
        self.align_right = align_right

    def __call__(self):

        return self.template(title=self.title, rows=self.rows,
                             header=self.header)
