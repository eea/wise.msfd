# pylint: skip-file
"""Base data provider for the MSFD data explorer API.

A provider is the only place that knows how a given article/reporting cycle is
read from the database. It receives the current filter selections and returns
JSON friendly structures that are independent of the underlying data source,
so an Elasticsearch backed implementation can replace the SQL one later
without changing the API contract.

Filters are described as :class:`Facet` instances. Each facet knows how to turn
its selection into SQL conditions and how to serialize itself for the frontend:
checkboxes/toggles (multi-select), a numeric range and free text search. The
frontend only reads ``type`` and renders the matching widget, so new facet
shapes can be added here without touching the frontend.
"""
from __future__ import absolute_import

import logging
import math
import os
from contextlib import contextmanager

from sqlalchemy import func, literal, or_

from wise.msfd import db
from wise.msfd.db import threadlocals
from wise.msfd.explorer.serializers import (
    format_area,
    format_date,
    format_month,
    format_reported_date,
    glossary_label,
    mru_label,
    name_as_title,
    serialize_cell,
    serialize_multi_cell,
    to_text,
)

logger = logging.getLogger('wise.msfd')

#: Hard upper bound on the number of rows a single page may return. The
#: frontend asks for 10 by default; anything above this is rejected by
#: clamping so an anonymous caller cannot request an arbitrarily large page.
MAX_PAGE_SIZE = 200
#: Hard upper bound on the rows returned by ``all=1`` (whole-result download).
#: This is deliberately far below the table size: ``all=1`` is a bulk export on
#: a permission-less (``zope2.View``) endpoint with no rate limiting, so a
#: single request must not be able to materialize a huge result. Override with
#: the ``MSFD_EXPLORER_MAX_ALL_ROWS`` environment variable if a deployment
#: needs larger exports.


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


MAX_ALL_ROWS = max(_env_int('MSFD_EXPLORER_MAX_ALL_ROWS', 10000), 1)
#: Hard upper bound on the number of values accepted for one facet selection,
#: keeping the generated ``IN (...)`` clause (and its query plan) small.
MAX_FACET_VALUES = 100
#: Hard upper bound on the length of a free-text search term.
MAX_TEXT_LENGTH = 200


class ExplorerError(Exception):
    """Raised when the explorer backend cannot serve the request."""


@contextmanager
def db_session(session_name):
    """Run a block of code against one of the MSFD database sessions."""
    saved = getattr(threadlocals, 'session_name', None)
    threadlocals.session_name = session_name

    try:
        yield db.session()
    finally:
        threadlocals.session_name = saved


class Column(object):
    """One column of the result table.

    ``source`` is the database column the value is read from (defaults to
    ``key``). ``static`` makes a column that has no database backing (e.g. the
    reporting cycle). ``format`` selects one of the display formatters.
    """

    __slots__ = ('key', 'label', 'source', 'align', 'format', 'static',
                 'hidden', 'expandable', 'min_width', 'separator', '_sortable')

    def __init__(self, key, label, source=None, align=None, format=None,
                 static=None, hidden=False, expandable=False, min_width=None,
                 separator=';', sortable=True):
        self.key = key
        self.label = label
        self.source = source if source is not None else key
        self.align = align
        self.format = format
        self.static = static
        self.hidden = hidden
        #: whether the frontend may sort on this column. A derived column that
        #: has no mapped source (e.g. the Article 9 region) opts out.
        self._sortable = sortable
        #: long free text column: the frontend truncates the cell and lets the
        #: user reveal the full value in place.
        self.expandable = expandable
        #: minimum rendered width in px, enforced by the frontend so short
        #: columns cannot collapse below a readable size. ``None`` lets the
        #: browser size the column from its content.
        self.min_width = min_width
        #: delimiter of a ``format='multi'`` column (multi valued cell).
        self.separator = separator

    @property
    def sortable(self):
        return self._sortable and self.static is None


class Facet(object):
    """A multi-select (checkboxes) filter of an article/reporting cycle."""

    type = 'checkboxes'

    def __init__(self, name, label, column, labeler=None, expression=None):
        self.name = name
        self.label = label
        self.column = column
        self.labeler = labeler
        #: optional ``callable(column) -> expression`` applied to the mapped
        #: column before use, so a facet can match/group on a normalized value
        #: (e.g. trailing whitespace stripped from padded codes) without the
        #: stored value leaking into the wire options.
        self.expression = expression

    def label_for(self, value):
        if self.labeler:
            return self.labeler(value)

        return glossary_label(value)

    def sql_column(self, provider):
        """The mapped column, after this facet's optional expression."""
        column = provider.mapper.c[self.column]

        if self.expression is not None:
            return self.expression(column)

        return column

    # -- data conditions -------------------------------------------------
    def conditions(self, provider):
        """SQL conditions contributed by this facet's own selection."""
        values = provider.selected(self.name)

        if not values:
            return []

        return [self.sql_column(provider).in_(values)]

    # -- serialization ---------------------------------------------------
    def build(self, session, provider):
        column = self.sql_column(provider)
        conditions = provider.conditions_except(self.name)
        selected = set(provider.selected(self.name))

        query = (
            session.query(column, func.count())
            .filter(*conditions)
            .group_by(column)
            .order_by(column)
        )

        options = []
        seen = set()

        for value, count in query:
            if value is None:
                continue

            seen.add(value)

            if not count and value not in selected:
                # hide unselected options that would yield no rows
                continue

            options.append({
                'value': value,
                'label': to_text(self.label_for(value)),
                'count': int(count or 0),
                'selected': value in selected,
            })

        # keep selected values visible even when they dropped to zero
        for value in selected:
            if value in seen:
                continue

            options.append({
                'value': value,
                'label': to_text(self.label_for(value)),
                'count': 0,
                'selected': True,
            })

        options.sort(key=lambda option: (option['label'] or '').lower())

        return {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'options': options,
        }


class TogglesFacet(Facet):
    """Same data as a checkbox facet, but rendered as a group of buttons."""

    type = 'toggles'


class MultiValueFacet(Facet):
    """A multi-select filter over a column packing several values in a cell.

    Some reporting cycles store a list of codes in one database column, joined
    by a delimiter (e.g. ``'D5C1;D5C2'``,
    ``'PresEnvContUPBTs,PresEnvContSeafood'``). A plain ``IN (...)`` facet
    cannot filter those rows, and a naive ``LIKE '%D5%'`` would also match
    ``D5C1``. This facet matches *whole* tokens, tolerating stray spaces
    around the delimiter, and explodes the distinct values into one option
    per token with the number of rows carrying it.
    """

    type = 'checkboxes'

    def __init__(self, name, label, column, separator=';', labeler=None,
                 expression=None):
        super(MultiValueFacet, self).__init__(
            name, label, column, labeler=labeler, expression=expression
        )
        self.separator = separator

    #: escape character used when a reported token itself contains a LIKE
    #: wildcard (``%`` or ``_``), so it reaches the database verbatim.
    like_escape = '~'

    def tokens(self, value):
        """The individual, trimmed tokens stored in one cell value."""
        if value in (None, ''):
            return []

        return [
            token.strip()
            for token in to_text(value).split(self.separator)
            if token.strip()
        ]

    @classmethod
    def _pattern(cls, token):
        # a reported token may contain ``%`` or ``_`` (e.g.
        # ``BioDisturb_other``); escape them instead of dropping them.
        token = token.replace(u' ', u'')
        token = token.replace(cls.like_escape, cls.like_escape * 2)
        token = token.replace(u'%', cls.like_escape + u'%')

        return token.replace(u'_', cls.like_escape + u'_')

    def _padded(self, provider):
        """``<sep>value<sep>`` with spaces removed, for whole-token LIKE."""
        normalized = func.replace(self.sql_column(provider), u' ', u'')
        separator = literal(self.separator)

        return separator + normalized + separator

    def conditions(self, provider):
        values = provider.selected(self.name)

        if not values:
            return []

        padded = self._padded(provider)
        conditions = []

        for value in values:
            token = self._pattern(value)

            if not token:
                continue

            pattern = u'%{0}{1}{0}%'.format(self.separator, token)
            conditions.append(padded.like(pattern, escape=self.like_escape))

        if not conditions:
            return []

        return [or_(*conditions)]

    def build(self, session, provider):
        column = self.sql_column(provider)
        conditions = provider.conditions_except(self.name)
        selected = set(provider.selected(self.name))

        rows = (
            session.query(column, func.count())
            .filter(*conditions)
            .group_by(column)
            .all()
        )

        counts = {}

        for value, count in rows:
            # ``set`` avoids counting a token twice when it is repeated inside
            # a single cell value.
            for token in set(self.tokens(value)):
                counts[token] = counts.get(token, 0) + int(count or 0)

        options = []

        for token, count in counts.items():
            if not count and token not in selected:
                continue

            options.append({
                'value': token,
                'label': to_text(self.label_for(token)),
                'count': int(count),
                'selected': token in selected,
            })

        # keep selected tokens visible even when the cross filter dropped them
        for token in selected:
            if token in counts:
                continue

            options.append({
                'value': token,
                'label': to_text(self.label_for(token)),
                'count': 0,
                'selected': True,
            })

        options.sort(key=lambda option: (option['label'] or '').lower())

        return {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'options': options,
        }


class RangeFacet(object):
    """A numeric range filter (min/max), e.g. ``area=0,500000``."""

    type = 'range'

    def __init__(self, name, label, column, unit=None, step=None):
        self.name = name
        self.label = label
        self.column = column
        self.unit = unit
        self.step = step

    def bounds(self, provider):
        """
        Return the selected ``(min, max)`` as floats, or ``(None, None)``.
        """
        values = provider.selected(self.name)
        low = high = None

        if len(values) >= 1 and values[0] not in ('', None):
            low = provider._as_float(values[0], None)

        if len(values) >= 2 and values[1] not in ('', None):
            high = provider._as_float(values[1], None)

        return low, high

    def conditions(self, provider):
        low, high = self.bounds(provider)
        column = provider.mapper.c[self.column]
        conditions = []

        if low is not None:
            conditions.append(column >= low)

        if high is not None:
            conditions.append(column <= high)

        return conditions

    def build(self, session, provider):
        column = provider.mapper.c[self.column]
        conditions = provider.conditions_except(self.name)
        low, high = self.bounds(provider)

        data_min, data_max = (
            session.query(func.min(column), func.max(column))
            .filter(*conditions)
            .one()
        )

        if data_min is None:
            data_min, data_max = 0, 0

        return {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'unit': self.unit,
            'step': self.step,
            'min': data_min,
            'max': data_max,
            'selectedMin': low if low is not None else data_min,
            'selectedMax': high if high is not None else data_max,
        }


class TextFacet(object):
    """A free text search filter (contains match)."""

    type = 'text'

    def __init__(self, name, label, column, placeholder=None):
        self.name = name
        self.label = label
        self.column = column
        self.placeholder = placeholder or ''

    def term(self, provider):
        values = provider.selected(self.name)

        if not values or not values[0]:
            return ''

        return values[0].strip()[:MAX_TEXT_LENGTH]

    def conditions(self, provider):
        term = self.term(provider)

        if not term:
            return []

        column = provider.mapper.c[self.column]

        return [column.ilike(u'%{}%'.format(term))]

    def build(self, session, provider):
        return {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'placeholder': self.placeholder,
            'value': self.term(provider),
        }


class BaseProvider(object):
    #: article number, as used by the API (e.g. ``'4'``)
    article = None
    #: block ``article_select`` slug (e.g. ``'marine-units'``)
    article_slug = None
    #: reporting cycle key / database session (e.g. ``'2024'``)
    cycle = None
    #: human readable cycle label
    cycle_label = None
    #: short cycle label, used in the result rows (e.g. ``'2024 - 2030'``)
    cycle_display = None
    #: title of the record, shown above the table
    record_title = ''
    #: database session to use (see ``wise.msfd.db.DBS``)
    session_name = None

    #: SQLAlchemy Table or mapped class exposing the data
    mapper = None
    #: default ordering of the result rows
    order_by = ()
    #: columns never selected from the database
    excluded_columns = ()
    #: columns selected but not displayed (only used when ``columns`` is empty)
    blacklist = ()
    #: columns printed raw, without glossary lookup
    blacklist_labels = ()
    #: tuple of :class:`Column`; when empty the mapper columns are displayed
    columns = ()
    #: tuple of facet instances
    facets = ()
    #: key of the :class:`Column` that groups the result rows (e.g. countries).
    #: When set, ``build_data`` also returns a ``groups`` list and the rows are
    #: ordered by this column first, so a group never mixes with another one.
    group_by = None
    #: cell transforms used by ``serialize_cell``; ``{}`` disables the global
    #: ``TRANSFORMS`` map, which is what the 2012 cycle (raw ``MarineUnitID``)
    #: needs. ``None`` keeps the default behaviour.
    cell_transforms = None

    def __init__(self, selections=None, page=0, page_size=25, sort=None,
                 direction=None, all_rows=False):
        self.selections = selections or {}
        self.page = max(self._as_int(page, 0), 0)
        self.page_size = min(
            max(self._as_int(page_size, 25), 1), MAX_PAGE_SIZE
        )
        self.sort = sort
        self.direction = (direction or 'asc').lower()
        self.all_rows = bool(all_rows)

    @staticmethod
    def _as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_float(value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def selected(self, name):
        """Return the currently selected values for a facet, as a list."""
        values = self.selections.get(name) or []

        if isinstance(values, str):
            values = [values]

        values = [v for v in values if v not in (None, '')]

        return values[:MAX_FACET_VALUES]

    def facet_by_name(self, name):
        for facet in self.facets:
            if facet.name == name:
                return facet

        return None

    # -- conditions ------------------------------------------------------
    def conditions_except(self, name):
        """Apply every *other* selection, but not the facet's own one.

        This is what makes the option lists cross filter each other.
        """
        conditions = list(self.base_conditions())

        for facet in self.facets:
            if facet.name == name:
                continue

            conditions.extend(facet.conditions(self))

        return conditions

    def base_conditions(self):
        """Conditions that always apply, independent of the facet selection.

        Providers override this to narrow the underlying table (e.g. the 2012
        Article 7 cycle keeps only the latest reported designations per
        country). It is folded into both :meth:`data_conditions` and
        :meth:`conditions_except`, so the facet option counts are computed on
        exactly the same rows as the results table.
        """
        return []

    def data_conditions(self):
        conditions = list(self.base_conditions())

        for facet in self.facets:
            conditions.extend(facet.conditions(self))

        return conditions

    # -- columns ---------------------------------------------------------
    def selectable_columns(self):
        if self.columns:
            names = []

            for column in self.columns:
                if column.static is None and column.source not in names:
                    names.append(column.source)

            keys = set(self.mapper.c.keys())

            return [self.mapper.c[name] for name in names if name in keys]

        return [c for c in self.mapper.c
                if c.name not in self.excluded_columns]

    def display_fields(self):
        return [
            c.name for c in self.selectable_columns()
            if c.name not in self.blacklist
        ]

    def build_columns(self):
        if self.columns:
            return [
                {
                    'key': column.key,
                    'label': column.label,
                    'align': column.align,
                    'format': column.format,
                    'sortable': column.sortable,
                    'expandable': column.expandable,
                    'minWidth': column.min_width,
                }
                for column in self.columns
                if not column.hidden
            ]

        return [
            {'key': field, 'label': name_as_title(field), 'align': None,
             'sortable': True}
            for field in self.display_fields()
        ]

    def column_by_key(self, key):
        for column in self.columns:
            if column.key == key:
                return column

        # dynamic columns: the key is the mapper field name
        if not self.columns and key in self.display_fields():
            return Column(key, name_as_title(key))

        return None

    # -- database --------------------------------------------------------
    def _get_session(self):
        session = db.session()

        if isinstance(session, db.MockSession):
            raise ExplorerError('MSFD database is not available')

        return session

    # -- filters ---------------------------------------------------------
    def build_filters(self):
        with db_session(self.session_name):
            session = self._get_session()

            try:
                return [facet.build(session, self) for facet in self.facets]
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to build filters')
                raise ExplorerError('MSFD database is not available')

    # -- data ------------------------------------------------------------
    def apply_sort(self, query):
        # Ordered mapping of column -> direction; a dict keeps the insertion
        # order and removes columns that would otherwise be repeated (e.g. the
        # group column also being listed in ``order_by``).
        specs = {}

        def set_order(column, direction):
            specs[column] = direction

        # The grouping column always sorts first so the rows of one group stay
        # together; the user sort is applied inside each group.
        group_column = (
            self.column_by_key(self.group_by) if self.group_by else None
        )

        if group_column is not None and group_column.source:
            set_order(self.mapper.c[group_column.source], 'asc')

        # The user sort is primary; the provider's default ``order_by`` only
        # fills in the columns it did not already cover, as a stable
        # tiebreaker. Applying it after the user sort keeps the user direction
        # when it targets a column that also appears in ``order_by``.
        column = self.column_by_key(self.sort) if self.sort else None

        # A derived column (e.g. the Article 9 region) has a source that is not
        # mapped; skip it rather than failing the request, and fall back to the
        # provider's default ordering.
        if (
            column is not None and
            column.source and
            column.source in self.mapper.c
        ):
            set_order(self.mapper.c[column.source], self.direction)

        for name in self.order_by:
            column = self.mapper.c[name]

            if column not in specs:
                set_order(column, 'asc')

        clauses = [
            col.desc() if direction == 'desc' else col.asc()
            for col, direction in specs.items()
        ]

        return query.order_by(*clauses) if clauses else query

    def build_groups(self, session, rows):
        """Group serialized rows by ``group_by`` for the current page.

        Returns a list of ``{key, label, count, meta}`` dicts in the order the
        groups appear in ``rows``. ``count`` is the total number of rows in the
        whole (filtered) result set, ``meta`` is filled by
        :meth:`build_group_meta` and can hold extra detail that is not part of
        the flat table (e.g. the country description on the 2012 cycle).
        """
        if not self.group_by:
            return None

        column = self.column_by_key(self.group_by)

        if column is None or not column.source:
            return None

        source = self.mapper.c[column.source]
        conditions = self.data_conditions()
        counts = dict(
            session.query(source, func.count())
            .filter(*conditions)
            .group_by(source)
            .all()
        )

        groups = []
        seen = set()

        for row in rows:
            cell = row.get(self.group_by) or {}
            key = cell.get('raw')

            if key in seen:
                continue

            seen.add(key)
            groups.append({
                'key': key,
                'label': cell.get('text') or to_text(key),
                'count': int(counts.get(key, 0)),
                'meta': {},
            })

        meta = self.build_group_meta(
            session, [group['key'] for group in groups]
        ) or {}

        for group in groups:
            group['meta'] = meta.get(group['key'], {})

        return groups

    def build_group_meta(self, session, group_keys):
        """Extra detail per group, keyed by the group key. Default: none."""
        return {}

    def build_data(self):
        with db_session(self.session_name):
            session = self._get_session()

            try:
                conditions = self.data_conditions()
                total = (
                    session.query(func.count())
                    .select_from(self.mapper)
                    .filter(*conditions)
                    .scalar()
                ) or 0

                page_count = (
                    int(math.ceil(total / float(self.page_size)))
                    if self.page_size else 1
                ) or 1

                columns = self.selectable_columns()
                query = session.query(*columns).filter(*conditions)
                query = self.apply_sort(query)

                if self.all_rows:
                    # Bound the whole-result download so ``all=1`` cannot
                    # return an unbounded table.
                    query = query.limit(MAX_ALL_ROWS)
                    page = 0
                    page_count = 1
                    truncated = total > MAX_ALL_ROWS
                else:
                    # Clamp before applying the OFFSET so an arbitrarily large
                    # ``page`` cannot force an expensive deep-offset scan.
                    page = min(max(self.page, 0), page_count - 1)
                    query = (
                        query.limit(self.page_size)
                        .offset(page * self.page_size)
                    )
                    truncated = False

                rows = list(query)
                serialized_rows = [
                    self.serialize_row(row) for row in rows
                ]
                groups = self.build_groups(session, serialized_rows)
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to fetch data')
                raise ExplorerError('MSFD database is not available')

        return {
            'columns': self.build_columns(),
            'rows': serialized_rows,
            'pagination': {
                'page': page,
                'pageSize': self.page_size,
                'pageCount': page_count,
                'total': int(total),
                'truncated': truncated,
            },
            'groupBy': self.group_by,
            'groups': groups,
            'meta': self.build_meta(rows),
        }

    def serialize_row(self, row):
        if not self.columns:
            return {
                field: serialize_cell(
                    getattr(row, field), field, self.blacklist_labels,
                    self.cell_transforms,
                )
                for field in self.display_fields()
            }

        out = {}

        for column in self.columns:
            if column.static is not None:
                out[column.key] = {
                    'raw': column.static,
                    'text': column.static,
                    'tooltip': None,
                    'empty': False,
                }
                continue

            value = getattr(row, column.source, None)

            if column.format == 'area':
                out[column.key] = serialize_cell(
                    format_area(value), column.key, (), {}
                )
            elif column.format == 'date':
                out[column.key] = serialize_cell(
                    format_date(value), column.key, (), {}
                )
            elif column.format == 'date_month':
                out[column.key] = serialize_cell(
                    format_month(value), column.key, (), {}
                )
            elif column.format == 'multi':
                out[column.key] = serialize_multi_cell(
                    value, column.separator
                )
            elif column.format == 'mru':
                out[column.key] = serialize_cell(
                    mru_label(value), column.key, (), {}
                )
            elif column.format == 'mru_multi':
                out[column.key] = serialize_multi_cell(
                    value, column.separator, item_labeler=mru_label
                )
            else:
                out[column.key] = serialize_cell(
                    value, column.source, self.blacklist_labels,
                    self.cell_transforms,
                )

        return out

    def build_summary(self):
        """Return the optional summary/insights payload for this provider.

        The payload is self describing so that the frontend needs a single,
        generic renderer: ``{'cards': [...], 'charts': [...]}``. Providers that
        have not (yet) implemented a summary return ``None``; the service then
        omits the ``summary`` key instead of failing.
        """
        return None

    def build_meta(self, rows):
        reported_date = None

        for row in rows:
            reported_date = getattr(row, 'ReportingDate', None)

            if reported_date:
                break

        return {
            'recordTitle': self.record_title,
            'reportedDate': format_reported_date(reported_date),
        }
