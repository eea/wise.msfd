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


def regionalsection(klass):
    SECTIONS.append(klass)


class RegionalDescriptorsSimpleTable(BaseRegSummaryView):
    """ Implementation for a simple table, with a title, headers and data

    title: a string
    headers: return a list of strings which represent the headers(first row)
        of the table
    setup_data: returns a list of rows which represent the data

    """

    template = ViewPageTemplateFile("pt/simple-table.pt")
    title = ''

    def setup_data(self):
        return []

    def get_table_headers(self):
        return []

    def __call__(self):
        data = self.setup_data()
        headers = self.get_table_headers()
        title = self.title

        return self.template(title=title, data=data, headers=headers)


@regionalsection
class Article11CoverageOfActivities(RegionalDescriptorsSimpleTable):

    features_table = sql.t_MSFD_12_8cOverview
    title = 'Coverage of activities by monitoring programmes'

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


@regionalsection
class PressuresActivities(RegionalDescriptorsSimpleTable):

    pressures_table = sql.t_MSFD_8b_8bPressures
    title = 'Pressures and associated activities affecting the marine waters'

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


@regionalsection
class OverallConclusion2012(RegionalDescriptorsSimpleTable,
                            AssessmentDataMixin):
    title = "Overall conclusion - descriptor-level"
    articles = [
        ('Art9', 'Article 9: Determination of GES'),
        ('Art8', 'Article 8: Initial assessment'),
        ('Art10', 'Article 10: Environmental targets'),
    ]
    # get_reg_assessments_data_2012
    # def get_assessment_data(self, region, article, descriptor):
    #     data = ASSESSMENTS_2012
    #
    #     for row in data:
    #         if row.region.strip() != region:
    #             continue
    #
    #         if row.descriptor.strip() != descriptor:
    #             continue
    #
    #         if article not in row.article.replace(' ', ''):
    #             continue
    #
    #         return row

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
    year = "2012"

    render_header = True

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Regional summary report: {}".format(
                self.region_name,
            ),
            countries=", ".join([x[1] for x in self.available_countries])
        )
        # trans_edit_html = self.translate_view()()

        self.tables = [
            report_header,
            # trans_edit_html,
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
