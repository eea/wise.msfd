# pylint: skip-file
"""Article 19.3 "Datasets used" -- 2018 Article 8 & 10 information type.

Reads the base tables the legacy 2018 Article 19.3 form uses:

* ``Indicators_IndicatorAssessment`` -- the indicator assessment (the result
  grain: one row per reported indicator, matching the legacy form's main row);
* ``Indicators_Dataset`` -- the datasets filed for the assessment (URL / MD
  URL), packed into one ``';'``-joined cell each;
* ``Indicators_Feature_GESComponent`` / ``Indicators_Feature_Feature`` -- the
  GES components and their features (a two-hop child table), packed per
  assessment;
* ``Indicators_MarineUnit`` -- the marine reporting units the assessment
  covers, packed per assessment;
* ``ReportedInformation`` -- the reported file (country, reported date).

The child tables are packed to one cell per assessment and joined to the
assessment row, so an indicator with several datasets or marine units stays a
single row. Only the latest reported file per ``(country, schema)`` is shown,
mirroring ``db.latest_import_ids_2018()``, which the legacy form applied. The
Region/Subregion filter and cell are derived from the Article 4 MRU
publication.
"""
from __future__ import absolute_import

from sqlalchemy import func, select

from wise.msfd import sql2018
from wise.msfd.explorer.providers.article19_base import (
    MULTI_SEPARATOR,
    Article19DatasetsProvider,
    packed_cell,
)
from wise.msfd.explorer.providers.base import (
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.providers.regions import MruRegionFacet
from wise.msfd.explorer.serializers import country_label

INFORMATION_TYPE = '2018 Article 8 & 10'


class Article19Cycle2018Provider(Article19DatasetsProvider):
    """Datasets reported under Article 19.3 for the 2018 Article 8 & 10."""

    cycle = '2018'
    cycle_label = INFORMATION_TYPE
    cycle_display = INFORMATION_TYPE
    session_name = '2018'

    # Injectable source tables: tests point them at an in-memory database.
    dataset = sql2018.IndicatorsDataset.__table__
    assessment = sql2018.IndicatorsIndicatorAssessment.__table__
    ges_component = sql2018.IndicatorsFeatureGESComponent.__table__
    feature = sql2018.IndicatorsFeatureFeature.__table__
    marine_unit = sql2018.IndicatorsMarineUnit.__table__
    reported = sql2018.ReportedInformation.__table__

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql2018.MRUsPublication.__table__
    region_mru_id_column = 'thematicId'
    region_region_column = 'rZoneId'
    region_mru_column = 'MarineReportingUnit'

    order_by = ('CountryCode', 'IndicatorCode')

    def __init__(self, *args, **kwargs):
        assessment = self.assessment
        reported = self.reported
        dataset = self.dataset

        #: The assessment is the result grain (as in the legacy form). Its
        #: country and reported date live on the reported file.
        assessments = (
            select(
                assessment.c.Id.label('IdIndicatorAssessment'),
                assessment.c.IndicatorCode.label('IndicatorCode'),
                assessment.c.IndicatorTitle.label('IndicatorTitle'),
                assessment.c.IdReportedInformation.label('ImportId'),
                reported.c.CountryCode.label('CountryCode'),
                reported.c.ReportingDate.label('ReportingDate'),
            )
            .select_from(
                assessment.join(
                    reported,
                    assessment.c.IdReportedInformation == reported.c.Id,
                )
            )
            .distinct()
            .subquery()
        )

        key = ['IdIndicatorAssessment']

        # Features are two hops away from the assessment: the GES component
        # links the assessment to its features. Pack both per assessment.
        pairs = select(
            self.ges_component.c.IdIndicatorAssessment.label(
                'IdIndicatorAssessment'
            ),
            self.ges_component.c.GESComponent.label('GESComponent'),
            self.feature.c.Feature.label('Feature'),
        ).select_from(
            self.ges_component.join(
                self.feature,
                self.feature.c.IdGESComponent == self.ges_component.c.Id,
            )
        ).distinct().subquery()

        component = packed_cell(pairs, key, 'GESComponent', 'GESComponent')
        feature_cell = packed_cell(pairs, key, 'Feature', 'Feature')
        marine_unit = packed_cell(
            self.marine_unit, key, 'MarineReportingUnit', 'MarineReportingUnit'
        )
        #: An assessment can file several datasets; pack them into one
        #: ``';'``-joined cell each so the result stays one row per indicator
        #: (the legacy form showed them as an extra-data list).
        dataset_url = packed_cell(dataset, key, 'URL', 'URL')
        dataset_md_url = packed_cell(dataset, key, 'MD_URL', 'MD_URL')

        def link(cell):
            return (
                cell.c.IdIndicatorAssessment
                == assessments.c.IdIndicatorAssessment
            )

        self.mapper = select(
            assessments.c.IdIndicatorAssessment.label('AssessmentId'),
            assessments.c.CountryCode.label('CountryCode'),
            assessments.c.ImportId.label('ImportId'),
            assessments.c.IndicatorCode.label('IndicatorCode'),
            assessments.c.IndicatorTitle.label('IndicatorTitle'),
            assessments.c.ReportingDate.label('ReportingDate'),
            dataset_url.c.URL.label('URL'),
            dataset_md_url.c.MD_URL.label('MD_URL'),
            component.c.GESComponent.label('GESComponent'),
            feature_cell.c.Feature.label('Feature'),
            marine_unit.c.MarineReportingUnit.label('MarineReportingUnit'),
        ).select_from(
            assessments
            .outerjoin(dataset_url, link(dataset_url))
            .outerjoin(dataset_md_url, link(dataset_md_url))
            .outerjoin(component, link(component))
            .outerjoin(feature_cell, link(feature_cell))
            .outerjoin(marine_unit, link(marine_unit))
        ).subquery()

        super(Article19Cycle2018Provider, self).__init__(*args, **kwargs)

    def base_conditions(self):
        """Keep only the latest reported file of each ``(country, schema)``.

        Mirrors ``db.latest_import_ids_2018()``, which the legacy form applied.
        """
        inner = self.reported.alias('ri_latest')
        latest = (
            select(func.max(inner.c.Id))
            .group_by(inner.c.CountryCode, inner.c.Schema)
        )

        return [self.mapper.c['ImportId'].in_(latest)]

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
            'MarineReportingUnit',
            'Marine reporting unit(s)',
            'MarineReportingUnit',
            format='mru_multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'GESComponent',
            'GES Component / Criteria',
            'GESComponent',
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
            'GESComponent',
            separator=MULTI_SEPARATOR,
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Feature',
            separator=MULTI_SEPARATOR,
        ),
    )
