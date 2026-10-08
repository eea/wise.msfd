# pylint: skip-file
"""Derived Region/Subregion support for providers whose table has no region.

Some Article 9 base tables (and the Article 7 authorities table) carry no
region column, while the redesigned explorer still offers a Region and
Subregion filter. The region is therefore derived from the Article 4 marine
reporting units: every ``MarineReportingUnit`` id is looked up in the Marine
Reporting Unit publication of the same cycle, which maps it to its region.

A provider opts in with :class:`MruRegionMixin` by pointing it at the
Article 4 table (``region_mru_table``, ``region_mru_id_column``,
``region_region_column``) and telling it whether its own MRU column holds
one id or several ``';'``-joined ids (``packed = True``). The mixin exposes
the mapping to the :class:`MruRegionFacet`, which filters and counts like
every other facet, and to :meth:`MruRegionMixin.region_cell`, which builds
the table cell.
"""
from __future__ import absolute_import

from sqlalchemy import func, literal, or_

from wise.msfd.explorer.serializers import glossary_label, to_text


class MruRegionMixin(object):
    """Provider mixin exposing a ``MarineReportingUnit`` -> region mapping."""

    #: Article 4 MRU publication table holding the id -> region mapping.
    region_mru_table = None
    #: column of ``region_mru_table`` holding the Marine Reporting Unit id
    region_mru_id_column = None
    #: column of ``region_mru_table`` holding the region / subregion code
    region_region_column = None
    #: key of the provider column holding the MRU id(s) to map
    region_mru_column = 'MarineReportingUnit'

    _region_map = None

    def region_map(self, session):
        """Return ``(mru -> region, region -> set(mru))`` mappings.

        Built once per provider instance from the Article 4 table, so the
        result table and every facet count agree on the same mapping.
        """
        if self._region_map is None:
            table = self.region_mru_table
            id_column = table.c[self.region_mru_id_column]
            region_column = table.c[self.region_region_column]
            rows = (
                session.query(id_column, region_column)
                .distinct()
                .all()
            )

            mru_region = {}
            region_mrus = {}

            for mru_id, region in rows:
                if not mru_id or not region:
                    continue

                mru_id = to_text(mru_id)
                region = to_text(region)

                mru_region[mru_id] = region
                region_mrus.setdefault(region, set()).add(mru_id)

            self._region_map = (mru_region, region_mrus)

        return self._region_map

    def region_facet(self):
        for facet in self.facets:
            if isinstance(facet, MruRegionFacet):
                return facet

        return None

    def region_cell(self, row):
        """Serialize the derived Region cell for one mapped row."""
        facet = self.region_facet()

        if facet is None:
            return None

        value = getattr(row, facet.mru_column, None)
        mru_region, _region_mrus = self.region_map(self._get_session())
        regions = facet.regions_of(value, mru_region)

        if not regions:
            return {
                'raw': None,
                'text': None,
                'tooltip': None,
                'empty': True,
            }

        return facet.serialize(regions)


class MruRegionFacet(object):
    """Region/Subregion filter derived from the Article 4 marine units.

    Both the option list and the filter come from the id -> region mapping, so
    the facet cross filters exactly like the other ones: its own selection is
    excluded from the option counts, while a selected region stays visible even
    when it dropped to zero rows. Filtering is by MRU id, which keeps it exact
    even when a row packs several ids in one cell.
    """

    type = 'checkboxes'

    #: escape character used when a reported id contains a LIKE wildcard.
    like_escape = '~'

    def __init__(self, name, label, mru_column='MarineReportingUnit',
                 packed=False, separator=';', labeler=None):
        self.name = name
        self.label = label
        self.mru_column = mru_column
        self.packed = packed
        self.separator = separator
        self.labeler = labeler or glossary_label

    # -- token helpers ---------------------------------------------------
    def tokens(self, value):
        if value in (None, ''):
            return []

        return [
            token.strip()
            for token in to_text(value).split(self.separator)
            if token.strip()
        ]

    @classmethod
    def _pattern(cls, token):
        token = token.replace(u' ', u'')
        token = token.replace(cls.like_escape, cls.like_escape * 2)
        token = token.replace(u'%', cls.like_escape + u'%')

        return token.replace(u'_', cls.like_escape + u'_')

    def _padded(self, column):
        """``<sep>value<sep>`` with spaces removed, for whole-token LIKE."""
        normalized = func.replace(column, u' ', u'')
        separator = literal(self.separator)

        return separator + normalized + separator

    def regions_of(self, value, mru_region):
        """The distinct regions reached by the MRU id(s) of one cell."""
        if not self.packed:
            region = mru_region.get(to_text(value))

            return [region] if region else []

        regions = []

        for token in self.tokens(value):
            region = mru_region.get(token)

            if region and region not in regions:
                regions.append(region)

        return regions

    def serialize(self, regions):
        """Build the ``{raw, text, tooltip, empty}`` cell for the regions."""
        raw = self.separator.join(regions)
        labels = [to_text(self.labeler(region)) for region in regions]
        text = u', '.join(labels)

        return {
            'raw': raw,
            'text': text or None,
            'tooltip': raw if labels != regions else None,
            'empty': not text,
        }

    # -- data conditions -------------------------------------------------
    def conditions(self, provider):
        selected = provider.selected(self.name)

        if not selected:
            return []

        _mru_region, region_mrus = provider.region_map(provider._get_session())
        ids = set()

        for region in selected:
            ids.update(region_mrus.get(region, ()))

        if not ids:
            return []

        column = provider.mapper.c[self.mru_column]

        if not self.packed:
            return [column.in_(sorted(ids))]

        # one id can be packed with others in a single cell; match whole
        # tokens only, never a substring.
        padded = self._padded(column)
        conditions = []

        for mru_id in sorted(ids):
            token = self._pattern(mru_id)
            pattern = u'%{0}{1}{0}%'.format(self.separator, token)
            conditions.append(padded.like(pattern, escape=self.like_escape))

        return [or_(*conditions)]

    # -- serialization ---------------------------------------------------
    def build(self, session, provider):
        column = provider.mapper.c[self.mru_column]
        conditions = provider.conditions_except(self.name)
        selected = set(provider.selected(self.name))
        mru_region, _region_mrus = provider.region_map(session)

        rows = (
            session.query(column, func.count())
            .filter(*conditions)
            .group_by(column)
            .all()
        )

        counts = {}

        for value, count in rows:
            for region in self.regions_of(value, mru_region):
                counts[region] = counts.get(region, 0) + int(count or 0)

        options = []

        for region, count in counts.items():
            if not count and region not in selected:
                continue

            options.append({
                'value': region,
                'label': to_text(self.labeler(region)),
                'count': int(count),
                'selected': region in selected,
            })

        # keep a selected region visible even when it dropped to zero rows.
        for region in selected:
            if region in counts:
                continue

            options.append({
                'value': region,
                'label': to_text(self.labeler(region)),
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
