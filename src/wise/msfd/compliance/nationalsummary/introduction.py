# -*- coding: utf-8 -*-

import logging
from collections import defaultdict, namedtuple
from datetime import datetime

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql2018
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from lpod.document import odf_new_document
from lpod.heading import odf_create_heading

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


class AssessmentAreas2018(BaseNatSummaryView):
    """ Implementation of 1.3 Assessment areas (Marine Reporting Units) """

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
            description = row.nameText or row.nameTxtInt
            translation = get_translated(description, self.country_code) or ""
            self._translatable_values.append(description)

            res.append((row.Region, row.spZoneType, row.thematicId,
                        description, translation))

        return res

    def __call__(self):
        data = self.get_data()

        return self.template(data=data)


class ReportingHistoryTable(BaseNatSummaryView):
    """ Reporting history and performance
    """

    template = ViewPageTemplateFile('pt/report-history-compound-table.pt')

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


class Introduction(BaseNatSummaryView):
    """ Implementation of section 1.Introduction """

    template = ViewPageTemplateFile('pt/introduction.pt')

    @property
    def document_title(self):
        text = u"""Marine Strategy Framework Directive - Article 12 technical 
        assessment of the 2018 updates of Articles 8, 9 and 10"""

        return text

    def header_table_rows(self):
        rows = [
            (u'Country', self.country_name),
            (u'Date', self.date),
            (u'Status', self.status),
            (u'Logos', ""),
            (u'Disclaimer', self.disclaimer),
            (u'Authors', self.authors),
            (u'Contract', self.contract),
            (u'Contact', self.contact)
        ]

        return rows

    @property
    def disclaimer(self):
        text = u"""The opinions expressed in this document are the sole 
        responsibility of the authors and do not necessarily represent the 
        official position of the European Commission."""

        return text

    @property
    def authors(self):
        text = u"""Paola Banfi, Guillermo Gea, Lucille Labayle, David Landais, 
        Melanie Muro, Goncalo Moreira, Alicia McNeil, and Imbory Thomas. 
        The main authors are Richard White (D1, 4, 6), Elena San Martin (D2), 
        Suzannah Walmsley (D3), William Parr (D5), Christophe Le Visage (D7),
        Norman Green (D8 and 9), Annemie Volckaert (D10) and Frank Thomsen 
        (D11)."""

        return text

    @property
    def contract(self):
        text = u"""No 11.0661/ENV/2018/791580/SER/ENV.C.2."""

        return text

    @property
    def contact(self):
        text = u"""Milieu Consulting Sprl, Chaussée de Charleroi 112, B-1060, 
        Brussels. Tel: +32 2 506 1000; fax : +32 2 514 3603; 
        e-mail: melanie.muro@milieu.be and paola.banfi@milieu.be; 
        web address: www.milieu.be."""

        return text

    @timeit
    def reporting_history(self):
        view = ReportingHistoryTable(self, self.request)

        return view()

    @property
    def date(self):
        date = datetime.now().strftime("%d %B %Y")

        return date

    @property
    def status(self):
        status = "Draft"

        return status

    @property
    def scope_of_marine_waters(self):
        output = self.get_field_value('scope_of_marine_waters')

        return output

    @property
    def assessment_methodology(self):
        output = self.get_field_value('assessment_methodology')

        return output

    @property
    @timeit
    def assessment_areas(self):
        view = AssessmentAreas2018(self, self.request)

        return view()

    def get_odt_data(self):
        res = []

        title = odf_create_heading(1, u"Basic commercial document")
        res.append(title)

        return res

    def __call__(self):

        @timeit
        def render_introduction():
            return self.template()

        return render_introduction()