# pylint: skip-file
"""Provider for Article 4, 2024-2030 reporting cycle.

The 2024 data source is the reporting table
``data.ART4_GEO_GeographicalBoundaries`` (the table Discodata publishes as
``MSFD2024_ART4_GEO_GeographicalBoundaries``), so the explorer shows exactly
the rows the public data set does. That table carries no MRU size, so it is
left-joined to ``spatial.MarineReportingUnit_Publication`` on the MRU id and
country to
read ``sizeValue`` for the Area column and the area-based Summary & insights.
MRUs without a publication entry keep their row, with an empty area.

A designation that ended before today is historical reporting and is hidden
(``desigEnd`` earlier than the current date); a designation without an end
date is ongoing and stays visible.
"""
from __future__ import absolute_import

from datetime import date

from sqlalchemy import and_, func, or_, select

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


def _legislation_name(column):
    """Trimmed legislation short name, with blank reports turned into NULL.

    Some MRUs report a bare space for their legislation, which would surface
    in the facet as a nameless option. Collapsing blank (and NULL) values to
    ``NULL`` lets the facet's normal "skip empty values" rule drop them,
    while grouping on the trimmed value keeps padded short names from
    splitting into separate options.
    """
    return func.nullif(func.trim(func.coalesce(column, u'')), u'')


class Article4Cycle2024Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2024-2030."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2024'
    cycle_label = '2024-2030 reporting cycle'
    cycle_display = '2024 - 2030'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2024'

    #: Injectable source tables: tests point them at an in-memory database.
    boundaries = sql2024.t_ART4_GEO_GeographicalBoundaries
    publication = sql2024.t_MarineReportingUnit_Publication

    order_by = ('countryCode', 'MarineReportingUnitId')

    def __init__(self, *args, **kwargs):
        boundaries = self.boundaries
        publication = self.publication

        # Join on the MRU id *and* the country so a shared id can never pick
        # up another country's size. The whole join is a sub-query so every
        # column keeps its plain name, which the column/facet lookups below
        # expect (a raw ``Join`` would key its columns by table name).
        self.mapper = select(
            boundaries.c.CountryCode.label('countryCode'),
            boundaries.c.MarineReportingUnitId.label('MarineReportingUnitId'),
            boundaries.c.MarineReportingUnitIdOld.label(
                'MarineReportingUnitIdOld'
            ),
            boundaries.c.MarineReportingUnitName.label(
                'MarineReportingUnitName'
            ),
            boundaries.c.RegionSubRegion.label('RegionSubRegion'),
            boundaries.c.legisSName.label('legisSName'),
            boundaries.c.nameText.label('nameText'),
            boundaries.c.desigEnd.label('desigEnd'),
            publication.c.sizeValue.label('sizeValue'),
        ).select_from(
            boundaries.outerjoin(
                publication,
                and_(
                    publication.c.MarineReportingUnitId ==
                    boundaries.c.MarineReportingUnitId,
                    publication.c.countryCode == boundaries.c.CountryCode,
                ),
            )
        ).subquery()

        super(Article4Cycle2024Provider, self).__init__(*args, **kwargs)

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
            'MarineReportingUnitIdOld',
            'Marine Reporting Unit ID (old)',
            'MarineReportingUnitIdOld',
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
            'Legislation',
            'legisSName',
            # show the reported value as-is rather than a glossary label
            labeler=to_text,
            # blank (' ') reported values are dropped instead of becoming an
            # empty option
            expression=_legislation_name,
        ),
    )

    # -- conditions ------------------------------------------------------
    def base_conditions(self):
        """Hide designations that ended before today.

        ``desigEnd`` is an ISO-8601 date string (``YYYY-MM-DD``) in the
        reporting table, so it is compared as a string against today's date:
        that is portable across SQL Server and the SQLite test harness. An
        empty end date means the designation is open ended and is kept.
        """
        today = date.today().isoformat()
        desig_end = func.trim(
            func.coalesce(self.mapper.c['desigEnd'], u'')
        )

        return [or_(desig_end == u'', desig_end >= today)]

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
                # card(
                #     'total_area',
                #     'Total Area Covered',
                #     stats['total'],
                #     AREA_UNIT,
                #     'Sum of MRU areas',
                #     [],
                #     None,
                #     'chart area',
                # ),
                card(
                    'median_area',
                    'Median MRU Size',
                    stats['median'],
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
                    hint='Number of Marine Reporting Units in each size '
                         'range.',
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
