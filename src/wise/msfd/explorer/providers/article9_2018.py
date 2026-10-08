# pylint: skip-file
"""Provider for Article 9 (GES determination), 2018-2024 reporting exercise.

The 2018 data source is ``dbo.V_ART9_GES_2018``, the view that joins the GES
component to its determination, features and marine reporting units. It
carries one row per reported determination (a component can be reported
several times, and each determination can span several features and marine
reporting units), which is what the redesigned explorer shows.

``Features`` packs several codes into one cell joined by ``,``, so that filter
uses :class:`MultiValueFacet`; ``GESComponent`` holds a single code and stays a
plain facet.
"""
from __future__ import absolute_import

from wise.msfd import sql2018
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.serializers import country_label, glossary_label, to_text


class Article9Cycle2018Provider(BaseProvider):
    """GES determinations reported under Article 9 for 2018-2024."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2018'
    cycle_label = '2018 reporting exercise'
    cycle_display = '2018 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2018'

    mapper = sql2018.t_V_ART9_GES_2018
    order_by = ('CountryCode', 'Region', 'GESComponent')

    # Free text / already human readable fields shown as reported.
    blacklist_labels = (
        'MarineReportingUnit', 'GESDescription', 'JustificationDelay',
        'JustificationNonUse', 'DeterminationDate', 'UpdateType',
    )

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column('Region', 'Region / Subregion', 'Region'),
        Column('GESComponent', 'GES Component / Criteria', 'GESComponent'),
        Column(
            'Features',
            'Feature(s)',
            'Features',
            format='multi',
            separator=',',
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
        Column('UpdateType', 'Update type', 'UpdateType', min_width=170),
        Column('DeterminationDate', 'Determination date', 'DeterminationDate'),
        Column('ReportingDate', 'Reported date', 'ReportingDate'),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2018 reporting exercise',
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
            'UpdateType',
            # the reported value is already human readable
            labeler=to_text,
        ),
        Facet(
            'ges_component',
            'GES Component / Criteria',
            'GESComponent',
        ),
        MultiValueFacet(
            'feature',
            'Feature',
            'Features',
            separator=',',
        ),
    )
