#pylint: skip-file
""" Forms and views for Article 13-14 search
"""
from __future__ import absolute_import
from itertools import chain

from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm
from wise.msfd.search.base import ItemDisplayForm, MainForm
from wise.msfd.search.utils import register_form_art14

from wise.msfd.search.article13.a13_2016 import MemberStatesForm


class StartArticle14Form(MainForm):
    record_title = title = 'Article 14 - Exceptions'
    session_name = '2012'
    name = 'exceptions'
    report_type = "Exceptions"

    fields = Fields(interfaces.IStartArticle14)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        db.threadlocals.session_name = session_name

        return klass(self, self.request)


@register_form_art14
class Article142016Form(EmbeddedForm):
    record_title = 'Article 14 - Exceptions'
    title = '2016 reporting exercise'
    report_type = "Exceptions"
    session_name = '2012'
    name = 'exceptions'

    fields = Fields(interfaces.IArticles1314Region)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


@register_form_art14
class Article142022Form(EmbeddedForm):
    """Article142022Form"""
    record_title = 'Article 14 - Exceptions'
    title = '2022 reporting exercise'
    report_type = "Exceptions"
    session_name = '2018'

    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Article142022DescriptorForm(self, self.request)


class Article142022DescriptorForm(EmbeddedForm):
    """Article142022DescriptorForm"""

    fields = Fields(interfaces.IGESComponentsA142022)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Article142022Display(self, self.request)


class Article142022Display(ItemDisplayForm):
    """ Article142022Display """
    title = "Exceptions display"
    mapper_class = sql2018.t_V_ART14_Exceptions_2022
    order_field = 'CountryCode'
    css_class = 'left-side-form'
    blacklist = ("ReportingDate", "CountryCode")
    blacklist_labels = ["Exception_code", "ExceptionOldCode",
                        "Exception_name"]

    def get_reported_date(self):
        return self.item.ReportingDate

    def get_current_country(self):
        country = self.print_value(self.item.CountryCode, 'CountryCode')

        return country

    @db.use_db_session('2018')
    def download_results(self):
        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')

        conditions = []

        if countries:
            conditions.append(self.mapper_class.c.CountryCode.in_(countries))

        sess = db.session()
        q = sess.query(self.mapper_class).filter(
            *conditions).order_by(self.order_field)

        rows_filtered = []

        for row in q:
            ges_reported = row.GEScomponent.split(';')
            # sometimes GEScomponents are separated by comma too
            # also split by comma
            ges_reported = [d.split(',') for d in ges_reported]
            ges_reported = chain.from_iterable(ges_reported)
            ges_reported = set([d.strip() for d in ges_reported])

            if set(ges_comps).intersection(set(ges_reported)):
                rows_filtered.append(row)

        xlsdata = [
            ('MSFD14Measures', rows_filtered)
        ]

        return xlsdata

    @db.use_db_session('2018')
    def get_db_results(self):
        page = self.get_page()

        countries = self.get_form_data_by_key(self, 'member_states')
        ges_comps = self.get_form_data_by_key(self, 'ges_component')

        conditions = []

        if countries:
            conditions.append(self.mapper_class.c.CountryCode.in_(countries))

        sess = db.session()
        q = sess.query(self.mapper_class).filter(
            *conditions).order_by(self.order_field)

        rows_filtered = []

        for row in q:
            ges_reported = row.GEScomponent.split(';')
            # sometimes GEScomponents are separated by comma too
            # also split by comma
            ges_reported = [d.split(',') for d in ges_reported]
            ges_reported = chain.from_iterable(ges_reported)
            ges_reported = set([d.strip() for d in ges_reported])

            if set(ges_comps).intersection(set(ges_reported)):
                rows_filtered.append(row)

        total = len(rows_filtered)
        if not total:
            return [0, {}]

        item = rows_filtered[page]

        return [total, item]

