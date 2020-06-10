from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .base import BaseRegSummaryView


class SimpleTable(BaseRegSummaryView):
    template = ViewPageTemplateFile('pt/simple-report-table.pt')
    show_header = False

    def __init__(self, context, request, header, rows, title=None):
        super(SimpleTable, self).__init__(context, request)

        self.header = header
        self.title = title
        self.rows = rows

    def __call__(self):

        return self.template(title=self.title, rows=self.rows,
                             header=self.header)
