# pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm, MarineUnitIDSelectForm
from wise.msfd.utils import (all_values_from_field, db_objects_to_dict)
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art19


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
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')
    conditions_ind_assess = list()
    css_class = "left-side-form"
    blacklist_labels = ('IndicatorCode',)

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

        country = self.print_value(res.CountryCode, 'CountryCode')

        return country

    @db.use_db_session('2018')
    def download_results(self):
        parent = self.context.context.context

        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        ges_components_mc = parent.ges_components_mc
        marine_mc = parent.marine_mc

        ids_needed = set(self.ids_indicator_main) & set(self.ids_ind_ass_ges)

        count, indicator_assessment = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(ids_needed),
            raw=True
        )

        ids_indicator = [x.Id for x in indicator_assessment]

        count, indicator_dataset = db.get_all_records(
            sql2018.IndicatorsDataset,
            sql2018.IndicatorsDataset.IdIndicatorAssessment.in_(ids_indicator),
            raw=True
        )

        count, feature_ges_comp = db.get_all_records(
            ges_components_mc,
            ges_components_mc.IdIndicatorAssessment.in_(ids_indicator),
            raw=True
        )
        id_ges_components = [x.Id for x in feature_ges_comp]

        count, feature_feature = db.get_all_records(
            features_mc,
            features_mc.IdGESComponent.in_(id_ges_components),
            raw=True
        )

        count, marine_unit = db.get_all_records(
            marine_mc,
            marine_mc.IdIndicatorAssessment.in_(ids_indicator),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('IndicatorsIndicatorAssessment', indicator_assessment),
            ('IndicatorsDataset', indicator_dataset),
            ('IndicatorsFeatureFeature', feature_feature),
            ('IndicatorsFeatureGESComponent', feature_ges_comp),
            ('IndicatorsMarineUnit', marine_unit),
        ]

        return xlsdata

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
                ('Indicators dataset', {'': indicators_dataset})
            )

        count, marine_unit = db.get_all_records(
            marine_mc,
            marine_mc.IdIndicatorAssessment == id_indicator_assessment
        )
        marine_unit_ids = db_objects_to_dict(marine_unit,
                                             excluded_columns)

        if marine_unit_ids:
            res.append(
                ('Marine unit ID(s)', {'': marine_unit_ids})
            )

        return res


@register_form_art19
class A2018ArticleIndicators(EmbeddedForm):
    record_title = 'Indicators (Article 8 & 10)'
    title = '2018 Article 8 & 10'
    session_name = '2018'

    mapper_class = sql2018.IndicatorsIndicatorAssessment
    features_mc = sql2018.IndicatorsFeatureFeature
    ges_components_mc = sql2018.IndicatorsFeatureGESComponent
    marine_mc = sql2018.IndicatorsMarineUnit

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2018IndicatorsGesComponent(self, self.request)
