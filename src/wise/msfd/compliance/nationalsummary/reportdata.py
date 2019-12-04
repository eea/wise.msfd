import logging
from collections import defaultdict, namedtuple

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
# from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.data import get_report_filename
from wise.msfd.utils import (ItemList, TemplateMixin,  # RawRow,
                             db_objects_to_dict, timeit)

from ..nationaldescriptors.a7 import Article7
from ..nationaldescriptors.a34 import Article34
from ..nationaldescriptors.base import BaseView
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


class Article34Copy(Article34):
    """ Class to override the template """
    template = ViewPageTemplateFile('pt/report-data-secondary.pt')
    title = "Articles 3 & 4 Marine regions"


class Article7Copy(Article7):
    """ Class to override the template """
    template = ViewPageTemplateFile('pt/report-data-secondary.pt')
    title = "Article 7 Competent authorities"


class ArticleTable(BaseView):
    impl = {
        'Art3-4': Article34Copy,
        'Art7': Article7Copy,
    }

    is_translatable = True

    def __init__(self, context, request, article):
        super(ArticleTable, self).__init__(context, request)

        self._article = article
        self.klass = self.impl[article]

    year = '2012'

    @property
    def article(self):
        return self._article

    @property
    def descriptor(self):
        return 'Not linked'

    @property
    def muids(self):
        return []

    @property
    def country_region_code(self):
        return 'No region'

    def get_article_title(self, klass):
        tmpl = u"<h4>{}</h4>"
        title = klass.title

        return tmpl.format(title)

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file

        return get_report_filename(
            self.year, self.country_code, self.country_region_code,
            art or self.article, self.descriptor
        )

    def __call__(self):
        try:
            self.view = self.klass(
                self, self.request, self.country_code,
                self.country_region_code, self.descriptor, self.article,
                self.muids
            )
            rendered_view = self.view()
        except:
            rendered_view = 'Error getting report'

        return self.get_article_title(self.klass) + rendered_view


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
                _k[0],  # Report type
                ItemList(rows=filenames),  # Filenames
                _k[1],  # Envelope url
                _k[2],  # Report due
                _k[3],  # Report date
                _k[4]  # Report delay
            ]
            rows.append(values)

        sorted_rows = sorted(rows,
                             key=lambda _row: (_row[4], _row[2], _row[0]),
                             reverse=True)

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
        trans_edit_html = self.translate_view()()

        self.tables = [
            report_header,
            ArticleTable(self, self.request, 'Art7'),
            ArticleTable(self, self.request, 'Art3-4'),
            ReportingHistoryTable(self, self.request),
            trans_edit_html,
        ]

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'translate' in self.request.form:
            for table in self.tables:
                if (hasattr(table, 'is_translatable')
                        and table.is_translatable):
                    view = table.view
                    view.auto_translate()

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        @timeit
        def render_html():
            return self.index()

        return render_html()
