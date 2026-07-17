# pylint: skip-file
from __future__ import absolute_import
import logging
from sqlalchemy import or_
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm, MarineUnitIDSelectForm
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art10
from wise.msfd.utils import (
    all_values_from_field, db_objects_to_dict, group_data, like_pattern,
)

logger = logging.getLogger('wise.msfd')

BLACKLIST = (
    'CountryCode', 'ReportingDate',
    'SnapshotId', 'Comment',
    'MarineReportingUnit', 'GEScomponent', 'Feature',
    'TargetPurpose', 'RelatedMeasures',
)

EXCLUDED_COLUMNS = (
    'SnapshotId', 'Comment',
)


def _split(value):
    """Split a semicolon-delimited string into a list of stripped values."""
    if not value:
        return []

    return [x.strip() for x in value.split(';') if x.strip()]


class A2024Art10Display(ItemDisplayForm):
    session_name = '2024'

    mapper_class = sql2024.t_ART10_Targets_Target
    order_field = 'TargetCode'

    data_template = ViewPageTemplateFile('../pt/item-display.pt')
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot-a10-2024.pt')

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
        marine_unit_id = data.get('marine_unit_id')

        t = sql2024.t_ART10_Targets_Target

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            or_conditions = [
                t.c.GEScomponent.like(like_pattern(gc))
                for gc in ges_components
            ]
            conditions.append(or_(*or_conditions))

        if features:
            or_conditions = [
                t.c.Feature.like(like_pattern(f))
                for f in features
            ]
            conditions.append(or_(*or_conditions))

        if marine_unit_id:
            conditions.append(
                t.c.MarineReportingUnit.like(like_pattern(marine_unit_id))
            )

        count, item = db.get_item_by_conditions_table(
            t, 'TargetCode', *conditions, page=page
        )

        self.blacklist = BLACKLIST
        return count, item

    @db.use_db_session('2024')
    def get_extra_data(self):
        if not self.item:
            return []

        res = []

        # Marine Reporting Unit(s)
        mrus = _split(getattr(self.item, 'MarineReportingUnit', ''))
        if mrus:
            res.append(
                ('', {
                    '': [{'Marine Unit(s)': x} for x in mrus]
                })
            )

        # GES Component(s)
        ges_comps = _split(getattr(self.item, 'GEScomponent', ''))
        if ges_comps:
            res.append(
                ('', {
                    '': [{'GES Component': x} for x in ges_comps]
                })
            )

        # Feature(s)
        feats = _split(getattr(self.item, 'Feature', ''))
        if feats:
            res.append(
                ('', {
                    '': [{'Feature(s)': x} for x in feats]
                })
            )

        # Target Purpose(s)
        purposes = _split(getattr(self.item, 'TargetPurpose', ''))
        if purposes:
            res.append(
                ('', {
                    '': [{'Target Purpose': x} for x in purposes]
                })
            )

        # Related Measure(s)
        measures = _split(getattr(self.item, 'RelatedMeasures', ''))
        if measures:
            res.append(
                ('', {
                    '': [{'Measure': x} for x in measures]
                })
            )

        # Progress Assessment (from child table)
        country_code = self.item.CountryCode
        target_code = self.item.TargetCode

        pa = sql2024.t_ART10_Targets_ProgressAssessment

        sess = db.session()
        try:
            q = sess.query(pa).filter(
                pa.c.CountryCode == country_code,
                pa.c.TargetCode == target_code,
            ).order_by(pa.c.Parameter)

            progress_rows = q.all()
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            progress_rows = []

        if progress_rows:
            excluded = (
                'SnapshotId', 'Comment', 'ReportingDate',
                'CountryCode', 'TargetCode',
            )
            progress_dicts = db_objects_to_dict(progress_rows, excluded)
            progress_grouped = group_data(
                progress_dicts, 'Parameter', remove_pivot=False
            )

            res.append(
                ('Progress assessment', progress_grouped, 'Parameter')
            )

        return res

    @db.use_db_session('2024')
    def download_results(self):
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])
        marine_unit_id = data.get('marine_unit_id')

        t = sql2024.t_ART10_Targets_Target

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            or_conditions = [
                t.c.GEScomponent.like(like_pattern(gc))
                for gc in ges_components
            ]
            conditions.append(or_(*or_conditions))

        if features:
            or_conditions = [
                t.c.Feature.like(like_pattern(f))
                for f in features
            ]
            conditions.append(or_(*or_conditions))

        if marine_unit_id:
            conditions.append(
                t.c.MarineReportingUnit.like(like_pattern(marine_unit_id))
            )

        sess = db.session()
        columns = [
            c for c in t.c
            if c.name not in self.excluded_columns
        ]

        try:
            q = sess.query(*columns).filter(*conditions).order_by(
                t.c.CountryCode,
                t.c.TargetCode,
            )

            target_rows = q.all()
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return []

        # Also fetch progress assessment rows
        target_codes = [
            (row.CountryCode, row.TargetCode) for row in target_rows
        ]

        pa = sql2024.t_ART10_Targets_ProgressAssessment
        pa_columns = [
            c for c in pa.c
            if c.name not in self.excluded_columns
        ]

        progress_rows = []
        if target_codes:
            try:
                or_conditions = [
                    (pa.c.CountryCode == cc) & (pa.c.TargetCode == tc)
                    for cc, tc in target_codes
                ]
                q = sess.query(*pa_columns).filter(
                    or_(*or_conditions)
                ).order_by(
                    pa.c.CountryCode,
                    pa.c.TargetCode,
                    pa.c.Parameter,
                )
                progress_rows = q.all()
            except Exception:
                sess.rollback()
                logger.exception("MSFD database is timed out")

        xlsdata = [
            ('ART10_Targets_Target', target_rows),
        ]

        if progress_rows:
            xlsdata.append(
                ('ART10_Targets_ProgressAssessment', progress_rows),
            )

        return xlsdata


class A2024Art10MarineUnit(MarineUnitIDSelectForm):
    mapper_class = sql2024.t_ART10_Targets_Target

    def get_subform(self):
        return A2024Art10Display(self, self.request)

    def default_marine_unit_id(self):
        return all_values_from_field(self,
                                     self.fields['marine_unit_id'])

    @db.use_db_session('2024')
    def get_available_marine_unit_ids(self):
        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])

        t = sql2024.t_ART10_Targets_Target

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            or_conditions = [
                t.c.GEScomponent.like(like_pattern(gc))
                for gc in ges_components
            ]
            conditions.append(or_(*or_conditions))

        if features:
            or_conditions = [
                t.c.Feature.like(like_pattern(f))
                for f in features
            ]
            conditions.append(or_(*or_conditions))

        sess = db.session()
        try:
            q = sess.query(t.c.MarineReportingUnit).filter(
                *conditions
            ).distinct()
            all_mrus = set()

            for row in q:
                if row[0]:
                    for mru in row[0].split(';'):
                        mru = mru.strip()
                        if mru:
                            all_mrus.add(mru)
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return 0, []

        sorted_mrus = sorted(all_mrus)

        return len(sorted_mrus), sorted_mrus


class A2024Art10Features(EmbeddedForm):
    fields = Fields(interfaces.IFeatures2024A10)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art10MarineUnit(self, self.request)


class A2024Art10GesComponents(EmbeddedForm):
    fields = Fields(interfaces.IGESComponents2024A10)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art10Features(self, self.request)


# @register_form_art10
class A2024Article10(EmbeddedForm):
    record_title = 'Article 10 (Targets and associated indicators)'
    title = '2024 reporting exercise'
    session_name = '2024'
    permission = 'zope2.View'
    mapper_class = sql2024.t_ART10_Targets_Target

    fields = Fields(interfaces.ICountryCode2024A10)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art10GesComponents(self, self.request)
