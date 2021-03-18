# -*- coding: utf-8 -*-

from collections import defaultdict
import logging

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from Products.statusmessages.interfaces import IStatusMessage

from wise.msfd import db, sql2018
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.compliance.utils import group_by_mru
from wise.msfd.data import (get_all_report_filenames,
                            get_envelope_release_date, get_factsheet_url,
                            get_report_file_url, get_report_filename,
                            get_xml_report_data)
from wise.msfd.gescomponents import (ANTHROPOGENIC_FEATURES_SHORT_NAMES,
                                     DESCRIPTOR_TYPES, FEATURES_DB_2018,
                                     NOTHEME, THEMES_2018_ORDER)
from wise.msfd.labels import get_label
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, fixedorder_sortkey, items_to_rows,
                             timeit)

from ..nationaldescriptors.data import get_report_definition
from ..nationaldescriptors.reportdata import ReportData2018Secondary
from ..nationaldescriptors.proxy import Proxy2018
from .assessmentsummary import SummaryAssessment
from .base import BaseNatSummaryView
from .introduction import ReportingHistoryTable


logger = logging.getLogger('wise.msfd')


class ItemListOverview(ItemList):
    template = PageTemplateFile('pt/list.pt')


class ReportData2018SecondaryOverview(ReportData2018Secondary,
                                      BaseNatSummaryView):
    is_translatable = False
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header-secondary.pt'
    )

    @property
    def descriptor(self):
        return 'Not linked'

    @property
    def muids(self):
        return []

    @property
    def country_region_code(self):
        return 'No region'

    def render_reportdata(self):
        """
        1. Get all reported files under Article 7 or 3/4
        2. Render the data separately for all files
        3. Concat the rendered htmls into a single

        :return: rendered html
        """

        template = self.get_template(self.article)
        urls = get_all_report_filenames(self.country_code, self.article)

        rendered_results = []

        for (index, url) in enumerate(urls[:1]):
            prev_url = url
            view = self.get_implementation_view(url, prev_url)

            # Report Header
            report_date = get_envelope_release_date(url)

            view()      # updates the view
            data = [Proxy2018(row, self) for row in view.cols]

            if self.article == 'Art7':
                data_by_mru = group_by_mru(data)
            else:
                data_by_mru = {'no mru': data}

            fields = get_report_definition(
                self.year, self.article).get_fields()
            fields_filtered = [
                f for f in fields
                if self.render_sections.get(f.section, True)
            ]

            res = []

            for mru, rows in data_by_mru.items():
                _rows = items_to_rows(rows, fields_filtered)

                res.append((mru, _rows))

            report_header = self.report_header_template(
                title=self.title,
                report_date=report_date.date(),
                show_navigation=False,
                article_name=self.article_name
            )

            rendered_results.append(template(data=res,
                                             report_header=report_header,
                                             show_navigation=False))

        res = "<hr/>".join(rendered_results)

        return res or "No data found"

    def __call__(self):
        return self.render_reportdata()


class Article7Table(ReportData2018SecondaryOverview):
    article = 'Art7'
    title = 'Who is responsible for MSFD implementation?'
    render_sections = {}


class Article34TableMarineWaters(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Where is the MSFD implemented?'
    article_name = 'Art. 3(1) Marine waters'
    render_sections = {
        'marine_waters': True,
        'marine_areas': False,
        'cooperation': False,
    }


class Article34TableMarineAreas(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Areas for MSFD reporting'
    article_name = 'Art. 4/2017 Decision: Marine regions, subregions, ' \
                   'and subdivisions'
    render_sections = {
        'marine_waters': False,
        'marine_areas': True,
        'cooperation': False,
    }


class Article34TableCooperation(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Regional cooperation'
    article_name = 'Art. 5(2) and Art. 6 Regional cooperation'
    render_sections = {
        'marine_waters': False,
        'marine_areas': False,
        'cooperation': True,
    }


class AssessmentSummary2018(BaseNatSummaryView, AssessmentDataMixin):
    template = ViewPageTemplateFile('pt/summary-assessment-overview-2018.pt')
    year = '2018'
    cycle = 'Second cycle'
    cycle_year = '2018-2023'

    def __call__(self):
        self.setup_descriptor_level_assessment_data()

        table = SummaryAssessment(self, self.request, self.overall_scores,
                                  self.nat_desc_country_folder, self.year)

        self.summary_assess_data = table.setup_data()
        macro_assess_sum = table.template.macros['assessment-summary-table']

        return self.template(macro_assess_sum=macro_assess_sum)


class AssessmentSummary2012(AssessmentSummary2018):
    year = '2012'
    cycle = 'First cycle'
    cycle_year = '2012-2017'


class ReportingHistoryTableOverview(ReportingHistoryTable):
    show_header = True
    obligations_needed = None  # meaning we need all obligations
    view_template = ViewPageTemplateFile('pt/overview-report-history.pt')

    @property
    def all_obligations(self):
        data = self.data

        obligations = set([x.get('ReportingObligation') for x in data])

        return [[o] for o in obligations]

    def __call__(self):

        self.table = super(ReportingHistoryTableOverview, self).__call__()

        return self.view_template()


class PressuresTableBase(BaseNatSummaryView):
    template = ViewPageTemplateFile('pt/overview-press-marine-env-table.pt')
    features = FEATURES_DB_2018

    needed_subjects = (
        'Anthropogenic pressures on the marine environment',
    )
    column_header = "GES Descriptors"

    @timeit
    @db.use_db_session('2018')
    def get_data_art8(self):
        t = sql2018.t_V_ART8_GES_2018

        count, data = db.get_all_specific_columns(
            [t.c.GESComponent, t.c.PressureCodes, t.c.TargetCodes],
            t.c.CountryCode == self.country_code,
            t.c.PressureCodes.isnot(None)
        )

        return data

    def get_features_pressures_data(self):
        data = self.get_data_art8()
        out = defaultdict(set)

        for row in data:
            gescomp = row.GESComponent
            presscodes = set(row.PressureCodes.split(','))

            if '/' in row.GESComponent:
                gescomp = gescomp.split('/')[0]

            out[gescomp].update(presscodes)

        return out

    @property
    def report_access(self):
        nat_sum_id = 'national-descriptors-assessments'
        ccode = self.country_code.lower()
        cfolder = self._compliance_folder[nat_sum_id][ccode]
        url = cfolder.absolute_url() + '/reports'

        return url

    def get_feature_short_name(self, code):
        for _code, _name in ANTHROPOGENIC_FEATURES_SHORT_NAMES:
            if _code == code:
                return _name

        if code in self.features:
            return self.features.get[code].label

        return code

    def get_features_by_subject(self, subjects):
        features_order = [
            x[0]
            for x in ANTHROPOGENIC_FEATURES_SHORT_NAMES
        ]

        filtered = defaultdict(list)

        for k, v in self.features.items():
            if v.subject not in subjects:
                continue

            filtered[v.theme].append(v.name)

        out = [
            (k, sorted(v, key=lambda i: fixedorder_sortkey(i, features_order)))
            for k, v in filtered.items()
        ]

        sorted_out = sorted(
            out, key=lambda i: fixedorder_sortkey(i[0], THEMES_2018_ORDER)
        )

        return sorted_out

    @property
    def features_needed(self):
        return self.get_features_by_subject(self.needed_subjects)

    def __call__(self):
        return self.template()


class UsesHumanActivities(PressuresTableBase):
    section_title = 'Uses and human activities and their pressures ' \
                    'on marine environment'
    title = 'Analysis of predominant pressures and impacts, ' \
            'including human activity (Art. 8(1)(b))'
    column_header = "Uses and human activities (MSFD Annex III, Table 2b)"

    @property
    def uses_activities_features(self):
        subjects = (
            'Uses and human activities in or affecting the marine environment',
        )
        uses_activities = self.get_features_by_subject(subjects)
        filtered = [x for x in uses_activities if x[0] != 'No theme']

        return filtered

    @timeit
    @db.use_db_session('2018')
    def get_features_pressures_data(self):
        sess = db.session()
        esa_mru = sql2018.ART8ESAMarineUnit
        rep_info = sql2018.ReportedInformation
        esa_feat = sql2018.ART8ESAFeature
        esa_uses = sql2018.ART8ESAUsesActivity
        esa_uses_p = sql2018.ART8ESAUsesActivitiesPressure

        columns = [
            esa_mru.MarineReportingUnit, esa_feat.Feature,
            esa_uses_p.PressureCode
        ]

        conditions = [
            rep_info.Schema == 'ART8_ESA',
            rep_info.CountryCode == self.country_code
        ]

        res = sess.query(*columns) \
            .join(rep_info, esa_mru.IdReportedInformation == rep_info.Id) \
            .join(esa_feat, esa_feat.IdMarineUnit == esa_mru.Id) \
            .join(esa_uses, esa_uses.IdFeature == esa_feat.Id) \
            .join(esa_uses_p, esa_uses_p.IdUsesActivities == esa_uses.Id) \
            .filter(*conditions).distinct()

        out = defaultdict(set)

        for row in res:
            activ_feat = row.Feature
            press_code = row.PressureCode

            out[activ_feat].add(press_code)

        return out

    def data_table(self):
        data = self.get_features_pressures_data()

        out = []

        # general_pressures = set(['PresAll', 'Unknown'])

        for activ_theme, activ_features in self.uses_activities_features:
            descriptor_type_data = []

            for activ_feat in activ_features:
                features_rep = data.get(activ_feat, set())
                descriptor_data = []

                # we iterate on all pressures 'Non-indigenous species',
                # 'Microbial pathogens' etc. and check if the pressures
                # was reported for the current descriptor and feature
                for theme, features_for_theme in self.features_needed:
                    for feature in features_for_theme:
                        if feature.endswith('All'):
                            continue

                        # if pressure is ending with 'All' it applies to all
                        # features in the current theme
                        pressures = filter(
                            lambda i: i.endswith('All') or i == feature,
                            list(features_rep.intersection(
                                set(features_for_theme))
                            )
                        )

                        # These pressures apply to all themes and features
                        # general_pressures_reported = list(
                        #     general_pressures.intersection(features_rep)
                        # )

                        # pressures.extend(general_pressures_reported)

                        pressures = [
                            self.get_feature_short_name(x)
                            for x in pressures
                        ]

                        descriptor_data.append(ItemListOverview(pressures))

                descriptor_type_data.append((get_label(activ_feat, 'features'),
                                             descriptor_data))

            out.append((activ_theme, descriptor_type_data))

        return out


class PressureTableMarineEnv(PressuresTableBase):
    section_title = 'Pressures affecting environmental status'
    title = 'Assessments of current environental status and pressures ' \
            'and impacts (Art. 8(1)(a)(b))'

    def data_table(self):
        data = self.get_features_pressures_data()

        out = []

        general_pressures = set(['PresAll', 'Unknown'])

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                features_rep = data[descriptor]
                descriptor_data = []

                # we iterate on all pressures 'Non-indigenous species',
                # 'Microbial pathogens' etc. and check if the pressures
                # was reported for the current descriptor and feature
                for theme, features_for_theme in self.features_needed:
                    for feature in features_for_theme:
                        if feature.endswith('All'):
                            continue

                        # if pressure is ending with 'All' it applies to all
                        # features in the current theme
                        pressures = filter(
                            lambda i: i.endswith('All') or i == feature,
                            list(features_rep.intersection(
                                set(features_for_theme))
                            )
                        )

                        # These pressures apply to all themes and features
                        general_pressures_reported = list(
                            general_pressures.intersection(features_rep)
                        )

                        pressures.extend(general_pressures_reported)

                        pressures = [
                            self.get_feature_short_name(x)
                            for x in pressures
                        ]

                        descriptor_data.append(ItemListOverview(pressures))

                descriptor_type_data.append((descriptor, descriptor_data))

            out.append((descr_type, descriptor_type_data))

        return out


class GESExtentAchieved(PressuresTableBase):
    template = ViewPageTemplateFile('pt/overview-ges-extent-table.pt')

    section_title = 'Current environmental status and extent to ' \
                    'which GES is achieved'
    title = 'Assessments of current environental status and ' \
            'pressures and impacts (Art. 8(1)(a)(b))'

    def data_table(self):
        data = self.get_ges_extent_data()

        out = []

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                descriptor_data = [
                    row
                    for row in data
                    if row.GESComponent == descriptor
                ]

                descriptor_type_data.append((descriptor, descriptor_data))

            out.append((descr_type, descriptor_type_data))

        return out


class EnvironmentalTargetsTable(PressuresTableBase):
    section_title = 'Environmental targets to achieve GES'
    title = 'Environmental targets (Art. 10)'

    def get_env_targets_data(self):
        data = self.get_data_art8()
        out = defaultdict(set)

        for row in data:
            if not row.TargetCodes:
                continue

            gescomp = row.GESComponent

            if '/' in gescomp:
                gescomp = gescomp.split('/')[0]

            pressures = row.PressureCodes.split(',')
            targets = row.TargetCodes.split(',')

            for pressure in pressures:
                __key = '-'.join((gescomp, pressure))
                out[__key].update(targets)

        return out

    def data_table(self):
        pressures_data = self.get_features_pressures_data()
        env_targets_data = self.get_env_targets_data()
        out = []

        general_pressures = set(['PresAll', 'Unknown'])

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                features_rep = pressures_data[descriptor]
                descriptor_data = []

                # we iterate on all pressures 'Non-indigenous species',
                # 'Microbial pathogens' etc. and check if the pressures
                # was reported for the current descriptor and feature
                for theme, features_for_theme in self.features_needed:
                    for feature in features_for_theme:
                        if feature.endswith('All'):
                            continue

                        # if pressure is ending with 'All' it applies to all
                        # features in the current theme
                        pressures = filter(
                            lambda i: i.endswith('All') or i == feature,
                            list(features_rep.intersection(
                                set(features_for_theme))
                            )
                        )

                        # These pressures apply to all themes and features
                        general_pressures_reported = list(
                            general_pressures.intersection(features_rep)
                        )

                        pressures.extend(general_pressures_reported)

                        targets = set(sorted([
                            p
                            for press in pressures
                            for p in
                            env_targets_data['-'.join((descriptor, press))]
                        ]))

                        descriptor_data.append(ItemListOverview(targets))

                descriptor_type_data.append((descriptor, descriptor_data))

            out.append((descr_type, descriptor_type_data))

        return out


class ProgrammesOfMeasures(EnvironmentalTargetsTable):
    section_title = 'Measures to meet environmental targets and to achieve GES'
    title = 'Programme of measures (Art. 13)'
    column_header = "GES Descriptors"

    @db.use_db_session('2018')
    def get_measures_data(self):
        t = sql2018.t_V_ART10_Targets_2018

        count, data = db.get_all_specific_columns(
            [t.c.TargetCode, t.c.Measures],
            t.c.CountryCode == self.country_code,
            t.c.Measures.isnot(None)
        )

        return data

    def data_table(self):
        pressures_data = self.get_features_pressures_data()
        env_targets_data = self.get_env_targets_data()
        measures_data = self.get_measures_data()
        out = []

        general_pressures = set(['PresAll', 'Unknown'])

        for descr_type, descriptors in DESCRIPTOR_TYPES:
            descriptor_type_data = []

            for descriptor in descriptors:
                features_rep = pressures_data[descriptor]
                descriptor_data = []

                # we iterate on all pressures 'Non-indigenous species',
                # 'Microbial pathogens' etc. and check if the pressures
                # was reported for the current descriptor and feature
                for theme, features_for_theme in self.features_needed:
                    for feature in features_for_theme:
                        if feature.endswith('All'):
                            continue

                        # if pressure is ending with 'All' it applies to all
                        # features in the current theme
                        pressures = filter(
                            lambda i: i.endswith('All') or i == feature,
                            list(features_rep.intersection(
                                set(features_for_theme))
                            )
                        )

                        # These pressures apply to all themes and features
                        general_pressures_reported = list(
                            general_pressures.intersection(features_rep)
                        )

                        pressures.extend(general_pressures_reported)

                        targets = set(sorted([
                            p
                            for press in pressures
                            for p in
                            env_targets_data['-'.join((descriptor, press))]
                        ]))

                        # get the measures related to targets
                        measures = [
                            r.Measures.split(',')
                            for r in measures_data
                            if r.TargetCode in targets
                        ]
                        measures_flat = [
                            measure
                            for sublist in measures
                            for measure in sublist
                        ]

                        descriptor_data.append(ItemListOverview(measures_flat))

                descriptor_type_data.append((descriptor, descriptor_data))

            out.append((descr_type, descriptor_type_data))

        return out


class NationalOverviewView(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    def title(self):
        title = u"National overview: {}".format(self.country_name)

        return title

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.overview_header_template(
            title="National summary report: {}".format(
                self.country_name,
            )
        )
        self.tables = [
            report_header,
            Article7Table(self.context, self.request)(),
            Article34TableMarineWaters(self.context, self.request)(),
            Article34TableMarineAreas(self.context, self.request)(),
            Article34TableCooperation(self.context, self.request)(),
            UsesHumanActivities(self.context, self.request)(),
            PressureTableMarineEnv(self.context, self.request)(),
            EnvironmentalTargetsTable(self.context, self.request)(),
            ProgrammesOfMeasures(self.context, self.request)(),
            AssessmentSummary2012(self.context, self.request)(),
            AssessmentSummary2018(self.context, self.request)(),
            ReportingHistoryTableOverview(self.context, self.request)(),
            # trans_edit_html,
        ]

        return self.template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self.context.absolute_url())

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
