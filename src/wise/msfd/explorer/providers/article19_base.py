# pylint: skip-file
"""Shared building blocks for the Article 19.3 "Datasets used" providers.

Article 19.3 does not have reporting cycles: it collects the datasets
resulting from the GES assessments and the monitoring programmes, grouped by
*information type*. Each information type is served as its own explorer
"cycle" (2024 Article 8, 2020 Article 11 monitoring programmes, 2018
Article 8 & 10 and 2012 Article 19.3) and read from the same tables the legacy
``search`` forms use.

Every information type shows **one row per dataset** (the payload the member
state filed) enriched with the parent record's context. The 2018 and 2024
Article 8 & 10 types instead drive the result from the indicator assessment,
so an indicator with several datasets stays a single row (the datasets are
packed into ``';'``-joined cells, matching the legacy form whose main row was
the assessment). The context often
lives in child tables (features, marine reporting units, descriptors), so it
is aggregated back into one ``';'``-joined cell per parent and joined to the
dataset row, the same way the Article 9/2018 provider packs its features and
marine units. The aggregation is a portable ``group_concat`` (see
``aggregates.py``: SQLite ``group_concat``, SQL Server ``string_agg``).

None of the sources carries a usable region, so the Region/Subregion filter and
cell are derived from the Article 4 marine reporting units through
:class:`~wise.msfd.explorer.providers.regions.MruRegionMixin`.
"""
from __future__ import absolute_import

from sqlalchemy import func, literal, select

from wise.msfd.explorer.providers.aggregates import group_concat
from wise.msfd.explorer.providers.base import BaseProvider
from wise.msfd.explorer.providers.regions import MruRegionMixin
from wise.msfd.explorer.providers.summary import (
    bar_chart,
    card,
    covered_descriptors,
    descriptor_label,
    descriptor_link_counts,
    descriptor_points,
    distinct_count,
    group_counts,
    label_points,
    link_counts,
    total_rows,
)
from wise.msfd.explorer.serializers import country_label

#: delimiter child values are packed with; the matching multi-value facets and
#: bullet-list columns read it back.
MULTI_SEPARATOR = ';'

#: How many GES descriptors the Directive defines (D1 ... D11); the
#: denominator of the descriptor coverage card.
GES_DESCRIPTOR_TOTAL = 11


def packed_cell(table, key_columns, value_column, label,
                separator=MULTI_SEPARATOR):
    """Aggregate a table into one ``<sep>``-joined cell per composite key.

    ``table`` may be a ``Table`` or a sub-query. The values are de-duplicated
    and ordered before being joined, so a child table listing the same value
    twice contributes one token. Returns a sub-query carrying ``key_columns``
    plus the packed ``label`` column.
    """
    # NB: keep starred arguments last in ``select(...)``: a positional
    # argument after ``*args`` is a syntax error before Python 3.5, and the
    # CI linters still parse this package with Python 2.7.
    values = (
        select(
            *(list(table.c[key] for key in key_columns) +
              [table.c[value_column]])
        )
        .where(table.c[value_column].isnot(None))
        .distinct()
        .order_by(table.c[value_column])
        .subquery()
    )

    keys = [values.c[key] for key in key_columns]
    return (
        select(
            *(keys + [group_concat(
                values.c[value_column], literal(separator)
            ).label(label)])
        )
        .group_by(*keys)
        .subquery()
    )


def single_value(table, key_columns, value_column, label):
    """Collapse a table to one value per composite key.

    Used for a parent attribute that is repeated on every matching row (e.g.
    the indicator title); ``max`` is an arbitrary-but-stable pick.
    """
    values = (
        select(
            *(list(table.c[key] for key in key_columns) +
              [table.c[value_column]])
        )
        .where(table.c[value_column].isnot(None))
        .distinct()
        .subquery()
    )

    keys = [values.c[key] for key in key_columns]
    return (
        select(
            *(keys + [func.max(values.c[value_column]).label(label)])
        )
        .group_by(*keys)
        .subquery()
    )


class Article19DatasetsProvider(MruRegionMixin, BaseProvider):
    """Base provider for the Article 19.3 "Datasets used" information types."""

    article = '19.3'
    article_slug = 'datasets-used'
    record_title = 'Article 19.3 (Datasets used)'

    #: free text / reported values that must never be run through the glossary
    #: lookup (a title or URL that happens to match a glossary key would
    #: otherwise be rewritten).
    blacklist_labels = (
        'URL', 'MD_URL', 'DataAccess', 'DatasetRecord', 'DatasetLink',
        'IndicatorTitle', 'ProgrammeName', 'DateStamp', 'InformationType',
    )

    def selectable_columns(self):
        """Select the region source even when it is not a displayed column.

        The derived Region cell reads the row's ``MarineReportingUnit`` (or
        equivalent), which several information types only use for the region
        lookup and do not show as a column. An explicit ``columns`` list would
        otherwise leave that value out of the query.
        """
        columns = list(super(Article19DatasetsProvider,
                             self).selectable_columns())
        name = self.region_mru_column

        if name and name in self.mapper.c:
            source = self.mapper.c[name]

            if source not in columns:
                columns.append(source)

        return columns

    def serialize_row(self, row):
        """Serialize one row, filling the derived Region cell."""
        out = super(Article19DatasetsProvider, self).serialize_row(row)
        cell = self.region_cell(row)

        if cell is not None:
            out['Region'] = cell

        return out


class Article19SummaryMixin(object):
    """Summary & insights panel shared by the Article 19.3 information types.

    The information types do not share a schema, so the panel is built from
    whatever the cycle declares:

    ``summary_link_column``
        the column holding the dataset links (the 2020 cycle only reports how
        a monitoring programme's data can be accessed, so its column is a data
        access reference, not a dataset file);
    ``summary_md_column``
        the column holding the metadata links, when the cycle has one;
    ``summary_descriptor_column``
        the column holding the GES descriptor / component, when the cycle has
        one. Cells are exploded to their ``D<number>`` prefix (``D5C1``,
        ``D1.2`` and ``D6/D1`` all count), see
        :func:`~wise.msfd.explorer.providers.summary.descriptors_in`.

    Every cycle has a dataset link and a country, so those two cards (plus the
    per-country chart) are always drawn; the metadata and descriptor cards
    appear only where the cycle reports the column. A link counts as *valid*
    when it looks like a reference -- see
    :data:`~wise.msfd.explorer.providers.summary.LINK_RE` -- because the link
    fields are also used for placeholders ("Metadata not available", "nvt", a
    bare hostname), and counting every non-empty cell would report more links
    than were filed.

    A cycle with an extra breakdown overrides :meth:`_summary_extra_charts`.
    All aggregates honour the current facet selection but are independent of
    paging and sorting; the "N of M" denominators ignore the selection and
    keep only the cycle's own cut.
    """

    summary_link_column = None
    summary_md_column = None
    summary_descriptor_column = None
    #: label of one result row, used by the cards and chart captions
    summary_record_label = 'Datasets'
    summary_link_label = 'Dataset links'
    summary_md_label = 'Metadata links'
    summary_separator = MULTI_SEPARATOR

    def _summary_extra_charts(self, session, conditions):
        """Cycle specific charts; the shared panel does not need any."""
        return []

    def _build_summary(self, session):
        """KPIs and charts for the Summary & insights panel.

        The cards are count based: how many records match, how many of their
        dataset and metadata links are real references, how many descriptors
        and countries those records cover. The charts break the links down by
        descriptor and the records down by country.
        """
        conditions = self.data_conditions()
        # The "N of M" denominators ignore the facet selection but still apply
        # the provider's base cut (e.g. the 2018 latest reported file).
        base = self.base_conditions()
        mapper = self.mapper
        record_label = self.summary_record_label

        cards = [
            card(
                'records',
                record_label,
                int(total_rows(session, mapper, conditions)),
                None,
                '{} match your selection'.format(record_label),
                [],
                None,
                'clipboard',
            ),
        ]

        charts = []

        if self.summary_link_column:
            valid, reported = link_counts(
                session,
                mapper,
                conditions,
                mapper.c[self.summary_link_column],
                separator=self.summary_separator,
            )
            cards.append(card(
                'dataset_links',
                self.summary_link_label,
                int(valid),
                None,
                '{} that are online references'.format(
                    self.summary_link_label),
                [],
                int(reported),
                'linkify',
            ))

        if self.summary_md_column:
            valid, reported = link_counts(
                session,
                mapper,
                conditions,
                mapper.c[self.summary_md_column],
                separator=self.summary_separator,
            )
            cards.append(card(
                'metadata_links',
                self.summary_md_label,
                int(valid),
                None,
                '{} that are online references'.format(self.summary_md_label),
                [],
                int(reported),
                'linkify',
            ))

        if self.summary_descriptor_column:
            descriptor_column = mapper.c[self.summary_descriptor_column]
            covered = covered_descriptors(
                session, mapper, conditions, descriptor_column,
                separator=self.summary_separator,
            )
            covered_total = covered_descriptors(
                session, mapper, base, descriptor_column,
                separator=self.summary_separator,
            )
            cards.append(card(
                'descriptors',
                'GES Descriptors',
                len(covered),
                None,
                'Descriptors your selection covers',
                [],
                min(len(covered_total), GES_DESCRIPTOR_TOTAL),
                'th large',
                hint='A record covering several descriptors counts for each. '
                     'Only the descriptors actually reported are counted, so '
                     'this can stay below the 11 the Directive defines.',
            ))

            if self.summary_link_column:
                counts = descriptor_link_counts(
                    session, mapper, conditions, descriptor_column,
                    mapper.c[self.summary_link_column],
                    separator=self.summary_separator,
                )

                charts.append(bar_chart(
                    'descriptor_distribution',
                    '{} by GES Descriptor'.format(
                        self.summary_link_label),
                    descriptor_points(counts, descriptor_label),
                    orientation='h',
                    x_label='Number of {}'.format(
                        self.summary_link_label.lower()),
                    y_label='',
                    hint='{} per GES descriptor over the {} descriptors '
                         'reached. A record filed under several descriptors '
                         'contributes its links to each, so the bars can add '
                         'up to more than the link total.'.format(
                             self.summary_link_label, len(counts)),
                ))

        country_points = label_points(
            group_counts(session, mapper, conditions,
                         mapper.c['CountryCode']),
            country_label,
        )

        # cards.append(card(
        #     'countries',
        #     'Countries',
        #     len(country_points),
        #     None,
        #     'Member States match your selection',
        #     [],
        #     int(distinct_count(session, mapper, mapper.c['CountryCode'],
        #                        base)),
        #     'flag',
        # ))

        # charts.append(bar_chart(
        #     'country_distribution',
        #     '{} by Country'.format(self.summary_record_label),
        #     country_points,
        #     orientation='h',
        #     x_label='Number of {}'.format(record_label.lower()),
        #     y_label='',
        #     hint='{} reported by each Member State.'.format(record_label),
        # ))

        charts.extend(self._summary_extra_charts(session, conditions))

        return {'cards': cards, 'charts': charts}
