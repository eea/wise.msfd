
from sqlalchemy import or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from wise.msfd import db, sql2018
from wise.msfd.data import get_text_reports_2018
from wise.msfd.sql2018 import MarineReportingUnit, ReportingHistory
from wise.msfd.utils import ItemList

from ..nationalsummary.introduction import Introduction
from ..vocabulary import MARINE_WATERS_REGION_DATA
from .base import BaseRegSummaryView
from .utils import SimpleTable

# Source: StatisticsMarineRegionsWatersMRUs.xml / RegionsSubregions sheet
# eu_area source: EU28_MarineWaters_to_2020 sheet
REGIONS_SUBREGIONS = {
    'BAL': {
        'area': '392,215',
        'eu_area': '366,777',
        'subregions': []
    },
    'ATL': {
        'area': '15,462,049',
        'eu_area': '6,612,255',
        'subregions': [
            # region name, total area, eu area
            ('Greater North Sea', '654,179', '485,415'),
            ('Celtic Seas', '1,123,380', '1,115,665'),
            ('Bay of Biscay and the Iberian Coast', '803,349', '802,145'),
            ('Macaronesia', '3,967,476', '4,209,029'),
            ('Area of NEA outside the four MSFD subregions', '8,913,665', '')
        ]
    },
    'MED': {
        'area': '2,516,652',
        'eu_area': '1,637,561',
        'subregions': [
            # region name, total area, eu area
            ('Western Mediterranean Sea', '846,003', '650,893'),
            ('Adriatic Sea', '139,784', '120,062'),
            ('Ionian Sea and the Central Mediterranean Sea', '773,032', 
            '464,368'),
            ('Aegean-Levantine Sea', '757,833', '402,238'),
        ]
    },
    'BLK': {
        'area': '525,482',
        'eu_area': '63,227',
        'subregions': [
            # region name, total area, eu area
            ('Black Sea (excluding Seas of Marmara and Azov)', '473,894', ''),
            ('Black Sea - Sea of Marmara', '11,737', ''),
            ('Black Sea - Sea of Azov', '39,851', '')
        ]
    }
}


class RegionalIntroduction(BaseRegSummaryView, Introduction):
    """ Make National summary code compatible for Regional summary """

    template = ViewPageTemplateFile('pt/introduction.pt')
    rep_date_tpl = u'<a href="{}">{}</a>'

    def default(self):
        return ['-' for _ in self.available_countries]

    @property
    def available_countries(self):
        countries = super(RegionalIntroduction, self).available_countries
        c_sorted = sorted(countries, key=lambda i: i[1])

        return c_sorted

    @property
    def information_memberstate(self):
        text = u"""
By October 2018, the Member States were due to submit updates of the assessment
 of their marine waters (Article 8), the determination of GES (Article 9) and 
 the setting of environmental targets (Article 10), in accordance with 
 Article 17 of the Marine Strategy Framework Directive (MSFD, Directive 2008/56/EC).
<br/>The table gives details of when the Member States submitted their reports, in text (usually pdf) and elecronic (xml) format. E-reporting was undertaken in relation to specific geographic areas (Marine Reporting Units) which are specifed in an xml file (4geo.xml) and accompanied by geographic information system (GIS) shapefiles which allow the reported information to be displayed as maps. In cases where the Member State uploaded reports in stages (text reports) or modified previous versions (e-reports), multiple dates are shown.        
"""
        return text

    def _get_memberstate_reports(self, data, obligation):
        res = []

        for country_code, country_name in self.available_countries:
            values = []
            for row in data:
                if row.ReportingObligation != obligation:
                    continue

                if row.CountryCode != country_code:
                    continue

                date_received = row.DateReceived.date()
                envelope_url = row.LocationURL.replace(row.FileName, '')

                values.append((envelope_url, date_received))

            values = sorted(set(values), key=lambda i: i[1], reverse=True)
            unique_values = [
                self.rep_date_tpl.format(v[0], v[1])

                for v in values
            ]

            res.append(ItemList(unique_values, sort=False))

        return res

    def get_text_reports(self):
        res = []

        for country_code, country_name in self.available_countries:
            text_reports = get_text_reports_2018(country_code)
            values = []

            for row in text_reports:
                file_url = row[0]
                release_date = row[1].date()
                envelope_url = '/'.join(file_url.split('/')[:-1])

                values.append((envelope_url, release_date))

            values = sorted(set(values), key=lambda i: i[1], reverse=True)
            unique_values = [
                self.rep_date_tpl.format(v[0], v[1])

                for v in values
            ]

            res.append(ItemList(unique_values, sort=False))

        return res

    @db.use_db_session('2018')
    def memberstate_reports(self):
        mc = ReportingHistory
        _, data = db.get_all_records(
            mc,
            # mc.EnvelopeStatus == 'End',
        )

        rows = [
            ("", [x[1] for x in self.available_countries]),
            ("Text reports (pdf)", self.get_text_reports()),
            ("Electronic reports (xml)", self._get_memberstate_reports(
                data, 'MSFD - Articles 8, 9 and 10 - XML data')),
            ("Geographic data (4geo.xml; GIS shapefiles)",
             self._get_memberstate_reports(
                 data, 'MSFD - Article 4 - Spatial data')
             )
        ]
        view = SimpleTable(self, self.request, rows, align_right=False)

        return view()

    @property
    def reporting_areas_text(self):
        output = self.get_field_value('reporting_areas_text')

        return output

    @property
    def length_of_coastline(self):
        output = self.get_field_value('length_of_coastline')

        return output

    def marine_waters(self):
        klass = MarineWatersTable(self, self.request)

        return klass.marine_waters()

    def assessment_areas(self):
        klass = ReportingAreasTable(self, self.request)

        return klass.assessment_areas()


class ReportingAreasTable(RegionalIntroduction):
    @db.use_db_session('2018')
    def get_number_of_mrus(self):
        columns = ['CountryCode', 'MarineReportingUnitId', 'desigBegin',
                   '_4geo']
        cnt, data = db.get_all_specific_columns(
            [getattr(MarineReportingUnit, c)
             for c in columns],
            or_(MarineReportingUnit.desigBegin.isnot(None),
                MarineReportingUnit._4geo.isnot(None))
        )

        res = []

        for country_code, country_name in self.available_countries:
            cnt = [
                x
                for x in data
                if x.CountryCode == country_code
            ]

            res.append(len(cnt))

        return res

    def assessment_areas(self):
        rows = [
            ("", [x[1] for x in self.available_countries]),
            ("Number of Marine Reporting Units used",
             self.get_number_of_mrus()),
            ("Range of extent of Marine Reporting Units (km2)",
             self.default()),
            # ("Average extent of Marine Reporting Units (km2)", self.default())
        ]
        self.rows = rows
        view = SimpleTable(self, self.request, rows)

        return view()


class MarineWatersTable(RegionalIntroduction):
    seabed_types = [
        'Seabed/subsoil', 'Continental shelf', 'Seabed only',
        'Extended continental shelf', 'Fisheries Management Zone'
    ]

    water_column_types = ['Water column & seabed/subsoil', 'Marine waters',
        'Territorial waters', 'Water column + seabed',
        'Area designated for hydrocarbon exploration and exploitation'
    ]

    def _get_marine_water_by_type(self, data, types):
        res = []

        for country_id, country_name in self.available_countries:
            values = [
            int(row.Area_km2.replace(',', ''))
                for row in data
                if (row.Country == country_id and
                    row.Type in types and
                    row.Region == self.region_code)
            ]

            res.append("{:,}".format(sum(values)))

        return res

    @db.use_db_session('2018')
    def _get_marine_waters_data(self):
        column_names = ['Country', 'Subregion', 'Area_km2', 'Type']

        # cnt, data = db.get_all_specific_columns(
        #     [getattr(sql2018.t_MarineWaters.c, c) for c in column_names]
        # )

        data = MARINE_WATERS_REGION_DATA

        return data

    def get_proportion_row(self, data):
        types = self.seabed_types + self.water_column_types
        res = []
        # total = sum([
        #     float(row.Area_km2.replace(',', ''))
        #     for row in data
        #     if (row.Type in types and
        #         row.Region == self.region_code)
        # ])

        total = REGIONS_SUBREGIONS[self.region_code]['area']
        total = int(total.replace(',', ''))

        for country_id, country_name in self.available_countries:
            values = [
                float(row.Area_km2.replace(',', ''))
                for row in data
                if (row.Country == country_id and
                    row.Type in types and
                    row.Region == self.region_code)
            ]
            
            country_total = sum(values)
            res.append("{:.1f}%".format(country_total/total * 100))

        return res

    def get_seabed_only_row(self, data):
        types = self.seabed_types

        return self._get_marine_water_by_type(data, types)

    def get_water_seabed_row(self, data):
        types = self.water_column_types

        return self._get_marine_water_by_type(data, types)

    def marine_waters(self):
        data = self._get_marine_waters_data()

        rows = [
            ("", [x[1] for x in self.available_countries]),
            # ("Length of coastline (km)", self.default()),
            ("Area of marine waters (water column and seabed) (km2)",
             self.get_water_seabed_row(data)),
            ("Area of marine waters (seabed only - beyond EEZ or quivalent) "
             "(km2)", self.get_seabed_only_row(data)),
            ("Proportion of the region (areal %)",
             self.get_proportion_row(data))
        ]
        self.rows = rows
        view = SimpleTable(self, self.request, rows)

        return view()
