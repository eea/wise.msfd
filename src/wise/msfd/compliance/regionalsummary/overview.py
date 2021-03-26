# -*- coding: utf-8 -*-

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import sql, db
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.gescomponents import get_all_descriptors
from wise.msfd.labels import get_label
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from ..regionaldescriptors.assessment import ASSESSMENTS_2012
from .base import BaseRegSummaryView


logger = logging.getLogger('wise.msfd')


SECTIONS = []


def register_section(klass):
    SECTIONS.append(klass)


class RegionalDescriptorsSimpleTable(BaseRegSummaryView):
    """ Implementation for a simple table, with a title, headers and data

    title: a string
    headers: return a list of strings which represent the headers(first row)
        of the table
    setup_data: returns a list of rows which represent the data

    """

    template = ViewPageTemplateFile("pt/overview-simple-table.pt")
    title = ''
    _id = ''

    def setup_data(self):
        []

    def get_table_headers(self):
        countries = [x[1] for x in self.available_countries]

        return [''] + countries

    def __call__(self):
        data = self.setup_data()
        headers = self.get_table_headers()
        title = self.title

        return self.template(title=title, data=data, headers=headers)


@register_section
class CompetentAuthorities(RegionalDescriptorsSimpleTable):
    title = 'Compentent Authorities'
    _id = 'reg-overview-ca'

    def setup_data(self):
        rows = []
        values = []

        for country_id, country_name in self.available_countries:
            # TODO get values
            val = ''

            values.append(val)

        rows.append(('No of designated CAs', values))

        return rows


@register_section
class MarineWaters(RegionalDescriptorsSimpleTable):
    title = 'Marine waters'
    _id = 'reg-overview-mw'

    def setup_data(self):
        rows = []

        row_headers = [
            'Length of coastline (km)',
            'Area of marine waters (water column and seabed) (km2)',
            'Area of marine waters (seabed only - '
            'beyond EEZ or quivalent) (km2)',
            'Proportion of Baltic Sea region per Member State (areal %)'
        ]

        values = []

        for info in row_headers:
            for country_id, country_name in self.available_countries:
                # TODO get values
                val = ''

                values.append(val)

            rows.append((info, values))

        return rows


@register_section
class MarineRegionSubregions(RegionalDescriptorsSimpleTable):
    title = 'Marine region and subregions'
    _id = 'reg-overview-mrs'

    def get_table_headers(self):
        regions = [x[1] for x in self.available_subregions]

        return [''] + regions

    def setup_data(self):
        rows = []

        row_headers = [
            'Length of coastline (km) - total',
            'Length of coastline (km) - EU',
            'Length of coastline (km) - non EU',
            'Area (km2) - total',
            'Area (km2) - EU',
            'Area (km2) - non EU'
        ]

        values = []

        for info in row_headers:
            for country_id, country_name in self.available_countries:
                # TODO get values
                val = ''

                values.append(val)

            rows.append((info, values))

        return rows


@register_section
class MarineReportingAreas(RegionalDescriptorsSimpleTable):
    title = 'Marine reporting areas'
    _id = 'reg-overview-mra'

    def setup_data(self):
        rows = []

        row_headers = [
            'Number of MRUs used',
            'Range of extent of MRUs (km2)',
            'Average extent of MRUs (km2)',
        ]

        values = []

        for info in row_headers:
            for country_id, country_name in self.available_countries:
                # TODO get values
                val = ''

                values.append(val)

            rows.append((info, values))

        return rows


@register_section
class UsesHumanActivitiesPressures(RegionalDescriptorsSimpleTable):
    title = 'Uses and human activities, and associated pressures'
    _id = 'reg-overview-uses'


@register_section
class PressuresAffectingDescriptors(RegionalDescriptorsSimpleTable):
    title = 'Pressures affecting descriptors'
    _id = 'reg-overview-press'


@register_section
class ExtentGESAchieved(RegionalDescriptorsSimpleTable):
    title = 'Extent to which GES is achieved'
    _id = 'reg-overview-extent'


@register_section
class CurrentEnvitonmentalStatus(RegionalDescriptorsSimpleTable):
    title = 'Current environmental status'
    _id = 'reg-overview-env-stat'


@register_section
class EnvironmentalTargets(RegionalDescriptorsSimpleTable):
    title = 'Environmental targets on pressures'
    _id = 'reg-overview-env-target'


@register_section
class MeasuresPressures(RegionalDescriptorsSimpleTable):
    title = 'Measures on pressures'
    _id = 'reg-overview-meas'


@register_section
class ExceptionsGESAchieved(RegionalDescriptorsSimpleTable):
    title = 'Exceptions reported when targets or GES cannot be achieved'
    _id = 'reg-overview-exception'


@register_section
class Article92012(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 9 - Determination of GES (2012)'
    _id = 'reg-overview-art9-2012'


@register_section
class Article82012(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 8 (Assessments) (2012)'
    _id = 'reg-overview-art8-2012'


@register_section
class Article102012(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 10 (Environmental targets) (2012)'
    _id = 'reg-overview-art10-2012'


@register_section
class Article112014(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 11 (Monitoring programmes) (2014)'
    _id = 'reg-overview-art11-2014'


@register_section
class Article132016(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 13 (Programmes of measures) (2016)'
    _id = 'reg-overview-art13-2016'


@register_section
class Article142016(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 14 (Exceptions) (2016)'
    _id = 'reg-overview-art14-2016'


@register_section
class Article92018(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 9 - Determination of GES (2018)'
    _id = 'reg-overview-art9-2018'


@register_section
class Article82018(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 8 (Assessments) (2018)'
    _id = 'reg-overview-art8-2018'


@register_section
class Article102018(RegionalDescriptorsSimpleTable):
    title = 'Implementation of Art. 10 (Environmental targets) (2018)'
    _id = 'reg-overview-art10-2018'


@register_section
class Implementation2017Decision(RegionalDescriptorsSimpleTable):
    title = 'Implementation of 2017 Decision reporting scales/areas (2018)'
    _id = 'reg-overview-impl-2017'


@register_section
class RegionalCoherence2012(RegionalDescriptorsSimpleTable):
    title = 'Regional coherence: first cycle 2012-2017'
    _id = 'reg-overview-coh-2012'


@register_section
class RegionalCoherence2018(RegionalDescriptorsSimpleTable):
    title = 'Regional coherence: second cycle 2018-2023'
    _id = 'reg-overview-coh-2018'


# @register_section
class Article11CoverageOfActivities(RegionalDescriptorsSimpleTable):
    features_table = sql.t_MSFD_12_8cOverview
    title = 'Coverage of activities by monitoring programmes'
    _id = 'reg-overview-t1'

    @property
    @db.use_db_session('2012')
    def features(self):
        table = self.features_table

        features = db.get_unique_from_table(
            table, 'Features & Characteristics'
        )

        return features

    @db.use_db_session('2012')
    def get_db_data(self):
        table = self.features_table
        columns_needed = (
            'MemberState', 'Marine region/subregion',
            'Features & Characteristics', 'Found relevant by MS?',
            'Reported by MS?'
        )
        columns = [
            getattr(table.c, c)
            for c in columns_needed
        ]
        conditions = [
            getattr(table.c, 'Marine region/subregion').in_(
                self._region_folder._subregions
            ),
        ]

        _, data = db.get_all_specific_columns(
            columns,
            *conditions
        )

        return data

    def get_table_headers(self):
        countries = [x[1] for x in self.available_countries]

        return ['Activities'] + countries

    def setup_data(self):
        db_data = self.get_db_data()

        rows = []

        for feature in self.features:
            values = []
            for country_id, country_name in self.available_countries:
                reported_for_country = set([
                    getattr(r, 'Reported by MS?')
                    for r in db_data
                    if (getattr(r, 'Features & Characteristics')
                        .strip() == feature
                        and r.MemberState.strip() == country_id)
                ])

                values.append("; ".join(reported_for_country))

            feature_label = feature  # get_label(feature, None)

            if any(values):
                rows.append((feature_label, values))

        return rows


# @register_section
class PressuresActivities(RegionalDescriptorsSimpleTable):
    pressures_table = sql.t_MSFD_8b_8bPressures
    title = 'Pressures and associated activities affecting the marine waters'
    _id = 'reg-overview-t2'

    @property
    @db.use_db_session('2012')
    def pressures(self):
        table = self.pressures_table
        pressures = db.get_unique_from_table(table, 'Pressure')

        return pressures

    @db.use_db_session('2012')
    def get_db_data(self):
        table = self.pressures_table
        columns_needed = ('MemberState', 'Marine region/subregion',
                          'Pressure', 'Activity')
        columns = [
            getattr(table.c, c)
            for c in columns_needed
        ]
        conditions = [
            getattr(table.c, 'Marine region/subregion').in_(
                self._region_folder._subregions
            ),
            table.c.Activity != 'NotReported'
        ]

        _, data = db.get_all_specific_columns(
            columns,
            *conditions
        )

        return data

    def get_table_headers(self):
        countries = [x[1] for x in self.available_countries]

        return ['Pressures'] + countries

    def setup_data(self):
        db_data = self.get_db_data()

        rows = []

        for pressure in self.pressures:
            values = []
            for country_id, country_name in self.available_countries:
                activities_for_country = [
                    r.Activity
                    for r in db_data
                    if (r.Pressure.strip() == pressure
                        and r.MemberState.strip() == country_id)
                ]

                values.append("; ".join(activities_for_country))

            pressure_label = pressure  # get_label(pressure, None)

            if any(values):
                rows.append((pressure_label, values))

        return rows


# @register_section
class OverallConclusion2012(RegionalDescriptorsSimpleTable,
                            AssessmentDataMixin):
    title = "Overall conclusion - descriptor-level"
    articles = [
        ('Art9', 'Article 9: Determination of GES'),
        ('Art8', 'Article 8: Initial assessment'),
        ('Art10', 'Article 10: Environmental targets'),
    ]
    _id = 'reg-overview-t3'

    def setup_data(self):
        data = []
        descriptors = get_all_descriptors()

        for desc_code, desc_title in descriptors:
            conclusions = []

            for art_id, art_title in self.articles:
                concl = ''
                assess_data = self.get_reg_assessments_data_2012(
                    art_id, self.region_code, desc_code
                )

                if assess_data:
                    concl = assess_data[0].conclusion

                conclusions.append(concl)

            if any(conclusions):
                data.append((desc_title, conclusions))

        return data

    def get_table_headers(self):
        h = ['Article'] + [a[0] for a in self.articles]

        return h


class RegionalOverviewView(BaseRegSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    toc_template = ViewPageTemplateFile('pt/overview-table-of-contents.pt')
    year = "2012"

    render_header = True

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Regional overview: {}".format(
                self.region_name,
            ),
            countries=", ".join([x[1] for x in self.available_countries])
        )
        table_of_contents = self.toc_template(
            sections=SECTIONS
        )

        self.tables = [
            report_header,
            table_of_contents,
        ]
        for klass in SECTIONS:
            rendered_table = klass(self, self.request)()
            self.tables.append(rendered_table)

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self._country_folder.absolute_url())
            return self.request.response.redirect(url)

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'translate' in self.request.form:
            for value in self._translatable_values:
                retrieve_translation(self.country_code, value)

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        @timeit
        def render_html():
            return self.index()

        return render_html()
