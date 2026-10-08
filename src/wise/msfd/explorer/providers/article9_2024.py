# pylint: skip-file
"""Provider for Article 9 (GES determination), 2024-2030 reporting exercise.

The 2024 data source is the ``dbo.V_ART9_GES_2024`` view: it already joins the
GES component, its determination and the reported features, and carries the
region, the marine reporting unit, the update type and both justification
fields, so the explorer can expose one row per reported determination without
recreating any of those joins in the provider.

Unlike the 2018-2024 cycle, ``GEScomponent`` and ``Feature`` pack several codes
into one cell joined by ``;``, which is why those two filters use
:class:`MultiValueFacet`.
"""
from __future__ import absolute_import

from wise.msfd import sql2024
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.serializers import country_label, glossary_label, to_text


class Article9Cycle2024Provider(BaseProvider):
    """GES determinations reported under Article 9 for 2024-2030."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2024'
    cycle_label = '2024 reporting exercise'
    cycle_display = '2024 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2024'

    mapper = sql2024.t_V_ART9_GES_2024
    order_by = ('CountryCode', 'Region', 'GEScomponent')

    # Free text / already human readable fields whose value must be shown as
    # reported instead of run through the glossary label lookup.
    blacklist_labels = (
        'MarineReportingUnit', 'GESDescription', 'JustificationDelay',
        'JustificationNonUse', 'DeterminationDate', 'UpdateTypeGES',
    )

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column('Region', 'Region / Subregion', 'Region'),
        Column(
            'GEScomponent',
            'GES Component / Criteria',
            'GEScomponent',
            format='multi',
            separator=';',
        ),
        Column(
            'Feature',
            'Feature(s)',
            'Feature',
            format='multi',
            separator=';',
        ),
        Column(
            'MarineReportingUnit',
            'Marine Reporting Unit',
            'MarineReportingUnit',
            min_width=150,
        ),
        Column(
            'GESDescription',
            'GES Description',
            'GESDescription',
            expandable=True,
            min_width=280,
        ),
        Column(
            'JustificationDelay',
            'Justification for delay',
            'JustificationDelay',
            expandable=True,
            min_width=200,
        ),
        Column(
            'JustificationNonUse',
            'Justification for non-use',
            'JustificationNonUse',
            expandable=True,
            min_width=200,
        ),
        Column('UpdateTypeGES', 'Update type', 'UpdateTypeGES', min_width=170),
        Column('DeterminationDate', 'Determination date', 'DeterminationDate'),
        Column('ReportingDate', 'Reported date', 'ReportingDate'),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2024 reporting exercise',
            min_width=160,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'CountryCode',
            labeler=country_label,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            'Region',
            labeler=glossary_label,
        ),
        Facet(
            'update_type',
            'Update type',
            'UpdateTypeGES',
            # the reported value is already human readable
            labeler=to_text,
        ),
        MultiValueFacet(
            'ges_component',
            'GES Component / Criteria',
            'GEScomponent',
            separator=';',
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Feature',
            separator=';',
        ),
    )
