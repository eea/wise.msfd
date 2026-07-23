# pylint: skip-file
""" Forms and views for Article 18 - 2024 reporting year
"""
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art18_2024


class A18Measures2024Display(ItemDisplayForm):
    title = "Article 18 Measures (2024)"
    session_name = '2024'

    mapper_class = sql2024.t_ART18_Measures
    order_field = 'MeasureCode'
    css_class = 'left-side-form'

    blacklist = (
        'SnapshotId', 'ReportingDate', 'Comment',
    )

    def get_current_country(self):
        country_code = self.item.CountryCode

        return self.print_value(country_code, 'CountryCode')

    @db.use_db_session('2024')
    def get_reported_date(self):
        return self.format_reported_date(self.item.ReportingDate)

    @db.use_db_session('2024')
    def download_results(self):
        t = self.mapper_class
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_comps = data.get('ges_component', [])

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))
        if ges_comps:
            conditions.append(t.c.GEScomponent.in_(ges_comps))

        count, data = db.get_all_records(
            t,
            *conditions,
            raw=True
        )

        xlsdata = [
            ('ART18_Measures', data),
        ]

        return xlsdata

    @db.use_db_session('2024')
    def get_db_results(self):
        page = self.get_page()
        t = self.mapper_class
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_comps = data.get('ges_component', [])

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))
        if ges_comps:
            conditions.append(t.c.GEScomponent.in_(ges_comps))

        item = db.get_item_by_conditions_table(
            t, 'MeasureCode', *conditions, page=page
        )

        return item


# @register_form_art18_2024
class A18Measures2024Form(EmbeddedForm):
    """"""
    record_title = "Article 18 (Measures - 2024)"
    title = "Measure Progress"
    display_klass = A18Measures2024Display
    mapper_class = sql2024.t_ART18_Measures

    session_name = '2024'

    fields = Fields(interfaces.ICountryCode2024A18)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A18GES2024Form(self, self.request)

    @db.use_db_session('2024')
    def get_ges_components(self):
        t = self.mapper_class
        data = self.get_flattened_data(self)
        countries = data.get('member_states', [])
        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        count, measures = db.get_all_records(
            t,
            *conditions
        )
        ges_components = set([
            x.GEScomponent for x in measures if x.GEScomponent
        ])

        return ges_components


class A18GES2024Form(EmbeddedForm):
    """"""
    fields = Fields(interfaces.IGESComponentsA18)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    session_name = '2024'

    def get_subform(self):
        klass = self.context.display_klass

        return klass(self, self.request)
