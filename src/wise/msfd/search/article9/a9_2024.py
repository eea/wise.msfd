# pylint: skip-file
from __future__ import absolute_import
import logging
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art9

logger = logging.getLogger('wise.msfd')

BLACKLIST = (
    'CountryCode', 'ReportingDate',
    'SnapshotId', 'Comment',
)

EXCLUDED_COLUMNS = (
    'SnapshotId', 'Comment',
)


class A2024Art9Display(ItemDisplayForm):
    record_title = title = 'Article 9 (GES determination)'
    session_name = '2024'
    css_class = "left-side-form"

    mapper_class = sql2024.t_V_ART9_GES_2024
    order_field = 'MarineReportingUnit'

    data_template = ViewPageTemplateFile('../pt/item-display.pt')
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')

    blacklist = BLACKLIST
    excluded_columns = EXCLUDED_COLUMNS

    def get_current_country(self):
        country_code = self.item.CountryCode

        return self.print_value(country_code, 'CountryCode')

    @db.use_db_session('2024')
    def get_reported_date(self):
        return self.format_reported_date(self.item.ReportingDate)

    @db.use_db_session('2024')
    def get_db_results(self):
        page = self.get_page()
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])
        marine_units = data.get('marine_unit_id', [])

        t = sql2024.t_V_ART9_GES_2024

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        if marine_units:
            conditions.append(t.c.MarineReportingUnit.in_(marine_units))

        count, item = db.get_item_by_conditions_table(
            t, 'MarineReportingUnit', *conditions, page=page
        )

        self.blacklist = BLACKLIST

        return count, item

    @db.use_db_session('2024')
    def get_extra_data(self):
        if not self.item:
            return []

        # For A9 2024, the view V_ART9_GES_2024 is a flat table
        # without related sub-tables like the 2018 version.
        # JustificationNonUse and JustificationDelay are columns
        # directly on the view.
        return []

    @db.use_db_session('2024')
    def download_results(self):
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])
        marine_units = data.get('marine_unit_id', [])

        t = sql2024.t_V_ART9_GES_2024

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

        try:
            q = sess.query(*columns).filter(*conditions).order_by(
                t.c.CountryCode,
                t.c.MarineReportingUnit,
                t.c.GEScomponent,
                t.c.Feature,
            )

            all_rows = q.all()
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return []

        xlsdata = [
            ('V_ART9_GES_2024', all_rows),
        ]

        return xlsdata


class A2024Art9MarineUnit(EmbeddedForm):
    fields = Fields(interfaces.IMarineUnit2024A9)
    fields['marine_unit_id'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art9Display(self, self.request)

    @db.use_db_session('2024')
    def get_available_marine_unit_ids(self):
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])

        t = sql2024.t_V_ART9_GES_2024

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        sess = db.session()
        try:
            q = sess.query(
                t.c.MarineReportingUnit
            ).filter(*conditions).distinct()
            res = [row[0] for row in q if row[0]]
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return 0, []

        return len(res), sorted(res)


class A2024Art9Features(EmbeddedForm):
    fields = Fields(interfaces.IFeatures2024A9)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art9MarineUnit(self, self.request)


class A2024Art9GesComponents(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents2024A9)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art9Features(self, self.request)


@register_form_art9
class A2024Article9(EmbeddedForm):
    record_title = 'Article 9 (GES determination)'
    title = '2024 reporting exercise'
    session_name = '2024'
    permission = 'zope2.View'
    mapper_class = sql2024.t_V_ART9_GES_2024

    fields = Fields(interfaces.ICountryCode2024A9)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art9GesComponents(self, self.request)
