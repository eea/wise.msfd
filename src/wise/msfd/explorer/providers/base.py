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
from contextlib import contextmanager

from sqlalchemy import func

from wise.msfd import db
from wise.msfd.db import threadlocals
from wise.msfd.explorer.serializers import (
    format_area,
    format_reported_date,
    glossary_label,
    name_as_title,
    serialize_cell,
    to_text,
)

logger = logging.getLogger('wise.msfd')


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

    __slots__ = ('key', 'label', 'source', 'align', 'format', 'static')

    def __init__(self, key, label, source=None, align=None, format=None,
                 static=None):
        self.key = key
        self.label = label
        self.source = source if source is not None else key
        self.align = align
        self.format = format
        self.static = static

    @property
    def sortable(self):
        return self.static is None


class Facet(object):
    """A multi-select (checkboxes) filter of an article/reporting cycle."""

    type = 'checkboxes'

    def __init__(self, name, label, column, labeler=None):
        self.name = name
        self.label = label
        self.column = column
        self.labeler = labeler

    def label_for(self, value):
        if self.labeler:
            return self.labeler(value)

        return glossary_label(value)

    # -- data conditions -------------------------------------------------
    def conditions(self, provider):
        """SQL conditions contributed by this facet's own selection."""
        values = provider.selected(self.name)

        if not values:
            return []

        return [provider.mapper.c[self.column].in_(values)]

    # -- serialization ---------------------------------------------------
    def build(self, session, provider):
        column = provider.mapper.c[self.column]
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
        """Return the selected ``(min, max)`` as floats, or ``(None, None)``."""
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

        return values[0].strip() if values and values[0] else ''

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

    def __init__(self, selections=None, page=0, page_size=25, sort=None,
                 direction=None, all_rows=False):
        self.selections = selections or {}
        self.page = self._as_int(page, 0)
        self.page_size = max(self._as_int(page_size, 25), 1)
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

        return [v for v in values if v not in (None, '')]

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
        conditions = []

        for facet in self.facets:
            if facet.name == name:
                continue

            conditions.extend(facet.conditions(self))

        return conditions

    def data_conditions(self):
        conditions = []

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

        return [c for c in self.mapper.c if c.name not in self.excluded_columns]

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
                    'sortable': column.sortable,
                }
                for column in self.columns
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
        column = self.column_by_key(self.sort) if self.sort else None

        if column is not None and column.source:
            sort_column = self.mapper.c[column.source]

            if self.direction == 'desc':
                return query.order_by(sort_column.desc())

            return query.order_by(sort_column.asc())

        order = [self.mapper.c[name] for name in self.order_by]

        return query.order_by(*order) if order else query

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

                columns = self.selectable_columns()
                query = session.query(*columns).filter(*conditions)
                query = self.apply_sort(query)

                if not self.all_rows:
                    query = (
                        query.limit(self.page_size)
                        .offset(self.page * self.page_size)
                    )

                rows = list(query)
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to fetch data')
                raise ExplorerError('MSFD database is not available')

        page_count = (
            int(math.ceil(total / float(self.page_size)))
            if self.page_size else 1
        ) or 1

        if self.all_rows:
            page_count = 1
            page = 0
        else:
            page = min(max(self.page, 0), page_count - 1)

        return {
            'columns': self.build_columns(),
            'rows': [self.serialize_row(row) for row in rows],
            'pagination': {
                'page': page,
                'pageSize': self.page_size,
                'pageCount': page_count,
                'total': int(total),
            },
            'meta': self.build_meta(rows),
        }

    def serialize_row(self, row):
        if not self.columns:
            return {
                field: serialize_cell(
                    getattr(row, field), field, self.blacklist_labels
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
                    format_area(value), column.key, ()
                )
            else:
                out[column.key] = serialize_cell(
                    value, column.source, self.blacklist_labels
                )

        return out

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
