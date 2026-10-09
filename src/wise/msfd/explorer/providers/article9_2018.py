# pylint: skip-file
"""Provider for Article 9 (GES determination), 2018-2024 reporting exercise.

This cycle is read from the **base tables** the legacy ``search`` Article 9
form uses, not from the ``V_ART9_GES_2018`` view:

* ``ART9_GES_GESComponent`` -- one row per GES component (the determination's
  parent), holding the two justification fields and the link to the reported
  information;
* ``ART9_GES_GESDetermination`` -- the determination of a component (GES
  description, determination date, update type);
* ``ART9_GES_GESDetermination_Feature`` -- the features a determination
  covers;
* ``ART9_GES_MarineUnit`` -- the marine reporting units a determination
  covers;
* ``ReportedInformation`` -- the reported file (country and reported date).

The features and marine reporting units live in child tables, one row each.
The redesigned explorer shows **one row per GES determination** (i.e. per GES
description), so those two child tables are aggregated back into one cell per
determination, joined by ``';'``, and rendered as bullet lists. A component
with no determination, and a determination with no feature or MRU, is still
kept: the aggregation joins are outer joins and the packed cell is simply
empty. Only the latest reported file of each ``(country, schema)`` is shown,
which is the cut the legacy form applies through ``latest_import_ids_2018``.

The base tables carry no region: the Region/Subregion filter and cell are
derived from the Article 4 MRU publication, like the legacy explorer derived
regions elsewhere.
"""
from __future__ import absolute_import

from sqlalchemy import and_, func, literal, or_, select

from wise.msfd import sql2018
from wise.msfd.explorer.providers.aggregates import group_concat
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

#: delimiter the child-table values are packed with; the matching bullet list
#: columns and facets read it back.
MULTI_SEPARATOR = ';'


def _packed_values(table, value_column, key_column, label,
                   separator=MULTI_SEPARATOR):
    """Aggregate a child table into one ``<sep>``-joined cell per parent key.

    Returns a sub-query ``(key_column, label)`` with one row per distinct
    ``key_column``: the child values are de-duplicated and joined with
    ``separator``. The aggregate is portable (see ``aggregates.py``) so it runs
    on both the live SQL Server database and the SQLite test harness.
    """
    values = (
        select(table.c[key_column], table.c[value_column])
        .where(table.c[value_column].isnot(None))
        .distinct()
        .order_by(table.c[value_column])
        .subquery()
    )

    return (
        select(
            values.c[key_column],
            group_concat(
                values.c[value_column], literal(separator)
            ).label(label),
        )
        .group_by(values.c[key_column])
        .subquery()
    )


class Article9Cycle2018Provider(MruRegionMixin, BaseProvider):
    """GES determinations reported under Article 9 for 2018-2024."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2018'
    cycle_label = '2018 reporting exercise'
    cycle_display = '2018 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2018'

    # Injectable source tables: tests point them at an in-memory database.
    component = sql2018.ART9GESGESComponent.__table__
    reported = sql2018.ReportedInformation.__table__
    determination = sql2018.ART9GESGESDetermination.__table__
    feature = sql2018.ART9GESGESDeterminationFeature.__table__
    marine_unit = sql2018.ART9GESMarineUnit.__table__

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql2018.MRUsPublication.__table__
    region_mru_id_column = 'thematicId'
    region_region_column = 'rZoneId'

    order_by = ('CountryCode', 'GESComponent')

    # Free text / already human readable fields shown as reported.
    blacklist_labels = (
        'MarineReportingUnit', 'GESDescription', 'JustificationDelay',
        'JustificationNonUse', 'DeterminationDate', 'UpdateType',
    )

    def __init__(self, *args, **kwargs):
        component = self.component
        reported = self.reported
        determination = self.determination

        # The child tables are aggregated to one cell per determination, so
        # the result grain is one row per GES description. The base tables are
        # joined in a sub-query so every column keeps its plain name, which is
        # what the provider's column/facet lookups expect (a raw ``Join``
        # would key its columns by table name).
        feature_cell = _packed_values(
            self.feature, 'Feature', 'IdGESDetermination', 'Feature'
        )
        marine_unit_cell = _packed_values(
            self.marine_unit,
            'MarineReportingUnit',
            'IdGESDetermination',
            'MarineReportingUnit',
        )

        self.mapper = select(
            component.c.Id.label('ComponentId'),
            component.c.GESComponent.label('GESComponent'),
            component.c.JustificationDelay.label('JustificationDelay'),
            component.c.JustificationNonUse.label('JustificationNonUse'),
            reported.c.Id.label('ImportId'),
            reported.c.CountryCode.label('CountryCode'),
            reported.c.ReportingDate.label('ReportingDate'),
            determination.c.Id.label('DeterminationId'),
            determination.c.GESDescription.label('GESDescription'),
            determination.c.DeterminationDate.label('DeterminationDate'),
            determination.c.UpdateType.label('UpdateType'),
            feature_cell.c.Feature.label('Feature'),
            marine_unit_cell.c.MarineReportingUnit.label(
                'MarineReportingUnit'
            ),
        ).select_from(
            component
            .join(
                reported,
                component.c.IdReportedInformation == reported.c.Id,
            )
            .outerjoin(
                determination,
                determination.c.IdGESComponent == component.c.Id,
            )
            .outerjoin(
                feature_cell,
                feature_cell.c.IdGESDetermination == determination.c.Id,
            )
            .outerjoin(
                marine_unit_cell,
                marine_unit_cell.c.IdGESDetermination == determination.c.Id,
            )
        ).subquery()

        super(Article9Cycle2018Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column(
            'Region',
            'Region / Subregion',
            'Region',
            min_width=200,
            sortable=False,
        ),
        Column('GESComponent', 'GES Component / Criteria',
               'GESComponent', min_width=200),
        Column(
            'Feature',
            'Feature(s)',
            'Feature',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column(
            'MarineReportingUnit',
            'Marine Reporting Unit(s)',
            'MarineReportingUnit',
            format='mru_multi',
            separator=MULTI_SEPARATOR,
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
        Column('UpdateType', 'Update type', 'UpdateType', min_width=170),
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
            static='2018 reporting exercise',
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
            separator=MULTI_SEPARATOR,
        ),
        Facet(
            'update_type',
            'Update type',
            'UpdateType',
            # the reported value is already human readable
            labeler=to_text,
        ),
        Facet(
            'ges_component',
            'GES Component / Criteria',
            'GESComponent',
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Feature',
            separator=MULTI_SEPARATOR,
        ),
    )

    def base_conditions(self):
        """Keep only the latest reported file of each ``(country, schema)``.

        Mirrors ``db.latest_import_ids_2018``, which the legacy Article 9 form
        applied to the component table.
        """
        inner = self.reported.alias('ri_latest')
        latest = (
            select(func.max(inner.c.Id))
            .group_by(inner.c.CountryCode, inner.c.Schema)
        )

        return [self.mapper.c['ImportId'].in_(latest)]

    def _build_summary(self, session):
        """KPIs and charts for the Summary & insights panel.

        Four count-based cards (Marine Reporting Units, GES Components,
        Features and the justifications) and two distributions (the update
        type of every determination and the GES components they cover). The
        packed feature / marine-unit cells are counted per token, so a
        determination covering three features contributes to all three. All
        aggregates honour the current facet selection but are independent of
        paging and sorting.
        """
        conditions = self.data_conditions()
        # The "n of M" denominators ignore the facet selection but still apply
        # the provider's base cut (e.g. the latest reported file per country).
        base = self.base_conditions()
        mapper = self.mapper

        mru = mapper.c['MarineReportingUnit']
        component = mapper.c['GESComponent']
        feature = mapper.c['Feature']
        update_type = mapper.c['UpdateType']
        delay = mapper.c['JustificationDelay']
        non_use = mapper.c['JustificationNonUse']

        # A reported justification is present but non-empty; the free text is
        # counted, never charted.
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
        out = super(Article9Cycle2018Provider, self).serialize_row(row)
        cell = self.region_cell(row)

        if cell is not None:
            out['Region'] = cell

        return out
