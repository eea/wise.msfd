# pylint: skip-file
"""Provider for Article 9 (GES determination), 2012-2018 reporting exercise.

The 2012 data has no joined view like the later cycles. It is read from the
pair of tables the legacy explorer used:

* ``MSFD9_Descriptors`` -- one row per ``(MarineUnitID, ReportingFeature)``
  holding the GES description, thresholds, reference point and assessment
  method. This is the result grain;
* ``MSFD9_Imports`` -- the reporting metadata of the file the descriptors were
  filed in, which is where the country and the region/subregion come from
  (their codes are stored right padded, e.g. ``'DE         '``).

Features are *not* on the descriptor row: they live in ``MSFD9_Features``,
keyed by the descriptor. They are therefore exposed as a filter only (not a
column), applied with an ``EXISTS``-style sub-select against that table, so a
selected feature keeps the descriptor row without duplicating it per feature.

There is no update type on this cycle; the facet and column are omitted.
"""
from __future__ import absolute_import

from sqlalchemy import func, literal, or_, select

from wise.msfd import sql
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
)
from wise.msfd.explorer.serializers import country_label, glossary_label

COUNTRY_COLUMN = 'MSFD9_Import_ReportingCountry'
REGION_COLUMN = 'MSFD9_Import_ReportingRegion'


def _trim(column):
    """Strip the right padding of the fixed width reporting metadata codes."""
    return func.rtrim(column)


def _country(value):
    if value is None:
        return value

    return country_label(value.strip())


def _region(value):
    if value is None:
        return value

    return glossary_label(value.strip())


class FeatureFacet2012(object):
    """Feature filter backed by the ``MSFD9_Features`` child table.

    The descriptor row carries no feature, so the facet needs its own
    sub-select. ``conditions`` keeps the descriptors that have any of the
    selected features; ``build`` lists the features reachable through the
    descriptors matched by the other filters, with their row counts, so the
    option list cross filters exactly like the other facets.
    """

    type = 'checkboxes'

    #: escape character used when a reported token contains a LIKE wildcard.
    like_escape = '~'

    def __init__(self, name, label, separator=','):
        self.name = name
        self.label = label
        self.separator = separator
        self.labeler = glossary_label

    def tokens(self, value):
        if value in (None, ''):
            return []

        return [
            token.strip()
            for token in u'{}'.format(value).split(self.separator)
            if token.strip()
        ]

    @classmethod
    def _pattern(cls, token):
        token = token.replace(u' ', u'')
        token = token.replace(cls.like_escape, cls.like_escape * 2)
        token = token.replace(u'%', cls.like_escape + u'%')

        return token.replace(u'_', cls.like_escape + u'_')

    def _padded(self, column):
        separator = literal(self.separator)

        return separator + func.replace(column, u' ', u'') + separator

    def conditions(self, provider):
        values = provider.selected(self.name)

        if not values:
            return []

        features = provider.features
        padded = self._padded(features.c.FeaturesPressuresImpacts)
        conditions = []

        for value in values:
            token = self._pattern(value)

            if not token:
                continue

            pattern = u'%{0}{1}{0}%'.format(self.separator, token)
            conditions.append(padded.like(pattern, escape=self.like_escape))

        if not conditions:
            return []

        sub = select(features.c.MSFD9_Descriptor).where(or_(*conditions))

        return [provider.mapper.c.MSFD9_Descriptor_ID.in_(sub)]

    def build(self, session, provider):
        features = provider.features
        selected = set(provider.selected(self.name))
        other = provider.conditions_except(self.name)

        descriptor_ids = (
            session.query(provider.mapper.c.MSFD9_Descriptor_ID)
            .filter(*other)
        )

        # Count *descriptors*, not feature rows: a descriptor may list the
        # same feature several times (once per feature type), but selecting
        # the feature keeps the descriptor once, so the option count must
        # match the number of result rows the selection would leave.
        rows = (
            session.query(
                features.c.FeaturesPressuresImpacts,
                func.count(func.distinct(features.c.MSFD9_Descriptor)),
            )
            .filter(features.c.MSFD9_Descriptor.in_(descriptor_ids))
            .group_by(features.c.FeaturesPressuresImpacts)
            .all()
        )

        counts = {}

        for value, count in rows:
            for token in set(self.tokens(value)):
                counts[token] = counts.get(token, 0) + int(count or 0)

        options = []

        for token, count in counts.items():
            if not count and token not in selected:
                continue

            options.append({
                'value': token,
                'label': self.labeler(token),
                'count': int(count),
                'selected': token in selected,
            })

        for token in selected:
            if token in counts:
                continue

            options.append({
                'value': token,
                'label': self.labeler(token),
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


class Article9Cycle2012Provider(BaseProvider):
    """GES determinations reported under Article 9 for 2012-2018."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2012'
    cycle_label = '2012 reporting exercise'
    cycle_display = '2012 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2012'

    # Injectable source tables: tests point them at an in-memory database.
    descriptors = sql.MSFD9Descriptor.__table__
    imports = sql.MSFD9Import.__table__
    features = sql.t_MSFD9_Features
    order_by = (COUNTRY_COLUMN, REGION_COLUMN, 'ReportingFeature')

    # The reporting metadata codes are right padded; strip them (and label the
    # country/region) before they reach the table.
    cell_transforms = {
        COUNTRY_COLUMN: _country,
        REGION_COLUMN: _region,
    }

    # Free text fields whose value must be shown as reported rather than run
    # through the glossary lookup.
    blacklist_labels = (
        'MarineUnitID', 'DescriptionGES', 'ThresholdValue',
        'ThresholdValueUnit', 'ReferencePointType', 'Baseline',
        'Proportion', 'AssessmentMethod', 'DevelopmentStatus',
        'MSFD9_Import_FileName',
    )

    def __init__(self, *args, **kwargs):
        # ``MSFD9_Descriptors`` holds the result rows and ``MSFD9_Imports`` the
        # reporting metadata (country, region, reported date). The two are
        # joined in a sub-query so every column keeps its plain name, which is
        # what the provider's column/facet lookups expect (a raw ``Join`` would
        # key its columns by table name).
        self.mapper = select(
            self.descriptors.join(
                self.imports,
                self.descriptors.c.MSFD9_Descriptors_Import
                == self.imports.c.MSFD9_Import_ID,
            )
        ).subquery()
        super(Article9Cycle2012Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('Country', 'Country', COUNTRY_COLUMN, min_width=90),
        Column(
            'Region',
            'Region / Subregion',
            REGION_COLUMN,
            min_width=130,
        ),
        Column(
            'ReportingFeature',
            'GES Component / Criteria',
            'ReportingFeature',
        ),
        Column(
            'MarineUnitID',
            'Marine Reporting Unit',
            'MarineUnitID',
            min_width=120,
        ),
        Column(
            'DescriptionGES',
            'GES Description',
            'DescriptionGES',
            expandable=True,
            min_width=280,
        ),
        Column('ThresholdValue', 'Threshold value', 'ThresholdValue'),
        Column('ThresholdValueUnit', 'Threshold unit', 'ThresholdValueUnit'),
        Column(
            'ReferencePointType',
            'Reference point type',
            'ReferencePointType',
            min_width=160,
        ),
        Column('Baseline', 'Baseline', 'Baseline', expandable=True),
        Column('Proportion', 'Proportion', 'Proportion'),
        Column(
            'AssessmentMethod',
            'Assessment method',
            'AssessmentMethod',
            expandable=True,
            min_width=220,
        ),
        Column(
            'DevelopmentStatus',
            'Development status',
            'DevelopmentStatus',
            expandable=True,
            min_width=220,
        ),
        Column(
            'ReportingDate',
            'Reported date',
            'MSFD9_Import_Time',
        ),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2012 reporting exercise',
            min_width=160,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            COUNTRY_COLUMN,
            labeler=country_label,
            expression=_trim,
        ),
        Facet(
            'region_subregions',
            'Region and Subregion',
            REGION_COLUMN,
            labeler=glossary_label,
            expression=_trim,
        ),
        Facet(
            'ges_component',
            'GES Component / Criteria',
            'ReportingFeature',
        ),
        FeatureFacet2012('feature', 'Feature'),
    )
