# pylint: skip-file
""" Forms and views for Article 19.3 - 2024 reporting year (Indicators)

    Tables used:
    - t_Indicators_IndicatorAssessment (main)
    - t_Indicators_Datasets (extra data)
    - t_Indicators_Feature (extra data / filtering)
"""
from __future__ import absolute_import
import logging
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from sqlalchemy import or_
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd.search import interfaces
from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.search.base import ItemDisplayForm
from wise.msfd.search.utils import register_form_art19
from wise.msfd.utils import db_objects_to_dict, like_pattern

logger = logging.getLogger('wise.msfd')


class A2024IndicatorsDisplay(ItemDisplayForm):
    title = "Indicator Display Form"
    session_name = '2024'

    mapper_class = sql2024.t_Indicators_IndicatorAssessment
    order_field = 'IndicatorCode'
    css_class = "left-side-form"
    extra_data_template = ViewPageTemplateFile('../pt/extra-data-pivot.pt')

    blacklist = (
        'SnapshotId', 'ReportingDate', 'Comment',
    )
    blacklist_labels = (
        'IndicatorCode',
    )

    # Fields whose values are semicolon-delimited and should be
    # displayed as a bullet list
    _semicolon_fields = {
        'GEScomponent', 'Feature', 'SourceAssessmentIndicator',
        'RelatedTargets', 'MarineReportingUnit',
    }

    def print_value(self, value, field_name=None):
        # Fields with semicolon-delimited values get split into a list.
        # Single values (no semicolon) fall through to parent, so that
        # existing TRANSFORMS (e.g. label lookups for GEScomponent,
        # Feature) still apply.
        if field_name in self._semicolon_fields and value and ';' in value:
            # Normalize separator variants: '; ' -> ';'
            items = [x.strip() for x in
                     value.replace('; ', ';').split(';') if x.strip()]

            if items:
                return u'<ul><li>' + u'</li><li>'.join(items) + \
                    u'</li></ul>'

        return super(A2024IndicatorsDisplay, self).print_value(
            value, field_name)

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

        t = sql2024.t_Indicators_IndicatorAssessment
        t_feat = sql2024.t_Indicators_Feature

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        # If GES component or feature filters are set, find matching
        # IndicatorCodes from the Feature table.
        # Use LIKE patterns because GEScomponent / Feature columns may
        # contain semicolon-delimited values.
        if ges_components or features:
            feat_conditions = []

            if countries:
                feat_conditions.append(
                    t_feat.c.CountryCode.in_(countries))

            if ges_components:
                feat_conditions.append(
                    or_(*[t_feat.c.GEScomponent.like(like_pattern(gc))
                           for gc in ges_components]))

            if features:
                feat_conditions.append(
                    or_(*[t_feat.c.Feature.like(like_pattern(f))
                           for f in features]))

            count, feat_rows = db.get_all_records(
                t_feat,
                *feat_conditions
            )
            indicator_codes = list(set([
                x.IndicatorCode for x in feat_rows
            ]))

            if indicator_codes:
                conditions.append(
                    t.c.IndicatorCode.in_(indicator_codes))
            else:
                return [0, None]

        count, item = db.get_item_by_conditions_table(
            t, 'IndicatorCode', *conditions, page=page
        )

        return count, item

    @db.use_db_session('2024')
    def get_extra_data(self):
        if not self.item:
            return {}

        country_code = self.item.CountryCode
        indicator_code = self.item.IndicatorCode

        res = []

        # Get related features (GES components & features)
        t_feat = sql2024.t_Indicators_Feature
        count, features = db.get_all_records(
            t_feat,
            t_feat.c.CountryCode == country_code,
            t_feat.c.IndicatorCode == indicator_code,
        )
        features = db_objects_to_dict(
            features,
            ('SnapshotId', 'ReportingDate', 'Comment',
             'CountryCode', 'IndicatorCode')
        )

        if features:
            res.append(
                ('Indicators feature', {'': features})
            )

        # Get related datasets (URLs)
        t_ds = sql2024.t_Indicators_Datasets
        count, datasets = db.get_all_records(
            t_ds,
            t_ds.c.CountryCode == country_code,
            t_ds.c.IndicatorCode == indicator_code,
        )
        datasets = db_objects_to_dict(
            datasets,
            ('SnapshotId', 'ReportingDate', 'Comment',
             'CountryCode', 'IndicatorCode')
        )

        if datasets:
            res.append(
                ('Indicators dataset', {'': datasets})
            )

        return res

    @db.use_db_session('2024')
    def download_results(self):
        t = self.mapper_class
        t_feat = sql2024.t_Indicators_Feature
        t_ds = sql2024.t_Indicators_Datasets

        data = self.get_flattened_data(self)

        countries = data.get('member_states', [])
        ges_components = data.get('ges_component', [])
        features = data.get('feature', [])

        conditions = []

        if countries:
            conditions.append(t.c.CountryCode.in_(countries))

        if ges_components or features:
            feat_conditions = []

            if countries:
                feat_conditions.append(
                    t_feat.c.CountryCode.in_(countries))

            if ges_components:
                feat_conditions.append(
                    or_(*[t_feat.c.GEScomponent.like(like_pattern(gc))
                           for gc in ges_components]))

            if features:
                feat_conditions.append(
                    or_(*[t_feat.c.Feature.like(like_pattern(f))
                           for f in features]))

            count, feat_rows = db.get_all_records(
                t_feat,
                *feat_conditions,
                raw=True
            )
            codes = list(set([x.IndicatorCode for x in feat_rows]))

            if codes:
                conditions.append(t.c.IndicatorCode.in_(codes))

        count, indicator_data = db.get_all_records(
            t,
            *conditions,
            raw=True
        )
        count, dataset_data = db.get_all_records(
            t_ds,
            raw=True
        )
        count, feature_data = db.get_all_records(
            t_feat,
            raw=True
        )

        xlsdata = [
            ('IndicatorsIndicatorAssessment', indicator_data),
            ('IndicatorsDataset', dataset_data),
            ('IndicatorsFeature', feature_data),
        ]

        return xlsdata


@register_form_art19
class A2024ArticleIndicators(EmbeddedForm):
    """ Article 19.3 indicators for 2024 reporting year.
    """
    record_title = 'Indicators (Article 8 & 10)'
    title = '2024 Article 8 & 10'
    session_name = '2024'

    mapper_class = sql2024.t_Indicators_IndicatorAssessment

    fields = Fields(interfaces.ICountryCode2024A19Ind)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024IndicatorsGesComponent(self, self.request)


class A2024IndicatorsGesComponent(EmbeddedForm):
    fields = Fields(interfaces.IGESComponent2024A19Ind)
    fields['ges_component'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024IndicatorsFeature(self, self.request)


class A2024IndicatorsFeature(EmbeddedForm):
    fields = Fields(interfaces.IFeature2024A19Ind)
    fields['feature'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A2024IndicatorsDisplay(self, self.request)
