# pylint: skip-file
from __future__ import absolute_import
from sqlalchemy import and_, or_
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art9


#########################
#       Article 9       #
#########################

class Art9Display(ItemDisplayForm):
    css_class = 'left-side-form'
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')
    show_extra_data = True

    blacklist = ('Id', 'IdGESComponent')

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

        country = self.print_value(res[0].CountryCode, 'CountryCode')

        return country

    def download_results(self):
        parent = self.context.context.context
        mapper_class = parent.mapper_class
        features_mc = parent.features_mc
        determination_mc = sql2018.ART9GESGESDetermination

        count, ges_component = db.get_all_records_outerjoin(
            mapper_class,
            sql2018.ReportedInformation,
            self.condition_ges_component,
            raw=True
        )
        id_ges_comp = [x.Id for x in ges_component]

        count, ges_determination = db.get_all_records(
            determination_mc,
            determination_mc.IdGESComponent.in_(id_ges_comp),
            raw=True
        )
        id_ges_deter = [x.Id for x in ges_determination]

        count, ges_deter_feature = db.get_all_records(
            features_mc,
            features_mc.IdGESDetermination.in_(id_ges_deter),
            raw=True
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

        return xlsdata

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
                # mapper_class.JustificationDelay.is_(None),
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

        if getattr(res, 'JustificationNonUse', 0):
            # or getattr(res, 'JustificationDelay', 0)
            self.show_extra_data = False

            return count, res

        self.show_extra_data = True
        id_ges_comp = res.Id

        # cnt, res = db.get_related_record(
        #     determination_mc,
        #     'IdGESComponent',
        #     id_ges_comp
        # )

        cnt, res = db.get_all_records_join(
            [mapper_class.GESComponent, mapper_class.JustificationDelay,
             determination_mc.GESDescription,
             determination_mc.Id, determination_mc.IdGESComponent,
             determination_mc.DeterminationDate, determination_mc.UpdateType],
            determination_mc,
            determination_mc.IdGESComponent == id_ges_comp
        )

        return count, res[0]

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
            ('', {
                '': [{'Marine Unit(s)': x} for x in marine_units]
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
