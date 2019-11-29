import logging
from sqlalchemy import or_

from io import BytesIO

import xlsxwriter
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.data import get_report_filename
from wise.msfd.gescomponents import get_features, get_parameters
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import db_objects_to_dict, RawRow, timeit

from .base import BaseNatSummaryView

logger = logging.getLogger('wise.msfd')


class NatSummaryTable(BaseNatSummaryView):
    """ Base class for tables """


class ReportingHistoryTable(BaseNatSummaryView):
    """ Reporting history and performance
    """

    template = ViewPageTemplateFile('pt/report-history-table.pt')

    def __init__(self, context, request):
        super(ReportingHistoryTable, self).__init__(context, request)

        # self.country_code = context.country_code
        # self.translate_value = context.translate_value
        self.data = self.get_reporting_history_data()

    @db.use_db_session('2018')
    def get_reporting_history_data(self):
        mc = sql2018.ReportingHistory

        _, res = db.get_all_records(
            mc,
            mc.CountryCode == self.country_code
        )

        res = db_objects_to_dict(res)

        return res

    def __call__(self):
        data = self.data
        rows = []

        for item in data:
            for name in item.keys():
                values = []

                for inner in data:
                    values.append(inner[name])

                raw_values = []
                vals = []
                for v in values:
                    raw_values.append(v)
                    vals.append(self.context.translate_value(
                        name, v, self.country_code))

                # values = [self.context.translate_value(name, value=v)
                #           for v in values]

                row = RawRow(name, vals, raw_values)
                rows.append(row)

            break       # only need the "first" row

        return self.template(data=rows)


class NationalSummaryView(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    # @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="National summary report: {}".format(
                self.country_name,
            )
        )

        tables = [
            report_header,
            ReportingHistoryTable(self, self.request),
        ]

        template = self.template

        return template(tables=tables)

    def __call__(self):
        report_html = self.render_reportdata()
        self.report_html = report_html

        @timeit
        def render_html():
            return self.index()

        return render_html()
