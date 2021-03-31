import logging

from collections import defaultdict
from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql, sql2018
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..interfaces import IMarineUnitIDsSelect
from ..labels import GES_LABELS
from ..utils import all_values_from_field, db_objects_to_dict, group_data
from .base import ItemDisplay, ItemDisplayForm, MainForm, MultiItemDisplayForm
from .utils import data_to_xls, register_form_art11, register_form_section


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
    title = "Monitoring Programmes - 2020"
    session_name = '2018'

    fields = Fields(interfaces.IRegionSubregionsArt112020)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

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
        return A11MProgrammeDisplay2020(self, self.request)


class A11MProgrammeDisplay2020(ItemDisplayForm, A112020Mixin):
    css_class = 'left-side-form'
    title = "Monitoring Programmes display"
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART11ProgrammesMonitoringProgramme

    blacklist_labels = ('ProgrammeCode', )

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
        return []

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
            {'': [{'': x} for x in data_db],}
        )

        return result

    def get_extra_data(self):
        if not self.item:
            return {}

        res = []

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeDataAcces,
            'DataAccess',
            'Data Access'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit,
            'MarineReportingUnit',
            'MarineReportingUnit(s)'
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
            'Monitoring Purpose'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeMonitoringType,
            'MonitoringType',
            'Monitoring Type'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeOldProgrammeCode,
            'OldProgrammeCode',
            'Old Programme Code'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeOtherPoliciesConvention,
            'OtherPoliciesConventions',
            'Other Policies Conventions'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCoordination,
            'RegionalCooperation_coordination',
            'Regional Cooperation Coordination'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeRegionalCooperationCountry,
            'RegionalCooperation_countries',
            'Regional Cooperation Countries'
        )
        res.append(_data)

        _data = self.create_extra_data(
            sql2018.ART11ProgrammesMonitoringProgrammeSpatialScope,
            'SpatialScope',
            'Spatial Scope'
        )
        res.append(_data)

        return res


# @register_form_art11
class A11MonitoringStrategyForm2020(EmbeddedForm):
    record_title = 'Article 11 (Monitoring Programmes)'
    title = "Monitoring Strategy - 2020"

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return None
