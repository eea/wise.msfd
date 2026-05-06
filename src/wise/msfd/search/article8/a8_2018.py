# pylint: skip-file
from __future__ import absolute_import
from collections import OrderedDict
from sqlalchemy import and_, func, or_, types as sqltypes
from sqlalchemy.sql.elements import literal_column
from sqlalchemy.sql.expression import cast
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm, MarineUnitIDSelectForm
from wise.msfd.sql_extra import MSFD4GeographicalAreaID
from wise.msfd.utils import (all_values_from_field, db_objects_to_dict,
                             group_data, ItemLabel, ItemList)
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_a8_2018

#########################
#     Article 8.1ab     #
#########################


class A2018Art81abDisplay(ItemDisplayForm):
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')

    secondary_extra_template_v2 = ViewPageTemplateFile(
        '../pt/extra-data-pivot-8ab-v2.pt'
    )

    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    blacklist_labels = ['Criteria']

    def get_reported_date(self):
        return self.get_reported_date_2018()

    def get_import_id(self):
        id_mru = self.item.IdMarineUnit

        _, res = db.get_related_record(
            sql2018.ART8GESMarineUnit,
            'Id',
            id_mru
        )

        import_id = res.IdReportedInformation

        return import_id

    def download_results(self):
        data = self.get_flattened_data(self)
        parent = self.context.context.context.context

        mc_countries = sql2018.ReportedInformation
        overall_status_mc = parent.features_mc
        mapper_class = sql2018.ART8GESMarineUnit

        marine_units = self.context.get_available_marine_unit_ids()[1]
        member_states = data.get('member_states')
        features = data.get('feature')
        ges_components = data.get('ges_component')

        count, marine_unit = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            and_(mapper_class.MarineReportingUnit.in_(marine_units),
                 mc_countries.CountryCode.in_(member_states),
                 mc_countries.Id.in_(self.latest_import_ids_2018())
                 ),
            raw=True
        )
        id_marine_units = [x.Id for x in marine_unit]

        from wise.msfd.db import session
        sess = session()
        mc_overall_pressure = sql2018.ART8GESOverallStatusPressure
        mc_overall_target = sql2018.ART8GESOverallStatusTarget
        mc_crit_val_ind = sql2018.ART8GESCriteriaValuesIndicator
        mc_elem_status = sql2018.ART8GESElementStatu
        mc_crit_status = sql2018.ART8GESCriteriaStatu
        mc_crit_value = sql2018.ART8GESCriteriaValue
        art8data = (sess.query(
            mapper_class.Id,
            mapper_class.MarineReportingUnit,
            overall_status_mc.GESComponent,
            overall_status_mc.Feature,
            overall_status_mc.GESExtentUnit,
            overall_status_mc.GESAchieved,
            overall_status_mc.AssessmentsPeriod,
            overall_status_mc.DescriptionOverallStatus,
            overall_status_mc.IntegrationRuleTypeCriteria,
            overall_status_mc.IntegrationRuleDescriptionCriteria,
            overall_status_mc.IntegrationRuleDescriptionReferenceCriteria,
            overall_status_mc.IntegrationRuleTypeParameter,
            overall_status_mc.IntegrationRuleDescriptionParameter,
            overall_status_mc.IntegrationRuleDescriptionReferenceParameter,
            func.string_agg(cast(mc_overall_pressure.PressureCode, sqltypes.Unicode),
                            literal_column("'###'")).label("PressureCode"),
            func.string_agg(cast(mc_overall_target.TargetCode, sqltypes.Unicode),
                            literal_column("'###'")).label("TargetCode"),
            mc_elem_status.Element,
            mc_elem_status.Element2,
            mc_elem_status.ElementSource,
            mc_elem_status.ElementCode,
            mc_elem_status.Element2Code,
            mc_elem_status.ElementCodeSource,
            mc_elem_status.Element2CodeSource,
            mc_elem_status.DescriptionElement,
            mc_elem_status.ElementStatus,
            mc_crit_status.Criteria,
            mc_crit_status.CriteriaStatus,
            mc_crit_status.DescriptionCriteria,
            mc_crit_status.IdOverallStatus,
            mc_crit_value.Parameter,
            mc_crit_value.ParameterOther,
            mc_crit_value.ThresholdValueUpper,
            mc_crit_value.ThresholdValueLower,
            mc_crit_value.ThresholdQualitative,
            mc_crit_value.ThresholdValueSource,
            mc_crit_value.ThresholdValueSourceOther,
            mc_crit_value.ValueAchievedUpper,
            mc_crit_value.ValueAchievedLower,
            mc_crit_value.ValueUnit,
            mc_crit_value.ValueUnitOther,
            mc_crit_value.ProportionThresholdValue,
            mc_crit_value.ProportionThresholdValueUnit,
            mc_crit_value.ProportionValueAchieved,
            mc_crit_value.Trend,
            mc_crit_value.ParameterAchieved,
            mc_crit_value.DescriptionParameter,
            func.string_agg(cast(mc_crit_val_ind.IndicatorCode, sqltypes.Unicode),
                            literal_column("'###'")).label("IndicatorCode")
        )
            .outerjoin(overall_status_mc, mapper_class.Id == overall_status_mc.IdMarineUnit)
            .outerjoin(mc_overall_pressure, mc_overall_pressure.IdOverallStatus == overall_status_mc.Id)
            .outerjoin(mc_overall_target, mc_overall_target.IdOverallStatus == overall_status_mc.Id)
            .outerjoin(mc_elem_status, mc_elem_status.IdOverallStatus == overall_status_mc.Id)
            .outerjoin(mc_crit_status, or_(
                mc_crit_status.IdElementStatus == mc_elem_status.Id,
                mc_crit_status.IdOverallStatus == overall_status_mc.Id))
            .outerjoin(mc_crit_value, mc_crit_value.IdCriteriaStatus == mc_crit_status.Id)
            .outerjoin(mc_crit_val_ind, mc_crit_val_ind.IdCriteriaValues == mc_crit_value.Id)
            .filter(
            mapper_class.Id.in_(id_marine_units),
            overall_status_mc.Feature.in_(features),
            overall_status_mc.GESComponent.in_(ges_components)
        )
            .group_by(
            mapper_class.Id,
            mapper_class.MarineReportingUnit,
            overall_status_mc.GESComponent,
            overall_status_mc.Feature,
            overall_status_mc.GESExtentUnit,
            overall_status_mc.GESAchieved,
            overall_status_mc.AssessmentsPeriod,
            overall_status_mc.DescriptionOverallStatus,
            overall_status_mc.IntegrationRuleTypeCriteria,
            overall_status_mc.IntegrationRuleDescriptionCriteria,
            overall_status_mc.IntegrationRuleDescriptionReferenceCriteria,
            overall_status_mc.IntegrationRuleTypeParameter,
            overall_status_mc.IntegrationRuleDescriptionParameter,
            overall_status_mc.IntegrationRuleDescriptionReferenceParameter,
            mc_elem_status.Element,
            mc_elem_status.Element2,
            mc_elem_status.ElementSource,
            mc_elem_status.ElementCode,
            mc_elem_status.Element2Code,
            mc_elem_status.ElementCodeSource,
            mc_elem_status.Element2CodeSource,
            mc_elem_status.DescriptionElement,
            mc_elem_status.ElementStatus,
            mc_crit_status.Criteria,
            mc_crit_status.CriteriaStatus,
            mc_crit_status.DescriptionCriteria,
            mc_crit_status.IdOverallStatus,
            mc_crit_value.Parameter,
            mc_crit_value.ParameterOther,
            mc_crit_value.ThresholdValueUpper,
            mc_crit_value.ThresholdValueLower,
            mc_crit_value.ThresholdQualitative,
            mc_crit_value.ThresholdValueSource,
            mc_crit_value.ThresholdValueSourceOther,
            mc_crit_value.ValueAchievedUpper,
            mc_crit_value.ValueAchievedLower,
            mc_crit_value.ValueUnit,
            mc_crit_value.ValueUnitOther,
            mc_crit_value.ProportionThresholdValue,
            mc_crit_value.ProportionThresholdValueUnit,
            mc_crit_value.ProportionValueAchieved,
            mc_crit_value.Trend,
            mc_crit_value.ParameterAchieved,
            mc_crit_value.DescriptionParameter)
            .order_by(mapper_class.Id)
            .distinct()
        )

        art8data = [x for x in art8data]

        xlsdata = [
            ('Data', art8data)
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)
        parent = self.context.context.context.context

        countries = data.get('member_states', [])
        mrus = (data.get('marine_unit_id'), )
        features = data.get('feature', [])
        ges_components = data.get('ges_component', [])

        mapper_class = parent.mapper_class
        overall_status_mc = parent.features_mc
        mc_countries = sql2018.ReportedInformation

        conditions = [
            mc_countries.Id.in_(self.latest_import_ids_2018())
        ]

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        if mrus:
            conditions.append(mapper_class.MarineReportingUnit.in_(mrus))

        count, id_marine_units = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )
        id_marine_units = [int(x.Id) for x in id_marine_units]

        conditions_overall_status = and_(
            overall_status_mc.Feature.in_(features),
            overall_status_mc.GESComponent.in_(ges_components),
            overall_status_mc.IdMarineUnit.in_(id_marine_units)
        )

        self.features = features
        self.ges_components = ges_components

        res = db.get_item_by_conditions(
            overall_status_mc,
            'GESComponent',
            conditions_overall_status,
            page=page
        )

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        id_overall = self.item.Id

        pressure_codes = db.get_unique_from_mapper(
            sql2018.ART8GESOverallStatusPressure,
            'PressureCode',
            sql2018.ART8GESOverallStatusPressure.IdOverallStatus == id_overall
        )

        target_codes = db.get_unique_from_mapper(
            sql2018.ART8GESOverallStatusTarget,
            'TargetCode',
            sql2018.ART8GESOverallStatusTarget.IdOverallStatus == id_overall
        )

        res = []
        res_extra = []

        res.append(
            ('Related pressure(s)', {
                '': [{'PressureCode': x} for x in pressure_codes]
            }))

        res.append(
            ('Related target(s)', {
                '': [{'TargetCode': x} for x in target_codes]
            }))

        self.extra_data = res_extra

        return res

    def get_extra_data_v2(self):
        if not self.item:
            return {}

        id_overall = self.item.Id
        self.blacklist = ('Id', 'IdOverallStatus', 'IdElementStatus',
                          'IdCriteriaStatus', 'IdCriteriaValues',
                          '_criteria_statuses', '_criteria_values')

        excluded_columns = ()

        element_status_orig = db.get_all_columns_from_mapper(
            sql2018.ART8GESElementStatu,
            'Id',
            sql2018.ART8GESElementStatu.IdOverallStatus == id_overall
        )
        element_status = db_objects_to_dict(element_status_orig,
                                            excluded_columns)
        final_rows = []

        for row in element_status:
            _es = OrderedDict()
            _es.update(row)

            id_elem_status = row['Id']
            s = sql2018.ART8GESCriteriaStatu

            criteria_status_orig = db.get_all_columns_from_mapper(
                s,
                'Id',
                or_(s.IdOverallStatus == id_overall,
                    s.IdElementStatus == id_elem_status)
            )

            criteria_statuses = db_objects_to_dict(criteria_status_orig,
                                                   excluded_columns)
            _es['_criteria_statuses'] = []

            if not criteria_statuses:
                final_rows.append(_es.copy())
                continue

            for criteria_status in criteria_statuses:
                _cs = OrderedDict()
                _cs.update(criteria_status)
                _es['_criteria_statuses'].append(_cs)
                id_criteria_status = criteria_status['Id']

                s = sql2018.ART8GESCriteriaValue
                criteria_value_orig = db.get_all_columns_from_mapper(
                    s,
                    'Id',
                    s.IdCriteriaStatus == id_criteria_status
                )
                criteria_values = db_objects_to_dict(criteria_value_orig,
                                                     excluded_columns)

                _cs['_criteria_values'] = []
                if not criteria_values:
                    # final_rows.append(_row.copy())
                    continue

                for criteria_value in criteria_values:
                    _cv = OrderedDict()
                    _cv.update(criteria_value)
                    _cs['_criteria_values'].append(_cv)
                    id_criteria_value = criteria_value['Id']

                    s = sql2018.ART8GESCriteriaValuesIndicator
                    criteria_value_ind = db.get_unique_from_mapper(
                        s,
                        'IndicatorCode',
                        s.IdCriteriaValues == id_criteria_value
                    )

                    if not criteria_value_ind:
                        _cv.update(
                            {'Related Indicator(s)': ''}
                        )
                        continue

                    values = [
                        ItemLabel(v, self.print_value(v))
                        for v in criteria_value_ind
                    ]

                    _cv.update(
                        {'Related Indicator(s)': ItemList(values)}
                    )

            final_rows.append(_es.copy())

        _sorted_rows = sorted(final_rows, key=lambda d: d['Element'])
        # extra_final = _sorted_rows and change_orientation(_sorted_rows) or []

        return _sorted_rows

    def extras(self):
        html = self.extra_data_template(extra_data=self.get_extra_data())
        # extra_html = self.secondary_extra_template(extra_data=self.extra_data)
        extra_data_v2 = self.get_extra_data_v2()
        extra_v2 = self.secondary_extra_template_v2(extra_data=extra_data_v2)

        return html + extra_v2


@register_form_a8_2018
class A2018Article81ab(EmbeddedForm):
    record_title = title = 'Article 8.1ab (GES assessments)'
    mapper_class = sql2018.ART8GESMarineUnit
    display_klass = A2018Art81abDisplay
    target_mc = sql2018.ART8GESOverallStatu
    features_mc = sql2018.ART8GESOverallStatu
    features_relation_column = 'Id'
    ges_components_mc = sql2018.ART8GESOverallStatu
    ges_components_relation_column = 'Id'

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81abGesComponents(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])


class A2018Art81abFeatures(EmbeddedForm):
    fields = Fields(interfaces.IFeatures)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81abMarineUnitID(self, self.request)


class A2018Art81abGesComponents(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81abFeatures(self, self.request)


class A2018Art81abMarineUnitID(MarineUnitIDSelectForm):
    mapper_class = MSFD4GeographicalAreaID

    def get_subform(self):
        return A2018Art81abDisplay(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])

    def get_available_marine_unit_ids(self):
        # TODO filter by feature, ges component
        data = self.get_flattened_data(self)
        parent = self.context.context.context

        mapper_class = parent.mapper_class
        target_mc = parent.target_mc
        mc_countries = sql2018.ReportedInformation
        conditions = []

        id_marine_units = db.get_unique_from_mapper(
            target_mc,
            'IdMarineUnit',
            and_(target_mc.Feature.in_(data['feature']),
                 target_mc.GESComponent.in_(data['ges_component']))
        )

        if id_marine_units:
            conditions.append(mapper_class.Id.in_(id_marine_units))

        if 'member_states' in data:
            conditions.append(mc_countries.CountryCode.in_(
                data['member_states']))

        count, res = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )

        res = tuple(set([x.MarineReportingUnit for x in res]))

        sorted_ = sorted(res)

        return len(res), sorted_


#########################
#     Article 8.1c      #
#########################

class A2018Art81cDisplay(ItemDisplayForm):
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')
    id_marine_units = list()

    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    def get_reported_date(self):
        return self.get_reported_date_2018()

    def get_import_id(self):
        id_mru = self.item.IdMarineUnit

        _, res = db.get_related_record(
            sql2018.ART8ESAMarineUnit,
            'Id',
            id_mru
        )

        import_id = res.IdReportedInformation

        return import_id

    def download_results(self):
        data = self.get_flattened_data(self)
        parent = self.context.context.context

        mc_countries = sql2018.ReportedInformation
        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        features = data.get('feature', ())
        member_states = data.get('member_states')
        marine_units = self.context.get_available_marine_unit_ids()[1]

        count, marine_unit = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            and_(mapper_class.MarineReportingUnit.in_(marine_units),
                 mc_countries.CountryCode.in_(member_states),
                 mc_countries.Id.in_(self.latest_import_ids_2018())
                 ),
            raw=True
        )
        id_marine_units = [x.Id for x in marine_unit]

        conditions = list()
        conditions.append(features_mc.IdMarineUnit.in_(id_marine_units))

        if features:
            conditions.append(features_mc.Feature.in_(features))

        count, feature = db.get_all_records(
            features_mc,
            *conditions,
            raw=True
        )
        id_feature = [x.Id for x in feature]
        id_marine_units = [x.IdMarineUnit for x in feature]

        count, marine_unit = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(id_marine_units),
            raw=True
        )

        count, feature_nace = db.get_all_records(
            sql2018.ART8ESAFeatureNACE,
            sql2018.ART8ESAFeatureNACE.IdFeature.in_(id_feature),
            raw=True
        )

        count, feature_ges_comp = db.get_all_records(
            sql2018.ART8ESAFeatureGESComponent,
            sql2018.ART8ESAFeatureGESComponent.IdFeature.in_(id_feature),
            raw=True
        )

        count, cost_degradation = db.get_all_records(
            sql2018.ART8ESACostDegradation,
            sql2018.ART8ESACostDegradation.IdFeature.in_(id_feature),
            raw=True
        )
        id_cost_degrad = [x.Id for x in cost_degradation]

        mc = sql2018.ART8ESACostDegradationIndicator
        count, cost_degradation_ind = db.get_all_records(
            mc,
            mc.IdCostDegradation.in_(id_cost_degrad),
            raw=True
        )

        count, uses_activity = db.get_all_records(
            sql2018.ART8ESAUsesActivity,
            sql2018.ART8ESAUsesActivity.IdFeature.in_(id_feature),
            raw=True
        )
        id_uses_act = [x.Id for x in uses_activity]

        mc = sql2018.ART8ESAUsesActivitiesIndicator
        count, uses_activity_ind = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act),
            raw=True
        )

        mc = sql2018.ART8ESAUsesActivitiesEcosystemService
        count, uses_activity_eco = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act),
            raw=True
        )

        mc = sql2018.ART8ESAUsesActivitiesPressure
        count, uses_activity_pres = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('ART8ESAMarineUnit', marine_unit),
            ('ART8ESAFeature', feature),
            ('ART8ESAFeatureNACE', feature_nace),
            ('ART8ESAFeatureGESComponent', feature_ges_comp),
            ('ART8ESACostDegradation', cost_degradation),
            ('ART8ESACostDegradationIndicator', cost_degradation_ind),
            ('ART8ESAUsesActivity', uses_activity),
            ('ART8ESAUsesActivitiesIndicator', uses_activity_ind),
            ('ART8ESAUsesActEcosystemService', uses_activity_eco),
            ('ART8ESAUsesActivitiesPressure', uses_activity_pres),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)
        parent = self.context.context.context

        countries = data.get('member_states', ())
        features = data.get('feature', ())
        mrus = (data.get('marine_unit_id', ()), )

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        mc_countries = sql2018.ReportedInformation

        conditions = [
            mc_countries.Id.in_(self.latest_import_ids_2018())
        ]

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        if mrus:
            conditions.append(mapper_class.MarineReportingUnit.in_(mrus))

        count, id_marine_units = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )
        id_marine_units = [int(x.Id) for x in id_marine_units]
        self.id_marine_units = id_marine_units

        res = db.get_item_by_conditions(
            features_mc,
            'Id',
            and_(features_mc.Feature.in_(features),
                 features_mc.IdMarineUnit.in_(id_marine_units)),
            page=page
        )

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        id_feature = self.item.Id
        excluded_columns = ('Id', 'IdFeature')

        nace_codes = db.get_unique_from_mapper(
            sql2018.ART8ESAFeatureNACE,
            'NACECode',
            sql2018.ART8ESAFeatureNACE.IdFeature == id_feature
        )

        ges_components = db.get_unique_from_mapper(
            sql2018.ART8ESAFeatureGESComponent,
            'GESComponent',
            sql2018.ART8ESAFeatureGESComponent.IdFeature == id_feature
        )

        cost_degradation_orig = db.get_all_columns_from_mapper(
            sql2018.ART8ESACostDegradation,
            'Id',
            sql2018.ART8ESACostDegradation.IdFeature == id_feature
        )
        cost_degradation = db_objects_to_dict(cost_degradation_orig,
                                              excluded_columns)

        ids_cost_degradation = [x.Id for x in cost_degradation_orig]
        mc = sql2018.ART8ESACostDegradationIndicator
        cost_degradation_indicators = db.get_unique_from_mapper(
            mc,
            'IndicatorCode',
            mc.IdCostDegradation.in_(ids_cost_degradation)
        )

        uses_activities_orig = db.get_all_columns_from_mapper(
            sql2018.ART8ESAUsesActivity,
            'Id',
            sql2018.ART8ESAUsesActivity.IdFeature == id_feature
        )
        uses_activities = db_objects_to_dict(uses_activities_orig,
                                             excluded_columns)

        ids_uses_act = [x.Id for x in uses_activities_orig]
        s = sql2018.ART8ESAUsesActivitiesIndicator
        uses_act_indicators = db.get_unique_from_mapper(
            s,
            'IndicatorCode',
            s.IdUsesActivities.in_(ids_uses_act)
        )

        s = sql2018.ART8ESAUsesActivitiesEcosystemService
        uses_act_eco = db.get_unique_from_mapper(
            s,
            'EcosystemServiceCode',
            s.IdUsesActivities.in_(ids_uses_act)
        )

        s = sql2018.ART8ESAUsesActivitiesPressure
        uses_act_pres = db.get_unique_from_mapper(
            s,
            'PressureCode',
            s.IdUsesActivities.in_(ids_uses_act)
        )

        res = list()

        res.append(
            ('NACE code(s)', {
                '': [{'NACECode': x} for x in nace_codes]
            }))

        res.append(
            ('GES component(s)', {
                '': [{'GESComponent': x} for x in ges_components]
            }))

        res.append(
            ('Cost Degradation', {'': cost_degradation})
        )

        res.append(
            ('Cost Degradation Indicator(s)', {
                '': [{'IndicatorCode': x}
                     for x in cost_degradation_indicators]
            }))

        res.append(
            ('Uses Activities', {'': uses_activities})
        )

        res.append(
            ('Uses Activities Indicator(s)', {
                '': [{'IndicatorCode': x} for x in uses_act_indicators]
            }))

        res.append(
            ('Uses Activities Ecosystem Service(s)', {
                '': [{'EcosystemServiceCode': x} for x in uses_act_eco]
            }))

        res.append(
            ('Uses Activities Pressure(s)', {
                '': [{'PressureCode': x} for x in uses_act_pres]
            }))

        return res


class A2018Features81cForm(EmbeddedForm):

    fields = Fields(interfaces.IFeatures81c)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81cMarineUnitId(self, self.request)


class A2018Art81cMarineUnitId(MarineUnitIDSelectForm):
    mapper_class = MSFD4GeographicalAreaID

    def get_subform(self):
        return A2018Art81cDisplay(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])

    def get_available_marine_unit_ids(self):
        # TODO filter by feature, ges component
        data = self.get_flattened_data(self)
        parent = self.context.context

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        mc_countries = sql2018.ReportedInformation
        conditions = []

        id_marine_units = db.get_unique_from_mapper(
            features_mc,
            'IdMarineUnit',
            features_mc.Feature.in_(data['feature'])
        )

        if id_marine_units:
            conditions.append(mapper_class.Id.in_(id_marine_units))

        if 'member_states' in data:
            conditions.append(mc_countries.CountryCode.in_(
                data['member_states']))

        count, res = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )

        res = tuple(set([x.MarineReportingUnit for x in res]))

        sorted_ = sorted(res)

        return len(res), sorted_


@register_form_a8_2018
class A2018Article81c(EmbeddedForm):
    record_title = 'Article 8.1c (Economic and social analysis assessments)'
    title = 'Article 8.1c (ESA assessments)'
    mapper_class = sql2018.ART8ESAMarineUnit
    display_klass = A2018Art81cDisplay
    features_mc = sql2018.ART8ESAFeature

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Features81cForm(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])
