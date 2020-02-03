import logging
from collections import defaultdict, namedtuple
from datetime import datetime

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql2018
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from .base import BaseNatSummaryView
from .odt_utils import (create_heading, create_paragraph, create_table,
                        DOCUMENT_TITLE, STYLES)

logger = logging.getLogger('wise.msfd')


def compoundrow(self, title, rows, show_header=True):
    """ Function to return a compound row for 2012 report"""

    FIELD = namedtuple("Field", ["name", "title"])
    field = FIELD(title, title)

    return CompoundRow(self, self.request, field, rows, show_header)


class CompoundRow(TemplateMixin):
    template = ViewPageTemplateFile('pt/compound-row.pt')

    def __init__(self, context, request, field, rows, show_header=True):
        self.context = context
        self.request = request
        self.field = field
        self.rows = rows
        self.rowspan = len(rows)
        self.show_header = show_header


class AssessmentAreas2018(BaseNatSummaryView):
    """ Implementation of 1.3 Reporting areas (Marine Reporting Units) """

    template = ViewPageTemplateFile('pt/assessment-areas.pt')

    @db.use_db_session('2018')
    def get_data(self):
        mapper_class = sql2018.MRUsPublication
        res = []

        # for better query speed we get only these columns
        col_names = ('Country', 'Region', 'thematicId', 'nameTxtInt',
                     'nameText', 'spZoneType', 'legisSName', 'Area')
        columns = [getattr(mapper_class, name) for name in col_names]

        count, data = db.get_all_specific_columns(
            columns,
            mapper_class.Country == self.country_code
        )

        for row in data:
            description = row.nameText or row.nameTxtInt or ""
            translation = get_translated(description, self.country_code) or ""
            if not translation:
                retrieve_translation(self.country_code, description)

            self._translatable_values.append(description)

            res.append((row.Region, row.spZoneType, row.thematicId,
                        description, translation))

        return res

    def __call__(self):
        data = self.get_data()

        self.areas_data = data

        return self.template(data=data)


class ReportingHistoryTable(BaseNatSummaryView):
    """ Implementation for the reporting history table
    """

    template = ViewPageTemplateFile('pt/report-history-compound-table.pt')
    show_header = False

    def __init__(self, context, request):
        super(ReportingHistoryTable, self).__init__(context, request)

        self.data = self.get_reporting_history_data()

    @db.use_db_session('2018')
    def get_reporting_history_data(self):
        obligation = 'MSFD reporting on Initial Assessments (Art. 8), ' \
                     'Good Environmental Status (Art.9), Env. targets & ' \
                     'associated indicators (Art.10) & related reporting on ' \
                     'geographic areas, regional cooperation and metadata.'
        mc = sql2018.ReportingHistory

        _, res = db.get_all_records(
            mc,
            mc.CountryCode == self.country_code,
            mc.ReportingObligation == obligation
        )

        res = db_objects_to_dict(res)

        return res

    def location_url(self, location, filename):
        tmpl = "<a href={} target='_blank'>{}</a>"
        location = location.replace(filename, '')

        return location
        # return tmpl.format(location, location)

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
            compoundrow(self, obligation, self.get_article_row(obligation),
                        show_header=self.show_header)

            for obligation in obligations
        ]

        self.report_hystory_data = self.allrows[0].rows

        return self.template(rows=self.allrows)


class ReportedInformationTable(BaseNatSummaryView):
    """ Alternate implementation for the reporting history table
    Reads data from sql2018.ReportedInformation
    """

    template = ViewPageTemplateFile('pt/report-history-compound-table.pt')
    show_header = False

    def __init__(self, context, request):
        super(ReportedInformationTable, self).__init__(context, request)

        self.data = self.get_reporting_history_data()

    @db.use_db_session('2018')
    def get_reporting_history_data(self):

        mc = sql2018.ReportedInformation

        _, res = db.get_all_records(
            mc,
            mc.CountryCode == self.country_code,
        )

        res = db_objects_to_dict(res)

        return res

    def location_url(self, location, filename):
        tmpl = "<a href={} target='_blank'>{}</a>"
        location = location.replace(filename, '')

        # return location
        return tmpl.format(location, location)

    def format_date(self, date):
        if not date:
            return date

        # formatted = date.strftime('%m/%d/%Y')
        formatted = date.date()

        return formatted

    def headers(self):
        headers = (
            'Files available', 'Access to reports',
            'Report due', 'Report received', 'Reporting delay (days)'
        )

        return headers

    def get_article_rows(self):
        # Group the data by envelope, report due, report date and report delay
        data = self.data
        rows = []

        groups = defaultdict(list)

        for row in data:
            filename = row.get('ReportedFileLink').split('/')[-1]
            envelope = self.location_url(row.get('ReportedFileLink'), filename)

            # Article 18 files not relevant for this report, exclude them
            if 'art18' in envelope:
                continue

            report_due = datetime(year=2018, month=10, day=15).date()
            report_date = row.get('ReportingDate')
            report_delay = report_due - report_date
            k = (envelope, report_due, report_date, report_delay.days)

            groups[k].append(filename)

        for _k, filenames in groups.items():
            values = [
                ItemList(rows=filenames),  # Filenames
                _k[0],  # Envelope url
                _k[1],  # Report due
                _k[2],  # Report date
                _k[3]  # Report delay
            ]
            rows.append(values)

        sorted_rows = sorted(rows,
                             key=lambda _row: (_row[3], _row[1]),
                             reverse=True)

        return sorted_rows

    def __call__(self):
        self.allrows = [
            compoundrow(self, 'Row', self.get_article_rows(),
                        show_header=self.show_header)
        ]

        self.report_hystory_data = self.allrows[0].rows

        return self.template(rows=self.allrows)


class Introduction(BaseNatSummaryView):
    """ Implementation of section 1.Introduction """

    template = ViewPageTemplateFile('pt/introduction.pt')

    @property
    def document_title(self):
        text = u"Marine Strategy Framework Directive - Article 12 technical " \
               u"assessment of the 2018 updates of Articles 8, 9 and 10"

        return text

    @timeit
    def reporting_history(self):
        view = ReportedInformationTable(self, self.request)
        rendered_view = view()

        self.report_hystory_data = view.report_hystory_data

        return rendered_view

    @property
    def information_memberstate(self):
        text = u"Between July and October 2018, the Member States were due " \
               u"to submit updates of the assessment of their marine waters " \
               u"(Article 8), the determination of GES (Article 9) and the " \
               u"setting of environmental targets (Article 10), in " \
               u"accordance with Article 17 of the Marine Strategy " \
               u"Framework Directive (MSFD)."

        return text

    @property
    def scope_of_marine_waters(self):
        output = self.get_field_value('scope_of_marine_waters')

        return output

    @property
    def assessment_methodology(self):
        output = self.get_field_value('assessment_methodology')

        return output

    @property
    def assessment_areas_title(self):
        text = u"The table lists the Marine Reporting Units used for the " \
               u"2018 reporting on updates of Articles 8, 9 and 10."

        return text

    @property
    @timeit
    def assessment_areas(self):
        view = AssessmentAreas2018(self, self.request)
        rendered_view = view()

        self.assessment_areas_data = view.areas_data

        return rendered_view

    def get_odt_data(self, document):
        res = []

        title = create_paragraph(self.document_title,
                                 style=STYLES[DOCUMENT_TITLE])
        res.append(title)

        # 1. Introduction
        title = create_heading(1, u'Introduction')
        res.append(title)

        # 1.1 Reporting history
        title = create_heading(
            2, u'Information reported by the Member State'
        )
        res.append(title)
        p = create_paragraph(self.information_memberstate)
        res.append(p)

        # headers = ('Report format',' Files available', 'Access to reports',
        #            'Report due', 'Report received', 'Reporting delay (days)')
        headers = (
            'Files available', 'Access to reports',
            'Report due', 'Report received', 'Reporting delay (days)'
        )

        p = create_heading(3, u"Reporting history")
        res.append(p)
        table = create_table(document, self.report_hystory_data,
                             headers=headers)
        res.append(table)

        # 1.2 Marine waters
        title = create_heading(2, u"Member State's marine waters")
        res.append(title)
        text = self.get_transformed_richfield_text('scope_of_marine_waters')
        p = create_paragraph(text)
        res.append(p)

        # 1.3 Marine Unit Ids
        title = create_heading(
            2, u'Reporting areas (Marine Reporting Units)'
        )
        res.append(title)
        p = create_paragraph(self.assessment_areas_title)
        res.append(p)

        headers = ('Region', 'Zone Type', 'MarineUnitID',
                   'Marine Reporting Unit Description',
                   'Marine Reporting Unit Description (Translated)')
        table = create_table(document, self.assessment_areas_data,
                             headers=headers)
        res.append(table)

        # 1.4 Assessment methodology
        title = create_heading(2, u'Assessment methodology')
        res.append(title)
        text = self.get_transformed_richfield_text('assessment_methodology')
        p = create_paragraph(text)
        res.append(p)

        return res

    def __call__(self):

        @timeit
        def render_introduction():
            return self.template()

        return render_introduction()