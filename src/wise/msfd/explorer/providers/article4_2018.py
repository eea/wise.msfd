# pylint: skip-file
"""Provider for Article 4, 2018-2024 reporting cycle.

The 2018 data source is the ``MRUs_Publication`` table. It predates the
``MarineReportingUnit_Publication`` table used for 2024-2030 and names some
fields differently, but carries the same information the redesigned explorer
exposes: the MRU identifier (``thematicId``), its name (``nameTxtInt``), the
region/subregion (``rZoneId``), the size in km\u00b2 (``Area``),
the legislation short name (``legisSName``) and the name in the national
language (``nameText``).

Note: the ``MRUsPublication`` model declares a ``Region`` column that does not
exist in the database. Only the columns referenced below are ever selected, so
the stale mapping is harmless as long as it is not touched.
"""
from __future__ import absolute_import

from wise.msfd import sql2018
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


class Article4Cycle2018Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2018-2024."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2018'
    cycle_label = '2018-2024 reporting cycle'
    cycle_display = '2018 - 2024'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2018'

    # ``MRUsPublication`` is a mapped class, the explorer expects a Table.
    mapper = sql2018.MRUsPublication.__table__
    order_by = ('Country', 'thematicId')

    # Fields whose reported value is shown as-is rather than run through the
    # glossary label lookup.
    blacklist_labels = ('thematicId', 'legisSName', 'nameTxtInt', 'nameText')

    columns = (
        Column(
            'thematicId',
            'Marine Reporting Unit ID',
            'thematicId',
        ),
        Column(
            'nameTxtInt',
            'Marine Reporting Unit Name',
            'nameTxtInt',
        ),
        Column('rZoneId', 'Region / Subregion', 'rZoneId'),
        Column(
            'Area',
            u'Area (km\u00b2)',
            'Area',
            align='right',
            format='area',
        ),
        Column('legisSName', 'Legislation', 'legisSName'),
        Column(
            'ReportingCycle',
            'Reporting cycle',
            static='2018 - 2024',
        ),
        Column('nameText', 'National name', 'nameText'),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'Country',
            labeler=country_label,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            'rZoneId',
            labeler=glossary_label,
        ),
        RangeFacet(
            'area',
            u'Area (km\u00b2)',
            'Area',
            unit=u'km\u00b2',
        ),
        TextFacet(
            'mru_id',
            'MRU identifier (ID)',
            'thematicId',
            placeholder='Search by MRU identifier...',
        ),
        TextFacet(
            'mru_name',
            'MRU name',
            'nameTxtInt',
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

        The 2018 columns mirror the 2024 ones (area, region), so the panel
        shares that cycle's cards and charts, and adds three breakdowns the
        legacy cycle only exposes here: the management ``Type``, the reported
        legislation and the country distribution. All aggregates honour the
        current facet selection but are independent of paging and sorting.
        """
        conditions = self.data_conditions()
        region = self.mapper.c['rZoneId']
        size = self.mapper.c['Area']

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

        type_points = label_points(
            group_counts(session, self.mapper, conditions,
                         self.mapper.c['Type']),
            to_text,
        )

        legislation_points = label_points(
            group_counts(session, self.mapper, conditions,
                         self.mapper.c['legisSName']),
            to_text,
        )

        country_points = label_points(
            group_counts(session, self.mapper, conditions,
                         self.mapper.c['Country']),
            country_label,
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
                # bar_chart(
                #     'type_distribution',
                #     'Marine Reporting Units by management type',
                #     type_points,
                #     orientation='h',
                #     x_label='Number of MRUs',
                #     y_label='',
                #     hint='Number of Marine Reporting Units reported for each '
                #          'management type.',
                # ),
                # bar_chart(
                #     'legislation_distribution',
                #     'Marine Reporting Units by legislation',
                #     legislation_points,
                #     orientation='h',
                #     x_label='Number of MRUs',
                #     y_label='',
                #     hint='Number of Marine Reporting Units designated under '
                #          'each piece of legislation.',
                # ),
                # bar_chart(
                #     'country_distribution',
                #     'Marine Reporting Units by country',
                #     country_points,
                #     orientation='h',
                #     x_label='Number of MRUs',
                #     y_label='',
                #     hint='Number of Marine Reporting Units reported by each '
                #          'country.',
                # ),
            ],
        }
