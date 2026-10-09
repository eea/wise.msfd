# pylint: skip-file
"""Shared building blocks for the Summary & insights payload.

A provider that wants a summary implements ``_build_summary(session)`` and
returns a self-describing ``{'cards': [...], 'charts': [...]}`` dict, so the
frontend can render any article/cycle with one generic component. This module
holds the pieces shared by the Article 4 cycles: the MRU size buckets, the SQL
aggregates over the area column, and the card / bar-chart constructors.

Keeping the constructors here (rather than in each provider) means a change to
the payload contract only has to be made once, and the cycle providers only
describe *which* numbers and charts they expose.
"""
from __future__ import absolute_import

from sqlalchemy import case, distinct, func

from wise.msfd.explorer.serializers import to_text

AREA_UNIT = u'km\u00b2'

#: Size distribution buckets used by the summary chart. Each entry is
#: ``(label, lower, upper)`` where ``None`` marks an open end. The buckets are
#: disjoint and cover every value; the upper bound of each label is inclusive,
#: except ``> 250,000`` which is strictly greater.
SIZE_BUCKETS = (
    (u'< 1,000', None, 1000),
    (u'1,000 \u2013 10,000', 1000, 10000),
    (u'10,000 \u2013 50,000', 10000, 50000),
    (u'50,000 \u2013 100,000', 50000, 100000),
    (u'100,000 \u2013 250,000', 100000, 250000),
    (u'> 250,000', 250000, None),
)


def number(value):
    """Return a JSON friendly ``float`` (or ``None``) for a SQL aggregate."""
    if value is None:
        return None

    return float(value)


def card(key, label, value, unit=None, caption=None, details=None,
         value_of=None, icon=None, hint=None):
    """Build one KPI card of the summary payload."""
    return {
        'key': key,
        'label': label,
        'value': value,
        'unit': unit,
        'caption': caption,
        'details': details or [],
        'valueOf': value_of,
        'icon': icon,
        'hint': hint,
    }


def bar_chart(key, title, points, orientation='v', x_label='', y_label='',
              hint=None):
    """Build one bar chart of the summary payload.

    ``orientation`` is ``'v'`` (categories on the x axis) or ``'h'`` (categories
    on the y axis). The value axis is always numeric; the frontend only reads
    the fields present here and picks the axes from ``orientation``.
    """
    return {
        'key': key,
        'type': 'bar',
        'orientation': orientation,
        'title': title,
        'xLabel': x_label,
        'yLabel': y_label,
        'hint': hint,
        'points': points,
    }


def label_points(rows, labeler=None):
    """Turn ``(value, count)`` rows into sorted chart points.

    Labels are rendered with ``labeler`` when given (e.g. ``glossary_label``)
    and always coerced to text, then sorted by descending count with the label
    as a stable tiebreaker.
    """
    points = []

    for value, count in rows:
        label = labeler(value) if labeler else value
        points.append({'label': to_text(label), 'value': int(count)})

    return sorted(points, key=lambda point: (-point['value'],
                                             point['label'] or ''))


def total_rows(session, mapper, conditions):
    """Number of rows matching the current facet selection."""
    return (
        session.query(func.count())
        .select_from(mapper)
        .filter(*conditions)
        .scalar()
    ) or 0


def area_stats(session, mapper, conditions, size):
    """Sum/average/min/max of the area column, ignoring rows without a size.

    Rows with a missing size are excluded so they never pollute the sum, the
    average or the distribution. Returns a dict of JSON friendly floats.
    """
    total, avg, minimum, maximum = (
        session.query(
            func.sum(size),
            func.avg(size),
            func.min(size),
            func.max(size),
        )
        .select_from(mapper)
        .filter(*conditions)
        .filter(size.isnot(None))
        .one()
    )
    return {
        'total': number(total),
        'avg': number(avg),
        'min': number(minimum),
        'max': number(maximum),
    }


def group_counts(session, mapper, conditions, column, skip_null=True):
    """``(value, count)`` rows grouped by ``column``.

    ``skip_null`` drops rows whose group value is ``None``; that matches the
    facet behaviour, where a null value can never be selected.
    """
    query = (
        session.query(column, func.count())
        .select_from(mapper)
        .filter(*conditions)
    )

    if skip_null:
        query = query.filter(column.isnot(None))

    return query.group_by(column).all()


def distinct_count(session, mapper, column, conditions=()):
    """Number of distinct non-null values of ``column``.

    Used for the denominator of a "N of M" KPI: the count ignores the current
    selection so the card can read e.g. ``4 / 10``.
    """
    return (
        session.query(func.count(distinct(column)))
        .select_from(mapper)
        .filter(*conditions)
        .filter(column.isnot(None))
        .scalar()
    ) or 0


def token_list(value, separator=';'):
    """The distinct, trimmed tokens packed in one cell value.

    Some cycles store several codes in one column (``'D1C2;D1C3'``); the
    tokens are de-duplicated so a cell that repeats a token still counts as
    one. Anything without a separator is a single token.
    """
    if value in (None, ''):
        return []

    seen = []

    for token in to_text(value).split(separator):
        token = token.strip()

        if token and token not in seen:
            seen.append(token)

    return seen


def explode_counts(session, mapper, conditions, column, separator=';'):
    """``{token: rows}`` for a column packing several tokens per cell.

    A row contributes 1 to every distinct token it carries, which is what
    makes the card/denominator counts and the distribution chart agree with
    the multi-value facets (they explode the same way). ``conditions`` is the
    current facet selection; pass ``()`` for the cycle-wide denominator.
    """
    rows = (
        session.query(column, func.count())
        .select_from(mapper)
        .filter(*conditions)
        .filter(column.isnot(None))
        .group_by(column)
        .all()
    )

    counts = {}

    for value, count in rows:
        for token in token_list(value, separator):
            counts[token] = counts.get(token, 0) + int(count or 0)

    return counts


def multi_distinct_count(session, mapper, column, conditions=(),
                         separator=';'):
    """Number of distinct tokens of a packed ``column``.

    The packed analogue of :func:`distinct_count`: used for the denominator of
    a "N of M" KPI.
    """
    return len(explode_counts(
        session, mapper, conditions, column, separator=separator
    ))


def size_bucket_expr(size):
    """SQL ``CASE`` assigning every size to exactly one :data:`SIZE_BUCKETS`."""
    return case(
        (size < 1000, SIZE_BUCKETS[0][0]),
        (size < 10000, SIZE_BUCKETS[1][0]),
        (size < 50000, SIZE_BUCKETS[2][0]),
        (size < 100000, SIZE_BUCKETS[3][0]),
        (size <= 250000, SIZE_BUCKETS[4][0]),
        else_=SIZE_BUCKETS[5][0],
    )


def size_distribution_points(session, mapper, conditions, size):
    """Bar-chart points for the MRU size distribution (missing sizes skipped)."""
    bucket = size_bucket_expr(size)
    counts = dict(
        session.query(bucket, func.count())
        .select_from(mapper)
        .filter(*conditions)
        .filter(size.isnot(None))
        .group_by(bucket)
        .all()
    )

    return [
        {'label': label, 'value': int(counts.get(label, 0))}
        for label, _lower, _upper in SIZE_BUCKETS
    ]
