# pylint: skip-file
"""Base data provider for the MSFD data explorer API.

A provider is the only place that knows how a given article/reporting cycle is
read from the database. It receives the current filter selections and returns
JSON friendly structures that are independent of the underlying data source,
so an Elasticsearch backed implementation can replace the SQL one later
without changing the API contract.
"""
from __future__ import absolute_import

import logging
from collections import OrderedDict
from contextlib import contextmanager

from sqlalchemy import func

from wise.msfd import db
from wise.msfd.db import threadlocals
from wise.msfd.explorer.serializers import (
    country_label,
    format_reported_date,
    glossary_label,
    name_as_title,
    serialize_cell,
    to_text,
)

logger = logging.getLogger('wise.msfd')


class ExplorerError(Exception):
    """Raised when the explorer backend cannot serve the request."""


class Facet(object):
    """Description of one filter of an article/reporting cycle."""

    def __init__(self, name, label, column, type='checkboxes', labeler=None):
        self.name = name
        self.label = label
        self.column = column
        self.type = type
        self.labeler = labeler

    def label_for(self, value):
        if self.labeler:
            return self.labeler(value)

        return glossary_label(value)


@contextmanager
def db_session(session_name):
    """Run a block of code against one of the MSFD database sessions."""
    saved = getattr(threadlocals, 'session_name', None)
    threadlocals.session_name = session_name

    try:
        yield db.session()
    finally:
        threadlocals.session_name = saved


class BaseProvider(object):
    #: article number, as used by the API (e.g. ``'4'``)
    article = None
    #: block ``article_select`` slug (e.g. ``'marine-units'``)
    article_slug = None
    #: reporting cycle key / database session (e.g. ``'2024'``)
    cycle = None
    #: human readable cycle label
    cycle_label = None
    #: title of the record, shown above the table
    record_title = ''
    #: database session to use (see ``wise.msfd.db.DBS``)
    session_name = None

    #: SQLAlchemy Table or mapped class exposing the data
    mapper = None
    #: column used to group rows into pages (one page == one country)
    group_field = None
    #: ordering of the result rows
    order_by = ()
    #: columns never selected from the database
    excluded_columns = ()
    #: columns selected but not displayed
    blacklist = ()
    #: columns printed raw, without glossary lookup
    blacklist_labels = ()
    #: tuple of :class:`Facet`
    facets = ()

    def __init__(self, selections=None, page=0):
        self.selections = selections or {}
        self.page = self._as_int(page, 0)

    @staticmethod
    def _as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def selected(self, name):
        """Return the currently selected values for a facet, as a list."""
        values = self.selections.get(name) or []

        if isinstance(values, str):
            values = [values]

        return [v for v in values if v]

    # -- columns ---------------------------------------------------------
    def selectable_columns(self):
        return [c for c in self.mapper.c if c.name not in self.excluded_columns]

    def display_fields(self):
        return [
            c.name for c in self.selectable_columns()
            if c.name not in self.blacklist
        ]

    def build_columns(self):
        return [
            {'key': field, 'label': name_as_title(field)}
            for field in self.display_fields()
        ]

    # -- filters ---------------------------------------------------------
    def _facet_conditions(self, facet):
        """Apply every *other* selection, but not the facet's own one.

        This is what makes the option lists cross filter each other.
        """
        conditions = []

        for other in self.facets:
            if other.name == facet.name:
                continue

            values = self.selected(other.name)

            if values:
                conditions.append(self.mapper.c[other.column].in_(values))

        return conditions

    def _get_session(self):
        session = db.session()

        if isinstance(session, db.MockSession):
            raise ExplorerError('MSFD database is not available')

        return session

    def build_filters(self):
        with db_session(self.session_name):
            session = self._get_session()

            try:
                return [
                    self._build_facet(session, facet)
                    for facet in self.facets
                ]
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to build filters')
                raise ExplorerError('MSFD database is not available')

    def _build_facet(self, session, facet):
        column = self.mapper.c[facet.column]
        conditions = self._facet_conditions(facet)
        selected = set(self.selected(facet.name))

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
                'label': to_text(facet.label_for(value)),
                'count': int(count or 0),
                'selected': value in selected,
            })

        # keep selected values visible even when they dropped to zero
        for value in selected:
            if value in seen:
                continue

            options.append({
                'value': value,
                'label': to_text(facet.label_for(value)),
                'count': 0,
                'selected': True,
            })

        options.sort(key=lambda option: (option['label'] or '').lower())

        return {
            'name': facet.name,
            'label': facet.label,
            'type': facet.type,
            'options': options,
        }

    # -- data ------------------------------------------------------------
    def data_conditions(self):
        conditions = []

        for facet in self.facets:
            values = self.selected(facet.name)

            if values:
                conditions.append(self.mapper.c[facet.column].in_(values))

        return conditions

    def build_data(self):
        with db_session(self.session_name):
            session = self._get_session()

            try:
                columns = self.selectable_columns()
                order = [self.mapper.c[name] for name in self.order_by]
                query = (
                    session.query(*columns)
                    .filter(*self.data_conditions())
                    .order_by(*order)
                )
                rows = list(query)
            except ExplorerError:
                raise
            except Exception:
                session.rollback()
                logger.exception('MSFD explorer: unable to fetch data')
                raise ExplorerError('MSFD database is not available')

        groups = OrderedDict()

        for row in rows:
            key = getattr(row, self.group_field)
            groups.setdefault(key, []).append(row)

        countries = sorted(groups.keys())
        page_count = len(countries)
        page = min(max(self.page, 0), page_count - 1) if page_count else 0
        current = countries[page] if page_count else None

        fields = self.display_fields()
        current_rows = groups.get(current, [])

        return {
            'columns': self.build_columns(),
            'rows': [self.serialize_row(row, fields) for row in current_rows],
            'pagination': {'page': page, 'pageCount': page_count},
            'meta': self.build_meta(current, current_rows),
        }

    def serialize_row(self, row, fields=None):
        fields = fields or self.display_fields()

        return {
            field: serialize_cell(
                getattr(row, field), field, self.blacklist_labels
            )
            for field in fields
        }

    def build_meta(self, current_country, rows):
        reported_date = None

        for row in rows:
            reported_date = getattr(row, 'ReportingDate', None)

            if reported_date:
                break

        return {
            'recordTitle': self.record_title,
            'reportedDate': format_reported_date(reported_date),
            'country': country_label(current_country),
            'countryCode': current_country,
        }
