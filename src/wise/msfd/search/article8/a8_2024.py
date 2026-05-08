# pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.utils import group_data
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_a8_2024


class A2024Art8GesDisplay(ItemDisplayForm):
    record_title = title = 'Article 8.1ab (GES assessments)'
    session_name = '2024'
    css_class = "left-side-form"

    mapper_class = sql2024.t_V_ART8_GES_2024
    order_field = 'MarineReportingUnit'

    data_template = ViewPageTemplateFile('../pt/item-display-rows.pt')

    blacklist = (
        'CountryCode', 'ReportingDate'
    )
    blacklist_labels = (
        'CountryCode',
    )
    excluded_columns = (
        'SnapshotId',
    )

    def get_current_country(self):
        country_code = self.item[0]['CountryCode']

        return self.print_value(country_code, 'CountryCode')

    @db.use_db_session('2024')
    def get_reported_date(self):
        return self.format_reported_date(self.item[0]['ReportingDate'])

    @db.use_db_session('2024')
    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])
        marine_units = data.get('marine_unit_id', [])

        t = sql2024.t_V_ART8_GES_2024

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        if marine_units:
            conditions.append(t.c.MarineReportingUnit.in_(marine_units))

        sess = db.session()
        q = sess.query(t).filter(*conditions).order_by(
            t.c.CountryCode,
            t.c.MarineReportingUnit,
            t.c.GEScomponent,
            t.c.Feature,
        )

        all_rows = q.all()
        data_rows = []
        for row in all_rows:
            row_dict = dict(row._mapping)
            data_rows.append(row_dict)

        if not data_rows:
            return 0, []

        grouped = group_data(data_rows, 'MarineReportingUnit',
                             remove_pivot=False)

        pages = sorted(grouped.keys())
        count = len(pages)

        if not count:
            return 0, []

        if page >= count:
            page = count - 1

        current_mru = pages[page]
        items = grouped[current_mru]

        return count, items

    @db.use_db_session('2024')
    def download_results(self):
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])
        marine_units = data.get('marine_unit_id', [])

        t = sql2024.t_V_ART8_GES_2024

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        if marine_units:
            conditions.append(t.c.MarineReportingUnit.in_(marine_units))

        sess = db.session()
        columns = [
            c for c in t.c
            if c.name not in self.excluded_columns
        ]

        q = sess.query(*columns).filter(*conditions).order_by(
            t.c.CountryCode,
            t.c.MarineReportingUnit,
            t.c.GEScomponent,
            t.c.Feature,
        )

        all_rows = q.all()

        xlsdata = [
            ('V_ART8_GES_2024', all_rows),
        ]

        return xlsdata


class A2024Art8MarineUnitID(EmbeddedForm):
    fields = Fields(interfaces.IMarineUnit2024A8)
    fields['marine_unit_id'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art8GesDisplay(self, self.request)

    @db.use_db_session('2024')
    def get_available_marine_unit_ids(self):
        data = self.get_flattened_data(self)
        parent = self.context.context

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])

        t = sql2024.t_V_ART8_GES_2024

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        sess = db.session()
        q = sess.query(t.c.MarineReportingUnit).filter(*conditions).distinct()
        res = [row[0] for row in q if row[0]]

        return len(res), sorted(res)


class A2024Art8Features(EmbeddedForm):
    fields = Fields(interfaces.IFeatures2024A8)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art8MarineUnitID(self, self.request)


class A2024Art8GesComponents(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents2024A8)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art8Features(self, self.request)


@register_form_a8_2024
class A2024Article81ab(EmbeddedForm):
    record_title = 'Article 8.1ab (GES assessments)'
    title = 'Article 8.1ab (GES assessments)'
    mapper_class = sql2024.t_V_ART8_GES_2024

    fields = Fields(interfaces.ICountryCode2024A8)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art8GesComponents(self, self.request)
