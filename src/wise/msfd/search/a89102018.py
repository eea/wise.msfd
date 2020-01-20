# TODO: we need to check behavior of this module after modifications to
# extractData() in EmbeddedForm

from collections import OrderedDict
from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql, sql2018
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..sql_extra import MSFD4GeographicalAreaID
from ..utils import (all_values_from_field, change_orientation,
                     db_objects_to_dict, group_data, ItemLabel, ItemList)
from .base import ItemDisplayForm
from .utils import (data_to_xls, register_form_a8_2018, register_form_art9,
                    register_form_art19, register_form_art10)


#########################
#       Article 9       #
#########################

class Art9Display(ItemDisplayForm):
    css_class = 'left-side-form'
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    show_extra_data = True

    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    def get_import_id(self):
        if hasattr(self.item, 'IdReportedInformation'):
            return self.item.IdReportedInformation

        id_ges = self.item.IdGESComponent

        _, res = db.get_related_record(
            sql2018.ART9GESGESComponent,
            'Id',
            id_ges
        )

        import_id = res.IdReportedInformation

        return import_id

    def get_reported_date(self):
        return self.get_reported_date_2018()

    def get_current_country(self):
        id_ges_comp = getattr(self.item, 'IdGESComponent', None)
        if not id_ges_comp:
            id_ges_comp = self.item.Id

        mc = sql2018.ReportedInformation
        mc_join = sql2018.ART9GESGESComponent

        _, res = db.get_all_records_join(
            [mc.CountryCode],
            mc_join,
            mc_join.Id == id_ges_comp
        )

        country = self.print_value(res[0].CountryCode)

        return country

    def download_results(self):
        parent = self.context.context.context
        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        determination_mc = sql2018.ART9GESGESDetermination

        count, ges_component = db.get_all_records(
            mapper_class,
            self.condition_ges_component
        )
        id_ges_comp = [x.Id for x in ges_component]

        count, ges_determination = db.get_all_records(
            determination_mc,
            determination_mc.IdGESComponent.in_(id_ges_comp)
        )
        id_ges_deter = [x.Id for x in ges_determination]

        count, ges_deter_feature = db.get_all_records(
            features_mc,
            features_mc.IdGESDetermination.in_(id_ges_deter)
        )

        count, ges_marine_unit = db.get_all_records(
            sql2018.ART9GESMarineUnit,
            sql2018.ART9GESMarineUnit.IdGESDetermination.in_(id_ges_deter)
        )

        xlsdata = [
            # worksheet title, row data
            ('ART9GESGESComponent', ges_component),
            ('ART9GESGESDetermination', ges_determination),
            ('ART9GESGESDeterminationFeature', ges_deter_feature),
            ('ART9GESMarineUnit', ges_marine_unit),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        parent = self.context.context.context

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        determination_mc = parent.determination_mc

        data = self.get_flattened_data(self)

        member_states = data.get('member_states', ())
        ges_components = data.get('ges_component', ())
        features = data.get('feature', ())

        count, id_ges_components = db.get_all_records_join(
            [determination_mc.IdGESComponent,
             features_mc.Feature],
            features_mc,
            features_mc.Feature.in_(features)
        )
        id_ges_components = [x.IdGESComponent for x in id_ges_components]
        id_ges_components = tuple(set(id_ges_components))

        self.condition_ges_component = and_(
            sql2018.ReportedInformation.CountryCode.in_(member_states),
            sql2018.ReportedInformation.Id.in_(self.latest_import_ids_2018()),
            mapper_class.GESComponent.in_(ges_components),
            or_(mapper_class.Id.in_(id_ges_components),
                mapper_class.JustificationDelay.is_(None),
                mapper_class.JustificationNonUse.is_(None)
                )
        )

        count, res = db.get_item_by_conditions_joined(
            mapper_class,
            sql2018.ReportedInformation,
            'Id',
            self.condition_ges_component,
            page=page
        )

        if not res:
            return 0, []

        if getattr(res, 'JustificationDelay', 0) \
                or getattr(res, 'JustificationNonUse', 0):
            self.show_extra_data = False

            return count, res

        self.show_extra_data = True
        id_ges_comp = res.Id
        cnt, res = db.get_related_record(
            determination_mc,
            'IdGESComponent',
            id_ges_comp
        )

        return count, res

    def get_extra_data(self):
        if not self.item or not self.show_extra_data:
            return {}

        mc = sql2018.ART9GESMarineUnit
        id_ges_deter = self.item.Id

        marine_units = db.get_unique_from_mapper(
            mc,
            'MarineReportingUnit',
            mc.IdGESDetermination == id_ges_deter
        )

        res = list()

        res.append(
            ('Marine Unit IDs', {
                '': [{'Marine Unit Id': x} for x in marine_units]
            })
        )

        return res


@register_form_art9
class A2018Article9(EmbeddedForm):
    record_title = 'Article 9 (GES determination)'
    title = "2018 reporting exercise"
    permission = "zope2.View"
    session_name = '2018'
    mapper_class = sql2018.ART9GESGESComponent
    display_klass = Art9Display
    features_mc = sql2018.ART9GESGESDeterminationFeature
    determination_mc = sql2018.ART9GESGESDetermination

    fields = Fields(interfaces.ICountryCode2018Art9)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018GesComponentA9(self, self.request)


class A2018GesComponentA9(EmbeddedForm):
    fields = Fields(interfaces.IGESComponentsA9)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018FeatureA9(self, self.request)


class A2018FeatureA9(EmbeddedForm):
    fields = Fields(interfaces.IFeaturesA9)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Art9Display(self, self.request)


#########################
#       Article 10      #
#########################

class A2018Art10Display(ItemDisplayForm):
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    target_ids = tuple()

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
            sql2018.ART10TargetsMarineUnit,
            'Id',
            id_mru
        )

        import_id = res.IdReportedInformation

        return import_id

    def get_current_country(self):
        """ Calls the get_current_country from super class (BaseUtil)
            which is a general implementation for getting the country.
            Some MRUs are missing from the t_MSFD4_GegraphicalAreasID,
            and we need an alternative way to retrieve the country
        """

        country = super(A2018Art10Display, self).get_current_country()

        if country:
            return country

        monitoring_programme = self.item.ID
        mc = sql.MSFD11MON
        mc_join = sql.MSFD11MP

        _, res = db.get_all_records_outerjoin(
            mc,
            mc_join,
            mc_join.MonitoringProgramme == monitoring_programme
        )

        country = self.print_value(res[0].MemberState)

        return country

    def download_results(self):
        data = self.get_flattened_data(self)

        parent = self.context.context.context.context
        mapper_class = parent.mapper_class
        target_mc = parent.target_mc

        marine_units = self.context.get_available_marine_unit_ids()[1]

        count, target_feature = db.get_all_records(
            sql2018.ART10TargetsTargetFeature,
            sql2018.ART10TargetsTargetFeature.Feature.in_(data['feature'])
        )
        feature_id_target = [x.IdTarget for x in target_feature]

        s = sql2018.ART10TargetsTargetGESComponent
        count, target_ges = db.get_all_records(
            s,
            s.GESComponent.in_(data['ges_component'])
        )
        ges_id_target = [x.IdTarget for x in target_ges]

        count, marine_unit_ids = db.get_all_records_outerjoin(
            mapper_class,
            sql2018.ReportedInformation,
            and_(mapper_class.MarineReportingUnit.in_(marine_units),
                 sql2018.ReportedInformation.CountryCode.in_(
                     data['member_states']),
                 sql2018.ReportedInformation.Id.in_(
                     self.latest_import_ids_2018())
                 )
        )
        marine_unit_ids = [x.Id for x in marine_unit_ids]

        count, target = db.get_all_records(
            target_mc,
            and_(target_mc.IdMarineUnit.in_(marine_unit_ids),
                 target_mc.Id.in_(set(feature_id_target) & set(ges_id_target)))
        )
        target_ids = [x.Id for x in target]
        marine_unit_ids = [x.IdMarineUnit for x in target]

        count, marine_unit = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(marine_unit_ids)
        )

        s = sql2018.ART10TargetsProgressAssessment
        count, target_progress = db.get_all_records(
            s,
            s.IdTarget.in_(target_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('ART10TargetsMarineUnit', marine_unit),
            ('ART10TargetsTarget', target),
            ('ART10TargetsTargetFeature', target_feature),
            ('ART10TargetsTargetGESComponent', target_ges),
            ('ART10TargetsProgressAssessment', target_progress),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)

        member_states = data.get('member_states')
        marine_units = (data.get('marine_unit_id'), )

        if isinstance(marine_units, str):
            marine_units = (marine_units, )
        features = data.get('feature')
        ges_components = data.get('ges_component')

        parent = self.context.context.context.context
        mapper_class = parent.mapper_class
        target_mc = parent.target_mc

        count, marine_unit_ids = db.get_all_records_outerjoin(
            mapper_class,
            sql2018.ReportedInformation,
            and_(mapper_class.MarineReportingUnit.in_(marine_units),
                 sql2018.ReportedInformation.CountryCode.in_(member_states),
                 sql2018.ReportedInformation.Id.in_(
                     self.latest_import_ids_2018())
                 )
        )

        marine_unit_ids = [x.Id for x in marine_unit_ids]

        target_ids = db.get_unique_from_mapper(
            target_mc,
            'Id',
            target_mc.IdMarineUnit.in_(marine_unit_ids)
        )
        target_ids = map(int, target_ids)

        features_ids = db.get_unique_from_mapper(
            sql2018.ART10TargetsTargetFeature,
            'IdTarget',
            sql2018.ART10TargetsTargetFeature.Feature.in_(features)
        )
        features_ids = map(int, features_ids)

        s = sql2018.ART10TargetsTargetGESComponent
        ges_components_ids = db.get_unique_from_mapper(
            s,
            'IdTarget',
            s.GESComponent.in_(ges_components)
        )
        ges_components_ids = map(int, ges_components_ids)

        target_ids_all = tuple(set(target_ids)
                               & set(features_ids)
                               & set(ges_components_ids))

        res = db.get_item_by_conditions(
            target_mc,
            'Id',
            target_mc.Id.in_(target_ids_all),
            page=page
        )

        return res

    def get_extra_data(self):
        if not self.item:
            return []

        target_id = self.item.Id
        mc = sql2018.ART10TargetsProgressAssessment
        mc_join = sql2018.ART10TargetsProgressAssessmentIndicator

        cols = [getattr(mc, c) for c in mc.__table__.c.keys()] + \
            [getattr(mc_join, c) for c in mc_join.__table__.c.keys()]

        count, result = db.get_all_records_join(
            cols,
            mc_join,
            getattr(mc, 'IdTarget') == target_id
        )

        excluded_columns = ('Id', 'IdTarget', 'IdProgressAssessment')

        paremeters = db_objects_to_dict(result, excluded_columns)
        paremeters = group_data(paremeters, 'Parameter', remove_pivot=False)

        res = [
            ('Progress assessment', paremeters),
        ]

        return res


class A2018Art10FeaturesForm(EmbeddedForm):
    fields = Fields(interfaces.IFeatures)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art10GesComponentsForm(self, self.request)

    def get_available_ges_components(self):
        pass


class A2018Art10GesComponentsForm(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018MarineUnitID(self, self.request)


class A2018MarineUnitID(MarineUnitIDSelectForm):
    mapper_class = MSFD4GeographicalAreaID

    def get_subform(self):
        return A2018Art10Display(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])

    def get_available_marine_unit_ids(self):
        # TODO filter by feature, ges component
        data = self.get_flattened_data(self)
        parent = self.context.context.context

        mapper_class = parent.mapper_class
        target_mc = parent.target_mc
        features_mc = parent.features_mc
        ges_components_mc = parent.ges_components_mc
        mc_countries = sql2018.ReportedInformation
        conditions = []

        target_ids_ges = db.get_unique_from_mapper(
            ges_components_mc,
            'IdTarget',
            ges_components_mc.GESComponent.in_(data['ges_component'])
        )
        target_ids_feature = db.get_unique_from_mapper(
            features_mc,
            'IdTarget',
            features_mc.Feature.in_(data['feature'])
        )
        target_ids_all = set(target_ids_ges) & set(target_ids_feature)

        id_marine_units = db.get_unique_from_mapper(
            target_mc,
            'IdMarineUnit',
            target_mc.Id.in_(target_ids_all)
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


@register_form_art10
class A2018Article10(EmbeddedForm):
    record_title = 'Article 10 (Targets and associated indicators)'
    title = "2018 reporting exercise"
    permission = "zope2.View"
    session_name = '2018'

    mapper_class = sql2018.ART10TargetsMarineUnit
    display_klass = A2018Art10Display
    target_mc = sql2018.ART10TargetsTarget
    features_mc = sql2018.ART10TargetsTargetFeature
    features_relation_column = 'IdTarget'
    ges_components_mc = sql2018.ART10TargetsTargetGESComponent
    ges_components_relation_column = 'IdTarget'

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art10FeaturesForm(self, self.request)

    def get_available_features(self):
        pass


#########################
#     Article 8.1ab     #
#########################

class A2018Art81abDisplay(ItemDisplayForm):
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    secondary_extra_template = ViewPageTemplateFile(
        'pt/extra-data-pivot-8ab.pt'
    )

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
                 )
        )
        id_marine_units = [x.Id for x in marine_unit]

        count, overall_status = db.get_all_records(
            overall_status_mc,
            overall_status_mc.Feature.in_(features),
            overall_status_mc.GESComponent.in_(ges_components),
            overall_status_mc.IdMarineUnit.in_(id_marine_units)
        )
        id_overall_status = [x.Id for x in overall_status]
        id_marine_units = [x.IdMarineUnit for x in overall_status]

        count, marine_unit = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(id_marine_units)
        )

        mc = sql2018.ART8GESOverallStatusPressure
        count, overall_status_pressure = db.get_all_records(
            mc,
            mc.IdOverallStatus.in_(id_overall_status)
        )

        mc = sql2018.ART8GESOverallStatusTarget
        count, overall_status_target = db.get_all_records(
            mc,
            mc.IdOverallStatus.in_(id_overall_status)
        )

        mc = sql2018.ART8GESElementStatu
        count, element_status = db.get_all_records(
            mc,
            mc.IdOverallStatus.in_(id_overall_status)
        )
        id_element_status = [x.Id for x in element_status]

        mc = sql2018.ART8GESCriteriaStatu
        count, criteria_status = db.get_all_records(
            mc,
            or_(mc.IdOverallStatus.in_(id_overall_status),
                mc.IdElementStatus.in_(id_element_status))
        )
        id_criteria_status = [x.Id for x in criteria_status]

        mc = sql2018.ART8GESCriteriaValue
        count, criteria_value = db.get_all_records(
            mc,
            mc.IdCriteriaStatus.in_(id_criteria_status)
        )
        id_criteria_value = [x.Id for x in criteria_value]

        mc = sql2018.ART8GESCriteriaValuesIndicator
        count, criteria_value_ind = db.get_all_records(
            mc,
            mc.IdCriteriaValues.in_(id_criteria_value)
        )

        xlsdata = [
            # worksheet title, row data
            ('ART8GESMarineUnit', marine_unit),
            ('ART8GESOverallStatus', overall_status),
            ('ART8GESOverallStatusPressure', overall_status_pressure),
            ('ART8GESOverallStatusTarget', overall_status_target),
            ('ART8GESElementStatus', element_status),
            ('ART8GESCriteriaStatus', criteria_status),
            ('ART8GESCriteriaValue', criteria_value),
            ('ART8GESCriteriaValuesIndicator', criteria_value_ind),
        ]

        return data_to_xls(xlsdata)

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
            'Id',
            conditions_overall_status,
            page=page
        )

        return res

    def get_extra_data_old(self):
        if not self.item:
            return {}

        id_overall = self.item.Id

        excluded_columns = ('Id', 'IdOverallStatus', 'IdElementStatus',
                            'IdCriteriaStatus', 'IdCriteriaValues')

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

        element_status_orig = db.get_all_columns_from_mapper(
            sql2018.ART8GESElementStatu,
            'Id',
            sql2018.ART8GESElementStatu.IdOverallStatus == id_overall
        )
        element_status = db_objects_to_dict(element_status_orig,
                                            excluded_columns)
        element_status_pivot = list()

        for x in element_status:
            element = x.get('Element', '') or ''
            element2 = x.get('Element2', '') or ''
            elements = [el for el in (element, element2) if el]

            x['Element / Element2'] = ' / '.join(elements)
            element_status_pivot.append(x)

        id_elem_status = []

        if element_status:
            element_status_pivot = group_data(element_status_pivot,
                                              'Element / Element2')

            # TODO get the Id for the selected element status
            id_elem_status = [x.Id for x in element_status_orig]

        s = sql2018.ART8GESCriteriaStatu
        conditions = list()
        conditions.append(s.IdOverallStatus == id_overall)

        if element_status_pivot:
            conditions.append(
                s.IdElementStatus.in_(id_elem_status)
            )

        criteria_status_orig = db.get_all_columns_from_mapper(
            sql2018.ART8GESCriteriaStatu,
            'Id',
            or_(*conditions)
        )
        criteria_status = db_objects_to_dict(criteria_status_orig,
                                             excluded_columns)
        criteria_status = group_data(
            criteria_status, 'Criteria', remove_pivot=False
        )

        # TODO get the Id for the selected criteria status
        id_criteria_status = [x.Id for x in criteria_status_orig]
        s = sql2018.ART8GESCriteriaValue
        criteria_value_orig = db.get_all_columns_from_mapper(
            s,
            'Id',
            s.IdCriteriaStatus.in_(id_criteria_status)
        )
        criteria_value = db_objects_to_dict(criteria_value_orig,
                                            excluded_columns)
        criteria_value = group_data(
            criteria_value, 'Parameter', remove_pivot=False
        )

        # TODO get the Id for the selected criteria value
        id_criteria_value = [x.Id for x in criteria_value_orig]

        s = sql2018.ART8GESCriteriaValuesIndicator
        criteria_value_ind = db.get_unique_from_mapper(
            s,
            'IndicatorCode',
            s.IdCriteriaValues.in_(id_criteria_value)
        )

        res = []

        res.append(
            ('Related pressure(s)', {
                '': [{'PressureCode': x} for x in pressure_codes]
            }))

        res.append(
            ('Related target(s)', {
                '': [{'TargetCode': x} for x in target_codes]
            }))

        res.append(
            ('Element Status', element_status_pivot)
        )

        res.append(
            ('Criteria Status', criteria_status)
        )

        res.append(
            ('Parameter assessments', criteria_value)
        )

        res.append(
            ('Related indicator', {
                '': [{'IndicatorCode': x} for x in criteria_value_ind]
            }))

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        id_overall = self.item.Id

        self.blacklist = ('Id', 'IdOverallStatus', 'IdElementStatus',
                          'IdCriteriaStatus', 'IdCriteriaValues')
        excluded_columns = ()

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

        element_status_orig = db.get_all_columns_from_mapper(
            sql2018.ART8GESElementStatu,
            'Id',
            sql2018.ART8GESElementStatu.IdOverallStatus == id_overall
        )
        element_status = db_objects_to_dict(element_status_orig,
                                            excluded_columns)

        final_rows = []

        for row in element_status:
            _row = OrderedDict()
            _row.update(row)

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

            if not criteria_statuses:
                final_rows.append(_row.copy())
                continue

            for criteria_status in criteria_statuses:
                _row.update(criteria_status)
                id_criteria_status = criteria_status['Id']

                s = sql2018.ART8GESCriteriaValue
                criteria_value_orig = db.get_all_columns_from_mapper(
                    s,
                    'Id',
                    s.IdCriteriaStatus == id_criteria_status
                )
                criteria_values = db_objects_to_dict(criteria_value_orig,
                                                     excluded_columns)

                if not criteria_values:
                    final_rows.append(_row.copy())
                    continue

                for criteria_value in criteria_values:
                    _row.update(criteria_value)
                    id_criteria_value = criteria_value['Id']

                    s = sql2018.ART8GESCriteriaValuesIndicator
                    criteria_value_ind = db.get_unique_from_mapper(
                        s,
                        'IndicatorCode',
                        s.IdCriteriaValues == id_criteria_value
                    )

                    if not criteria_value_ind:
                        final_rows.append(_row.copy())
                        continue

                    values = [
                        ItemLabel(v, self.print_value(v))
                        for v in criteria_value_ind
                    ]

                    _row.update(
                        {'IndicatorCode': ItemList(values)}
                    )

                    final_rows.append(_row.copy())

        _sorted_rows = sorted(final_rows, key=lambda d: d['Element'])
        extra_final = change_orientation(_sorted_rows)

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

        res_extra.append(
            ('Element Status, Criteria Status, '
             'Parameter assessments and Related indicator', extra_final)
        )

        self.extra_data = res_extra

        return res

    def extras(self):
        html = self.extra_data_template(extra_data=self.get_extra_data())
        extra_html = self.secondary_extra_template(extra_data=self.extra_data)

        return html + extra_html


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
        return A2018Art81abFeatures(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])


class A2018Art81abFeatures(EmbeddedForm):
    fields = Fields(interfaces.IFeatures)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81abGesComponents(self, self.request)


class A2018Art81abGesComponents(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018Art81abMarineUnitID(self, self.request)


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
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
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
                 )
        )
        id_marine_units = [x.Id for x in marine_unit]

        conditions = list()
        conditions.append(features_mc.IdMarineUnit.in_(id_marine_units))

        if features:
            conditions.append(features_mc.Feature.in_(features))

        count, feature = db.get_all_records(
            features_mc,
            *conditions
        )
        id_feature = [x.Id for x in feature]
        id_marine_units = [x.IdMarineUnit for x in feature]

        count, marine_unit = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(id_marine_units)
        )

        count, feature_nace = db.get_all_records(
            sql2018.ART8ESAFeatureNACE,
            sql2018.ART8ESAFeatureNACE.IdFeature.in_(id_feature)
        )

        count, feature_ges_comp = db.get_all_records(
            sql2018.ART8ESAFeatureGESComponent,
            sql2018.ART8ESAFeatureGESComponent.IdFeature.in_(id_feature)
        )

        count, cost_degradation = db.get_all_records(
            sql2018.ART8ESACostDegradation,
            sql2018.ART8ESACostDegradation.IdFeature.in_(id_feature)
        )
        id_cost_degrad = [x.Id for x in cost_degradation]

        mc = sql2018.ART8ESACostDegradationIndicator
        count, cost_degradation_ind = db.get_all_records(
            mc,
            mc.IdCostDegradation.in_(id_cost_degrad)
        )

        count, uses_activity = db.get_all_records(
            sql2018.ART8ESAUsesActivity,
            sql2018.ART8ESAUsesActivity.IdFeature.in_(id_feature)
        )
        id_uses_act = [x.Id for x in uses_activity]

        mc = sql2018.ART8ESAUsesActivitiesIndicator
        count, uses_activity_ind = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act)
        )

        mc = sql2018.ART8ESAUsesActivitiesEcosystemService
        count, uses_activity_eco = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act)
        )

        mc = sql2018.ART8ESAUsesActivitiesPressure
        count, uses_activity_pres = db.get_all_records(
            mc,
            mc.IdUsesActivities.in_(id_uses_act)
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

        return data_to_xls(xlsdata)

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


#########################
#      Indicators       #
#########################

class A2018IndicatorsGesComponent(EmbeddedForm):
    fields = Fields(interfaces.IIndicatorsGesComponent)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018IndicatorsFeature(self, self.request)


class A2018IndicatorsFeature(EmbeddedForm):
    fields = Fields(interfaces.IIndicatorsFeature)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018IndicatorsDisplay(self, self.request)


class A2018IndicatorsMarineUnitId(MarineUnitIDSelectForm):
    """ TODO Not used
    """

    def get_subform(self):
        return A2018IndicatorsDisplay(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])

    def get_available_marine_unit_ids(self):
        # TODO filter by feature, ges component
        parent = self.context.context.context
        data = self.get_flattened_data(self)

        mapper_class = parent.mapper_class
        ges_comp_mc = parent.ges_components_mc
        features_mc = parent.features_mc
        marine_mc = parent.marine_mc

        countries = data.get('member_states')
        ges_components = data.get('ges_component')
        features = data.get('feature')

        mc_countries = sql2018.ReportedInformation

        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, ids_indicator = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )
        ids_indicator = [int(x.Id) for x in ids_indicator]

        conditions = list()

        if features:
            conditions.append(features_mc.Feature.in_(features))

        if ges_components:
            conditions.append(ges_comp_mc.GESComponent.in_(ges_components))
        count, ids_ind_ass = db.get_all_records_outerjoin(
            ges_comp_mc,
            features_mc,
            *conditions
        )
        ids_ind_ass = [int(x.IdIndicatorAssessment) for x in ids_ind_ass]

        ids_indicator = tuple(set(ids_indicator) & set(ids_ind_ass))

        count, marine_units = db.get_all_records_join(
            [mapper_class.Id, marine_mc.MarineReportingUnit],
            marine_mc,
            mapper_class.Id.in_(ids_indicator),
        )
        res = [x.MarineReportingUnit for x in marine_units]
        res = tuple(set(res))

        sorted_ = sorted(res)

        return len(res), sorted_


class A2018IndicatorsDisplay(ItemDisplayForm):
    title = "Indicator Display Form"
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    conditions_ind_assess = list()

    css_class = "left-side-form"

    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    def get_reported_date(self):
        return self.get_reported_date_2018()

    def get_import_id(self):
        import_id = self.item.IdReportedInformation

        return import_id

    def get_current_country(self):
        report_id = self.item.IdReportedInformation

        _, res = db.get_related_record(
            sql2018.ReportedInformation,
            'Id',
            report_id
        )

        country = self.print_value(res.CountryCode)

        return country

    def download_results(self):
        parent = self.context.context.context

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        ges_components_mc = parent.ges_components_mc
        marine_mc = parent.marine_mc

        ids_needed = set(self.ids_indicator_main) & set(self.ids_ind_ass_ges)

        count, indicator_assessment = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(ids_needed)
        )

        ids_indicator = [x.Id for x in indicator_assessment]

        count, indicator_dataset = db.get_all_records(
            sql2018.IndicatorsDataset,
            sql2018.IndicatorsDataset.IdIndicatorAssessment.in_(ids_indicator)
        )

        count, feature_ges_comp = db.get_all_records(
            ges_components_mc,
            ges_components_mc.IdIndicatorAssessment.in_(ids_indicator)
        )
        id_ges_components = [x.Id for x in feature_ges_comp]

        count, feature_feature = db.get_all_records(
            features_mc,
            features_mc.IdGESComponent.in_(id_ges_components)
        )

        count, marine_unit = db.get_all_records(
            marine_mc,
            marine_mc.IdIndicatorAssessment.in_(ids_indicator)
        )

        xlsdata = [
            # worksheet title, row data
            ('IndicatorsIndicatorAssessment', indicator_assessment),
            ('IndicatorsDataset', indicator_dataset),
            ('IndicatorsFeatureFeature', feature_feature),
            ('IndicatorsFeatureGESComponent', feature_ges_comp),
            ('IndicatorsMarineUnit', marine_unit),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)
        parent = self.context.context.context

        countries = data.get('member_states', ())
        ges_components = data.get('ges_component', ())
        features = data.get('feature', ())
        # mrus = (data.get('marine_unit_id', ()), )

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        ges_components_mc = parent.ges_components_mc
        marine_mc = parent.marine_mc
        mc_countries = sql2018.ReportedInformation

        conditions = [
            mc_countries.Id.in_(self.latest_import_ids_2018())
        ]

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, ids_indicator = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )
        ids_indicator_main = [int(x.Id) for x in ids_indicator]

        conditions = list()

        if features:
            conditions.append(features_mc.Feature.in_(features))

        if ges_components:
            conditions.append(
                ges_components_mc.GESComponent.in_(ges_components))
        count, ids_ind_ass = db.get_all_records_outerjoin(
            ges_components_mc,
            features_mc,
            *conditions
        )
        ids_ind_ass_ges = [int(x.IdIndicatorAssessment) for x in ids_ind_ass]

        ids_ind_ass_marine = db.get_unique_from_mapper(
            marine_mc,
            'IdIndicatorAssessment',
            # marine_mc.MarineReportingUnit.in_(mrus)
        )
        ids_ind_ass_marine = [int(x) for x in ids_ind_ass_marine]

        conditions = list()

        if ids_indicator_main:
            conditions.append(mapper_class.Id.in_(ids_indicator_main))

        if ids_ind_ass_ges:
            conditions.append(mapper_class.Id.in_(ids_ind_ass_ges))

        self.ids_indicator_main = ids_indicator_main
        self.ids_ind_ass_ges = ids_ind_ass_ges

        if ids_ind_ass_marine:
            conditions.append(mapper_class.Id.in_(ids_ind_ass_marine))

        res = db.get_item_by_conditions(
            mapper_class,
            'Id',
            *conditions,
            page=page
        )

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        parent = self.context.context.context
        mc = sql2018.IndicatorsDataset
        marine_mc = parent.marine_mc
        id_indicator_assessment = self.item.Id

        indicators_dataset = db.get_all_columns_from_mapper(
            mc,
            'Id',
            mc.IdIndicatorAssessment == id_indicator_assessment
        )
        excluded_columns = ('Id', 'IdIndicatorAssessment')

        indicators_dataset = db_objects_to_dict(indicators_dataset,
                                                excluded_columns)

        res = list()

        if indicators_dataset:
            res.append(
                ('Indicators Dataset', {'': indicators_dataset})
            )

        count, marine_unit = db.get_all_records(
            marine_mc,
            marine_mc.IdIndicatorAssessment == id_indicator_assessment
        )
        marine_unit_ids = db_objects_to_dict(marine_unit,
                                             excluded_columns)

        if marine_unit_ids:
            res.append(
                ('MarineUnitID(s)', {'': marine_unit_ids})
            )

        return res


@register_form_art19
class A2018ArticleIndicators(EmbeddedForm):
    record_title = 'Indicators (Article 8 & 10)'
    title = '2018 reporting exercise'
    session_name = '2018'

    mapper_class = sql2018.IndicatorsIndicatorAssessment
    features_mc = sql2018.IndicatorsFeatureFeature
    ges_components_mc = sql2018.IndicatorsFeatureGESComponent
    marine_mc = sql2018.IndicatorsMarineUnit

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018IndicatorsGesComponent(self, self.request)
