# pylint: skip-file
from __future__ import absolute_import
import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql2018
from ..base import EmbeddedForm
from ..utils import db_objects_to_dict
from .base import ItemDisplayForm2018
from .utils import register_form_art11

logger = logging.getLogger('wise.msfd')


class A112020Mixin:
    def get_programme_codes_needed(self):
        data = db.A11_REGIONS_COUNTRIES
        data_desc = db.A11_DESCR_PROG_CODES
        regions = self.get_form_data_by_key(self, 'region_subregions')
        countries = self.get_form_data_by_key(self, 'member_states')
        descriptors = self.get_form_data_by_key(self, 'ges_component')

        if regions:
            data = [x for x in data if x.Region in regions]

        if countries:
            data = [x for x in data if x.CountryCode in countries]

        if descriptors:
            data_desc = [x for x in data_desc if x.Descriptor in descriptors]

        programme_codes = set([
            x.MonitoringProgrammes.upper()
            for x in data_desc
        ])

        final_prog_codes = set([
            x.ProgrammeCode
            for x in data
            if x.ProgrammeCode.upper() in programme_codes
        ])

        return final_prog_codes


@register_form_art11
class A11MonitoringProgrammeForm2020(EmbeddedForm):
    record_title = 'Article 11 (Monitoring Programmes) - 2020'
    title = "2020 Monitoring programmes"
    session_name = '2018'

    fields = Fields(interfaces.IRegionSubregionsArt112020)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    @property
    def display_class(self):
        return A11MProgrammeDisplay2020

    def get_subform(self):
        return A11MProgrammeMemberStateForm2020(self, self.request)


class A11MProgrammeMemberStateForm2020(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt112020)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A11MProgrammeDescriptorForm2020(self, self.request)


class A11MProgrammeDescriptorForm2020(EmbeddedForm):
    fields = Fields(interfaces.IGESComponentArt112020)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        display_class = self.context.context.display_class

        return display_class(self, self.request)


class A11MProgrammeDisplay2020(ItemDisplayForm2018, A112020Mixin):
    css_class = 'left-side-form'
    title = "Monitoring Programmes display"
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART11ProgrammesMonitoringProgramme

    blacklist_labels = ('ProgrammeCode', 'RelatedIndicator_code')

    def download_results(self):
        prog_codes = self.get_programme_codes_needed()

        count, mp_data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.ProgrammeCode.in_(prog_codes),
            raw=True
        )
        mp_ids = [x.Id for x in mp_data]

        count, features = db.get_all_records(
            sql2018.ART11ProgrammesFeature,
            sql2018.ART11ProgrammesFeature.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )
        feature_ids = [x.Id for x in features]

        count, elements = db.get_all_records(
            sql2018.ART11ProgrammesElement,
            sql2018.ART11ProgrammesElement.IdFeature.in_(feature_ids),
            raw=True
        )
        element_ids = [x.Id for x in elements]

        count, criterias = db.get_all_records(
            sql2018.ART11ProgrammesCriterion,
            sql2018.ART11ProgrammesCriterion.IdElement.in_(element_ids),
            raw=True
        )
        criteria_ids = [x.Id for x in criterias]

        mc = sql2018.ART11ProgrammesCriteriaParameter
        count, crit_params = db.get_all_records(
            mc,
            mc.IdCriteria.in_(criteria_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesRelatedIndicator
        count, indicators = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeDataAcces
        count, data_access = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit
        count, mru = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeMonitoringMethod
        count, method = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeMonitoringPurpose
        count, purpose = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeMonitoringType
        count, type = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeOldProgrammeCode
        count, oldcode = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeOtherPoliciesConvention
        count, policies = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCoordination
        count, coord = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCountry
        count, country = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mc = sql2018.ART11ProgrammesMonitoringProgrammeSpatialScope
        count, scope = db.get_all_records(
            mc,
            mc.IdMonitoringProgramme.in_(mp_ids),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('ART11MonitoringProgramme', mp_data),
            ('ART11Feature', features),
            ('ART11Element', elements),
            ('ART11Criterion', criterias),
            ('ART11CriteriaParameter', crit_params),
            ('ART11RelatedIndicator', indicators),
            ('ART11MPDataAcces', data_access),
            ('ART11MPMarineReportingUnit', mru),
            ('ART11MPMonitoringMethod', method),
            ('ART11MPMonitoringPurpose', purpose),
            ('ART11MPMonitoringType', type),
            ('ART11MPOldProgrammeCode', oldcode),
            ('ART11MPOtherPoliciesConvention', policies),
            ('ART11MPRegionalCoopCoord', coord),
            ('ART11MPRegionalCoopCountry', country),
            ('ART11MPSpatialScope', scope),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        prog_codes = self.get_programme_codes_needed()

        count, item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            self.mapper_class.ProgrammeCode.in_(prog_codes),
            page=page
        )

        return count, item

    def create_extra_data(self, mc, col_name, title):
        mp_id = self.item.Id

        data_db = db.get_unique_from_mapper(
            mc,
            col_name,
            mc.IdMonitoringProgramme == mp_id
        )
        result = [title, {}]

        if not data_db:
            return result

        result = (
            title,
            {'': [{'': x} for x in data_db], }
        )

        return result

    def get_extra_data(self):
        if not self.item:
            return {}
        mp_id = self.item.Id

        mc_mp = self.mapper_class
        mc_feat = sql2018.ART11ProgrammesFeature
        mc_elem = sql2018.ART11ProgrammesElement
        mc_crit = sql2018.ART11ProgrammesCriterion
        mc_param = sql2018.ART11ProgrammesCriteriaParameter

        columns = [
            mc_mp.Id,
            mc_feat.Feature,
            mc_elem.Element,
            mc_param.Parameter,
            mc_crit.ParameterOther,
            mc_crit.GESCriteria
        ]

        sess = db.session()
        features_elements = sess.query(*columns) \
            .join(mc_feat, mc_feat.IdMonitoringProgramme == mc_mp.Id) \
            .join(mc_elem, mc_elem.IdFeature == mc_feat.Id) \
            .join(mc_crit, mc_crit.IdElement == mc_elem.Id) \
            .join(mc_param, mc_param.IdCriteria == mc_crit.Id) \
            .filter(mc_mp.Id == mp_id)

        features_elements = db_objects_to_dict(features_elements, ('Id', ))
        title = 'Features, Elements, Parameters and Criterias'
        _data = [title, {}]

        if features_elements:
            _data = (title, {'': features_elements})

        res = [_data]

        title = 'Related indicators'
        mc = sql2018.ART11ProgrammesRelatedIndicator
        count, indicator_data = db.get_all_specific_columns(
            [mc.RelatedIndicator_code, mc.RelatedIndicator_name],
            mc.IdMonitoringProgramme == mp_id
        )
        indicator_data = db_objects_to_dict(indicator_data)
        _data = [title, {}]

        if indicator_data:
            _data = (title, {'': indicator_data})

        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeDataAcces,
            'DataAccess',
            'Data access'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit,
            'MarineReportingUnit',
            'Marine reporting unit(s)'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMonitoringMethod,
            'MonitoringMethod',
            'Monitoring Method'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMonitoringPurpose,
            'MonitoringPurpose',
            'Monitoring purpose'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMonitoringType,
            'MonitoringType',
            'Monitoring type'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeOldProgrammeCode,
            'OldProgrammeCode',
            'Old programme code'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeOtherPoliciesConvention,
            'OtherPoliciesConventions',
            'Other policies conventions'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCoordination,
            'RegionalCooperation_coordination',
            'Regional cooperation coordination'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCountry,
            'RegionalCooperation_countries',
            'Regional cooperation countries'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeSpatialScope,
            'SpatialScope',
            'Spatial scope'
        )
        res.append(_data)

        return res


@register_form_art11
class A11MonitoringStrategyForm2020(EmbeddedForm):
    record_title = 'Article 11 (Monitoring Strategies) - 2020'
    title = "2020 Monitoring strategies"
    session_name = '2018'

    fields = Fields(interfaces.IRegionSubregionsArt112020)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    @property
    def display_class(self):
        return A11MStrategyDisplay2020

    def get_subform(self):
        return A11MProgrammeMemberStateForm2020(self, self.request)


class A11MStrategyDisplay2020(ItemDisplayForm2018, A112020Mixin):
    css_class = 'left-side-form'
    title = "Monitoring Strategies display"
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART11StrategiesMonitoringStrategy
    extra_data_template_v2 = ViewPageTemplateFile('pt/extra-data-pivot-a11.pt')
    # blacklist_labels = ()
    blacklist = ()

    def get_import_id(self):
        metadata_id = self.item.IdMetadata

        count, metadata = db.get_related_record(
            sql2018.ART11StrategiesMetadatum,
            'Id',
            metadata_id
        )
        import_id = metadata.IdReportedInformation

        return import_id

    def download_results(self):
        prog_codes = self.get_programme_codes_needed()
        mc = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme

        strategy_ids = db.get_unique_from_mapper(
            mc,
            'IdMonitoringStrategy',
            mc.MonitoringProgrammes.in_(prog_codes),
            raw=True
        )

        count, strategy_data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.Id.in_(strategy_ids),
            raw=True
        )
        metadata_ids = [x.IdMetadata for x in strategy_data]
        strategy_ids = [x.Id for x in strategy_data]

        mc = sql2018.ART11StrategiesMetadatum
        count, metadata = db.get_all_records(
            mc,
            mc.Id.in_(metadata_ids),
            raw=True
        )

        mc = sql2018.ART11StrategiesMetadataResponsibleCompetentAuthority
        count, comp_auth = db.get_all_records(
            mc,
            mc.IdMetadata.in_(metadata_ids),
            raw=True
        )

        mc = sql2018.ART11StrategiesMetadataResponsibleOrganisation
        count, resp_org = db.get_all_records(
            mc,
            mc.IdMetadata.in_(metadata_ids),
            raw=True
        )

        mc = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme
        count, mon_prog = db.get_all_records(
            mc,
            mc.IdMonitoringStrategy.in_(strategy_ids),
            raw=True
        )

        mc = sql2018.ART11StrategiesMonitoringStrategyRelatedMeasure
        count, measures = db.get_all_records(
            mc,
            mc.IdMonitoringStrategy.in_(strategy_ids),
            raw=True
        )

        mc = sql2018.ART11StrategiesMonitoringStrategyRelatedTarget
        count, targets = db.get_all_records(
            mc,
            mc.IdMonitoringStrategy.in_(strategy_ids),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('ART11MonitoringStrategy', strategy_data),
            ('ART11Metadata', metadata),
            ('ART11ResponsibleCompAuthority', comp_auth),
            ('ART11ResponsibleOrganisation', resp_org),
            ('ART11StrategyMonitoringProg', mon_prog),
            ('ART11StrategyRelatedMeasure', measures),
            ('ART11StrategyRelatedTarget', targets),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        prog_codes = self.get_programme_codes_needed()
        descriptors = self.get_form_data_by_key(self, 'ges_component')
        mc = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme

        strategy_ids = db.get_unique_from_mapper(
            mc,
            'IdMonitoringStrategy',
            mc.MonitoringProgrammes.in_(prog_codes)
        )

        conditions = [self.mapper_class.Id.in_(strategy_ids)]

        if descriptors:
            conditions.append(self.mapper_class.Descriptor.in_(descriptors))

        count, item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            *conditions,
            page=page
        )

        return count, item

    def create_extra_data(self, mc, col_name, title, *conditions):
        data_db = db.get_unique_from_mapper(
            mc,
            col_name,
            *conditions
        )
        result = [title, {}]

        if not data_db:
            return result

        result = (
            title,
            {'': [{'': x} for x in data_db]}
        )

        return result

    def get_extra_data(self):
        if not self.item:
            return {}

        res = []

        meta_id = self.item.IdMetadata
        strat_id = self.item.Id

        title = 'Metadata'
        _data = [title, {}]
        count, metadata = db.get_all_records(
            sql2018.ART11StrategiesMetadatum,
            sql2018.ART11StrategiesMetadatum.Id == meta_id
        )
        metadata = db_objects_to_dict(metadata,
                                      ('Id', 'IdReportedInformation'))

        if metadata:
            _data = (title, {'': metadata})

        res.append(_data)

        # mc = sql2018.ART11StrategiesMetadataResponsibleCompetentAuthority
        # _data = self.create_extra_data(
        #     mc,
        #     'ResponsibleCompetentAuthority',
        #     'Responsible competent authority',
        #     mc.IdMetadata == meta_id
        # )
        # res.append(_data)

        # mc = sql2018.ART11StrategiesMetadataResponsibleOrganisation
        # _data = self.create_extra_data(
        #     mc,
        #     'ResponsibleOrganisations',
        #     'Responsible organisations',
        #     mc.IdMetadata == meta_id
        # )
        # res.append(_data)

        # mc = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme
        # _data = self.create_extra_data(
        #     mc,
        #     'MonitoringProgrammes',
        #     'Monitoring programmes',
        #     mc.IdMonitoringStrategy == strat_id
        # )
        # res.append(_data)

        # mc = sql2018.ART11StrategiesMonitoringStrategyRelatedMeasure
        # title = 'Related measures'
        # _data = [title, {}]
        # count, measures = db.get_all_records(
        #     mc,
        #     mc.IdMonitoringStrategy == strat_id
        # )
        # measures = db_objects_to_dict(measures,
        #                               ('Id', 'IdMonitoringStrategy'))

        # if measures:
        #     _data = (title, {'': measures})

        # res.append(_data)

        # mc = sql2018.ART11StrategiesMonitoringStrategyRelatedTarget
        # _data = self.create_extra_data(
        #     mc,
        #     'RelatedTargets',
        #     'Related targets',
        #     mc.IdMonitoringStrategy == strat_id
        # )
        # res.append(_data)

        return res

    def extras(self):
        html = self.extra_data_template(extra_data=self.get_extra_data())

        extra_data = []
        meta_id = self.item.IdMetadata
        strat_id = self.item.Id

        mc = sql2018.ART11StrategiesMetadataResponsibleCompetentAuthority
        data_db = db.get_unique_from_mapper(
            mc,
            'ResponsibleCompetentAuthority',
            mc.IdMetadata == meta_id
        )
        data_db = [x for x in data_db if x]
        extra_data.append(['Responsible competent authority', data_db or []])

        mc = sql2018.ART11StrategiesMetadataResponsibleOrganisation
        data_db = db.get_unique_from_mapper(
            mc,
            'ResponsibleOrganisations',
            mc.IdMetadata == meta_id
        )
        data_db = [x for x in data_db if x]
        extra_data.append(['Responsible organisations', data_db or []])

        mc = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme
        data_db = db.get_unique_from_mapper(
            mc,
            'MonitoringProgrammes',
            mc.IdMonitoringStrategy == strat_id
        )
        data_db = [x for x in data_db if x]
        extra_data.append(['Monitoring programmes', data_db or []])

        # TODO 
        mc = sql2018.ART11StrategiesMonitoringStrategyRelatedMeasure
        _, data_db = db.get_all_records(
            mc,
            mc.IdMonitoringStrategy == strat_id
        )
        # RelatedMeasure_code, RelatedMeasure_name
        data_db = [
            "{} - {}".format(x.RelatedMeasure_code, x.RelatedMeasure_name)
            for x in data_db 
            if x
        ]
        extra_data.append(['Related measures', data_db or []])

        mc = sql2018.ART11StrategiesMonitoringStrategyRelatedTarget
        data_db = db.get_unique_from_mapper(
            mc,
            'RelatedTargets',
            mc.IdMonitoringStrategy == strat_id
        )
        data_db = [x for x in data_db if x]
        extra_data.append(['Related targets', data_db or []])

        extra_html = self.extra_data_template_v2(extra_data=([
            "Responsible competent authority, organisations, monitoring programmes, related measures, related targets", extra_data
        ],))

        return html + extra_html
