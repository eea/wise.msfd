# pylint: skip-file
"""Provider for Article 9 (GES determination), 2024-2030 reporting exercise.

The 2024 data source is the ``data.ART9_GES_GEScomponent`` **base table** the
legacy ``search`` form reads, not the ``dbo.V_ART9_GES_2024`` view. It already
joins the GES component, its determination and the reported features, and
carries the marine reporting unit, the update type and both justification
fields, so the explorer can expose one row per reported component without
recreating any of those joins in the provider. The base table has no region;
the Region/Subregion filter and cell are derived from the Article 4 MRU
publication (see ``providers/regions.py``).

Unlike the 2018-2024 cycle, ``GEScomponent``, ``Feature`` and
``MarineReportingUnit`` pack several codes into one cell joined by ``;``, which
is why the first two filters use :class:`MultiValueFacet` and the region facet
runs in ``packed`` mode.
"""
from __future__ import absolute_import

from sqlalchemy import and_, or_

from wise.msfd import sql2024
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.providers.regions import MruRegionFacet, MruRegionMixin
from wise.msfd.explorer.providers.summary import (
    bar_chart,
    card,
    group_counts,
    label_points,
    multi_distinct_count,
    total_rows,
)
from wise.msfd.explorer.serializers import country_label, to_text


class Article9Cycle2024Provider(MruRegionMixin, BaseProvider):
    """GES determinations reported under Article 9 for 2024-2030."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2024'
    cycle_label = '2024 reporting exercise'
    cycle_display = '2024 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2024'

    # The base table the legacy ``search`` form reads, not the
    # ``V_ART9_GES_2024`` view. It already packs ``GEScomponent``, ``Feature``
    # and ``MarineReportingUnit`` into single cells joined by ``';'``.
    mapper = sql2024.t_ART9_GES_GEScomponent

    #: Article 4 MRU publication used to derive the region of each MRU. The
    #: cell packs several ids, hence ``packed=True`` on the region facet.
    region_mru_table = sql2024.t_MarineReportingUnit_Publication
    region_mru_id_column = 'MarineReportingUnitId'
    region_region_column = 'RegionSubRegion'

    order_by = ('CountryCode', 'GEScomponent')

    # Free text / already human readable fields whose value must be shown as
    # reported instead of run through the glossary label lookup.
    blacklist_labels = (
        'MarineReportingUnit', 'GESDescription', 'JustificationDelay',
        'JustificationNonUse', 'DeterminationDate', 'UpdateTypeGES',
    )

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column(
            'Region',
            'Region / Subregion',
            'Region',
            min_width=200,
            sortable=False,
        ),
        Column(
            'GEScomponent',
            'GES Component / Criteria',
            'GEScomponent',
            separator=';',
            min_width=200,
        ),
        Column(
            'Feature',
            'Feature(s)',
            'Feature',
            format='multi',
            separator=';',
            min_width=200,
        ),
        Column(
            'MarineReportingUnit',
            'Marine Reporting Unit(s)',
            'MarineReportingUnit',
            format='mru_multi',
            separator=';',
            min_width=200,
        ),
        Column(
            'GESDescription',
            'GES Description',
            'GESDescription',
            expandable=True,
            min_width=280,
        ),
        Column(
            'JustificationDelay',
            'Justification for delay',
            'JustificationDelay',
            expandable=True,
            min_width=200,
        ),
        Column(
            'JustificationNonUse',
            'Justification for non-use',
            'JustificationNonUse',
            expandable=True,
            min_width=200,
        ),
        Column('UpdateTypeGES', 'Update type', 'UpdateTypeGES', min_width=170),
        Column(
            'DeterminationDate',
            'Determination date',
            'DeterminationDate',
            format='date_month',
        ),
        Column(
            'ReportingDate', 'Reported date', 'ReportingDate', format='date'
        ),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2024 reporting exercise',
            min_width=160,
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
            packed=True,
        ),
        Facet(
            'update_type',
            'Update type',
            'UpdateTypeGES',
            # the reported value is already human readable
            labeler=to_text,
        ),
        MultiValueFacet(
            'ges_component',
            'GES Component / Criteria',
            'GEScomponent',
            separator=';',
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Feature',
            separator=';',
        ),
    )

    def _build_summary(self, session):
        """KPIs and charts for the Summary & insights panel.

        Mirrors the 2018 cycle: four count-based cards (Marine Reporting Units,
        GES Components, Features and the justifications) and two distributions
        (the update type of every determination and the GES components they
        cover). ``GEScomponent``, ``Feature`` and ``MarineReportingUnit`` pack
        several codes per cell, so they are counted per token. All aggregates
        honour the current facet selection but are independent of paging and
        sorting.
        """
        conditions = self.data_conditions()
        # No base cut on this cycle; kept for symmetry with 2018 and future
        # overrides.
        base = self.base_conditions()
        mapper = self.mapper

        mru = mapper.c['MarineReportingUnit']
        component = mapper.c['GEScomponent']
        feature = mapper.c['Feature']
        update_type = mapper.c['UpdateTypeGES']
        delay = mapper.c['JustificationDelay']
        non_use = mapper.c['JustificationNonUse']

        has_delay = and_(delay.isnot(None), delay != u'')
        has_non_use = and_(non_use.isnot(None), non_use != u'')

        total = total_rows(session, mapper, conditions)

        mru_count = multi_distinct_count(session, mapper, mru, conditions)
        mru_total = multi_distinct_count(session, mapper, mru, base)

        component_count = multi_distinct_count(
            session, mapper, component, conditions
        )
        component_total = multi_distinct_count(
            session, mapper, component, base
        )

        feature_count = multi_distinct_count(
            session, mapper, feature, conditions
        )
        feature_total = multi_distinct_count(
            session, mapper, feature, base
        )

        justified = total_rows(
            session, mapper,
            list(conditions) + [or_(has_delay, has_non_use)],
        )
        delay_count = total_rows(
            session, mapper, list(conditions) + [has_delay]
        )
        non_use_count = total_rows(
            session, mapper, list(conditions) + [has_non_use]
        )

        update_points = label_points(
            group_counts(session, mapper, conditions, update_type), to_text,
        )

        return {
            'cards': [
                card(
                    'mru_count',
                    'Marine Reporting Units',
                    int(mru_count),
                    None,
                    'MRUs match your selection',
                    [],
                    int(mru_total),
                    'tint',
                ),
                card(
                    'component_count',
                    'GES Components / Criteria',
                    int(component_count),
                    None,
                    'Components match your selection',
                    [],
                    int(component_total),
                    'th large',
                ),
                card(
                    'feature_count',
                    'Features',
                    int(feature_count),
                    None,
                    'Features match your selection',
                    [],
                    int(feature_total),
                    'tags',
                    hint='A record covering several features counts for each; '
                         'features reported alongside a selected one are '
                         'included too.',
                ),
                card(
                    'justifications',
                    'Justifications reported',
                    int(justified),
                    None,
                    'Determinations carrying a justification',
                    [],
                    int(total),
                    'clipboard',
                ),
            ],
            'charts': [
                bar_chart(
                    'update_type',
                    'Determinations by update type',
                    update_points,
                    orientation='v',
                    y_label='Number of determinations',
                    hint='How many determinations are new, modified from a '
                         'previously reported one, or unchanged.',
                ),
                bar_chart(
                    'justification_distribution',
                    'Determinations by Justifications',
                    [
                        {'label': 'Justification for delay',
                         'value': int(delay_count)},
                        {'label': 'Justification for non-use',
                         'value': int(non_use_count)},
                    ],
                    orientation='v',
                    y_label='Number of determinations',
                    hint='Determinations carrying a justification for delay and '
                         'for non-use. A determination can carry both, so the '
                         'bars can sum to more than the justifications total.',
                ),
            ],
        }

    def serialize_row(self, row):
        out = super(Article9Cycle2024Provider, self).serialize_row(row)
        cell = self.region_cell(row)

        if cell is not None:
            out['Region'] = cell

        return out
