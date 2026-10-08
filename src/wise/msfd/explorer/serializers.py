# pylint: skip-file
"""Serialization helpers for the MSFD data explorer API.

These turn the presentation logic that the legacy explorer keeps inside
``wise.msfd.utils.print_value`` and ``wise.msfd.base.BaseUtil.name_as_title``
into plain, JSON friendly structures. No HTML is produced here; rendering is
left entirely to the frontend.
"""
from __future__ import absolute_import

import re
from datetime import date, datetime

from wise.msfd.labels import COMMON_LABELS, DISPLAY_LABELS, GES_LABELS
from wise.msfd.utils import TRANSFORMS

TAG_RE = re.compile(r'<[^>]+>')
ART11_NAME_RE = re.compile(r'^Q\d+\w\s+')


def strip_tags(value):
    """Remove HTML tags, keeping the readable text."""
    if isinstance(value, str):
        return TAG_RE.sub('', value)

    return value


def to_text(value):
    """Best effort conversion of a database value to a plain string."""
    if value is None:
        return None

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return u'{}'.format(value)


def as_json_value(value):
    """Make a database value JSON serializable."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return to_text(value)


def format_number(value):
    """Format a numeric value with thousands separators and no decimals."""
    if value is None or value == '':
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return to_text(value)

    return u'{:,.0f}'.format(number)


def format_area(value):
    """Format an area value (e.g. ``324999.6`` -> ``'325,000'``).

    The measuring unit is carried by the column label (``Area (km\u00b2)``),
    not by the cell value, so the table stays easy to scan and to sort.
    """
    return format_number(value)


def is_empty(value):
    """A value is empty when it is ``None`` or a blank string."""
    if value is None:
        return True

    if isinstance(value, str) and not value.strip():
        return True

    return False


def serialize_cell(value, field_name=None,
                   blacklist_labels=(), transforms=None):
    """Serialize one database value into a ``{raw, text, tooltip, empty}`` dict.

    The logic mirrors ``ItemDisplayForm.print_value``:

    * fields listed in ``transforms`` are transformed (e.g. ``CountryCode``);
    * fields listed in ``blacklist_labels`` are printed raw, without glossary
      lookup;
    * any other string that matches a glossary key is displayed as its label,
      with the raw code kept as a tooltip (this is what the legacy markup does
      with ``<span title="code">label</span>``).
    """
    if transforms is None:
        transforms = TRANSFORMS

    if is_empty(value):
        return {'raw': None, 'text': None, 'tooltip': None, 'empty': True}

    raw = as_json_value(value)
    text = to_text(value)
    tooltip = None

    if field_name and field_name in transforms:
        try:
            text = to_text(transforms[field_name](value))
        except Exception:
            text = to_text(value)
    elif field_name and field_name in blacklist_labels:
        text = to_text(value)
    elif isinstance(text, str) and text in COMMON_LABELS:
        label = to_text(strip_tags(COMMON_LABELS[text]))
        tooltip = text
        text = label

    return {
        'raw': raw,
        'text': text or None,
        'tooltip': tooltip,
        'empty': not text,
    }


def serialize_multi_cell(value, separator=';'):
    """Serialize a cell that packs several codes joined by ``separator``.

    Each token is run through the glossary lookup and the labels are joined
    with ``', '`` for display; the raw reported value is kept as both ``raw``
    and ``tooltip`` so the frontend can still show exactly what was filed.
    """
    if is_empty(value):
        return {'raw': None, 'text': None, 'tooltip': None, 'empty': True}

    raw = as_json_value(value)
    tokens = [
        token.strip()
        for token in to_text(value).split(separator)
        if token.strip()
    ]
    labels = [glossary_label(token) for token in tokens]
    text = u', '.join(labels)
    tooltip = to_text(value) if labels != tokens else None

    return {
        'raw': raw,
        'text': text or None,
        'tooltip': tooltip,
        'empty': not text,
    }


def name_as_title(text, article='ALL'):
    """Mirror of ``BaseUtil.name_as_title`` without needing a form instance."""
    if not text:
        return text

    labels = {}
    labels.update(DISPLAY_LABELS.get('ALL', {}))
    labels.update(DISPLAY_LABELS.get(article, {}))

    if text in labels:
        return labels[text]

    text = text.replace('_', ' ')
    text = ART11_NAME_RE.sub('', text)

    for idx in range(len(text) - 1):
        if text[idx].islower() and text[idx + 1].isupper():
            text = (text[:idx + 1] + ' ' + text[idx + 1].lower() +
                    text[idx + 2:])

    return text


def glossary_label(value, fallback=None):
    """Return the human readable label for a glossary code."""
    if value is None:
        return fallback

    default = fallback if fallback is not None else value

    return to_text(strip_tags(COMMON_LABELS.get(value, default)))


def country_label(code):
    """Return the human readable label for a country code."""
    if not code:
        return code

    countries = getattr(GES_LABELS, 'countries', {})

    return countries.get(code, code)


def format_reported_date(value):
    """Mirror of ``BaseUtil.format_reported_date``."""
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y %b %d')

    if not value:
        return 'Not available'

    return to_text(value)
