# pylint: skip-file
"""Provider for Article 4, 2024-2030 reporting cycle.

The 2024 data source is the ``spatial.MarineReportingUnit_Publication`` table:
unlike the legacy ``ART4_GEO_GeographicalBoundaries`` table it also carries the
MRU size (``sizeValue`` in ``sizeUom``) and the legislation short name
(``legisSName``), which the redesigned explorer exposes as filters and columns.
"""
from __future__ import absolute_import

import logging

from sqlalchemy import case, distinct, func

from wise.msfd import sql2024
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    ExplorerError,
    Facet,
    RangeFacet,
    TextFacet,
    TogglesFacet,
    db_session,
)
from wise.msfd.explorer.serializers import (country_label, glossary_label,
                                            to_text)

logger = logging.getLogger('wise.msfd')

# Size distribution buckets used by the summary chart. Each entry is
# ``(label, lower, upper)`` where ``None`` marks an open end. The buckets are
# disjoint and cover every value; the upper bound of each label is inclusive,
# except ``> 250,000`` which is strictly greater.
SIZE_BUCKETS = (
    (u'< 1,000', None, 1000),
    (u'1,000 \u2013 10,000', 1000, 10000),
    (u'10,000 \u2013 50,000', 10000, 50000),
    (u'50,000 \u2013 100,000', 50000, 100000),
    (u'100,000 \u2013 250,000', 100000, 250000),
    (u'> 250,000', 250000, None),
)


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
    def build_summary(self):
        """KPIs and charts for the Summary & insights panel.

        The payload is intentionally self describing (``cards`` + ``charts``)
        so the frontend stays a generic renderer and a future article/cycle can
        ship a completely different summary just by overriding this method.
        All aggregates honour the current facet selection (including the area
        range), but are independent of paging and sorting.
        """
        with db_session(self.session_name):
            session = self._get_session()

            try:
                return self._build_summary(session)
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to build summary')
                raise ExplorerError('MSFD database is not available')

    @staticmethod
    def _number(value):
        """Return a plain float (JSON friendly) or ``None``."""
        if value is None:
            return None

        return float(value)

    @staticmethod
    def _card(key, label, value, unit, caption, details, value_of, icon):
        return {
            'key': key,
            'label': label,
            'value': value,
            'unit': unit,
            'caption': caption,
            'details': details,
            'valueOf': value_of,
            'icon': icon,
            'hint': None,
        }

    def _build_summary(self, session):
        conditions = self.data_conditions()
        region = self.mapper.c['RegionSubRegion']
        size = self.mapper.c['sizeValue']

        total = (
            session.query(func.count())
            .select_from(self.mapper)
            .filter(*conditions)
            .scalar()
        ) or 0

        # Area aggregates ignore rows without a size, so a missing value never
        # pollutes the sum, the average or the distribution.
        total_area, avg_area, min_area, max_area = (
            session.query(
                func.sum(size),
                func.avg(size),
                func.min(size),
                func.max(size),
            )
            .select_from(self.mapper)
            .filter(*conditions)
            .filter(size.isnot(None))
            .one()
        )

        region_rows = (
            session.query(region, func.count())
            .select_from(self.mapper)
            .filter(*conditions)
            .filter(region.isnot(None))
            .group_by(region)
            .all()
        )

        region_points = sorted(
            (
                {'label': to_text(glossary_label(value)),
                 'value': int(count)}
                for value, count in region_rows
            ),
            key=lambda point: (-point['value'], point['label'] or ''),
        )

        # Denominator of the Regions KPI: every region the cycle reports,
        # regardless of the current selection.
        region_total = (
            session.query(func.count(distinct(region)))
            .select_from(self.mapper)
            .filter(region.isnot(None))
            .scalar()
        ) or 0

        # Buckets are disjoint and cover every value, and each label is
        # literally true: 10,000 starts the next bucket and only values
        # strictly greater than 250,000 reach the last one.
        bucket = case(
            (size < 1000, SIZE_BUCKETS[0][0]),
            (size < 10000, SIZE_BUCKETS[1][0]),
            (size < 50000, SIZE_BUCKETS[2][0]),
            (size < 100000, SIZE_BUCKETS[3][0]),
            (size <= 250000, SIZE_BUCKETS[4][0]),
            else_=SIZE_BUCKETS[5][0],
        )

        bucket_counts = dict(
            session.query(bucket, func.count())
            .select_from(self.mapper)
            .filter(*conditions)
            .filter(size.isnot(None))
            .group_by(bucket)
            .all()
        )

        size_points = [
            {'label': label, 'value': int(bucket_counts.get(label, 0))}
            for label, _lower, _upper in SIZE_BUCKETS
        ]

        area_unit = u'km\u00b2'

        return {
            'cards': [
                self._card(
                    'mru_count',
                    'Marine Reporting Units',
                    int(total),
                    None,
                    'MRUs match your selection',
                    [],
                    None,
                    'tint',
                ),
                self._card(
                    'total_area',
                    'Total Area Covered',
                    self._number(total_area),
                    area_unit,
                    'Sum of MRU areas',
                    [],
                    None,
                    'chart area',
                ),
                self._card(
                    'average_area',
                    'Average MRU Size',
                    self._number(avg_area),
                    area_unit,
                    None,
                    [
                        {'label': 'Min', 'value': self._number(min_area),
                         'unit': area_unit},
                        {'label': 'Max', 'value': self._number(max_area),
                         'unit': area_unit},
                    ],
                    None,
                    'map marker',
                ),
                self._card(
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
                {
                    'key': 'size_distribution',
                    'type': 'bar',
                    'orientation': 'v',
                    'title': 'Distribution of MRU size',
                    'xLabel': u'MRU area (km\u00b2)',
                    'yLabel': 'Number of MRUs',
                    'hint': 'Number of Marine Reporting Units in each size '
                            'range.',
                    'points': size_points,
                },
                {
                    'key': 'region_distribution',
                    'type': 'bar',
                    'orientation': 'h',
                    'title': 'Marine Reporting Units by Region / Subregion',
                    'xLabel': 'Number of MRUs',
                    'yLabel': '',
                    'hint': 'Number of Marine Reporting Units per region or '
                            'subregion.',
                    'points': region_points,
                },
            ],
        }
