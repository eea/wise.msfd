from itertools import chain

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql  # , sql_extra
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.utils import CompoundRow, ItemLabel, ItemList, Row, TableHeader

from ..a8_utils import UtilsArticle8
from .base import BaseRegDescRow, BaseRegComplianceView
from .utils import compoundrow, compoundrow2012, newline_separated_itemlist


class RegDescA82018Row(BaseRegDescRow):
    year = '2018'

    @compoundrow
    def get_feature_row(self):
        rows = []
        features = self.get_unique_values("Feature")

        for feature in features:
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                        and feature == row.Feature
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            rows.append((self.make_item_label(feature), values))

        return rows

    @compoundrow
    def get_element_row(self):
        rows = []
        elements = self.get_unique_values('Element')

        for element in elements:
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.Element == element
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            rows.append((element, values))

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

                if data:
                    value = newline_separated_itemlist(
                        u"{} ({})".format(
                            self.get_label_for_value(d.Parameter), len(data)
                        )
                        for d in data
                    )

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

        rows.append(('% of parameters with values (no. of parameters)', values))

        return rows

    @compoundrow
    def get_threshold_source_row(self):
        rows = []
        threshs = self.get_unique_values('ThresholdValueSource')

        values = []
        for country_code, country_name in self.countries:
            value = []
            data = [
                row.ThresholdValueSource
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.Parameter
            ]
            if not data:
                values.append(self.not_rep)
                continue

            for threshold_source in threshs:
                found = [x for x in data if x == threshold_source]
                value.append(u"{} ({})".format(threshold_source, len(found)))

            values.append(newline_separated_itemlist(value))

        rows.append((u'No. of parameters per level', values))

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
                   and row.Parameter #row.ProportionValueAchieved
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

            values.append(newline_separated_itemlist(value))

        rows.append((u'No. of trends per category', values))

        return rows

    @compoundrow
    def get_param_achieved_row(self):
        rows = []
        values = []
        param_achievs = self.get_unique_values('ParameterAchieved')

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

            values.append(newline_separated_itemlist(value))

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

        rows.append((u'No. of trends per category', values))

        return rows

    @compoundrow
    def get_crit_status_row(self):
        rows = []
        values = []
        crit_stats = self.get_unique_values('CriteriaStatus')

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

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of criteria per category', values))

        return rows

    @compoundrow
    def get_elem_status_row(self):
        rows = []
        values = []
        elem_stats = self.get_unique_values('ElementStatus')

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

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of elements per category', values))

        return rows

    @compoundrow
    def get_integration_type_param_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.IntegrationRuleTypeParameter
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.IntegrationRuleTypeParameter
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_desc_param_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.IntegrationRuleDescriptionParameter
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.IntegrationRuleDescriptionParameter
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_type_crit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.IntegrationRuleTypeCriteria
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.IntegrationRuleTypeCriteria
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_desc_crit_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.IntegrationRuleDescriptionCriteria
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.IntegrationRuleDescriptionCriteria
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)
                # value = list(data)[0]

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
            data = set([
                str(row.GESAchieved)
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.GESAchieved
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_assess_period_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                str(row.AssessmentsPeriod)
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.AssessmentsPeriod
            ])

            value = self.not_rep
            if data:
                value = newline_separated_itemlist(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_related_press_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.PressureCodes.split(',')
                for row in self.db_data
                if row.CountryCode == country_code
                    and row.PressureCodes
            ]

            pressures = set([x for x in chain(*data)])

            value = self.not_rep
            if pressures:
                value = newline_separated_itemlist(pressures)

            values.append(value)

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
        self.region = context.country_region_code
        db.threadlocals.session_name = self.session_name

        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()

        self.utils_art8 = UtilsArticle8(self.descriptor)

        self.import_data = self.get_import_data()
        self.base_data = self.get_base_data()
        self.topics = self.get_topics()
        self.suminfo2_data = self.get_suminfo2_data()
        self.status_data = self.get_status_data()
        self.activity_data = self.get_activity_data()
        self.metadata_data = self.get_metadata_data()

        self.allrows = [
            self.compoundrow2012('Member state', self.get_countries()),
            self.compoundrow2012('MarineUnitID [Reporting area]',
                                 self.get_marine_unit_id_nrs()),
            # TODO show the reported value, or Reported/Not reported ??
            self.compoundrow2012(
                'PressureLevelN/P/Oconcentration/ '
                'ImpactsPressureWater/Seabed: '
                'SumInfo1 [ProportionValueAchieved]',
                self.get_suminfo1_row()
            ),
            self.compoundrow2012('ImpactsPressureWater/Seabed: SumInfo2',
                                 self.get_suminfo2_row()),
            self.compoundrow2012('Status [CriteriaStatus]',
                                 self.get_criteria_status_row()),
            self.compoundrow2012('ActivityType', self.get_activity_type_row()),
            self.compoundrow2012(
                'RecentTimeStart/RecentTimeEnd/'
                'AssessmentDateStart/AssessmentDateEnd '
                '[AssessmentPeriod]',
                self.get_assessment_date_row()
            ),
        ]

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
                [mc_act.Activity, getattr(mc_act_d, table)],
                mc_act_d,
                getattr(mc_act_d, table).in_(base_ids)
            )

            results[table] = res

        return results

    def get_status_data(self):
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
            base_ids = [getattr(x, col_id) for x in self.base_data[table]]

            _, res = db.get_all_records(
                mc,
                getattr(mc, table).in_(base_ids)
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
                col_region == self.region
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

    def get_topics(self):
        result = []

        for table, res in self.base_data.items():
            topics_needed = self.utils_art8.get_topic_conditions(table)

            topics = [x.Topic for x in res]
            topics = set(topics)

            if topics_needed:
                topics = list(set(topics_needed) & topics)

            result.extend(topics)

        result = sorted(set(result))

        return result

    def get_suminfo2_elements(self):
        # Summary2 for MSFD8a
        result = []

        for table, res in self.suminfo2_data.items():
            column = 'SumInfo2'

            if table.startswith('MSFD8a'):
                column = 'Summary2'

            elements = [getattr(x, column) for x in res]

            result.extend(elements)

        result = sorted(set(result))

        return result

    def get_base_value(self, country, topic, col_name):
        for table, res in self.base_data.items():
            for row in res:
                if row.Topic != topic:
                    continue

                import_id = self.import_data[table][country]
                import_col = '{}_Import'.format(table)

                if import_id != getattr(row, import_col, 0):
                    continue

                return getattr(row, col_name, '')

        return ''

    def get_countries(self):
        rows = [('', self.countries)]

        return rows
        # return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        rows = [
            ('Number used',
             [len(self.all_countries[c]) for c in self.countries])
        ]

        return rows
        # return CompoundRow('MarineUnitID [Reporting area]', [row])

    def get_suminfo1_row(self):
        col_name = 'SumInfo1'

        rows = []

        for topic in self.topics:
            results = []

            for country in self.countries:
                value = self.get_base_value(country, topic, col_name)
                results.append(value)

            row = (topic, results)
            rows.append(row)

        label = 'PressureLevelN/P/Oconcentration/' \
                'ImpactsPressureWater/Seabed: ' \
                'SumInfo1 ' \
                '[ProportionValueAchieved]'

        return rows
        # return CompoundRow(label, rows)

    def get_suminfo2_row(self):
        rows = []

        elements = self.get_suminfo2_elements()

        for element in elements:
            results = []

            for country in self.countries:
                for table, res in self.suminfo2_data.items():
                    column = 'SumInfo2'

                    if table.startswith('MSFD8a'):
                        column = 'Summary2'

                    value = ''
                    base_import_id = self.import_data[table][country]

                    col_id = '{}_ID'.format(table)
                    col_import_id = '{}_Import'.format(table)
                    data = self.base_data[table]

                    base_ids = [
                        getattr(x, col_id)

                        for x in data

                        if getattr(x, col_import_id) == base_import_id
                    ]

                    suminfo_ids = [
                        getattr(x, table)

                        for x in res

                        if getattr(x, column) == element
                    ]

                    intersect = set(suminfo_ids) & set(base_ids)

                    if intersect:
                        value = 'Reported'

                        break

                results.append(value)

            row = (element, results)
            rows.append(row)

        label = 'ImpactsPressureWater/Seabed: ' \
                'SumInfo2'

        return rows
        # return CompoundRow(label, rows)

    def get_criteria_status_row(self):
        # MSFD8b_Nutrients_Assesment
        # MSFD8a_Species_StatusAssessment
        rows = []

        for topic in self.topics:
            topic_alt = self.utils_art8.get_proper_topic(topic)
            results = []

            for country in self.countries:
                value = ''

                for table, res in self.base_data.items():
                    if table not in self.status_data:
                        continue

                    base_import_id = self.import_data[table][country]
                    col_id = '{}_ID'.format(table)
                    col_import_id = '{}_Import'.format(table)

                    for row in res:
                        top = row.Topic
                        imp_id_ = getattr(row, col_import_id)

                        if base_import_id != imp_id_:
                            continue

                        if top != topic_alt:
                            continue

                        id_ = getattr(row, col_id)

                        status = [
                            getattr(x, 'Status', None)

                            for x in self.status_data[table]

                            if getattr(x, table) == id_
                        ]

                        if status:
                            value = status[0]

                            break

                    if value:
                        break

                results.append(value)

            row = (topic, results)
            rows.append(row)

        label = 'Status [CriteriaStatus]'

        return rows
        # return CompoundRow(label, rows)

    def get_activity_type_row(self):
        tables = self.base_data.keys()

        results = []

        for country in self.countries:
            value = ''

            for table in tables:
                if table not in self.activity_data:
                    continue

                base_import_id = self.import_data[table][country]
                col_id = '{}_ID'.format(table)
                col_import_id = '{}_Import'.format(table)

                base_ids = [
                    getattr(x, col_id)

                    for x in self.base_data[table]

                    if getattr(x, col_import_id) == base_import_id
                ]

                values = [
                    x.Activity

                    for x in self.activity_data[table]

                    if getattr(x, table) in base_ids
                ]

                value = ', '.join(sorted(set(values)))

            results.append(value)

        rows = [('', results)]

        label = 'ActivityType'

        return rows
        # return CompoundRow(label, [row])

    def get_assessment_date_row(self):
        tables = self.base_data.keys()

        results = []

        for country in self.countries:
            value = ''

            for table in tables:
                base_import_id = self.import_data[table][country]
                col_id = '{}_ID'.format(table)
                col_import_id = '{}_Import'.format(table)

                base_ids = [
                    getattr(x, col_id)

                    for x in self.base_data[table]

                    if getattr(x, col_import_id) == base_import_id
                ]

                values = [
                    (x.AssessmentDateStart, x.AssessmentDateEnd)

                    for x in self.metadata_data[table]

                    if (getattr(x, col_id) in base_ids and
                        x.Topic == 'Assessment' and
                        x.AssessmentDateStart is not None and
                        x.AssessmentDateEnd is not None)
                ]

                if not values:
                    values = [
                        (x.RecentTimeStart, x.RecentTimeEnd)

                        for x in self.base_data[table]

                        if (getattr(x, col_id) in base_ids and
                            getattr(x, 'RecentTimeStart', None) is not None and
                            getattr(x, 'RecentTimeEnd ', None) is not None)
                    ]

                if values:
                    value = '-'.join(values[0])

            results.append(value)

        rows = [('', results)]

        label = 'RecentTimeStart/RecentTimeEnd/' \
                'AssessmentDateStart/AssessmentDateEnd ' \
                '[AssessmentPeriod]'

        return rows
        # return CompoundRow(label, [row])
