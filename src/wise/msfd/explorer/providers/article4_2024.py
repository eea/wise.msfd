# pylint: skip-file
"""Provider for Article 4, 2024-2030 reporting cycle.

The 2024 data source is the ``spatial.MarineReportingUnit_Publication`` table:
unlike the legacy ``ART4_GEO_GeographicalBoundaries`` table it also carries the
MRU size (``sizeValue`` in ``sizeUom``) and the legislation short name
(``legisSName``), which the redesigned explorer exposes as filters and columns.
"""
from __future__ import absolute_import

from wise.msfd import sql2024
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    RangeFacet,
    TextFacet,
    TogglesFacet,
)
from wise.msfd.explorer.providers.summary import (
    AREA_UNIT,
    area_stats,
    bar_chart,
    card,
    distinct_count,
    group_counts,
    label_points,
    size_distribution_points,
    total_rows,
)
from wise.msfd.explorer.serializers import (country_label, glossary_label,
                                            to_text)


class Article4Cycle2024Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2024-2030."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2024'
    cycle_label = '2024-2030 reporting cycle'
    cycle_display = '2024 - 2030'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2024'

    mapper = sql2024.t_MarineReportingUnit_Publication
    order_by = ('countryCode', 'MarineReportingUnitId')

    # The legacy table's metadata columns are not displayed, but the explicit
    # ``columns`` below is what actually drives the query and the table.
    excluded_columns = ()

    blacklist_labels = (
        'thematicId', 'legisSName', 'nameText', 'nameTxtInt',
        'MarineReportingUnitId', 'MarineReportingUnitIdOld',
        'MarineReportingUnitName', 'legisName', 'legisLink',
    )

    columns = (
        Column(
            'MarineReportingUnitId',
            'Marine Reporting Unit ID',
            'MarineReportingUnitId',
        ),
        Column(
            'MarineReportingUnitName',
            'Marine Reporting Unit Name',
            'MarineReportingUnitName',
        ),
        Column('RegionSubRegion', 'Region / Subregion', 'RegionSubRegion'),
        Column(
            'Area',
            u'Area (km\u00b2)',
            'sizeValue',
            align='right',
            format='area',
        ),
        Column('legisSName', 'Legislation', 'legisSName'),
        Column(
            'ReportingCycle',
            'Reporting cycle',
            static='2024 - 2030',
        ),
        Column('nameText', 'National name', 'nameText'),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'countryCode',
            labeler=country_label,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            'RegionSubRegion',
            labeler=glossary_label,
        ),
        RangeFacet(
            'area',
            u'Area (km\u00b2)',
            'sizeValue',
            unit=u'km\u00b2',
        ),
        TextFacet(
            'mru_id',
            'MRU identifier (ID)',
            'MarineReportingUnitId',
            placeholder='Search by MRU identifier...',
        ),
        TextFacet(
            'mru_name',
            'MRU name',
            'MarineReportingUnitName',
            placeholder='Search by MRU name...',
        ),
        TogglesFacet(
            'legislation',
            'Legislation short name',
            'legisSName',
            # show the reported value as-is rather than a glossary label
            labeler=to_text,
        ),
    )

    # -- summary ---------------------------------------------------------
    def _build_summary(self, session):
        """KPIs and charts for the Summary & insights panel.

        All aggregates honour the current facet selection (including the area
        range), but are independent of paging and sorting. The shared helpers
        in :mod:`~wise.msfd.explorer.providers.summary` build the payload.
        """
        conditions = self.data_conditions()
        region = self.mapper.c['RegionSubRegion']
        size = self.mapper.c['sizeValue']

        total = total_rows(session, self.mapper, conditions)
        stats = area_stats(session, self.mapper, conditions, size)

        region_points = label_points(
            group_counts(session, self.mapper, conditions, region),
            glossary_label,
        )

        # Denominator of the Regions KPI: every region the cycle reports,
        # regardless of the current selection.
        region_total = distinct_count(session, self.mapper, region)

        size_points = size_distribution_points(
            session, self.mapper, conditions, size,
        )

        return {
            'cards': [
                card(
                    'mru_count',
                    'Marine Reporting Units',
                    int(total),
                    None,
                    'MRUs match your selection',
                    [],
                    None,
                    'tint',
                ),
                card(
                    'total_area',
                    'Total Area Covered',
                    stats['total'],
                    AREA_UNIT,
                    'Sum of MRU areas',
                    [],
                    None,
                    'chart area',
                ),
                card(
                    'average_area',
                    'Average MRU Size',
                    stats['avg'],
                    AREA_UNIT,
                    None,
                    [
                        {'label': 'Min', 'value': stats['min'],
                         'unit': AREA_UNIT},
                        {'label': 'Max', 'value': stats['max'],
                         'unit': AREA_UNIT},
                    ],
                    None,
                    'map marker',
                ),
                card(
                    'regions',
                    'Regions / Subregions',
                    len(region_points),
                    None,
                    'Marine regions / subregions',
                    [],
                    int(region_total),
                    'boxes',
                ),
            ],
            'charts': [
                bar_chart(
                    'size_distribution',
                    'Distribution of MRU size',
                    size_points,
                    orientation='v',
                    x_label=u'MRU area (km\u00b2)',
                    y_label='Number of MRUs',
                    hint='Number of Marine Reporting Units in each size range.',
                ),
                bar_chart(
                    'region_distribution',
                    'Marine Reporting Units by Region / Subregion',
                    region_points,
                    orientation='h',
                    x_label='Number of MRUs',
                    y_label='',
                    hint='Number of Marine Reporting Units per region or '
                         'subregion.',
                ),
            ],
        }
