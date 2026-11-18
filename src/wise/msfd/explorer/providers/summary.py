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

import re

from sqlalchemy import case, distinct, func

from wise.msfd.explorer.serializers import glossary_label, to_text

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

    ``orientation`` is ``'v'`` (categories on the x axis) or ``'h'``
    (categories on the y axis). The value axis is always numeric; the
    frontend only reads the fields present here and picks the axes from
    ``orientation``.
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


def median(values):
    """Middle value of ``values`` (mean of the two middle ones when even).

    Computed in Python because neither SQL Server (before
    ``PERCENTILE_CONT``) nor the SQLite test harness offers a portable median
    aggregate.
    """
    values = sorted(values)

    if not values:
        return None

    middle = len(values) // 2

    if len(values) % 2:
        return values[middle]

    return (values[middle - 1] + values[middle]) / 2.0


def area_stats(session, mapper, conditions, size):
    """Sum/median/min/max of the area column, ignoring rows without a size.

    Rows with a missing size are excluded so they never pollute the sum, the
    median or the distribution. Returns a dict of JSON friendly floats.
    """
    total, minimum, maximum = (
        session.query(
            func.sum(size),
            func.min(size),
            func.max(size),
        )
        .select_from(mapper)
        .filter(*conditions)
        .filter(size.isnot(None))
        .one()
    )

    sizes = (
        session.query(size)
        .select_from(mapper)
        .filter(*conditions)
        .filter(size.isnot(None))
        .all()
    )

    return {
        'total': number(total),
        'median': number(median([row[0] for row in sizes])),
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


#: A reported token counts as a link when it starts with a scheme or with a
#: bare ``www.`` host. The link fields also carry placeholders ("Metadata not
#: available", "nvt", "de") and prose, so "not empty" is not the same as
#: "links somewhere"; the check stays offline on purpose, because probing the
#: URLs would make the panel as slow as its slowest reporting country.
LINK_RE = re.compile(r'^(https?://|www\.)', re.IGNORECASE)

#: GES descriptors are reported either as the descriptor code itself (``D5``)
#: or as a component / criterion below it (``D5C1``, ``D1.2``, ``D1B``); the
#: descriptor is the ``D<number>`` prefix.
DESCRIPTOR_RE = re.compile(r'^(D\d+)', re.IGNORECASE)

#: the glossary labels GES codes by kind (``(Descriptor) D1 - ...``); a chart
#: that only plots descriptors does not need that reminder on every bar.
GLOSSARY_KIND_RE = re.compile(r'^\((?:Descriptor|Criteria)\)\s*')


def descriptor_label(code):
    """Chart label for a descriptor code (``D5 - Eutrophication``)."""
    return GLOSSARY_KIND_RE.sub('', glossary_label(code))


def link_counts(session, mapper, conditions, column, separator=';'):
    """``(valid, reported)`` link token counts of a packed link column.

    A row can file several links in one ``';'``-joined cell; every token
    counts once per row, the same rule the multi-value facets use, so a cell
    that repeats a link does not inflate the number. ``valid`` keeps only the
    tokens that look like a reference (:data:`LINK_RE`), ``reported`` is every
    token and is the denominator of the "N of M" card.
    """
    counts = explode_counts(
        session, mapper, conditions, column, separator=separator
    )

    valid = sum(
        count for token, count in counts.items()
        if LINK_RE.match(token)
    )

    return valid, sum(counts.values())


def descriptors_in(value, separator=';'):
    """The GES descriptors one packed code cell refers to.

    A cell may carry several values (``'D5C1;D5C2'``), and a value may name
    several descriptors at once (``'D6/D1'``), so both are exploded. Codes
    below a descriptor (``D5C1``, ``D1.2``, ``D1B``) are reduced to their
    descriptor. Anything else a member state filed -- ``NotRelevant``, or the
    bare criterion numbers some 2018 files carry -- is dropped rather than
    counted as a descriptor nobody reported.
    """
    found = []

    for token in token_list(value, separator):
        for part in token.split('/'):
            match = DESCRIPTOR_RE.match(part.strip().upper())

            if match and match.group(1) not in found:
                found.append(match.group(1))

    return found


def covered_descriptors(session, mapper, conditions, column,
                        separator=';'):
    """The distinct GES descriptors the matching rows report."""
    covered = set()

    rows = (
        session.query(column)
        .select_from(mapper)
        .filter(*conditions)
        .all()
    )

    for (value,) in rows:
        covered.update(descriptors_in(value, separator))

    return covered


def descriptor_link_counts(session, mapper, conditions, descriptor_column,
                           link_column, separator=';'):
    """``{descriptor: links}`` for the datasets-by-descriptor chart.

    A single link cannot be attributed to one descriptor: the descriptors are
    reported for the whole record (an indicator covers every descriptor it
    names), so each link of a record counts for each of its descriptors. A
    record filed under two descriptors therefore contributes its links to
    both, and the bars can add up to more than the link total.
    """
    counts = {}

    rows = (
        session.query(descriptor_column, link_column)
        .select_from(mapper)
        .filter(*conditions)
        .all()
    )

    for descriptor_value, link_value in rows:
        links = len(token_list(link_value, separator))

        if not links:
            continue

        for descriptor in descriptors_in(descriptor_value, separator):
            counts[descriptor] = counts.get(descriptor, 0) + links

    return counts


def descriptor_points(counts, labeler=None):
    """Chart points for a ``{descriptor: count}`` mapping, ``D1`` first.

    Descriptors are ordered by number (``D2`` before ``D10``), not by size:
    the panel is read against the Directive's descriptor list, and a stable
    order makes two reporting cycles easy to compare.
    """
    points = []

    for descriptor in sorted(counts, key=lambda code: int(code[1:])):
        label = labeler(descriptor) if labeler else descriptor
        points.append({
            'label': to_text(label),
            'value': int(counts[descriptor]),
        })

    return points


def size_bucket_expr(size):
    """SQL ``CASE`` assigning each size to one :data:`SIZE_BUCKETS` bucket."""
    return case(
        (size < 1000, SIZE_BUCKETS[0][0]),
        (size < 10000, SIZE_BUCKETS[1][0]),
        (size < 50000, SIZE_BUCKETS[2][0]),
        (size < 100000, SIZE_BUCKETS[3][0]),
        (size <= 250000, SIZE_BUCKETS[4][0]),
        else_=SIZE_BUCKETS[5][0],
    )


def size_distribution_points(session, mapper, conditions, size):
    """Bar-chart points for the MRU size distribution.

    Missing sizes are skipped.
    """
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
