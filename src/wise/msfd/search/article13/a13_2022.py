# pylint: skip-file
""" Forms and views for Article 13 - 2022 reporting year
"""
from __future__ import absolute_import
import logging
from itertools import chain

from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art13, register_form_art1318

logger = logging.getLogger('wise.msfd')


@register_form_art1318
class Article13_2022Form(EmbeddedForm):
    """Bridge: Article 13 - 2022"""
    record_title = title = 'Article 13 - Measures'
    report_type = "Measures"
    session_name = '2018'

    fields = Fields()

    def update(self):
        super(EmbeddedForm, self).update()
        self.data, errors = self.extractData()
        subform = self.get_subform()
        if subform is not None:
            self.subform = subform

    def get_subform(self):
        return Article132022Form(self, self.request)


@register_form_art13
class Article132022Form(EmbeddedForm):
    """Article132022Form"""
    record_title = 'Article 13 - Measures'
    title = '2022 reporting exercise'
    report_type = "Measures"
    session_name = '2018'

    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Article132022DescriptorForm(self, self.request)


class Article132022DescriptorForm(EmbeddedForm):
    """Article132022DescriptorForm"""

    fields = Fields(interfaces.IGESComponentsA132022)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Article132022Display(self, self.request)


class Article132022Display(ItemDisplayForm):
    """ Article132022Display """
    title = "Measure Progress display"
    mapper_class = sql2018.t_V_ART13_Measures_2022
    order_field = 'CountryCode'
    css_class = 'left-side-form'
    blacklist = ("ReportingDate", "CountryCode")
    blacklist_labels = ["MeasureCode", "MeasureOldCode",
                        "ImplementationDelay", "PoliciesConventions",
                        "RelevantKTMs", "CoordinationLevel"]

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
        try:
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
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return []

        xlsdata = [
            ('MSFD13Measures', rows_filtered)
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
        try:
            q = sess.query(self.mapper_class).filter(
                *conditions).order_by(self.order_field)

            rows_filtered = []

            for row in q:
                if not row.GEScomponent:
                    continue
                ges_reported = row.GEScomponent.split(';')
                # sometimes GEScomponents are separated by comma too
                # also split by comma
                ges_reported = [d.split(',') for d in ges_reported]
                ges_reported = chain.from_iterable(ges_reported)
                ges_reported = set([d.strip() for d in ges_reported])

                if set(ges_comps).intersection(set(ges_reported)):
                    rows_filtered.append(row)
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return [0, {}]

        total = len(rows_filtered)
        if not total:
            return [0, {}]

        item = rows_filtered[page]

        return [total, item]
