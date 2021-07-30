import logging
from collections import defaultdict, namedtuple
from datetime import datetime

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql2018
from wise.msfd.data import get_text_reports_2018
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, natural_sort_key, timeit)

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
    """ Implementation of 1.4 Reporting areas (Marine Reporting Units) """

    template = ViewPageTemplateFile('pt/assessment-areas.pt')

    @db.use_db_session('2018')
    def get_data(self):
        mapper_class = sql2018.MRUsPublication
        mc_mru_descr = sql2018.MarineReportingUnit
        res = []

        marine_waters_data = self.context._get_marine_waters_data()
        marine_waters_total = sum([
            x[2]
            for x in marine_waters_data
            if x[0] == self.country_code
         ])

        # for better query speed we get only these columns
        col_names = ('Country', 'rZoneId', 'thematicId', 'nameTxtInt',
                     'nameText', 'spZoneType', 'legisSName', 'Area')
        columns = [getattr(mapper_class, name) for name in col_names]

        count, data = db.get_all_specific_columns(
            columns,
            mapper_class.Country == self.country_code
        )
        mrus_needed = [x.thematicId for x in data]

        _, mru_descriptions = db.get_all_specific_columns(
            [mc_mru_descr.MarineReportingUnitId, mc_mru_descr.Description,
             mc_mru_descr.nameTxtInt, mc_mru_descr.nameText],
            mc_mru_descr.MarineReportingUnitId.in_(mrus_needed)
        )

        _, art8_data = db.get_all_specific_columns(
            [sql2018.t_V_ART8_GES_2018.c.MarineReportingUnit,
             sql2018.t_V_ART8_GES_2018.c.GESComponent],
            sql2018.t_V_ART8_GES_2018.c.CountryCode == self.country_code
        )
        _, art9_data = db.get_all_specific_columns(
            [sql2018.t_V_ART9_GES_2018.c.MarineReportingUnit,
             sql2018.t_V_ART9_GES_2018.c.GESComponent],
            sql2018.t_V_ART9_GES_2018.c.CountryCode == self.country_code
        )
        art8_art9_data = set(art8_data + art9_data)

        for row in data:
            mru = row.thematicId
            description = [
                x.Description
                # (x.nameTxtInt is not None and x.nameTxtInt.strip()
                #  or x.nameText or "")
                for x in mru_descriptions
                if x.MarineReportingUnitId == mru
            ]
            if not description:
                description = row.nameTxtInt or row.nameText or ""
            else:
                description = description[0]

            translation = get_translated(description, self.country_code) or ""
            area = int(round(row.Area))

            if not translation:
                retrieve_translation(self.country_code, description)

            self._translatable_values.append(description)

            prop_water = int(round((area / marine_waters_total) * 100))

            descr_list = set([
                x[1]
                for x in art8_art9_data
                if x[0] == row.thematicId
            ])
            descr_list = sorted(descr_list, key=natural_sort_key)
            descr_list_norm = []

            for d in descr_list:
                try:
                    desc = get_descriptor(d).template_vars['title']
                except:
                    desc = d

                descr_list_norm.append(desc)

            descriptors = ', '.join(descr_list_norm)

            res.append((row.rZoneId, row.spZoneType, mru,
                        description, translation, '{:,}'.format(area),
                        prop_water, descriptors))

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
        text_reports = get_text_reports_2018(self.country_code)
        data_text = []

        # FileName, LocationURL, DateDue, DateReleased, ReportingDelay
        for row in text_reports:
            _row = {}

            file_url = row[0]
            release_date = row[1]
            file_url_split = file_url.split('/')
            text_report_ob = 'MSFD - Articles 8, 9 and 10 - Text reports'

            _row['ReportingObligation'] = text_report_ob
            _row['FileName'] = file_url_split[-1]
            _row['LocationURL'] = file_url
            _row['DateDue'] = datetime.strptime('15-10-2018', '%d-%m-%Y')
            _row['DateReleased'] = release_date
            _row['ReportingDelay'] = None

            data_text.append(_row)

        self.data.extend(data_text)

    @property
    def obligations_needed(self):
        obligations = (
            'MSFD - Article 4 - Spatial data',
            'MSFD - Articles 8, 9 and 10 - XML data'
        )

        return obligations

    @db.use_db_session('2018')
    def get_reporting_history_data(self):
        # obligation = 'MSFD reporting on Initial Assessments (Art. 8), ' \
        #              'Good Environmental Status (Art.9), Env. targets & ' \
        #              'associated indicators (Art.10) & related reporting on '\
        #              'geographic areas, regional cooperation and metadata.'

        mc = sql2018.ReportingHistory
        conditions = [
            mc.CountryCode == self.country_code,
            mc.DateReleased.isnot(None)  # skip not released files
        ]

        if self.obligations_needed:
            conditions.append(
                mc.ReportingObligation.in_(self.obligations_needed)
            )

        # skip not released files as they are deleted from CDR (Germany)
        _, res = db.get_all_records(
            mc,
            *conditions
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
            'Report due', 'Report received', 'Difference (days)'
        )

        return headers

    def calculate_reporting_delay(self, reporting_delay, report_due,
                                  report_date):
        # if reporting_delay:
        #     return -reporting_delay

        timedelta = report_due - report_date

        return "{:+d}".format(timedelta.days)

    def get_data_by_obligations(self, obligations):
        # Group the data by envelope, report due, report date
        # and report delay
        data = [
            row for row in self.data

            if row.get('ReportingObligation') in obligations

        ]
        rows = []

        groups = defaultdict(list)

        for row in data:
            filename = row.get('FileName')
            envelope = self.location_url(row.get('LocationURL'), filename)
            report_due = self.format_date(row.get('DateDue'))
            report_date = self.format_date(row.get('DateReleased'))

            report_delay = self.calculate_reporting_delay(
                row.get('ReportingDelay'), report_due, report_date
            )
            k = (envelope, report_due, report_date, report_delay)

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
                             key=lambda _row: (_row[3], _row[2]),
                             reverse=True)

        return sorted_rows

    @property
    def all_obligations(self):
        data = self.data

        obligations = [set([x.get('ReportingObligation') for x in data])]

        return obligations

    def __call__(self):
        self.allrows = [
            compoundrow(self, ", ".join(obligations),
                        self.get_data_by_obligations(obligations),
                        show_header=self.show_header)
            for obligations in self.all_obligations
            ]

        # needed for odt export, which is not used anymore
        # self.report_hystory_data = self.allrows[0].rows

        return self.template(rows=self.allrows)


class ReportedInformationTable(BaseNatSummaryView):
    """ Alternate implementation for the reporting history table
    Reads data from sql2018.ReportedInformation

    TODO currently not used
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
            'Report due', 'Report received', 'Difference (days)'
        )

        return headers

    def get_text_and_spacial_files(self):
        view = ReportingHistoryTable(self, self.request)
        view()

        return view.report_hystory_data

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

        text_files = self.get_text_and_spacial_files()
        rows.extend(text_files)

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

    @db.use_db_session('2018')
    def _get_marine_waters_data(self):
        column_names = ['Country', 'Subregion', 'Area_km2', 'Type']

        cnt, data = db.get_all_specific_columns(
            [getattr(sql2018.t_MarineWaters.c, c) for c in column_names]
        )

        return data

    def __get_water_seabed_value(self, types):
        data = self._get_marine_waters_data()

        values = [
            int(row.Area_km2)
            for row in data
            if (row.Country == self.country_code and
                row.Type in types)
        ]

        return "{:,}".format(sum(values))

    @property
    def water_seabed_value(self):
        types = ['Water column & seabed/subsoil', 'Marine waters']

        return self.__get_water_seabed_value(types)

    @property
    def seabed_only_value(self):
        types = ['Seabed/subsoil']

        return self.__get_water_seabed_value(types)

    @property
    def document_title(self):
        text = u"Marine Strategy Framework Directive - Article 12 technical " \
               u"assessment of the 2018 updates of Articles 8, 9 and 10"

        return text

    @timeit
    def reporting_history_table(self):
        # view = ReportedInformationTable(self, self.request)
        view = ReportingHistoryTable(self, self.request)
        rendered_view = view()

        # self.report_hystory_data = view.report_hystory_data

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
    def reporting_areas(self):
        output = self.get_field_value('reporting_areas')

        return output

    @property
    def assessment_methodology(self):
        output = self.get_field_value('assessment_methodology')

        return output

    @property
    @timeit
    def assessment_areas_table(self):
        """ 1.4 Reporting areas """
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
        #            'Report due', 'Report received', 'Difference (days)')
        headers = (
            'Files available', 'Access to reports',
            'Report due', 'Report received', 'Difference (days)'
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