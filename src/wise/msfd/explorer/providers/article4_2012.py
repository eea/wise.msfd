# pylint: skip-file
"""Provider for Article 4, 2012-2018 reporting cycle.

The 2012 data source is the pair of legacy tables used by the old explorer:

* ``MSFD4_GegraphicalAreasID`` -- one row per marine reporting unit
  (``MarineUnitID``), its region (``RegionSubRegions``), the kind of area
  (``AreaType``: region, subregion, marine waters part, subdivision or
  assessment area) and the name reported in the marine units sheet
  (``MarineUnits_ReportingAreas``);
* ``MSFD4_GeograpicalAreasDescription`` -- the free text description the member
  state filed for its marine waters (region/subregion, subdivisions and
  assessment areas), one row per reporting import.

The redesigned explorer exposes the reporting units, but this cycle is rendered
grouped by country: every country header can be expanded to show the free text
description, mirroring the way the legacy form showed the description record
above the list of marine reporting units. That is why this provider is the only
Article 4 one that declares ``group_by``.

Unlike 2018/2024 the 2012 cycle has no area size nor legislation, so those
columns are absent. ``cell_transforms = {}`` disables the global ``TRANSFORMS``
map, which would otherwise rewrite the ``MarineUnitID`` values into
``"No name available (DE_ANS)"``.
"""
from __future__ import absolute_import

from wise.msfd import sql
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    TextFacet,
)
from wise.msfd.explorer.serializers import country_label, glossary_label


class Article4Cycle2012Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2012-2018."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2012'
    cycle_label = '2012-2018 reporting cycle'
    cycle_display = '2012 - 2018'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2012'

    mapper = sql.t_MSFD4_GegraphicalAreasID
    order_by = ('MemberState', 'MarineUnitID')

    # ``MarineUnitID`` is in the global ``TRANSFORMS``; this cycle wants the
    # raw identifiers, so the whole transform map is disabled for the cells.
    cell_transforms = {}

    blacklist_labels = (
        'MarineUnitID', 'MarineUnits_ReportingAreas', 'AreaType',
    )

    # Rows are shown grouped by country; the ``Country`` column is only used to
    # build the group headers, so it is hidden from the table itself.
    group_by = 'MemberState'

    columns = (
        Column(
            'MarineUnitID',
            'Marine Reporting Unit ID',
            'MarineUnitID',
        ),
        Column(
            'MarineUnits_ReportingAreas',
            'Marine Reporting Unit Name',
            'MarineUnits_ReportingAreas',
        ),
        Column(
            'RegionSubRegions',
            'Region / Subregion',
            'RegionSubRegions',
        ),
        Column('AreaType', 'Area Type', 'AreaType'),
        Column('MemberState', 'Country', 'MemberState', hidden=True),
        Column(
            'ReportingCycle',
            'Reporting cycle',
            static='2012 - 2018',
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'MemberState',
            labeler=country_label,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            'RegionSubRegions',
            labeler=glossary_label,
        ),
        Facet(
            'area_types',
            'Area Type',
            'AreaType',
            labeler=glossary_label,
        ),
        TextFacet(
            'mru_id',
            'MRU identifier (ID)',
            'MarineUnitID',
            placeholder='Search by MRU identifier...',
        ),
        TextFacet(
            'mru_name',
            'MRU name',
            'MarineUnits_ReportingAreas',
            placeholder='Search by MRU name...',
        ),
    )

    def build_group_meta(self, session, group_keys):
        """Country description text, keyed by the member state code."""
        keys = [key for key in group_keys if key]

        if not keys:
            return {}

        area_ids = self.mapper
        descr = sql.t_MSFD4_GeograpicalAreasDescription

        # Each country reports a single import; map country -> import id first,
        # then fetch the description text for those imports. Two small queries
        # avoid joining/aggregating the wide text columns.
        import_by_country = {}

        for country, import_id in (
            session.query(
                area_ids.c.MemberState,
                area_ids.c.MSFD4_GegraphicalAreasID_Import,
            )
            .filter(area_ids.c.MemberState.in_(keys))
            .distinct()
            .all()
        ):
            import_by_country.setdefault(country, import_id)

        import_ids = [
            import_id for import_id in import_by_country.values()
            if import_id is not None
        ]
        descriptions = {}

        if import_ids:
            for import_id, region, subdivisions, assessment_areas in (
                session.query(
                    descr.c.MSFD4_GeograpicalAreasDescription_Import,
                    descr.c.RegionSubregion,
                    descr.c.Subdivisions,
                    descr.c.AssessmentAreas,
                ).filter(
                    descr.c.MSFD4_GeograpicalAreasDescription_Import.in_(
                        import_ids
                    )
                )
            ):
                descriptions[import_id] = (
                    region, subdivisions, assessment_areas
                )

        labels = (
            ('region', u'Region / Subregion'),
            ('subdivisions', u'Subdivisions'),
            ('assessment_areas', u'Assessment areas'),
        )
        meta = {}

        for country, import_id in import_by_country.items():
            values = descriptions.get(import_id)

            if not values:
                continue

            fields = []

            for (key, label), value in zip(labels, values):
                if value and str(value).strip():
                    fields.append({
                        'key': key,
                        'label': label,
                        'value': str(value).strip(),
                    })

            if fields:
                meta[country] = {'fields': fields}

        return meta
