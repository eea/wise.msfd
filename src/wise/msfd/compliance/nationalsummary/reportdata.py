from collections import defaultdict, namedtuple

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
from wise.msfd.utils import (db_objects_to_dict, ItemList, RawRow,
                             TemplateMixin, timeit)

from .base import BaseNatSummaryView

logger = logging.getLogger('wise.msfd')


def compoundrow(self, title, rows):
    """ Function to return a compound row for 2012 report"""

    FIELD = namedtuple("Field", ["name", "title"])
    field = FIELD(title, title)

    return CompoundRow(self, self.request, field, rows)


class CompoundRow(TemplateMixin):
    template = ViewPageTemplateFile('pt/compound-row.pt')

    def __init__(self, context, request, field, rows):
        self.context = context
        self.request = request
        self.field = field
        self.rows = rows
        self.rowspan = len(rows)


class NatSummaryTable(BaseNatSummaryView):
    """ Base class for tables """


class ReportingHistoryTable(BaseNatSummaryView):
    """ Reporting history and performance
    """

    template = ViewPageTemplateFile('pt/report-history-compound-table.pt')

    def __init__(self, context, request):
        super(ReportingHistoryTable, self).__init__(context, request)

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

    def location_url(self, location, filename):
        tmpl = "<a href={} target='_blank'>{}</a>"
        location = location.replace(filename, '')

        return tmpl.format(location, location)

    def format_date(self, date):
        if not date:
            return date

        # formatted = date.strftime('%m/%d/%Y')
        formatted = date.date()

        return formatted

    def headers(self):
        headers = (
            'Report format', 'Files available', 'Access to reports',
            'Report due', 'Report received', 'Reporting delay (days)'
        )

        return headers

    def get_article_row(self, obligation):
        # Group the data by report type, envelope, report due, report date
        # and report delay
        data = [
            row for row in self.data
            if row.get('ReportingObligation') == obligation

        ]
        rows = []

        groups = defaultdict(list)

        for row in data:
            filename = row.get('FileName')
            report_type = row.get('ReportType')
            envelope = self.location_url(row.get('LocationURL'), filename)
            report_due = self.format_date(row.get('DateDue'))
            report_date = self.format_date(row.get('DateReceived'))
            report_delay = row.get('ReportingDelay')
            k = (report_type, envelope, report_due, report_date, report_delay)

            groups[k].append(filename)

        for _k, filenames in groups.items():
            values = [
                _k[0],
                ItemList(rows=filenames),
                # ", ".join(filenames),
                _k[1],
                _k[2],
                _k[3],
                _k[4]
            ]
            rows.append(values)

        sorted_rows = sorted(rows, key=lambda _row: _row[4], reverse=True)

        return sorted_rows

    def __call__(self):
        data = self.data

        obligations = set([x.get('ReportingObligation') for x in data])

        self.allrows = [
            compoundrow(self, obligation, self.get_article_row(obligation))
            for obligation in obligations
        ]

        return self.template(rows=self.allrows)


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
