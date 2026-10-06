# pylint: skip-file
"""Provider for Article 4, 2024-2030 reporting cycle."""
from __future__ import absolute_import

from wise.msfd import sql2024
from wise.msfd.explorer.providers.base import BaseProvider, Facet
from wise.msfd.explorer.serializers import country_label, glossary_label


class Article4Cycle2024Provider(BaseProvider):
    """Marine Reporting Units reported under Article 4 for 2024-2030."""

    article = '4'
    article_slug = 'marine-units'
    cycle = '2024'
    cycle_label = '2024-2030 reporting cycle'
    record_title = 'Article 4 (Marine Units)'
    session_name = '2024'

    mapper = sql2024.t_ART4_GEO_GeographicalBoundaries
    group_field = 'CountryCode'
    order_by = ('CountryCode', 'MarineReportingUnitId')

    excluded_columns = (
        'MarineReportingUnitGeometry',
        'localId', 'namespace', 'versionId',
        'nameTxtLan', 'themaIdSch', 'beginLife',
        'rZoneIdSch', 'SnapshotId',
        'Comment', 'legisDateT',
    )

    blacklist = ('CountryCode', 'ReportingDate')

    blacklist_labels = (
        'thematicId', 'legisSName', 'nameText', 'nameTxtInt',
        'MarineReportingUnitId', 'MarineReportingUnitIdOld',
        'MarineReportingUnitName', 'legisName', 'legisLink',
    )

    facets = (
        Facet('region_subregions', 'Region and Subregion',
              'RegionSubRegion', labeler=glossary_label),
        Facet('member_states', 'Country', 'CountryCode',
              labeler=country_label),
    )
