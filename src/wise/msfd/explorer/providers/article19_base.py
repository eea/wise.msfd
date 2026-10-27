# pylint: skip-file
"""Shared building blocks for the Article 19.3 "Datasets used" providers.

Article 19.3 does not have reporting cycles: it collects the datasets
resulting from the GES assessments and the monitoring programmes, grouped by
*information type*. Each information type is served as its own explorer
"cycle" (2024 Article 8 & 10, 2020 Article 11 monitoring programmes, 2018
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

#: delimiter child values are packed with; the matching multi-value facets and
#: bullet-list columns read it back.
MULTI_SEPARATOR = ';'


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
