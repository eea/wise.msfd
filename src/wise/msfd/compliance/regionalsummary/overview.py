# -*- coding: utf-8 -*-
from collections import Counter
import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import sql, db
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.gescomponents import (DESCRIPTOR_TYPES, FEATURES_ORDER,
                                     get_all_descriptors, get_descriptor)
from wise.msfd.labels import get_label
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from ..nationalsummary.overview import (ExceptionsReported,
                                        GESExtentAchieved,
                                        ItemListOverview,
                                        PressureTableMarineEnv,
                                        ProgrammesOfMeasures,
                                        TableOfContents,
                                        UsesHumanActivities)
from .base import BaseRegSummaryView
from .introduction import MarineWatersTable, ReportingAreasTable
from .descriptor_assessments import RegDescriptorLevelAssessments

logger = logging.getLogger('wise.msfd')


SECTIONS = []
NATIONAL_ASSESSMENT_DATA = {}
REGIONAL_ASSESSMENT_DATA = {}

REGIONS_SUBREGIONS = {
    'BAL': {
        'area': '392,215',
        'subregions': []
    },
    'ATL': {
        'area': '15,462,049',
        'subregions': [
            ('Greater North Sea', '654,179'),
            ('Celtic Seas', '1,123,380'),
            ('Bay of Biscay and the Iberian Coast', '803,349'),
            ('Macaronesia', '3,967,476')
        ]
    },
    'MED': {
        'area': '2,516,652',
        'subregions': [
            ('Western Mediterranean Sea', '846,003'),
            ('Adriatic Sea', '139,784'),
            ('Ionian Sea and the Central Mediterranean Sea', '773,032'),
            ('Aegean-Levantine Sea', '757,833'),
        ]
    },
    'BLK': {
        'area': '525,482',
        'subregions': [
            ('Black Sea (excluding Seas of Marmara and Azov)', '473,894'),
            ('Black Sea - Sea of Marmara', '11,737'),
            ('Black Sea - Sea of Azov', '39,851')
        ]
    }
}


def register_section(klass):
    SECTIONS.append(klass)

    return klass


DESCRIPTORS_FEATURES = {
    'D1.1': ['BirdsBenthicFeeding', 'BirdsGrazing', 'BirdsPelagicFeeding',
             'BirdsSurfaceFeeding', 'BirdsWading'],
    'D1.2': ['MamSeals'],
    'D1.3': ['Not reported'],
    'D1.4': ['FishCoastal', 'FishDemersalShelf', 'FishPelagicShelf'],
    'D1.5': ['Not reported'],
    'D1.6': ['HabPelBHT'],
    'D2': ['PresEnvNISnew'],
    'D3': ['FishCommercial'],
    'D4': ['EcosysCoastal'],
    'D5': ['PresEnvEutrophi'],
    'D6': ['PresPhyLoss', 'HabBenBHT'],
    'D7': [],
    'D8': ['PresEnvContUPBTs', 'PresEnvAcuPolluEvents'],
    'D9': ['PresEnvContSeafood'],
    'D10': ['PresEnvLitter'],
    'D11': ['PresEnvSoundContinuous'],
}


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
    editable_text = ''

    def get_color_class(self, value):
        return ''

    def setup_data(self):
        return []

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
    title = 'Competent Authorities'
    _id = 'reg-overview-ca'

    @db.use_db_session('2012')
    def get_ca_data(self):
        cnt, data = db.get_competent_auth_data()

        return data

    def setup_data(self):
        data = self.get_ca_data()
        rows = []
        values = []

        for country_id, country_name in self.available_countries:
            # TODO get values
            vals = [
                x
                for x in data
                if x.C_CD == country_id
            ]

            values.append(len(vals))

        rows.append(('No. of designated CAs', values))

        return rows


@register_section
class MarineWaters(RegionalDescriptorsSimpleTable):
    title = 'Marine waters'
    _id = 'reg-overview-mw'

    @property
    def editable_text(self):
        field_name = 'marine_waters'
        folder = self.context.context
        default = "-"

        if not hasattr(folder, field_name):
            return default

        progress = getattr(folder, field_name)
        output = getattr(progress, 'output', default)

        return output

    def setup_data(self):
        view = MarineWatersTable(self, self.request)
        view.marine_waters()
        rows = view.rows[1:]

        # row_headers = [
        #     'Length of coastline (km)',
        #     'Area of marine waters (water column and seabed) (km2)',
        #     'Area of marine waters (seabed only - '
        #     'beyond EEZ or quivalent) (km2)',
        #     'Proportion of Baltic Sea region per Member State (areal %)'
        # ]
        #
        # for info in row_headers:
        #     values = []
        #
        #     for country_id, country_name in self.available_countries:
        #         # TODO get values
        #         val = ''
        #
        #         values.append(val)
        #
        #     rows.append((info, values))

        return rows


@register_section
class MarineRegionSubregions(RegionalDescriptorsSimpleTable):
    title = 'Marine region and subregions'
    _id = 'reg-overview-mrs'

    def get_table_headers(self):
        regions = ["Region: " + self.country_name]
        subregions = [
            "Subregion: " + x[0]
            for x in REGIONS_SUBREGIONS[self.region_code]['subregions']
        ]

        return [''] + regions + subregions

    def setup_data(self):
        rows = []

        row_headers = [
            # 'Length of coastline (km) - total',
            # 'Length of coastline (km) - EU',
            # 'Length of coastline (km) - non EU',
            'Area (km2) - total',
            # 'Area (km2) - EU',
            # 'Area (km2) - non EU'
        ]

        region = REGIONS_SUBREGIONS[self.region_code]

        for info in row_headers:
            values = [region['area']]

            for subregion in region['subregions']:
                values.append(subregion[1])

            rows.append((info, values))

        return rows


# @register_section
class MarineReportingAreas(RegionalDescriptorsSimpleTable):
    """ TODO removed from regional assessment summary and overview pages
    """

    title = 'Marine reporting areas'
    _id = 'reg-overview-mra'

    def setup_data(self):
        view = ReportingAreasTable(self, self.request)
        view.assessment_areas()
        rows = view.rows[1:]

        return rows


@register_section
class UsesHumanActivitiesPressures(RegionalDescriptorsSimpleTable,
                                   UsesHumanActivities):
    title = 'Uses and human activities, and associated pressures'
    _id = 'reg-overview-uses'
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')
    # features = FEATURES_DB_2018

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        # setup data to be available at 'features_pressures_data' attr
        self.get_features_pressures_data()
        data = self.features_pressures_data
        out = []

        for activ_theme, activ_features in self.uses_activities_features:
            theme_data = []

            for activ_feat in activ_features:
                # if activ_feat.endswith('All'):
                #     continue

                activity_data = []

                for country_id, country_name in self.available_countries:
                    pressures = [
                        x[3]
                        for x in data
                        if x[0] == country_id and x[2] == activ_feat
                    ]

                    sorted_press = sorted(
                        set(pressures), key=lambda i: fixedorder_sortkey(
                            i, FEATURES_ORDER)
                    )

                    pressures = [
                        self.get_feature_short_name(x)
                        for x in sorted_press
                    ]

                    activity_data.append(ItemListOverview(pressures,
                                                          sort=False))

                theme_data.append((get_label(activ_feat, 'features'),
                                   activity_data))

            out.append((activ_theme, theme_data))

        return out


@register_section
class PressuresAffectingDescriptors(RegionalDescriptorsSimpleTable,
                                    PressureTableMarineEnv):
    title = 'Pressures affecting descriptors'
    _id = 'reg-overview-press'
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        # setup data to be available at 'features_pressures_data' attr
        self.get_features_pressures_data()
        data = self.features_pressures_data

        out = []
        general_pressures = set(['PresAll', ])  # 'Unknown'

        for theme, features_for_theme in self.features_needed:
            theme_data = []
            theme_general_pressures = set([
                x
                for x in features_for_theme
                if x.endswith('All')
            ])

            for feature in features_for_theme:
                if feature.endswith('All'):
                    continue

                feature_data = []
                for country_id, country_name in self.available_countries:
                    # if pressure is ending with 'All' it applies to all
                    # features in the current theme
                    descriptors_rep = []

                    for x in data:
                        descr = x[1]

                        try:
                            descr = get_descriptor(descr).template_vars['title']
                        except:
                            pass

                        ccode = x[0]

                        if ccode != country_id:
                            continue

                        feats = set(x[2].split(','))

                        if(feature in feats
                            or general_pressures.intersection(feats)
                            or theme_general_pressures.intersection(feats)):

                            descriptors_rep.append(descr)

                    feature_data.append(ItemListOverview(set(descriptors_rep)))

                theme_data.append(
                    (self.get_feature_short_name(feature), feature_data)
                )

            out.append((theme, theme_data))

        return out


@register_section
class ExtentGESAchieved(RegionalDescriptorsSimpleTable, GESExtentAchieved):
    title = 'Extent to which GES is achieved'
    _id = 'reg-overview-extent'
    template = ViewPageTemplateFile('pt/overview-descriptor-pressures-table.pt')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        data = self.get_ges_extent_data()

        out = []

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = []

                for feature in DESCRIPTORS_FEATURES[descriptor]:
                    feature_data = []

                    for country_id, country_name in self.available_countries:
                        _v = [
                            x.GESExtentUnit
                            for x in data
                            if (x.CountryCode == country_id and
                                x.Feature == feature)
                        ]
                        _vals = Counter(_v)
                        len_v = len(_v)

                        if feature == 'PresEnvNISnew':
                            _vals = [
                                "{0}: {1}".format(k, v)
                                for k, v in _vals.items()
                                if k
                            ]
                        else:
                            _vals = [
                                "{0}: {1} ({2} of {3})".format(
                                    k, int((float(v) / len_v) * 100), v, len_v)
                                for k, v in _vals.items()
                                if k
                            ]

                        feature_data.append(ItemListOverview(_vals))

                    descriptor_data.append((get_label(feature, 'features'),
                                           feature_data))

                descriptor_type_data.append([
                    self.get_descriptor_title(descriptor), descriptor_data])

            out.append([descr_type, descriptor_type_data])

        return out

@register_section
class CurrentEnvitonmentalStatus(RegionalDescriptorsSimpleTable,
                                 GESExtentAchieved):
    title = 'Current environmental status'
    _id = 'reg-overview-env-stat'
    template = ViewPageTemplateFile('pt/overview-descriptor-pressures-table.pt')

    def get_color_class(self, value):
        colors = {
            "Unknown": 'ges-1',
            "Not assessed": 'ges-2',
            "Not relevant": 'ges-3',
            "GES expected to be achieved later than 2020, no Article 14 exception reported": 'ges-4',
            "GES expected to be achieved later than 2020, Article 14 exception reported": 'ges-5',
            "GES expected to be achieved by 2020": 'ges-6',
            "GES achieved": 'ges-7',
        }

        return colors.get(value, 'ges-1')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        data = self.get_ges_extent_data()

        out = []

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = []

                for feature in DESCRIPTORS_FEATURES[descriptor]:
                    feature_data = []

                    for country_id, country_name in self.available_countries:
                        v = [
                            x.GESAchieved
                            for x in data
                            if (x.CountryCode == country_id and
                                x.Feature == feature)
                        ]
                        v = v and v[0] or ''

                        feature_data.append(v)

                    descriptor_data.append((get_label(feature, 'features'),
                                           feature_data))

                descriptor_type_data.append([
                    self.get_descriptor_title(descriptor), descriptor_data])

            out.append([descr_type, descriptor_type_data])

        return out


@register_section
class EnvironmentalTargets(RegionalDescriptorsSimpleTable,
                           PressureTableMarineEnv):
    title = 'Environmental targets on pressures'
    _id = 'reg-overview-env-target'
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        # setup data to be available at 'features_pressures_data' attr
        self.get_features_pressures_data()
        data = self.features_pressures_data

        out = []
        general_pressures = set(['PresAll', ])  # 'Unknown'

        for theme, features_for_theme in self.features_needed:
            theme_data = []
            theme_general_pressures = set([
                x
                for x in features_for_theme
                if x.endswith('All')
            ])

            for feature in features_for_theme:
                if feature.endswith('All'):
                    continue

                feature_data = []
                for country_id, country_name in self.available_countries:
                    # if pressure is ending with 'All' it applies to all
                    # features in the current theme
                    targets_rep = []

                    for x in data:
                        targets = x[3]
                        ccode = x[0]

                        if not targets:
                            continue

                        if ccode != country_id:
                            continue

                        feats = set(x[2].split(','))

                        if(feature in feats
                            or general_pressures.intersection(feats)
                            or theme_general_pressures.intersection(feats)):

                            targets_rep.extend(targets.split(','))

                    targets_count = len(set(targets_rep))

                    feature_data.append(targets_count)

                theme_data.append(
                    (self.get_feature_short_name(feature), feature_data)
                )

            out.append((theme, theme_data))

        return out


@register_section
class MeasuresPressures(RegionalDescriptorsSimpleTable, ProgrammesOfMeasures):
    title = 'Measures on pressures'
    _id = 'reg-overview-meas'
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        # setup data to be available at 'features_pressures_data' attr
        self.get_features_pressures_data()
        data = self.features_pressures_data
        measures_data = self.get_measures_data()

        out = []
        general_pressures = set(['PresAll', ])  # 'Unknown'

        for theme, features_for_theme in self.features_needed:
            theme_data = []
            theme_general_pressures = set([
                x
                for x in features_for_theme
                if x.endswith('All')
            ])

            for feature in features_for_theme:
                if feature.endswith('All'):
                    continue

                feature_data = []
                for country_id, country_name in self.available_countries:
                    # if pressure is ending with 'All' it applies to all
                    # features in the current theme
                    targets_rep = []

                    for x in data:
                        targets = x[3]
                        ccode = x[0]

                        if not targets:
                            continue

                        if ccode != country_id:
                            continue

                        feats = set(x[2].split(','))

                        if(feature in feats
                            or general_pressures.intersection(feats)
                            or theme_general_pressures.intersection(feats)):

                            targets_rep.extend(targets.split(','))

                    targets_rep = set(targets_rep)

                    measures = [
                        r.Measures.split(',')
                        for r in measures_data
                        if r.TargetCode in targets_rep
                    ]
                    measures_flat = [
                        measure
                        for sublist in measures
                        for measure in sublist
                    ]

                    feature_data.append(len(set(measures_flat)))

                theme_data.append(
                    (self.get_feature_short_name(feature), feature_data)
                )

            out.append((theme, theme_data))

        return out


@register_section
class ExceptionsGESAchieved(RegionalDescriptorsSimpleTable,
                            ExceptionsReported):
    title = 'Exceptions reported when targets or GES cannot be achieved'
    _id = 'reg-overview-exception'
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')

    @property
    def country_code(self):
        countries = [x[0] for x in self.available_countries]

        return countries

    def setup_data(self):
        data = self.get_ges_extent_data()

        out = []

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = []

                for country_id, country_name in self.available_countries:
                    rep_data = [
                        row.ReportingDate.year
                        for row in data
                        if row.InfoText == descriptor.split('.')[0] and
                           row.MemberState.strip() == country_id
                    ]
                    # TODO get exception type
                    exception_year = ''

                    if rep_data:
                        exception_year = rep_data[0]

                    descriptor_data.append(exception_year)

                descriptor_type_data.append([
                    self.get_descriptor_title(descriptor), descriptor_data])

            out.append([descr_type, descriptor_type_data])

        return out


class BaseNationalAssessmentOverviewTable(RegionalDescriptorsSimpleTable,
                                          PressureTableMarineEnv):

    template = ViewPageTemplateFile('pt/overview-assessment-summary.pt')
    section = 'national'

    def setup_data(self):
        self.table_headers = []

        out = []

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = []

                for country_id, country_name in self.available_countries:
                    data = NATIONAL_ASSESSMENT_DATA[country_id]
                    regions = set([
                        x[0]
                        for x in data
                        if (x[0] == self.region_code
                            or x[0] in self.subregions)
                    ])

                    if country_name not in [x[0] for x in self.table_headers]:
                        self.table_headers.append((country_name, regions))

                    for region in regions:
                        __key = (region, descriptor, self.article, self.year)
                        val = data[__key]

                        if not val:
                            val = ['Not assessed', '3']

                        descriptor_data.append(val)

                descriptor_type_data.append([
                    self.get_descriptor_title(descriptor), descriptor_data])

            out.append([descr_type, descriptor_type_data])

        return out


@register_section
class Article92012(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 9 - Determination of GES (2012)'
    _id = 'reg-overview-art9-2012'
    year = '2012'
    article = 'Art9'


@register_section
class Article82012(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 8 (Assessments) (2012)'
    _id = 'reg-overview-art8-2012'
    year = '2012'
    article = 'Art8'


@register_section
class Article102012(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 10 (Environmental targets) (2012)'
    _id = 'reg-overview-art10-2012'
    year = '2012'
    article = 'Art10'


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
class Article92018(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 9 - Determination of GES (2018)'
    _id = 'reg-overview-art9-2018'
    year = '2018'
    article = 'Art9'


@register_section
class Article82018(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 8 (Assessments) (2018)'
    _id = 'reg-overview-art8-2018'
    year = '2018'
    article = 'Art8'


@register_section
class Article102018(BaseNationalAssessmentOverviewTable):
    title = 'Implementation of Art. 10 (Environmental targets) (2018)'
    _id = 'reg-overview-art10-2018'
    year = '2018'
    article = 'Art10'


@register_section
class Implementation2017Decision(RegionalDescriptorsSimpleTable):
    title = 'Implementation of 2017 Decision reporting scales/areas (2018)'
    _id = 'reg-overview-impl-2017'


@register_section
class RegionalCoherence2012(RegionalDescriptorsSimpleTable,
                            RegDescriptorLevelAssessments,
                            PressureTableMarineEnv):
    title = 'Regional coherence: first cycle 2012-2017'
    _id = 'reg-overview-coh-2012'
    template = ViewPageTemplateFile('pt/overview-assessment-summary.pt')
    year = '2012'
    section = 'regional'

    def setup_data(self):
        out = []
        data = REGIONAL_ASSESSMENT_DATA[self.region_code]

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = []

                for article in self.ARTICLE_ORDER:
                    default = ['Not found', '3']

                    __key = (self.region_code, descriptor, article, self.year)
                    val = data.get(__key, default)

                    descriptor_data.append(val)

                descriptor_type_data.append([
                    self.get_descriptor_title(descriptor), descriptor_data])

            out.append([descr_type, descriptor_type_data])

        return out


@register_section
class RegionalCoherence2018(RegionalCoherence2012):
    title = 'Regional coherence: second cycle 2018-2023'
    _id = 'reg-overview-coh-2018'
    year = '2018'


class RegionalOverviewView(BaseRegSummaryView, AssessmentDataMixin):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Regional overview: {}".format(
                self.region_name,
            ),
            countries=", ".join([x[1] for x in self.available_countries]),
            can_translate=False
        )

        self.tables = [
            report_header,
            TableOfContents(self, self.request, SECTIONS),
        ]
        for klass in SECTIONS:
            rendered_table = klass(self, self.request)()
            self.tables.append(rendered_table)

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        # setup national assessment data
        for country_id, country_name in self.available_countries:
            self.setup_descriptor_level_assessment_data(country_id)
            country_data = self.overall_scores
            NATIONAL_ASSESSMENT_DATA[country_id] = country_data

        # setup regional assessment data
        view = RegDescriptorLevelAssessments(self, self.request)
        view.setup_descriptor_level_assessment_data()
        REGIONAL_ASSESSMENT_DATA[self.region_code] = view.overall_scores

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
