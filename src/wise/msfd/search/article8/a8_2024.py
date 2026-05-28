# pylint: skip-file
from __future__ import absolute_import
import logging
from collections import OrderedDict
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from sqlalchemy import or_
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.utils import db_objects_to_dict, ItemLabel, ItemList
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_a8_2024

logger = logging.getLogger('wise.msfd')

OVERALL_STATUS_BLACKLIST = (
    'CountryCode', 'ReportingDate',
    'SnapshotId', 'Comment',
)

ELEMENT_STATUS_DISPLAY_FIELDS = (
    'Element', 'Element2', 'SourceElementList', 'ElementExtent',
    'TrendElement', 'DescriptionElement', 'ElementStatus',
)

CRITERIA_STATUS_DISPLAY_FIELDS = (
    'Criteria', 'CriteriaStatus', 'DescriptionCriteria',
)

CRITERIA_VALUES_DISPLAY_FIELDS = (
    'Parameter', 'ThresholdValueUpper', 'ThresholdValueLower',
    'ThresholdValueOperator', 'ThresholdQualitative',
    'ThresholdValueSource', 'ValueAchievedUpper', 'ValueAchievedLower',
    'ValueUnit', 'ProportionThresholdValue',
    'ProportionValueAchieved', 'ProportionThresholdValueUnit',
    'TrendParameter', 'ParameterAchieved',
    'DescriptionParameter', 'Related Indicator(s)',
)

TREEVIEW_BLACKLIST = (
    'CountryCode', 'MarineReportingUnit', 'GEScomponent', 'Feature',
    'ReportingDate', 'SnapshotId', 'Comment',
    '_criteria_statuses', '_criteria_values',
)


class A2024Art8GesDisplay(ItemDisplayForm):
    record_title = title = 'Article 8.1ab (GES assessments)'
    session_name = '2024'
    css_class = "left-side-form"

    mapper_class = sql2024.t_ART8_GES_OverallStatus
    order_field = 'MarineReportingUnit'

    data_template = ViewPageTemplateFile('../pt/item-display.pt')
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')
    secondary_extra_template_v2 = ViewPageTemplateFile(
        '../pt/extra-data-pivot-8ab-v2.pt'
    )
    direct_criteria_template = ViewPageTemplateFile(
        '../pt/extra-data-pivot-8ab-direct.pt'
    )

    blacklist = OVERALL_STATUS_BLACKLIST
    blacklist_labels = (
        'CountryCode',
    )
    excluded_columns = (
        'SnapshotId', 'Comment',
    )

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

        t = sql2024.t_ART8_GES_OverallStatus

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

        self.blacklist = OVERALL_STATUS_BLACKLIST

        return count, item

    def _filter_dict(self, d, fields):
        filtered = OrderedDict()
        for k in fields:
            if k in d:
                filtered[k] = d[k]
        return filtered

    def _build_element_statuses(self, country_code, mru, ges_component,
                                feature):
        t_elem = sql2024.t_ART8_GES_ElementStatus
        t_crit = sql2024.t_ART8_GES_ElementStatus_CriteriaStatus
        t_val = sql2024.t_ART8_GES_ElementStatus_CriteriaStatus_CriteriaValues

        sess = db.session()

        conditions_elem = [
            t_elem.c.CountryCode == country_code,
            t_elem.c.MarineReportingUnit == mru,
            t_elem.c.GEScomponent == ges_component,
            t_elem.c.Feature == feature,
        ]

        try:
            element_rows = sess.query(t_elem).filter(*conditions_elem) \
                .order_by(t_elem.c.Element).all()
            element_dicts = db_objects_to_dict(
                element_rows,
                excluded_columns=('SnapshotId', 'Comment', 'ReportingDate')
            )

            final_rows = []

            for elem in element_dicts:
                elem_status = self._filter_dict(
                    elem, ELEMENT_STATUS_DISPLAY_FIELDS)
                elem_status['_criteria_statuses'] = []

                elem_element = elem.get('Element', '') or ''
                elem_element2 = elem.get('Element2', '') or ''

                crit_conditions = [
                    t_crit.c.CountryCode == country_code,
                    t_crit.c.MarineReportingUnit == mru,
                    t_crit.c.GEScomponent == ges_component,
                    t_crit.c.Feature == feature,
                    t_crit.c.Element == elem_element,
                ]
                if elem_element2:
                    crit_conditions.append(
                        t_crit.c.Element2 == elem_element2
                    )
                else:
                    crit_conditions.append(
                        or_(t_crit.c.Element2 == '', t_crit.c.Element2.is_(None))
                    )

                crit_rows = sess.query(t_crit).filter(*crit_conditions) \
                    .order_by(t_crit.c.Criteria).all()
                crit_dicts = db_objects_to_dict(
                    crit_rows,
                    excluded_columns=('SnapshotId', 'Comment', 'ReportingDate')
                )

                for crit in crit_dicts:
                    crit_status = self._filter_dict(
                        crit, CRITERIA_STATUS_DISPLAY_FIELDS
                    )
                    crit_status['_criteria_values'] = []

                    crit_criteria = crit.get('Criteria', '') or ''

                    val_conditions = [
                        t_val.c.CountryCode == country_code,
                        t_val.c.MarineReportingUnit == mru,
                        t_val.c.GEScomponent == ges_component,
                        t_val.c.Feature == feature,
                        t_val.c.Element == elem_element,
                        t_val.c.Criteria == crit_criteria,
                    ]
                    if elem_element2:
                        val_conditions.append(
                            t_val.c.Element2 == elem_element2
                        )
                    else:
                        val_conditions.append(
                            or_(t_val.c.Element2 == '',
                                t_val.c.Element2.is_(None))
                        )

                    val_rows = sess.query(t_val).filter(*val_conditions) \
                        .order_by(t_val.c.Parameter).all()
                    val_dicts = db_objects_to_dict(
                        val_rows,
                        excluded_columns=(
                            'SnapshotId', 'Comment', 'ReportingDate',
                        )
                    )

                    for val in val_dicts:
                        cv = self._filter_dict(
                            val, CRITERIA_VALUES_DISPLAY_FIELDS
                        )

                        indicator_str = val.get('RelatedIndicator', '') or ''
                        if indicator_str:
                            indicators = [
                                x.strip()
                                for x in indicator_str.split(';')
                                if x.strip()
                            ]
                            values = [
                                ItemLabel(v, self.print_value(v))
                                for v in indicators
                            ]
                            cv['Related Indicator(s)'] = ItemList(values)
                        else:
                            cv['Related Indicator(s)'] = ''

                        crit_status['_criteria_values'].append(cv)

                    elem_status['_criteria_statuses'].append(crit_status)

                final_rows.append(elem_status)
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return []

        return sorted(final_rows, key=lambda d: d.get('Element', '') or '')

    def _build_direct_criteria(self, country_code, mru, ges_component,
                               feature):
        t_crit = sql2024.t_ART8_GES_Direct_CriteriaStatus
        t_val = sql2024.t_ART8_GES_Direct_CriteriaStatus_CriteriaValues

        sess = db.session()

        crit_conditions = [
            t_crit.c.CountryCode == country_code,
            t_crit.c.MarineReportingUnit == mru,
            t_crit.c.GEScomponent == ges_component,
            t_crit.c.Feature == feature,
        ]

        try:
            crit_rows = sess.query(t_crit).filter(*crit_conditions) \
                .order_by(t_crit.c.Criteria).all()
            crit_dicts = db_objects_to_dict(
                crit_rows,
                excluded_columns=('SnapshotId', 'Comment', 'ReportingDate')
            )

            final_rows = []

            for crit in crit_dicts:
                crit_status = self._filter_dict(
                    crit, CRITERIA_STATUS_DISPLAY_FIELDS
                )
                crit_status['_criteria_values'] = []

                crit_criteria = crit.get('Criteria', '') or ''

                val_conditions = [
                    t_val.c.CountryCode == country_code,
                    t_val.c.MarineReportingUnit == mru,
                    t_val.c.GEScomponent == ges_component,
                    t_val.c.Feature == feature,
                    t_val.c.Criteria == crit_criteria,
                ]

                val_rows = sess.query(t_val).filter(*val_conditions) \
                    .order_by(t_val.c.Parameter).all()
                val_dicts = db_objects_to_dict(
                    val_rows,
                    excluded_columns=('SnapshotId', 'Comment', 'ReportingDate')
                )

                for val in val_dicts:
                    cv = self._filter_dict(val, CRITERIA_VALUES_DISPLAY_FIELDS)

                    indicator_str = val.get('RelatedIndicator', '') or ''
                    if indicator_str:
                        indicators = [
                            x.strip()
                            for x in indicator_str.split(';')
                            if x.strip()
                        ]
                        values = [
                            ItemLabel(v, self.print_value(v))
                            for v in indicators
                        ]
                        cv['Related Indicator(s)'] = ItemList(values)
                    else:
                        cv['Related Indicator(s)'] = ''

                    crit_status['_criteria_values'].append(cv)

                final_rows.append(crit_status)
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return []

        return final_rows

    @db.use_db_session('2024')
    def get_extra_data(self):
        if not self.item:
            return []

        pressures_str = getattr(self.item, 'RelatedPressures', '') or ''
        targets_str = getattr(self.item, 'RelatedTargets', '') or ''

        pressure_codes = [
            x.strip() for x in pressures_str.split(';') if x.strip()
        ] if pressures_str else []
        target_codes = [
            x.strip() for x in targets_str.split(';') if x.strip()
        ] if targets_str else []

        res = []

        res.append(
            ('Related pressure(s)', {
                '': [{'PressureCode': x} for x in pressure_codes]
            })
        )

        res.append(
            ('Related target(s)', {
                '': [{'TargetCode': x} for x in target_codes]
            })
        )

        self.extra_data = res
        return res

    @db.use_db_session('2024')
    def get_extra_data_v2(self):
        if not self.item:
            return []

        country_code = self.item.CountryCode
        mru = self.item.MarineReportingUnit
        ges_component = self.item.GEScomponent
        feature = self.item.Feature

        self.blacklist = TREEVIEW_BLACKLIST

        element_rows = self._build_element_statuses(
            country_code, mru, ges_component, feature
        )

        direct_rows = self._build_direct_criteria(
            country_code, mru, ges_component, feature
        )

        return element_rows, direct_rows

    def extras(self):
        html = self.extra_data_template(extra_data=self.get_extra_data())

        extra_data_v2 = self.get_extra_data_v2()
        if not extra_data_v2:
            return html

        element_rows, direct_rows = extra_data_v2

        element_html = self.secondary_extra_template_v2(
            extra_data=element_rows
        )

        direct_html = ''
        if direct_rows:
            direct_html = self._render_direct_criteria(direct_rows)

        return html + element_html + direct_html

    def _render_direct_criteria(self, direct_rows):
        self.blacklist = TREEVIEW_BLACKLIST
        return self.direct_criteria_template(direct_data=direct_rows)

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

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])

        t = sql2024.t_ART8_GES_OverallStatus

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components:
            conditions.append(t.c.GEScomponent.in_(ges_components))

        if features:
            conditions.append(t.c.Feature.in_(features))

        sess = db.session()
        try:
            q = sess.query(t.c.MarineReportingUnit).filter(*conditions).distinct()
            res = [row[0] for row in q if row[0]]
        except Exception:
            sess.rollback()
            logger.exception("MSFD database is timed out")
            return 0, []

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
    mapper_class = sql2024.t_ART8_GES_OverallStatus

    fields = Fields(interfaces.ICountryCode2024A8)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024Art8GesComponents(self, self.request)
