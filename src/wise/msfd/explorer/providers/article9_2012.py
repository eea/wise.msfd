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
keyed by the descriptor. They feed both the Feature filter, applied with an
``EXISTS``-style sub-select against that table (so a selected feature keeps the
descriptor row without duplicating it per feature), and the ``Feature(s)``
column, which packs the child rows into one grouped cell per descriptor.

There is no update type on this cycle; the facet and column are omitted.
"""
from __future__ import absolute_import

from sqlalchemy import func, literal, or_, select

from wise.msfd import sql
from wise.msfd.explorer.providers.aggregates import group_concat
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
)
from wise.msfd.explorer.providers.summary import (
    bar_chart,
    card,
    distinct_count,
    group_counts,
    label_points,
    token_list,
    total_rows,
)
from wise.msfd.explorer.serializers import (
    GROUP_SEPARATOR,
    ITEM_SEPARATOR,
    TYPE_SEPARATOR,
    country_label,
    glossary_label,
    to_text,
)

COUNTRY_COLUMN = 'MSFD9_Import_ReportingCountry'
REGION_COLUMN = 'MSFD9_Import_ReportingRegion'


def _grouped_values(table, value_column, type_column, key_column, label):
    """Pack a child table into one ``feature type -> features`` cell.

    Returns a sub-query ``(key_column, label)`` with one row per distinct
    ``key_column``. Each cell is a ``GROUP_SEPARATOR`` joined list of
    ``feature type + TYPE_SEPARATOR + ITEM_SEPARATOR joined features`` records,
    which :func:`serialize_grouped_multi_cell` splits back into groups. The
    aggregate is portable (see ``aggregates.py``) so it runs on both the live
    SQL Server database and the SQLite test harness.
    """
    values = (
        select(
            table.c[key_column],
            table.c[type_column],
            table.c[value_column],
        )
        .where(table.c[value_column].isnot(None))
        .distinct()
        .order_by(table.c[type_column], table.c[value_column])
        .subquery()
    )
    per_type = (
        select(
            values.c[key_column],
            values.c[type_column],
            group_concat(
                values.c[value_column], literal(ITEM_SEPARATOR)
            ).label('items'),
        )
        .group_by(values.c[key_column], values.c[type_column])
        .subquery()
    )

    return (
        select(
            per_type.c[key_column],
            group_concat(
                func.coalesce(per_type.c[type_column], literal(u''))
                .concat(literal(TYPE_SEPARATOR))
                .concat(per_type.c['items']),
                literal(GROUP_SEPARATOR),
            ).label(label),
        )
        .group_by(per_type.c[key_column])
        .subquery()
    )


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
        # key its columns by table name). The feature child table is packed to
        # one grouped cell per descriptor and joined left, so a descriptor with
        # no feature rows is kept with an empty cell.
        feature_cell = _grouped_values(
            self.features,
            'FeaturesPressuresImpacts',
            'FeatureType',
            'MSFD9_Descriptor',
            'Feature',
        )

        self.mapper = select(
            self.descriptors.join(
                self.imports,
                self.descriptors.c.MSFD9_Descriptors_Import ==
                self.imports.c.MSFD9_Import_ID,
            ).outerjoin(
                feature_cell,
                feature_cell.c.MSFD9_Descriptor ==
                self.descriptors.c.MSFD9_Descriptor_ID,
            )
        ).subquery()
        super(Article9Cycle2012Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('Country', 'Country', COUNTRY_COLUMN, min_width=90),
        Column(
            'Region',
            'Region / Subregion',
            REGION_COLUMN,
            min_width=200,
        ),
        Column(
            'ReportingFeature',
            'GES Component / Criteria',
            'ReportingFeature',
            min_width=200,
        ),
        Column(
            'Feature',
            'Feature(s)',
            'Feature',
            format='grouped_multi',
            min_width=200,
            max_items=10,
        ),
        Column(
            'MarineUnitID',
            'Marine Reporting Unit',
            'MarineUnitID',
            format='mru',
            min_width=200,
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
            format='date',
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

    def _feature_tokens(self, session, conditions):
        """Distinct feature codes reachable through the matching descriptors.

        The descriptor row carries no feature, so the child table is queried
        with the same sub-select the feature facet uses. A feature code is
        itself comma separated (``'BirdsAll,Acidification'``), so the cell is
        exploded into tokens.
        """
        descriptor_ids = (
            session.query(self.mapper.c['MSFD9_Descriptor_ID'])
            .filter(*conditions)
        )
        rows = (
            session.query(self.features.c.FeaturesPressuresImpacts)
            .filter(self.features.c.MSFD9_Descriptor.in_(descriptor_ids))
            .all()
        )

        tokens = set()

        for (value,) in rows:
            tokens.update(token_list(value, ','))

        return tokens

    def _build_summary(self, session):
        """KPIs and charts for the Summary & insights panel.

        Four count-based cards (Marine Reporting Units, GES Components,
        Features and the reference-point coverage) and two distributions (the
        reference point type and the GES components). This cycle reports no
        update type and no justification fields, so the reference point is
        what stands in for the determination metadata. All aggregates honour
        the current facet selection but are independent of paging and
        sorting.
        """
        conditions = self.data_conditions()
        # No base cut on this cycle; kept for symmetry with the other cycles.
        base = self.base_conditions()
        mapper = self.mapper

        mru = mapper.c['MarineUnitID']
        component = mapper.c['ReportingFeature']
        reference = mapper.c['ReferencePointType']

        total = total_rows(session, mapper, conditions)

        mru_count = distinct_count(session, mapper, mru, conditions)
        mru_total = distinct_count(session, mapper, mru, base)

        component_count = distinct_count(
            session, mapper, component, conditions
        )
        component_total = distinct_count(session, mapper, component, base)

        feature_count = len(self._feature_tokens(session, conditions))
        feature_total = len(self._feature_tokens(session, base))

        reference_counts = dict(
            group_counts(session, mapper, conditions, reference)
        )
        with_reference = (
            int(reference_counts.get('LimitReferencePoint', 0))
            + int(reference_counts.get('TargetReferencePoint', 0))
        )

        reference_points = label_points(
            reference_counts.items(), to_text,
        )

        return {
            'cards': [
                card(
                    'mru_count',
                    'Marine Reporting Units',
                    int(mru_count),
                    None,
                    'MRUs match your selection',
                    [],
                    int(mru_total),
                    'tint',
                ),
                card(
                    'component_count',
                    'GES Components / Criteria',
                    int(component_count),
                    None,
                    'Components match your selection',
                    [],
                    int(component_total),
                    'th large',
                ),
                card(
                    'feature_count',
                    'Features',
                    int(feature_count),
                    None,
                    'Features match your selection',
                    [],
                    int(feature_total),
                    'tags',
                    hint='A record covering several features counts for each; '
                         'features reported alongside a selected one are '
                         'included too.',
                ),
                card(
                    'reference_points',
                    'Determinations with a reference point',
                    int(with_reference),
                    None,
                    'Limit or target reference point reported',
                    [],
                    int(total),
                    'map marker',
                ),
            ],
            'charts': [
                bar_chart(
                    'reference_point_type',
                    'Determinations by reference point type',
                    reference_points,
                    orientation='v',
                    y_label='Number of determinations',
                    hint='How many descriptors report a limit reference point, '
                         'a target reference point, or none.',
                ),
            ],
        }
