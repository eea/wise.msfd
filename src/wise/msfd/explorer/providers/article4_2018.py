# pylint: skip-file
"""Provider for Article 4, 2018-2024 reporting cycle.

The 2018 data source is the ``MRUs_Publication`` table. It predates the
``MarineReportingUnit_Publication`` table used for 2024-2030 and names some
fields differently, but carries the same information the redesigned explorer
exposes: the MRU identifier (``thematicId``), its name (``nameTxtInt``), the
region/subregion (``rZoneId``), the size in km\u00b2 (``Area``),
the legislation short name (``legisSName``) and the name in the national
language (``nameText``).

Note: the ``MRUsPublication`` model declares a ``Region`` column that does not
exist in the database. Only the columns referenced below are ever selected, so
the stale mapping is harmless as long as it is not touched.
"""
from __future__ import absolute_import

from wise.msfd import sql2018
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    RangeFacet,
    TextFacet,
    TogglesFacet,
)
from wise.msfd.explorer.serializers import (country_label, glossary_label,
                                            to_text)


class Article4Cycle2018Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2018-2024."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2018'
    cycle_label = '2018-2024 reporting cycle'
    cycle_display = '2018 - 2024'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2018'

    # ``MRUsPublication`` is a mapped class, the explorer expects a Table.
    mapper = sql2018.MRUsPublication.__table__
    order_by = ('Country', 'thematicId')

    # Fields whose reported value is shown as-is rather than run through the
    # glossary label lookup.
    blacklist_labels = ('thematicId', 'legisSName', 'nameTxtInt', 'nameText')

    columns = (
        Column(
            'thematicId',
            'Marine Reporting Unit ID',
            'thematicId',
        ),
        Column(
            'nameTxtInt',
            'Marine Reporting Unit Name',
            'nameTxtInt',
        ),
        Column('rZoneId', 'Region / Subregion', 'rZoneId'),
        Column(
            'Area',
            u'Area (km\u00b2)',
            'Area',
            align='right',
            format='area',
        ),
        Column('legisSName', 'Legislation', 'legisSName'),
        Column(
            'ReportingCycle',
            'Reporting cycle',
            static='2018 - 2024',
        ),
        Column('nameText', 'National name', 'nameText'),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'Country',
            labeler=country_label,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            'rZoneId',
            labeler=glossary_label,
        ),
        RangeFacet(
            'area',
            u'Area (km\u00b2)',
            'Area',
            unit=u'km\u00b2',
        ),
        TextFacet(
            'mru_id',
            'MRU identifier (ID)',
            'thematicId',
            placeholder='Search by MRU identifier...',
        ),
        TextFacet(
            'mru_name',
            'MRU name',
            'nameTxtInt',
            placeholder='Search by MRU name...',
        ),
        TogglesFacet(
            'legislation',
            'Legislation short name',
            'legisSName',
            # show the reported value as-is rather than a glossary label
            labeler=to_text,
        ),
    )
