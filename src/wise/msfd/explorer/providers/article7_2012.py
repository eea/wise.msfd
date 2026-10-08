# pylint: skip-file
"""Provider for Article 7 (Competent Authorities), 2012 reporting exercise.

The authority or authorities a Member State designates for the implementation
of the Directive are reported once, under the 2012 reporting exercise
(``MS_CompetentAuthorities``). Unlike the other explorer articles there is no
per-cycle data: the explorer exposes a single reporting period, "2012 reporting
exercise", which the frontend renders as a static sidebar entry instead of the
reporting cycle dropdown.

A country may file the same authority several times over time (the unique key of
the table is ``C_CD, MSCACode, ReportingDate``). The legacy explorer shows only
the designations of a country's most recent report, and this provider reproduces
that cut through :meth:`base_conditions`, so the results table and every facet
count agree.

The table has no region column, but the redesigned explorer still offers a
Region and Subregion filter: each country is mapped to the marine regions it
reports marine units under in Article 4 (``MSFD4_GegraphicalAreasID``), and a
selected region keeps the authorities of those member states. A country that
spans several regions (e.g. France) therefore belongs to each of them.
"""
from __future__ import absolute_import

from sqlalchemy import func, select

from wise.msfd import db, sql
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
)
from wise.msfd.explorer.serializers import country_label, glossary_label

# ``GES_LABELS.countries`` (used by ``country_label``) has no entry for a
# couple of codes that still reported competent authorities, so complete it
# locally rather than falling back to the bare code in the results table.
COUNTRY_FALLBACKS = {
    'CZ': 'Czechia',
    'LU': 'Luxembourg',
}


def _country_label(code):
    """Country label for a ``C_CD`` code, completed with local fallbacks."""
    if not code:
        return code

    label = country_label(code)

    if label == code:
        return COUNTRY_FALLBACKS.get(code, code)

    return label


class CountryRegionFacet(object):
    """Region/Subregion filter derived from the Article 4 marine units.

    The competent authorities table carries no region, so both the option list
    and the filter are built from the country -> region mapping in
    ``MSFD4_GegraphicalAreasID``. The facet cross filters like every other one:
    its own selection is excluded from the option counts, so the counts follow
    the rest of the filters.
    """

    type = 'checkboxes'

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def conditions(self, provider):
        selected = provider.selected(self.name)

        if not selected:
            return []

        _, region_countries = provider.country_regions(db.session())
        countries = set()

        for region in selected:
            countries.update(region_countries.get(region, ()))

        return [provider.mapper.c.C_CD.in_(sorted(countries))]

    def build(self, session, provider):
        selected = set(provider.selected(self.name))
        conditions = provider.conditions_except(self.name)
        _, region_countries = provider.country_regions(session)

        rows = (
            session.query(provider.mapper.c.C_CD, func.count())
            .filter(*conditions)
            .group_by(provider.mapper.c.C_CD)
            .all()
        )
        country_counts = dict(rows)

        options = []

        for region, countries in region_countries.items():
            count = sum(
                country_counts.get(country, 0) for country in countries
            )

            if not count and region not in selected:
                continue

            options.append({
                'value': region,
                'label': glossary_label(region),
                'count': int(count),
                'selected': region in selected,
            })

        # Keep a selected region visible even when it dropped to zero rows.
        for region in selected:
            if not any(option['value'] == region for option in options):
                options.append({
                    'value': region,
                    'label': glossary_label(region),
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


class Article7Cycle2012Provider(BaseProvider):
    """Competent authorities reported under Article 7 (2012 exercise)."""

    article = '7'
    article_slug = 'competent-authorities'
    cycle = '2012'
    cycle_label = '2012 reporting exercise'
    cycle_display = '2012'
    record_title = 'Article 7 (Competent Authorities)'
    session_name = '2012'

    mapper = sql.t_MS_CompetentAuthorities
    order_by = ('C_CD', 'CompetentAuthorityName')

    # The results table shows the country as a readable name derived from
    # ``C_CD`` (the stored ``Country`` text mixes English and national names,
    # e.g. "Espa\u00f1a", "Lietuva"); every other field is printed as reported.
    cell_transforms = {'C_CD': _country_label}

    # The authority free-text fields are printed as reported; a stray value must
    # not be rewritten through the glossary lookup in ``serialize_cell``.
    blacklist_labels = (
        'Country', 'MSCACode', 'Auth_CD', 'CompetentAuthorityName',
        'CompetentAuthorityNameNL', 'Acronym', 'LegalStatus', 'City',
        'URL_CA', 'Responsibilities', 'Membership', 'Reference',
    )

    # ``min_width`` gives each column a readable floor: the browser still
    # sizes columns from their content, but the table scrolls horizontally
    # instead of squeezing free-text columns down to one word per line.
    columns = (
        Column('Country', 'Country', 'C_CD', min_width=90),
        Column(
            'CompetentAuthorityName',
            'Competent authority name',
            'CompetentAuthorityName',
            min_width=220,
        ),
        Column(
            'CompetentAuthorityNameNL',
            'Competent authority name (national language)',
            'CompetentAuthorityNameNL',
            min_width=220,
        ),
        Column('Acronym', 'Acronym', 'Acronym', min_width=110),
        Column('MSCACode', 'MSCA code', 'MSCACode', min_width=130),
        Column(
            'LegalStatus',
            'Legal status',
            'LegalStatus',
            expandable=True,
            min_width=200,
        ),
        Column('City', 'City', 'City', min_width=120),
        Column('URL', 'URL', 'URL_CA', min_width=200),
        Column(
            'ReportingDate',
            'Reported date',
            'ReportingDate',
            min_width=130,
        ),
        Column(
            'Responsibilities',
            'Responsibilities',
            'Responsibilities',
            expandable=True,
            min_width=200,
        ),
        Column(
            'Membership',
            'Membership',
            'Membership',
            expandable=True,
            min_width=180,
        ),
        Column(
            'Reference',
            'Reference',
            'Reference',
            expandable=True,
            min_width=180,
        ),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2012 reporting exercise',
            min_width=150,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'C_CD',
            labeler=_country_label,
        ),
        CountryRegionFacet('region_subregions', 'Region and Subregion'),
    )

    def __init__(self, *args, **kwargs):
        super(Article7Cycle2012Provider, self).__init__(*args, **kwargs)
        self._country_regions_cache = None

    def country_regions(self, session):
        """Return ``(country -> regions, region -> countries)`` mappings.

        Built once per request from the Article 4 marine units. Countries or
        regions without a code are ignored.
        """
        if self._country_regions_cache is None:
            regions = sql.t_MSFD4_GegraphicalAreasID
            rows = (
                session.query(
                    regions.c.MemberState, regions.c.RegionSubRegions
                )
                .distinct()
                .all()
            )

            country_regions = {}
            region_countries = {}

            for country, region in rows:
                if not country or not region:
                    continue

                country_regions.setdefault(country, set()).add(region)
                region_countries.setdefault(region, set()).add(country)

            self._country_regions_cache = (country_regions, region_countries)

        return self._country_regions_cache

    def base_conditions(self):
        """Keep only the latest reported designations of each country."""
        ca = self.mapper
        inner = ca.alias('ca_latest')

        latest = (
            select(func.max(inner.c.ReportingDate))
            .where(inner.c.C_CD == ca.c.C_CD)
            .correlate(ca)
            .scalar_subquery()
        )

        return [ca.c.ReportingDate == latest]
