
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql  # , sql_extra
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.gescomponents import get_label
from wise.msfd.utils import CompoundRow, ItemLabel, ItemList, Row, TableHeader

from ..a8_utils import UtilsArticle8
from ..base import BaseComplianceView
from .base import BaseRegDescRow
from .utils import compoundrow


class RegDescA82018Row(BaseRegDescRow):
    """"""

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
        element_sources = self.get_unique_values('ElementSource')

        for elem_source in element_sources:
            values = []
            for country_code, country_name in self.countries:
                data = [
                    row.Element
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.ElementSource == elem_source
                ]
                value = self.not_rep
                if data:
                    value = "{} elements".format(len(set(data)))

                values.append(value)

            rows.append((elem_source, values))

        return rows

    @compoundrow
    def get_crit_param_row(self):
        rows = []
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []
            for country_code, country_name in self.countries:
                data = set([
                    row.Parameter
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.Criteria == crit.id
                            # or row.GESComponent.split('/')[0] == crit.id)
                       and row.Parameter
                ])
                value = self.not_rep
                if data:
                    value = ItemList(
                        ItemLabel(d, get_label(d, self.field.label_collection))
                        for d in data
                    )

                values.append(value)

            rows.append((ItemLabel(crit.title, crit.name), values))

        return rows

    @compoundrow
    def get_threshold_value_row(self):
        rows = []
        values = []
        parameters = self.get_unique_values('Parameter')

        for country_code, country_name in self.countries:
            provided = 0
            for param in parameters:
                data = set([
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.Parameter == param
                       and (row.ThresholdValueUpper or row.ThresholdValueLower)
                ])
                if data:
                    provided += 1

            value = self.not_rep
            if provided:
                value = "Provided for {} (of {}) parameters" \
                    .format(provided, len(parameters))
            values.append(value)

        rows.append(('Quantitative values provided', values))

        return rows

    @compoundrow
    def get_threshold_source_row(self):
        rows = []
        threshs = self.get_unique_values('ThresholdValueSource')

        for threshold_source in threshs:
            values = []
            for country_code, country_name in self.countries:
                data = set([
                    row.Parameter
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.ThresholdValueSource == threshold_source
                ])
                value = self.not_rep
                if data:
                    value = "{} parameters".format(len(set(data)))

                values.append(value)

            rowlabel = get_label(threshold_source, self.field.label_collection)
            rows.append((ItemLabel(threshold_source, rowlabel), values))

        return rows

    @compoundrow
    def get_proportion_threshold_row(self):
        rows = []
        values = []
        params = self.get_unique_values('Parameter')

        for country_code, country_name in self.countries:
            data = set([
                (row.Parameter, row.ProportionThresholdValue)
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.ProportionThresholdValue
            ])

            value = self.not_rep
            if data:
                country_params = set([x[0] for x in data])
                proportion_vals = set([x[1] for x in data])

                value = "Range: {}-{}% ({} of {} parameters)".format(
                    int(min(proportion_vals)), int(max(proportion_vals)),
                    len(country_params), len(params)
                )

            values.append(value)

        rows.append(('Quantitative values provided', values))

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
                value = ItemList(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_param_achieved_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            param_achievs = self.get_unique_values('ParameterAchieved')

            value = []
            for param in param_achievs:
                data = set([
                    row.Parameter
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.ParameterAchieved == param
                ])

                if data:
                    text = "{} - {}".format(param, len(data))
                    value.append(text)

            values.append(ItemList(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_crit_status_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            crit_stats = self.get_unique_values('CriteriaStatus')

            value = []
            for crit_stat in crit_stats:
                data = set([
                    row.Criteria
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.CriteriaStatus == crit_stat
                ])

                if data:
                    text = "{} - {}".format(crit_stat, len(data))
                    value.append(text)

            values.append(ItemList(value))

        rows.append(('', values))

        return rows

    @compoundrow
    def get_elem_status_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            elem_stats = self.get_unique_values('ElementStatus')

            value = []
            for elem in elem_stats:
                data = set([
                    row.Element
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and row.ElementStatus == elem
                ])

                if data:
                    text = "{} - {}".format(elem, len(data))
                    value.append(text)

            values.append(ItemList(value))

        rows.append(('', values))

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
                value = ItemList(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_integration_desc_param_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                (row.Criteria, row.IntegrationRuleDescriptionParameter)
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.IntegrationRuleDescriptionParameter
            ])

            value = self.not_rep
            if data:
                value = ItemList(["{}: {}".format(x[0], x[1]) for x in data])

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
                value = ItemList(data)

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
                value = ItemList(data)

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
                value = ItemList(data)

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
                value = ItemList(data)

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
                value = ItemList(data)

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
                value = ItemList(data)

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
                value = ItemList(data)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_related_press_row(self):
        rows = []
        pressures = self.get_unique_values("PressureCodes")
        all_pressures = []
        for pres in pressures:
            all_pressures.extend(pres.split(','))

        for pressure in set(all_pressures):
            values = []
            for country_code, country_name in self.countries:
                data = set([
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and pressure in row.PressureCodes.split(',')
                ])

                value = self.not_rep
                if data:
                    value = self.rep

                values.append(value)

            row_label = ItemLabel(pressure,
                                  get_label(pressure, self.field.label_collection))
            rows.append((row_label, values))

        return rows


class RegDescA8(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.region = 'BAL'

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

        allrows = [
            self.get_countries(),
            self.get_marine_unit_id_nrs(),
            # TODO show the reported value, or Reported/Not reported ??
            self.get_suminfo1_row(),
            self.get_suminfo2_row(),
            self.get_criteria_status_row(),
            self.get_activity_type_row(),
            self.get_assessment_date_row()
        ]

        return self.template(rows=allrows)

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

        result = sorted(result)

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
        return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        row = Row('Number used',
                  [len(self.all_countries[c]) for c in self.countries])

        return CompoundRow('MarineUnitID [Reporting area]', [row])

    def get_suminfo1_row(self):
        col_name = 'SumInfo1'

        rows = []

        for topic in self.topics:
            results = []

            for country in self.countries:
                value = self.get_base_value(country, topic, col_name)
                results.append(value)

            row = Row(topic, results)
            rows.append(row)

        label = 'PressureLevelN/P/Oconcentration/' \
                'ImpactsPressureWater/Seabed: ' \
                'SumInfo1 ' \
                '[ProportionValueAchieved]'

        return CompoundRow(label, rows)

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

            row = Row(element, results)
            rows.append(row)

        label = 'ImpactsPressureWater/Seabed: ' \
                'SumInfo2'

        return CompoundRow(label, rows)

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

            row = Row(topic, results)
            rows.append(row)

        label = 'Status [CriteriaStatus]'

        return CompoundRow(label, rows)

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

        row = Row('', results)

        label = 'ActivityType'

        return CompoundRow(label, [row])

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

        row = Row('', results)

        label = 'RecentTimeStart/RecentTimeEnd/' \
                'AssessmentDateStart/AssessmentDateEnd ' \
                '[AssessmentPeriod]'

        return CompoundRow(label, [row])
