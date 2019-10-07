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
    # fields['monitoring_programme_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.data.get('data_type')

        return klass(self, self.request)

    # def default_monitoring_programme_types(self):
    #     field = self.fields['monitoring_programme_types']
    #
    #     return [int(x) for x in all_values_from_field(self, field)]


class A18MeasureProgressDisplay(ItemDisplayForm):
    title = "Measure Progress display"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART18MeasureProgres
    css_class = 'left-side-form'

    def download_results(self):
        pass

    def get_db_results(self):
        page = self.get_page()

        item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            # conditions,
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
        pass

    def get_db_results(self):
        page = self.get_page()

        item = db.get_item_by_conditions(
            self.mapper_class,
            'Id',
            # conditions,
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

    # fields = Fields(interfaces.IMemberStates)
    # fields['member_states'].widgetFactory = CheckBoxFieldWidget
    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A18DescriptorForm(self, self.request)


@register_form_art18
class A18CategoryForm(EmbeddedForm):
    """"""
    record_title = "Article 18 (Category)"
    title = "Category"
    display_klass = A18CategoryDisplay
    mapper_class = sql2018.ART18Category1bNotWFD

    # fields = Fields(interfaces.IMemberStates)
    # fields['member_states'].widgetFactory = CheckBoxFieldWidget
    fields = Fields(interfaces.ICountryCode)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A18DescriptorForm(self, self.request)


# class A18CountryForm(EmbeddedForm):
#     """"""
#
#     fields = Fields(interfaces.IMemberStates)
#     fields['member_states'].widgetFactory = CheckBoxFieldWidget
#
#     def get_subform(self):
#         return A18DescriptorForm(self, self.request)


class A18DescriptorForm(EmbeddedForm):
    """"""
    fields = Fields(interfaces.IGESComponentsA18)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.context.display_klass

        return klass(self, self.request)
