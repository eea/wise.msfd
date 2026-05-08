# pylint: skip-file
from __future__ import absolute_import
from sqlalchemy import and_
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql, sql2018
from wise.msfd.base import EmbeddedForm, MarineUnitIDSelectForm
from wise.msfd.sql_extra import MSFD4GeographicalAreaID
from wise.msfd.utils import (all_values_from_field, db_objects_to_dict,
                             group_data)
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art10
from six.moves import map


#########################
#       Article 10      #
#########################

class A2018Art10Display(ItemDisplayForm):
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')
    target_ids = tuple()

    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    blacklist_labels = ('TargetCode', )

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

        country = self.print_value(res[0].MemberState, 'CountryCode')

        return country

    def download_results(self):
        data = self.get_flattened_data(self)

        parent = self.context.context.context.context
        mapper_class = parent.mapper_class
        target_mc = parent.target_mc

        marine_units = self.context.get_available_marine_unit_ids()[1]

        count, target_feature = db.get_all_records(
            sql2018.ART10TargetsTargetFeature,
            sql2018.ART10TargetsTargetFeature.Feature.in_(data['feature']),
            raw=True
        )
        feature_id_target = [x.IdTarget for x in target_feature]

        s = sql2018.ART10TargetsTargetGESComponent
        count, target_ges = db.get_all_records(
            s,
            s.GESComponent.in_(data['ges_component']),
            raw=True
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
                 ),
            raw=True
        )
        marine_unit_ids = [x.Id for x in marine_unit_ids]

        count, target = db.get_all_records(
            target_mc,
            and_(target_mc.IdMarineUnit.in_(marine_unit_ids),
                 target_mc.Id.in_(set(feature_id_target) & set(ges_id_target))),
            raw=True
        )
        target_ids = [x.Id for x in target]
        marine_unit_ids = [x.IdMarineUnit for x in target]

        count, marine_unit = db.get_all_records(
            mapper_class,
            mapper_class.Id.in_(marine_unit_ids),
            raw=True
        )

        s = sql2018.ART10TargetsProgressAssessment
        count, target_progress = db.get_all_records(
            s,
            s.IdTarget.in_(target_ids),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('ART10TargetsMarineUnit', marine_unit),
            ('ART10TargetsTarget', target),
            ('ART10TargetsTargetFeature', target_feature),
            ('ART10TargetsTargetGESComponent', target_ges),
            ('ART10TargetsProgressAssessment', target_progress),
        ]

        return xlsdata

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
        target_ids = list(map(int, target_ids))

        features_ids = db.get_unique_from_mapper(
            sql2018.ART10TargetsTargetFeature,
            'IdTarget',
            sql2018.ART10TargetsTargetFeature.Feature.in_(features)
        )
        features_ids = list(map(int, features_ids))

        s = sql2018.ART10TargetsTargetGESComponent
        ges_components_ids = db.get_unique_from_mapper(
            s,
            'IdTarget',
            s.GESComponent.in_(ges_components)
        )
        ges_components_ids = list(map(int, ges_components_ids))

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

        mc_gescomp = sql2018.ART10TargetsTargetGESComponent
        count, res = db.get_all_records(
            mc_gescomp,
            mc_gescomp.IdTarget == target_id
        )
        gescomps = [{'GES Component': row.GESComponent} for row in res]

        mc_features = sql2018.ART10TargetsTargetFeature
        count, res = db.get_all_records(
            mc_features,
            mc_features.IdTarget == target_id
        )
        features = [{'Feature': row.Feature} for row in res]

        mc_measures = sql2018.ART10TargetsTargetMeasure
        count, res = db.get_all_records(
            mc_measures,
            mc_measures.IdTarget == target_id
        )
        measures = [{'Measure': row.Measure} for row in res]

        res = [
            ('GES Components', {'GES Components': gescomps}),
            ('Features', {'Features': features}),
            ('Measures', {'Measures': measures}),
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
