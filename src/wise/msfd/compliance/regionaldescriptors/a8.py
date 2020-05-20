from collections import Counter, defaultdict
from itertools import chain

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql  # , sql_extra
from wise.msfd.data import muids_by_country
from wise.msfd.gescomponents import (FEATURES_DB_2012, FEATURES_DB_2018,
                                     THEMES_2018_ORDER)
from wise.msfd.translation import get_translated
from wise.msfd.utils import ItemLabel, fixedorder_sortkey

from ..a8_utils import UtilsArticle8
from .base import BaseRegComplianceView, BaseRegDescRow
from .utils import compoundrow, compoundrow2012, newline_separated_itemlist


class RegDescA82018Row(BaseRegDescRow):
    year = '2018'

    def _sortkey(self, value, order):

        return fixedorder_sortkey(value, order)

    @compoundrow
    def get_feature_row(self):
        all_features = self.get_unique_values("Feature")
        themes_fromdb = FEATURES_DB_2018

        rows = []
        all_themes = defaultdict(list)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        all_themes = sorted(
            all_themes.items(),
            key=lambda t: fixedorder_sortkey(t[0], THEMES_2018_ORDER)
        )

        for theme, feats in all_themes:
            values = []

            for country_code, country_name in self.countries:
                value = []
                data = [
                    row.Feature

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and row.Feature
                ]
                count_features = Counter(data)

                for feature in feats:
                    cnt = count_features.get(feature, 0)

                    if not cnt:
                        continue

                    label = self.get_label_for_value(feature)
                    val = u"{} ({})".format(label, cnt)
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows

    @compoundrow
    def get_element_row(self):
        all_features = self.get_unique_values("Feature")
        themes_fromdb = FEATURES_DB_2018

        rows = []
        all_themes = defaultdict(list)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        all_themes = sorted(
            all_themes.items(),
            key=lambda t: fixedorder_sortkey(t[0], THEMES_2018_ORDER)
        )

        for theme, feats in all_themes:
            values = []

            for country_code, country_name in self.countries:
                value = []
                data = [
                    row

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and row.Feature
                ]

                crits = set([row.Criteria for row in data])

                for crit in crits:
                    elements_found = []

                    for feature in feats:
                        elements = [
                            row.Element

                            for row in data

                            if row.Feature == feature and row.Element
                            and row.Criteria == crit
                        ]

                        elements_found.extend(elements)

                    if elements_found:
                        elements_found = sorted(set(elements_found))
                        value.append(
                            u"{}: {}".format(crit, ", ".join(elements_found))
                        )

                value = set(value) or self.not_rep
                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows

    @compoundrow
    def get_element2_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.Element2

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Element2
            ]

            value = set(data) or self.not_rep
            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_element_source_row(self):
        rows = []
        values = []
        element_sources = self.get_unique_values('ElementSource')

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.ElementSource

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Element
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for elem_source in element_sources:
                found = [x for x in data if x == elem_source]
                value.append(u"{} ({})".format(elem_source, len(found)))

            values.append(newline_separated_itemlist(value))

        rows.append((u"No. of elements per level", values))

        return rows

    @compoundrow
    def get_crit_param_row(self):
        rows = []
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []

            for country_code, country_name in self.countries:
                data = [
                    row

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and row.Criteria == crit.id
                    # or row.GESComponent.split('/')[0] == crit.id)
                    and row.Parameter
                ]
                value = self.not_rep

                parameters = set([d.Parameter for d in data])
                _vals = []
                for param in parameters:
                    cnt = len([
                        r
                        for r in data
                        if r.Parameter == param
                    ])
                    _vals.append(u"{} ({})".format(
                        self.get_label_for_value(param), cnt)
                    )

                if data:
                    value = newline_separated_itemlist(_vals)

                values.append(value)

            rows.append((ItemLabel(crit.name, crit.title), values))

        return rows

    @compoundrow
    def get_threshold_value_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Parameter
            ]

            if not data:
                values.append(self.not_rep)

                continue

            total = len(data)
            thresholds = len([
                row for row in data

                if row.ThresholdValueUpper or row.ThresholdValueLower
            ])

            percentage = total and int((thresholds / float(total)) * 100) or 0

            value = u"{}% ({})".format(percentage, total)
            values.append(value)

        rows.append(('% of parameters with values (no. of parameters)',
                     values))

        return rows

    @compoundrow
    def get_threshold_source_row(self):
        rows = []
        threshs = self.get_unique_values('ThresholdValueSource')

        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []

            for country_code, country_name in self.countries:
                value = []
                data = [
                    row

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and row.Parameter
                ]

                for threshold_source in threshs:
                    found = [
                        x.ThresholdValueSource

                        for x in data

                        if x.ThresholdValueSource == threshold_source
                        and x.Criteria == crit.id
                    ]

                    if found:
                        value.append(u"{} ({})".format(
                            threshold_source, len(found))
                        )

                if not value:
                    values.append(self.not_rep)

                    continue

                values.append(newline_separated_itemlist(value))

            rows.append((ItemLabel(crit.name, crit.title), values))

        return rows

    @compoundrow
    def get_proportion_threshold_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.ProportionThresholdValue

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Parameter
            ]

            value = self.not_rep
            proportion_vals = [x for x in data if x]

            if proportion_vals:
                value = u"Range: {}-{}% ({} of {} parameters)".format(
                    int(min(proportion_vals)), int(max(proportion_vals)),
                    len(proportion_vals), len(data)
                )

            values.append(value)

        rows.append(('Range of % values (no. of parameters)', values))

        return rows

    @compoundrow
    def get_proportion_value_achieved_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.ProportionValueAchieved

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Parameter  # row.ProportionValueAchieved
            ]

            value = self.not_rep
            proportion_vals = [x for x in data if x]

            if proportion_vals:
                value = u"Range: {}-{}% ({} of {} parameters)".format(
                    int(min(proportion_vals)), int(max(proportion_vals)),
                    len(proportion_vals), len(data)
                )

            values.append(value)

        rows.append(('Range of % values (no. of parameters)', values))

        return rows

    @compoundrow
    def get_proportion_threshold_unit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.ProportionThresholdValueUnit

                for row in self.db_data

                if row.CountryCode == country_code
                and row.ProportionThresholdValueUnit
            ])

            value = self.not_rep

            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_trend_row(self):
        rows = []
        values = []
        trends = self.get_unique_values('Trend')
        order = ['Improving', 'Stable', 'Deteriorating', 'Unknown',
                 'Not relevant']

        trends = sorted(trends, key=lambda t: self._sortkey(t, order))

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.Trend

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Parameter
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for trend in trends:
                found = len([x for x in data if x == trend])

                percent = data and (float(found) / len(data) * 100) or 0
                value.append(
                    u"{0} ({1} or {2:.1f}%)".format(trend, found, percent)
                )

            values.append(newline_separated_itemlist(value, sort=False))

        rows.append((u'No. of trends per category', values))

        return rows

    @compoundrow
    def get_param_achieved_row(self):
        rows = []
        values = []
        param_achievs = self.get_unique_values('ParameterAchieved')
        order = ['Yes', 'Yes, based on low risk', 'No', 'Unknown',
                 'Not assessed']
        param_achievs = sorted(param_achievs,
                               key=lambda t: self._sortkey(t, order))

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.ParameterAchieved

                for row in self.db_data

                if row.CountryCode == country_code
                and row.Parameter
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for param in param_achievs:
                found = len([x for x in data if x == param])

                percent = data and (float(found) / len(data) * 100) or 0
                value.append(
                    u"{0} ({1} or {2:.1f}%)".format(param, found, percent)
                )

            values.append(newline_separated_itemlist(value, sort=False))

        rows.append(('No. of parameters per category', values))

        return rows

    @compoundrow
    def get_related_indicators_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            indicators = []
            data = [
                row.IndicatorCode

                for row in self.db_data

                if row.CountryCode == country_code
                and row.IndicatorCode
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for indic in data:
                splitted = indic.split(',')
                indicators.extend(splitted)

            values.append(newline_separated_itemlist(set(indicators)))

        rows.append((u'', values))

        return rows

    @compoundrow
    def get_crit_status_row(self):
        rows = []
        values = []
        crit_stats = self.get_unique_values('CriteriaStatus')
        order = ['Good', 'Good, based on low risk',
                 'Contributes to assessment of another criterion / ele',
                 'Not good', 'Unknown', 'Not assessed']

        crit_stats = sorted(crit_stats, key=lambda t: self._sortkey(t, order))

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.CriteriaStatus

                for row in self.db_data

                if row.CountryCode == country_code
                and row.CriteriaStatus
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for crit_stat in crit_stats:
                found = len([x for x in data if x == crit_stat])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    crit_stat, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value, sort=False))

        rows.append(('No. of criteria per category', values))

        return rows

    @compoundrow
    def get_elem_status_row(self):
        rows = []
        values = []
        elem_stats = self.get_unique_values('ElementStatus')
        order = ['Good', 'Good, based on low risk',
                 'Not good', 'Unknown', 'Not assessed']

        elem_stats = sorted(elem_stats, key=lambda t: self._sortkey(t, order))

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.ElementStatus

                for row in self.db_data

                if row.CountryCode == country_code
                and row.ElementStatus
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for elem in elem_stats:
                found = len([x for x in data if x == elem])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    elem, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value, sort=False))

        rows.append(('No. of elements per category', values))

        return rows

    @compoundrow
    def get_integration_type_param_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.IntegrationRuleTypeParameter

                for row in self.db_data

                if row.CountryCode == country_code
                and row.IntegrationRuleTypeParameter
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for param in set(data):
                found = len([x for x in data if x == param])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    param, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_desc_param_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            orig = []
            translated = []
            data = set([
                row.IntegrationRuleDescriptionParameter

                for row in self.db_data

                if row.CountryCode == country_code
                and row.IntegrationRuleDescriptionParameter
            ])

            if not data:
                values.append(self.not_rep)

                continue

            for description in data:
                transl = get_translated(description, country_code) or ''

                orig.append(description)
                translated.append(transl)

            value = (newline_separated_itemlist(orig),
                     newline_separated_itemlist(translated))

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_type_crit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.IntegrationRuleTypeCriteria

                for row in self.db_data

                if row.CountryCode == country_code
                and row.IntegrationRuleTypeCriteria
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for crit in set(data):
                found = len([x for x in data if x == crit])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    crit, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_desc_crit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            orig = []
            translated = []

            data = set([
                row.IntegrationRuleDescriptionCriteria

                for row in self.db_data

                if row.CountryCode == country_code
                and row.IntegrationRuleDescriptionCriteria
            ])

            if not data:
                values.append(self.not_rep)

                continue

            for description in data:
                transl = get_translated(description, country_code) or ''

                orig.append(description)
                translated.append(transl)

            value = (newline_separated_itemlist(orig),
                     newline_separated_itemlist(translated))

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_ges_extent_thresh_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                str(row.GESExtentThreshold)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.GESExtentThreshold
            ])

            value = self.not_rep

            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_ges_extent_achiev_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                str(row.GESExtentAchieved)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.GESExtentAchieved
            ])

            value = self.not_rep

            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_ges_extent_unit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                str(row.GESExtentUnit)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.GESExtentUnit
            ])

            value = self.not_rep

            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_ges_achiev_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                str(row.GESAchieved)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.GESAchieved
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for achiev in set(data):
                found = len([x for x in data if x == achiev])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    achiev, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_assess_period_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                str(row.AssessmentsPeriod)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.AssessmentsPeriod
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for period in set(data):
                found = len([x for x in data if x == period])
                total = len(data)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    period, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_related_press_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.PressureCodes.split(',')

                for row in self.db_data

                if row.CountryCode == country_code
                and row.PressureCodes
            ]

            pressures = [self.get_label_for_value(x) for x in chain(*data)]

            if not pressures:
                values.append(self.not_rep)

                continue

            for pressure in set(pressures):
                found = len([x for x in pressures if x == pressure])
                total = len(pressures)
                percentage = total and (found / float(total)) * 100 or 0

                text = u"{0} ({1} or {2:0.1f}%)".format(
                    pressure, found, percentage
                )
                value.append(text)

            values.append(newline_separated_itemlist(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_related_targets_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.TargetCodes.split(',')

                for row in self.db_data

                if row.CountryCode == country_code
                and row.TargetCodes
            ]

            targets = set([x for x in chain(*data)])

            value = self.not_rep

            if targets:
                value = len(targets)

            values.append(value)

        rows.append(('', values))

        return rows


class RegDescA82012(BaseRegComplianceView):
    session_name = '2012'
    year = "2012"
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    def __init__(self, context, request):
        super(RegDescA82012, self).__init__(context, request)
        self.region = context._countryregion_folder._subregions
        db.threadlocals.session_name = self.session_name

        # self.countries = countries_in_region(self.region)
        self.countries = [
            x[0] for x in context._countryregion_folder._countries_for_region
        ]
        self.all_countries = muids_by_country()

        self.utils_art8 = UtilsArticle8(self.descriptor)

        self.import_data = self.get_import_data()
        self.base_data = self.get_base_data()
        self.suminfo2_data = self.get_suminfo2_data()

        self.assessment_data = {}
        self.assessment_criteria_data = {}
        self.assessment_indicator_data = {}

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            assess_data = self.get_assessment_data(muids)
            self.assessment_data[country] = assess_data

            crit_data = self.get_assessment_criteria_data(assess_data)
            indic_data = self.get_assessment_indicator_data(assess_data)
            self.assessment_criteria_data[country] = crit_data
            self.assessment_indicator_data[country] = indic_data

        self.activity_data = self.get_activity_data()
        self.metadata_data = self.get_metadata_data()

        self.allrows = [
            self.compoundrow2012('Member state', self.get_countries()),
            self.compoundrow2012('Marine reporting units',
                                 self.get_marine_unit_id_nrs()),
            # TODO hard to implement
            # it is complicated to match the 'Topic' from base table with the
            # 'Feature' (SumInfo2) from _SumInfo2_ImpactedElements table
            # not all records from base table have relation to SumInfo2 table
            self.compoundrow2012('Features',
                                 self.get_features_row()),

            self.compoundrow2012('Elements',
                                 self.get_elements_row()),
            self.compoundrow2012('Criteria used',
                                 self.get_criteria_row()),
            self.compoundrow2012('Threshold values',
                                 self.get_threshold_values_row()),
            self.compoundrow2012('Proportion threshold values',
                                 self.get_proportion_threshold_values_row()),
            self.compoundrow2012('Baseline',
                                 self.get_baseline_row()),
            self.compoundrow2012('Proportion values achieved',
                                 self.get_proportion_values_achiev_row()),
            self.compoundrow2012('Assessment trend (status)',
                                 self.get_assessment_trend_row()),
            self.compoundrow2012('Criteria status',
                                 self.get_criteria_status_row()),
            self.compoundrow2012('Assessment period',
                                 self.get_assessment_period_row()),
            self.compoundrow2012('Related activities',
                                 self.get_related_activities_row()),
        ]

    def get_countries(self):
        rows = [('', self.countries)]

        return rows
        # return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        rows = [
            ('Number used',
             [len(self.all_countries.get(c, [])) for c in self.countries])
        ]

        return rows
        # return CompoundRow('MarineUnitID [Reporting area]', [row])

    def get_features_row(self):
        themes_fromdb = FEATURES_DB_2012
        rows = []
        feature_col = 'Topic'

        all_features = set([
            getattr(r, feature_col)

            for r in chain(*self.base_data.values())

            if getattr(r, feature_col) != 'InfoGaps'
        ])

        all_themes = defaultdict(list)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        for theme, feats in all_themes.items():
            values = []

            for country in self.countries:
                value = []
                muids = self.all_countries.get(country, [])

                for feature in feats:
                    data = [
                        r

                        for r in chain(*self.base_data.values())

                        if r.MarineUnitID in muids
                        and getattr(r, feature_col) == feature
                    ]

                    if not data:
                        continue

                    val = u"{} ({})".format(feature, len(data))
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows

    def get_elements_row(self):
        themes_fromdb = FEATURES_DB_2012
        rows = []

        # for tables MSFDb_ the feature column is 'SumInfo2'
        # for tables MSFDa_ the feature column is 'Summary2'
        feature_col_b = 'SumInfo2'
        feature_col_a = 'Summary2'

        def get_feature(obj):
            if hasattr(obj, feature_col_b):
                return getattr(obj, feature_col_b)

            return getattr(obj, feature_col_a)

        all_features = set([
            get_feature(r)

            for r in chain(*self.suminfo2_data.values())
        ])

        all_themes = defaultdict(list)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        for theme, feats in all_themes.items():
            values = []

            for country in self.countries:
                value = []
                muids = self.all_countries.get(country, [])

                for feature in feats:
                    data = [
                        r

                        for r in chain(*self.suminfo2_data.values())

                        if r.MarineUnitID in muids
                        and get_feature(r) == feature
                    ]

                    if not data:
                        continue

                    val = u"{} ({})".format(feature, len(data))
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows

    def get_criteria_row(self):
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        rows = []

        for crit in criterions:
            crit_ids = crit.all_ids()

            if crit.is_descriptor():
                crit_ids = [crit.id]

            values = []

            for country in self.countries:
                crit_data = self.assessment_criteria_data[country]
                indic_data = self.assessment_indicator_data[country]

                crit_vals = set([
                    row.CriteriaType

                    for row in chain(*crit_data.values())

                    if row.CriteriaType in crit_ids
                ])
                indic_vals = set([
                    row.GESIndicators

                    for row in chain(*indic_data.values())

                    if row.GESIndicators in crit_ids
                ])

                value = ", ".join(list(crit_vals) + list(indic_vals))

                values.append(value)

            row = (crit.title, values)
            rows.append(row)

        return rows

    def get_threshold_values_row(self):
        values = []

        for c in self.countries:
            indic_data = self.assessment_indicator_data[c]
            data = [
                x.ThresholdValue

                for x in chain(*indic_data.values())
            ]
            total = len(data)
            threshs = len([x for x in data if x])

            percentage = total and (threshs / float(total)) * 100 or 0.0
            value = u"{:0.1f}% ({})".format(percentage, total)

            values.append(value)

        rows = [('% of indicators with values (no. of indicators reported)',
                 values)]

        return rows

    def get_proportion_threshold_values_row(self):
        values = []

        for c in self.countries:
            value = self.not_rep

            indic_data = self.assessment_indicator_data[c]
            data = [
                x.ThresholdProportion

                for x in chain(*indic_data.values())
            ]

            if data:
                total = len(data)
                min_ = min(data)
                max_ = max(data)

                value = u"{} - {} ({})".format(min_, max_, total)

            values.append(value)

        rows = [('Range of % values (no. of indicators reported)',
                 values)]

        return rows

    def get_baseline_row(self):
        values = []

        for c in self.countries:
            value = []
            indic_data = self.assessment_indicator_data[c]
            data = [
                x.Baseline

                for x in chain(*indic_data.values())

                if x.Baseline
            ]

            for baseline in set(data):
                count_ = len([x for x in data if x == baseline])
                value.append(u"{} ({})".format(baseline, count_))

            values.append(newline_separated_itemlist(value))

        rows = [('No. of indicators reported per response',
                 values)]

        return rows

    def get_proportion_values_achiev_row(self):
        values = []

        def get_suminfo(obj):
            if hasattr(obj, 'SumInfo1'):
                return getattr(obj, 'SumInfo1')

            return getattr(obj, 'Summary1')

        for country in self.countries:
            value = []
            muids = self.all_countries.get(country, [])

            data = [
                get_suminfo(x)

                for x in chain(*self.base_data.values())

                if x.MarineUnitID in muids and get_suminfo(x)
                and x.Topic != 'InfoGaps'
            ]
            total = len(data)

            for suminfo in set(data):
                count_ = len([x for x in data if x == suminfo])
                percent = total and (count_ / float(total)) * 100 or 0.0

                value.append(u"{} ({} or {:0.1f}%)".format(
                    suminfo, count_, percent)
                )

            values.append(newline_separated_itemlist(value))

        rows = [('No. of criteria reported per category',
                 values)]

        return rows

    def get_assessment_trend_row(self):
        values = []

        def get_status_trend(obj):
            if hasattr(obj, 'StatusTrend'):
                return getattr(obj, 'StatusTrend')

            return getattr(obj, 'TrendStatus')

        for country in self.countries:
            value = []
            assess_data = self.assessment_data[country]

            data = [
                get_status_trend(x)

                for x in chain(*assess_data.values())

                if get_status_trend(x)
            ]
            total = len(data)

            for suminfo in set(data):
                count_ = len([x for x in data if x == suminfo])
                percent = total and (count_ / float(total)) * 100 or 0.0

                value.append(u"{} ({} or {:0.1f}%)".format(
                    suminfo, count_, percent)
                )

            values.append(newline_separated_itemlist(value))

        rows = [('No. of criteria assessments per category',
                 values)]

        return rows

    def get_criteria_status_row(self):
        values = []

        for country in self.countries:
            value = []
            assess_data = self.assessment_data[country]

            data = [
                x.Status

                for x in chain(*assess_data.values())

                if x.Status
            ]
            total = len(data)

            for suminfo in set(data):
                count_ = len([x for x in data if x == suminfo])
                percent = total and (count_ / float(total)) * 100 or 0.0

                value.append(u"{} ({} or {:0.1f}%)".format(
                    suminfo, count_, percent)
                )

            values.append(newline_separated_itemlist(value))

        rows = [('No. of criteria assessments per category',
                 values)]

        return rows

    def get_assessment_period_row(self):
        values = []

        for country in self.countries:
            value = []
            muids = self.all_countries.get(country, [])

            data = [
                x

                for x in chain(*self.metadata_data.values())

                if x.Topic == 'Assessment' and x.AssessmentDateStart
                and x.MarineUnitID in muids
            ]

            for row in data:
                value.append(u"{} - {}".format(
                    row.AssessmentDateStart, row.AssessmentDateEnd)
                )

            values.append(newline_separated_itemlist(value))

        rows = [('', values)]

        return rows

    def get_related_activities_row(self):
        values = []

        for country in self.countries:
            muids = self.all_countries.get(country, [])

            data = [
                x.Activity

                for x in chain(*self.activity_data.values())

                if x.Activity and x.MarineUnitID in muids
            ]
            value = ", ".join(sorted(set(data)))

            values.append(value)

        rows = [('', values)]

        return rows

    def __call__(self):
        return self.template(rows=self.allrows)

    @property
    def available_countries(self):
        return [(x, x) for x in self.countries]

    def compoundrow2012(self, title, rows):
        return compoundrow2012(self, title, rows)

    def get_metadata_data(self):
        tables = self.base_data.keys()

        results = {}

        for table in tables:
            meta = 't_{}Metadata'.format(table)

            mc_meta = getattr(sql, meta, None)

            if mc_meta is None:
                continue

            col_id = '{}_ID'.format(table)
            base_ids = [getattr(x, col_id) for x in self.base_data[table]]

            _, res = db.get_all_records(
                mc_meta,
                getattr(mc_meta.c, col_id).in_(base_ids)
            )

            results[table] = res

        return results

    def get_activity_data(self):
        tables = self.base_data.keys()

        results = {}

        for table in tables:
            act = '{}Activity'.format(table.replace('_', ''))
            act_descr = '{}ActivityDescription'.format(table.replace('_', ''))

            mc_act = getattr(sql, act, None)
            mc_act_d = getattr(sql, act_descr, None)

            if not mc_act:
                continue

            col_id = '{}_ID'.format(table)
            base_ids = [getattr(x, col_id) for x in self.base_data[table]]

            _, res = db.get_all_records_join(
                [mc_act.Activity, getattr(mc_act_d, table),
                 getattr(mc_act_d, 'MarineUnitID')],
                mc_act_d,
                getattr(mc_act_d, table).in_(base_ids)
            )

            results[table] = res

        return results

    def get_assessment_data(self, muids):
        tables = self.base_data.keys()

        results = {}

        for table in tables:
            suffix = 'Assesment'

            if table.startswith('MSFD8a'):
                suffix = 'StatusAssessment'

            mc_name = '{}{}'.format(table.replace('_', ''), suffix)
            mc = getattr(sql, mc_name, None)

            if not mc:
                continue

            col_id = '{}_ID'.format(table)
            base_ids = [
                getattr(x, col_id)

                for x in self.base_data[table]

                if x.MarineUnitID in muids
            ]

            _, res = db.get_all_records(
                mc,
                getattr(mc, table).in_(base_ids)
            )

            results[table] = res

        return results

    def get_assessment_criteria_data(self, assess_data):
        assessment_data = assess_data  # self.get_assessment_data(muids)
        tables = assessment_data.keys()
        results = {}

        for table in tables:
            # MSFD8b_Nutrients or MSFD8a_Species
            assess_suffix = 'Assesment'
            crit_suffix = 'AssesmentCriterion'

            if table.startswith('MSFD8a'):
                assess_suffix = 'StatusAssessment'
                crit_suffix = 'StatusCriteria'

            assess_col_id = '{}_{}_ID'.format(table, assess_suffix)
            assess_ids = [
                getattr(x, assess_col_id)

                for x in assessment_data[table]
            ]

            crit_mc_name = '{}{}'.format(table.replace('_', ''), crit_suffix)
            crit_mc = getattr(sql, crit_mc_name, None)

            if not crit_mc:
                continue

            crit_col_id = '{}_{}'.format(table, assess_suffix)

            _, res = db.get_all_records(
                crit_mc,
                getattr(crit_mc, crit_col_id).in_(assess_ids)
            )

            results[table] = res

        return results

    def get_assessment_indicator_data(self, assess_data):
        assessment_data = assess_data  # self.get_assessment_data(muids)
        tables = assessment_data.keys()
        results = {}

        for table in tables:
            # MSFD8b_Nutrients or MSFD8a_Species
            assess_suffix = 'Assesment'
            crit_suffix = 'AssesmentIndicator'

            if table.startswith('MSFD8a'):
                assess_suffix = 'StatusAssessment'
                crit_suffix = 'StatusIndicator'

            assess_col_id = '{}_{}_ID'.format(table, assess_suffix)
            assess_ids = [
                getattr(x, assess_col_id)

                for x in assessment_data[table]
            ]

            crit_mc_name = '{}{}'.format(table.replace('_', ''), crit_suffix)
            crit_mc = getattr(sql, crit_mc_name, None)

            if not crit_mc:
                continue

            crit_col_id = '{}_{}'.format(table, assess_suffix)

            _, res = db.get_all_records(
                crit_mc,
                getattr(crit_mc, crit_col_id).in_(assess_ids)
            )

            results[table] = res

        return results

    def get_import_data(self):
        tables = self.utils_art8.tables
        import_res = {}

        for table in tables:
            if table.startswith('MSFD8a'):
                prefix = 'MSFD8a'
            else:
                prefix = 'MSFD8b'

            mc = getattr(sql, '{}Import'.format(prefix))
            region = '{}_Import_ReportingRegion'.format(prefix)
            country = '{}_Import_ReportingCountry'.format(prefix)
            id_ = '{}_Import_ID'.format(prefix)

            col_region = getattr(mc, region)
            count, res = db.get_all_records(
                mc,
                col_region.in_(self.region)
            )

            result = {}

            for row in res:
                c = getattr(row, country)
                i = getattr(row, id_)
                result[c] = i

            import_res[table] = result

        return import_res

    def get_base_data(self):
        tables = self.utils_art8.tables

        results = {}

        for table in tables:
            mc = self.utils_art8.get_base_mc(table)
            conditions = []

            col_id = getattr(mc, '{}_Import'.format(table))

            conditions.append(col_id.in_(self.import_data[table].values()))

            _, res = db.get_all_records(
                mc,
                *conditions
            )

            results[table] = res

        return results

    def get_suminfo2_data(self):
        tables = self.base_data.keys()

        results = {}

        for table in tables:
            suffix = 'SumInfo2ImpactedElement'

            if table.startswith('MSFD8a'):
                suffix = 'Summary2'

            mc_name = '{}{}'.format(table.replace('_', ''), suffix)
            mc = getattr(sql, mc_name, None)

            if not mc:
                continue

            col_id = '{}_ID'.format(table)
            base_ids = [getattr(x, col_id) for x in self.base_data[table]]

            _, res = db.get_all_records(
                mc,
                getattr(mc, table).in_(base_ids)
            )

            results[table] = res

        return results
