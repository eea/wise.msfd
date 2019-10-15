from collections import defaultdict
from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql, sql2018
from ..base import EmbeddedForm
from ..interfaces import IMarineUnitIDsSelect
from ..utils import all_values_from_field, db_objects_to_dict, group_data
from .base import ItemDisplay, ItemDisplayForm, MainForm, MultiItemDisplayForm
from .utils import data_to_xls, register_form_art18, register_form_section


class StartArticle18Form(MainForm):
    """ Start form for Article 18 - 2019 reporting year
    """

    # record_title = 'Article 11'
    name = 'msfd-c5'
    session_name = '2018'

    fields = Fields(interfaces.IStartArticle18)

    def get_subform(self):
        klass = self.data.get('data_type')

        return klass(self, self.request)


class A18MeasureProgressDisplay(ItemDisplayForm):
    title = "Measure Progress display"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART18MeasureProgres
    css_class = 'left-side-form'

    def download_results(self):
        mc_descr = sql2018.ART18MeasureProgressDescriptor
        mc_countries = sql2018.ReportedInformation

        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')

        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, report_ids = db.get_all_records(
            mc_countries,
            *conditions
        )
        report_ids = [x.Id for x in report_ids]

        conditions = []
        if ges_comps:
            conditions.append(mc_descr.DescriptorCode.in_(ges_comps))

        count, measure_progress_ids = db.get_all_records(
            mc_descr,
            *conditions
        )
        measure_progress_ids = [
            x.IdMeasureProgress
            for x in measure_progress_ids
        ]

        count, measure_prog = db.get_all_records(
            self.mapper_class,
            self.mapper_class.IdReportedInformation.in_(report_ids),
            self.mapper_class.Id.in_(measure_progress_ids),
        )
        id_measure = [x.Id for x in measure_prog]

        count, measure_prog_descr = db.get_all_records(
            mc_descr,
            mc_descr.IdMeasureProgress.in_(id_measure)
        )

        xlsdata = [
            ('ART18MeasureProgres', measure_prog),  # worksheet title, row data
            ('ART18MeasureProgressDescriptor', measure_prog_descr),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        mc_descr = sql2018.ART18MeasureProgressDescriptor
        mc_countries = sql2018.ReportedInformation

        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')

        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, report_ids = db.get_all_records(
            mc_countries,
            *conditions
        )
        report_ids = [x.Id for x in report_ids]

        conditions = []
        if ges_comps:
            conditions.append(mc_descr.DescriptorCode.in_(ges_comps))

        count, measure_progress_ids = db.get_all_records(
            mc_descr,
            *conditions
        )
        measure_progress_ids = [
            x.IdMeasureProgress
            for x in measure_progress_ids
        ]

        item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            self.mapper_class.IdReportedInformation.in_(report_ids),
            self.mapper_class.Id.in_(measure_progress_ids),
            page=page
        )

        return item

    def get_extra_data(self):
        if not self.item:
            return {}

        mc = sql2018.ART18MeasureProgressDescriptor
        excluded_columns = ('IdMeasureProgress', )
        res = []
        id_measure = self.item.Id

        count, data = db.get_all_records(
            mc,
            mc.IdMeasureProgress == id_measure
        )

        data = db_objects_to_dict(data, excluded_columns)
        res.append(('MeasureProgress Descriptor', {'': data}))

        return res


class A18CategoryDisplay(ItemDisplayForm):
    title = "Measure Progress display"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART18Category1bNotWFD
    css_class = 'left-side-form'

    def download_results(self):
        mc_countries = sql2018.ReportedInformation
        mc_measure = sql2018.ART18Category1bNotWFDMeasure

        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')
        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, report_ids = db.get_all_records(
            mc_countries,
            *conditions
        )
        report_ids = [x.Id for x in report_ids]

        conditions = [self.mapper_class.IdReportedInformation.in_(report_ids)]

        if ges_comps:
            conditions.append(self.mapper_class.Descriptor.in_(ges_comps))

        count, category = db.get_all_records(
            self.mapper_class,
            *conditions
        )
        id_category = [x.Id for x in category]

        count, category_measure = db.get_all_records(
            mc_measure,
            mc_measure.IdCategory1bNotWFD.in_(id_category)
        )

        xlsdata = [
            ('ART18Category1bNotWFD', category),  # worksheet title, row data
            ('ART18Category1bNotWFDMeasure', category_measure),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()

        mc_countries = sql2018.ReportedInformation

        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')

        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, report_ids = db.get_all_records(
            mc_countries,
            *conditions
        )
        report_ids = [x.Id for x in report_ids]

        conditions = [self.mapper_class.IdReportedInformation.in_(report_ids)]

        if ges_comps:
            conditions.append(self.mapper_class.Descriptor.in_(ges_comps))

        item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            *conditions,
            page=page
        )

        return item

    def get_extra_data(self):
        if not self.item:
            return {}

        mc = sql2018.ART18Category1bNotWFDMeasure
        excluded_columns = ('Id', 'IdCategory1bNotWFD')
        res = []
        id_category = self.item.Id

        count, data = db.get_all_records(
            mc,
            mc.IdCategory1bNotWFD == id_category
        )

        data = db_objects_to_dict(data, excluded_columns)
        res.append(('Category1bNotWFDMeasure', {'': data}))

        return res


@register_form_art18
class A18MeasureProgressForm(EmbeddedForm):
    """"""
    record_title = "Article 18 (Measure Progress)"
    title = "Measure Progress"
    display_klass = A18MeasureProgressDisplay
    mapper_class = sql2018.ART18MeasureProgres

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A18DescriptorForm(self, self.request)

    def get_ges_components(self):
        mc = sql2018.ART18MeasureProgres
        mc_descr = sql2018.ART18MeasureProgressDescriptor
        mc_countries = sql2018.ReportedInformation

        conditions = []

        countries = self.get_form_data_by_key(self, 'member_states')

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, measure_progress = db.get_all_records_outerjoin(
            mc,
            mc_countries,
            *conditions
        )
        measure_progress_ids = [x.Id for x in measure_progress]

        count, ges_components = db.get_all_records(
            mc_descr,
            mc_descr.IdMeasureProgress.in_(measure_progress_ids)
        )
        ges_components = set([x.DescriptorCode for x in ges_components])

        return ges_components


@register_form_art18
class A18CategoryForm(EmbeddedForm):
    """"""
    record_title = "Article 18 (Category)"
    title = "Category"
    display_klass = A18CategoryDisplay
    mapper_class = sql2018.ART18Category1bNotWFD

    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A18DescriptorForm(self, self.request)

    def get_ges_components(self):
        mc_countries = sql2018.ReportedInformation

        conditions = []

        countries = self.get_form_data_by_key(self, 'member_states')

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, category_ids = db.get_all_records_outerjoin(
            self.mapper_class,
            mc_countries,
            *conditions
        )
        ges_components = set([x.Descriptor for x in category_ids])

        return ges_components


class A18DescriptorForm(EmbeddedForm):
    """"""
    fields = Fields(interfaces.IGESComponentsA18)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.context.display_klass

        return klass(self, self.request)
