# pylint: skip-file
"""Article 19.3 "Datasets used" -- 2024 Article 8 & 10 information type.

Reads the ``data.Indicators_*`` base tables the legacy 2024 Article 19.3 form
uses (not a view):

* ``Indicators_IndicatorAssessment`` -- the indicator (the result grain: one
  row per reported indicator);
* ``Indicators_Datasets`` -- the datasets filed for the indicator (URL / MD
  URL);
* ``Indicators_Feature`` -- the GES components and features the indicator
  covers.

A row is keyed by ``(CountryCode, IndicatorCode)``. The assessment metadata
and the feature child table can hold several rows per indicator, and an
indicator can file several datasets, so all of these are packed into one
``';'``-joined cell per indicator and joined back (the raw
``MarineReportingUnit`` may itself be ``';'``-joined). The result is driven by
the **indicator assessment**, so an indicator with no dataset keeps a row with
empty dataset cells (the legacy form's main row was the assessment). The
Region/Subregion filter and cell are derived from the Article 4 MRU
publication.
"""
from __future__ import absolute_import

from sqlalchemy import and_, select

from wise.msfd import sql2024
from wise.msfd.explorer.providers.article19_base import (
    MULTI_SEPARATOR,
    Article19DatasetsProvider,
    packed_cell,
    single_value,
)
from wise.msfd.explorer.providers.base import (
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.providers.regions import MruRegionFacet
from wise.msfd.explorer.serializers import country_label

INFORMATION_TYPE = '2024 Article 8 & 10'


class Article19Cycle2024Provider(Article19DatasetsProvider):
    """Datasets reported under Article 19.3 for the 2024 Article 8 & 10."""

    cycle = '2024'
    cycle_label = INFORMATION_TYPE
    cycle_display = INFORMATION_TYPE
    session_name = '2024'

    # Injectable source tables: tests point them at an in-memory database.
    dataset = sql2024.t_Indicators_Datasets
    assessment = sql2024.t_Indicators_IndicatorAssessment
    feature = sql2024.t_Indicators_Feature

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql2024.t_MarineReportingUnit_Publication
    region_mru_id_column = 'MarineReportingUnitId'
    region_region_column = 'RegionSubRegion'
    region_mru_column = 'MarineReportingUnit'

    order_by = ('CountryCode', 'IndicatorCode', 'URL')

    def __init__(self, *args, **kwargs):
        keys = ['CountryCode', 'IndicatorCode']
        dataset = self.dataset
        assessment = self.assessment
        feature = self.feature

        #: One row per reported indicator: the assessment drives the result so
        #: an indicator with no dataset keeps a row (with empty dataset cells),
        #: matching the legacy form, whose main row was the assessment.
        assessment_keys = (
            select(assessment.c.CountryCode, assessment.c.IndicatorCode)
            .distinct()
            .subquery()
        )
        title = single_value(
            assessment, keys, 'IndicatorTitle', 'IndicatorTitle'
        )
        assessment_date = single_value(
            assessment, keys, 'ReportingDate', 'AssessmentReportingDate'
        )
        source_assessment = packed_cell(
            assessment, keys, 'SourceAssessmentIndicator',
            'SourceAssessmentIndicator'
        )
        reporting_method = packed_cell(
            assessment, keys, 'ReportingMethodIndicator',
            'ReportingMethodIndicator'
        )
        unique_reference = packed_cell(
            assessment, keys, 'UniqueReference', 'UniqueReference'
        )
        related_targets = packed_cell(
            assessment, keys, 'RelatedTargets', 'RelatedTargets'
        )
        void_reason = packed_cell(
            assessment, keys, 'DatasetVoidReason', 'DatasetVoidReason'
        )
        regional_area = packed_cell(
            assessment, keys, 'RegionalAssessmentArea',
            'RegionalAssessmentArea'
        )
        component = packed_cell(
            feature, keys, 'GEScomponent', 'GEScomponent'
        )
        feature_cell = packed_cell(feature, keys, 'Feature', 'Feature')
        marine_unit = packed_cell(
            assessment, keys, 'MarineReportingUnit', 'MarineReportingUnit'
        )
        #: Several datasets can be filed for one indicator; they are packed
        #: into one ``';'``-joined cell each so the result stays one row per
        #: indicator (the legacy form showed them as an extra-data list).
        dataset_url = packed_cell(dataset, keys, 'URL', 'URL')
        dataset_md_url = packed_cell(dataset, keys, 'MD_URL', 'MD_URL')

        def link(cell, table):
            return and_(
                table.c.CountryCode == cell.c.CountryCode,
                table.c.IndicatorCode == cell.c.IndicatorCode,
            )

        self.mapper = select(
            assessment_keys.c.CountryCode.label('CountryCode'),
            assessment_keys.c.IndicatorCode.label('IndicatorCode'),
            dataset_url.c.URL.label('URL'),
            dataset_md_url.c.MD_URL.label('MD_URL'),
            assessment_date.c.AssessmentReportingDate.label('ReportingDate'),
            title.c.IndicatorTitle.label('IndicatorTitle'),
            source_assessment.c.SourceAssessmentIndicator.label(
                'SourceAssessmentIndicator'
            ),
            reporting_method.c.ReportingMethodIndicator.label(
                'ReportingMethodIndicator'
            ),
            unique_reference.c.UniqueReference.label('UniqueReference'),
            related_targets.c.RelatedTargets.label('RelatedTargets'),
            void_reason.c.DatasetVoidReason.label('DatasetVoidReason'),
            regional_area.c.RegionalAssessmentArea.label(
                'RegionalAssessmentArea'
            ),
            component.c.GEScomponent.label('GEScomponent'),
            feature_cell.c.Feature.label('Feature'),
            marine_unit.c.MarineReportingUnit.label('MarineReportingUnit'),
        ).select_from(
            assessment_keys
            .outerjoin(title, link(title, assessment_keys))
            .outerjoin(assessment_date, link(assessment_date, assessment_keys))
            .outerjoin(dataset_url, link(dataset_url, assessment_keys))
            .outerjoin(dataset_md_url, link(dataset_md_url, assessment_keys))
            .outerjoin(source_assessment, link(source_assessment,
                                               assessment_keys))
            .outerjoin(reporting_method, link(reporting_method,
                                              assessment_keys))
            .outerjoin(unique_reference, link(unique_reference,
                                              assessment_keys))
            .outerjoin(related_targets, link(related_targets, assessment_keys))
            .outerjoin(void_reason, link(void_reason, assessment_keys))
            .outerjoin(regional_area, link(regional_area, assessment_keys))
            .outerjoin(component, link(component, assessment_keys))
            .outerjoin(feature_cell, link(feature_cell, assessment_keys))
            .outerjoin(marine_unit, link(marine_unit, assessment_keys))
        ).subquery()

        super(Article19Cycle2024Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column(
            'Region',
            'Region / Subregion',
            'Region',
            min_width=200,
            sortable=False,
        ),
        Column('IndicatorCode', 'Indicator code', 'IndicatorCode'),
        Column(
            'IndicatorTitle',
            'Indicator title',
            'IndicatorTitle',
            expandable=True,
            min_width=250,
        ),
        Column(
            'SourceAssessmentIndicator',
            'Source assessment indicator',
            'SourceAssessmentIndicator',
            # format='multi',
            # separator=MULTI_SEPARATOR,
            min_width=180,
        ),
        Column(
            'ReportingMethodIndicator',
            'Reporting method indicator',
            'ReportingMethodIndicator',
            # format='multi',
            # separator=MULTI_SEPARATOR,
            min_width=180,
        ),
        Column(
            'UniqueReference',
            'Unique reference',
            'UniqueReference',
            min_width=220,
        ),
        Column(
            'RelatedTargets',
            'Related targets',
            'RelatedTargets',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'DatasetVoidReason',
            'Dataset void reason',
            'DatasetVoidReason',
            min_width=170,
        ),
        Column(
            'MarineReportingUnit',
            'Marine reporting unit(s)',
            'MarineReportingUnit',
            format='mru_multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'RegionalAssessmentArea',
            'Regional assessment area',
            'RegionalAssessmentArea',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'GEScomponent',
            'GES Component / Criteria',
            'GEScomponent',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'Feature',
            'Feature(s)',
            'Feature',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'URL',
            'Dataset URL',
            'URL',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=220,
        ),
        Column(
            'MD_URL',
            'Metadata URL',
            'MD_URL',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=220,
        ),
        Column(
            'ReportingDate', 'Reported date', 'ReportingDate', format='date'
        ),
        Column(
            'InformationType',
            'Information type',
            static=INFORMATION_TYPE,
            min_width=170,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'CountryCode',
            labeler=country_label,
        ),
        MruRegionFacet(
            'region_subregions',
            'Region and Subregion',
            mru_column='MarineReportingUnit',
            packed=True,
            separator=MULTI_SEPARATOR,
        ),
        MultiValueFacet(
            'ges_component',
            'GES Component / Criteria',
            'GEScomponent',
            separator=MULTI_SEPARATOR,
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Feature',
            separator=MULTI_SEPARATOR,
        ),
    )
