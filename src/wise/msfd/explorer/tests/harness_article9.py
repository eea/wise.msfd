# pylint: skip-file
"""Article 9 explorer harness.

Exercises the three Article 9 providers end to end against an in-memory SQLite
database seeded with representative rows, so the risky logic (multi valued
facets, whole token matching, the 2012 feature sub select, the 2018 base-table
join, the derived regions, label transforms and the result grain) is covered
without a database server. The 2024 cycle has no reachable ``MSFD2024_public``
in the development environment, which is why the harness feeds all three
providers the same way.

The 2018 and 2024 providers read the same **base tables** the legacy
``search`` Article 9 forms read (not the ``V_ART9_GES_*`` views); the harness
seeds those tables plus the Article 4 MRU publication used to derive the
region.

Run it inside the backend container, where the package (and its label data)
imports:

    docker exec -i marine-backend-p6 /app/bin/python \
        -m wise.msfd.explorer.tests.harness_article9
"""
from __future__ import absolute_import

from datetime import datetime

from sqlalchemy import (Column, Date, DateTime, Integer, MetaData, Table,
                        Unicode, create_engine)
from sqlalchemy.orm import sessionmaker

from wise.msfd.explorer.providers.article9_2012 import (
    Article9Cycle2012Provider)
from wise.msfd.explorer.providers.article9_2018 import (
    Article9Cycle2018Provider)
from wise.msfd.explorer.providers.article9_2024 import (
    Article9Cycle2024Provider)
from wise.msfd.explorer.providers.registry import available_providers
from wise.msfd.explorer.serializers import glossary_label

# ---------------------------------------------------------------------------
# schema + fixtures
# ---------------------------------------------------------------------------
metadata = MetaData()

# -- Article 9 / 2024 base table (data.ART9_GES_GEScomponent) ----------------
art9_2024 = Table(
    'ART9_GES_GEScomponent_2024', metadata,
    Column('row_id', Integer, primary_key=True),
    Column('CountryCode', Unicode(2)),
    Column('ReportingDate', DateTime),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('JustificationDelay', Unicode),
    Column('JustificationNonUse', Unicode),
    Column('Feature', Unicode),
    Column('GESDescriptor', Unicode),
    Column('DeterminationDate', Unicode),
    Column('UpdateTypeGES', Unicode),
    Column('GESDescription', Unicode),
    Column('SnapshotId', Integer),
    Column('Comment', Unicode),
)

# -- Article 9 / 2018 base tables -------------------------------------------
art9_2018_component = Table(
    'ART9_GES_GESComponent', metadata,
    Column('Id', Integer, primary_key=True),
    Column('GESComponent', Unicode),
    Column('JustificationDelay', Unicode),
    Column('JustificationNonUse', Unicode),
    Column('IdReportedInformation', Integer),
)

art9_2018_determination = Table(
    'ART9_GES_GESDetermination', metadata,
    Column('Id', Integer, primary_key=True),
    Column('GESDescription', Unicode),
    Column('DeterminationDate', Unicode),
    Column('UpdateType', Unicode),
    Column('IdGESComponent', Integer),
)

art9_2018_feature = Table(
    'ART9_GES_GESDetermination_Feature', metadata,
    Column('Id', Integer, primary_key=True),
    Column('Feature', Unicode),
    Column('IdGESDetermination', Integer),
)

art9_2018_marine_unit = Table(
    'ART9_GES_MarineUnit', metadata,
    Column('MarineReportingUnit', Unicode, primary_key=True),
    Column('IdGESDetermination', Integer, primary_key=True),
)

reported_info = Table(
    'ReportedInformation', metadata,
    Column('Id', Integer, primary_key=True),
    Column('CountryCode', Unicode(2)),
    Column('Schema', Unicode),
    Column('ReportingDate', Date),
)

# -- Article 4 MRU publication, used to derive the region -------------------
mrus_2018 = Table(
    'MRUs_Publication', metadata,
    Column('thematicId', Unicode, primary_key=True),
    Column('rZoneId', Unicode(3)),
)

mrus_2024 = Table(
    'MarineReportingUnit_Publication', metadata,
    Column('MarineReportingUnitId', Unicode, primary_key=True),
    Column('RegionSubRegion', Unicode(3)),
)

# -- Article 9 / 2012 tables -------------------------------------------------
descriptors = Table(
    'MSFD9_Descriptors', metadata,
    Column('MSFD9_Descriptor_ID', Integer, primary_key=True),
    Column('MarineUnitID', Unicode),
    Column('ReportingFeature', Unicode),
    Column('DescriptionGES', Unicode),
    Column('ThresholdValue', Unicode),
    Column('ThresholdValueUnit', Unicode),
    Column('ReferencePointType', Unicode),
    Column('Baseline', Unicode),
    Column('Proportion', Unicode),
    Column('AssessmentMethod', Unicode),
    Column('DevelopmentStatus', Unicode),
    Column('MSFD9_Descriptors_Import', Integer),
)

imports = Table(
    'MSFD9_Imports', metadata,
    Column('MSFD9_Import_ID', Integer, primary_key=True),
    Column('MSFD9_Import_Time', DateTime),
    Column('MSFD9_Import_ReportingCountry', Unicode(11)),
    Column('MSFD9_Import_ReportingRegion', Unicode(11)),
    Column('MSFD9_Import_FileName', Unicode),
)

features = Table(
    'MSFD9_Features', metadata,
    Column('feature_id', Integer, primary_key=True),
    Column('MarineUnitID', Unicode),
    Column('ReportingFeature', Unicode),
    Column('FeaturesPressuresImpacts', Unicode),
    Column('FeatureType', Unicode),
    Column('MSFD9_Descriptor', Integer),
)

engine = create_engine('sqlite://')
metadata.create_all(engine)
session = sessionmaker(bind=engine)()


def seed():
    session.execute(art9_2024.insert(), [
        # multi valued component + feature, with stray spaces
        {'row_id': 1, 'CountryCode': 'DE', 'ReportingDate': None,
         'GEScomponent': 'D5C1; D5C2', 'Feature': 'Nutrients; Contaminants',
         'UpdateTypeGES': 'New determination',
         'MarineReportingUnit': 'ANS-DE-1; ANS-DE-2',
         'GESDescription': 'Good status', 'JustificationDelay': None,
         'JustificationNonUse': None, 'DeterminationDate': None},
        {'row_id': 2, 'CountryCode': 'DE', 'ReportingDate': None,
         'GEScomponent': 'D5C1', 'Feature': 'Nutrients',
         'UpdateTypeGES': 'New determination', 'MarineReportingUnit': 'ANS-DE-2',
         'GESDescription': 'Good status', 'JustificationDelay': 'delay',
         'JustificationNonUse': None, 'DeterminationDate': None},
        {'row_id': 3, 'CountryCode': 'FR', 'ReportingDate': datetime(2018, 7, 6, 11, 2, 18),
         'GEScomponent': 'D1C1', 'Feature': 'Birds_all',
         'UpdateTypeGES': 'Modified from reported determination',
         'MarineReportingUnit': 'MWE-FR-1', 'GESDescription': 'Partial',
         'JustificationDelay': None, 'JustificationNonUse': None,
         'DeterminationDate': '202401'},
    ])

    session.execute(mrus_2024.insert(), [
        {'MarineReportingUnitId': 'ANS-DE-1', 'RegionSubRegion': 'ANS'},
        {'MarineReportingUnitId': 'ANS-DE-2', 'RegionSubRegion': 'ANS'},
        {'MarineReportingUnitId': 'MWE-FR-1', 'RegionSubRegion': 'MWE'},
    ])

    # FI has an old import (Id 1) and a newer one (Id 5); only the newest is
    # shown. SE has a single import.
    session.execute(reported_info.insert(), [
        {'Id': 5, 'CountryCode': 'FI', 'Schema': 'MSFD_Art9',
         'ReportingDate': datetime(2018, 7, 6, 11, 2, 18)},
        {'Id': 1, 'CountryCode': 'FI', 'Schema': 'MSFD_Art9',
         'ReportingDate': None},
        {'Id': 2, 'CountryCode': 'SE', 'Schema': 'MSFD_Art9',
         'ReportingDate': None},
    ])
    session.execute(art9_2018_component.insert(), [
        {'Id': 1, 'GESComponent': 'D5C1', 'JustificationDelay': None,
         'JustificationNonUse': None, 'IdReportedInformation': 5},
        {'Id': 2, 'GESComponent': 'D5C2', 'JustificationDelay': None,
         'JustificationNonUse': 'nonuse', 'IdReportedInformation': 5},
        {'Id': 3, 'GESComponent': 'D1C1', 'JustificationDelay': None,
         'JustificationNonUse': None, 'IdReportedInformation': 2},
        # filed under the old FI import; must never surface
        {'Id': 9, 'GESComponent': 'D9C9', 'JustificationDelay': None,
         'JustificationNonUse': None, 'IdReportedInformation': 1},
    ])
    session.execute(art9_2018_determination.insert(), [
        {'Id': 10, 'GESDescription': 'Good status', 'DeterminationDate': '2024',
         'UpdateType': 'New determination', 'IdGESComponent': 1},
        {'Id': 11, 'GESDescription': 'Good status 2',
         'DeterminationDate': '2024', 'UpdateType': 'New determination',
         'IdGESComponent': 1},
        {'Id': 12, 'GESDescription': 'Good status 3',
         'DeterminationDate': '2024', 'UpdateType': 'New determination',
         'IdGESComponent': 2},
        {'Id': 13, 'GESDescription': 'Same as last reported',
         'DeterminationDate': '201806', 'UpdateType': 'Same as last reported',
         'IdGESComponent': 3},
        {'Id': 19, 'GESDescription': 'Ghost', 'DeterminationDate': '2000',
         'UpdateType': 'New determination', 'IdGESComponent': 9},
    ])
    session.execute(art9_2018_feature.insert(), [
        {'Id': 1, 'Feature': 'Nutrients', 'IdGESDetermination': 10},
        {'Id': 2, 'Feature': 'Contaminants', 'IdGESDetermination': 10},
        {'Id': 3, 'Feature': 'BirdsAll', 'IdGESDetermination': 11},
        {'Id': 4, 'Feature': 'Nutrients', 'IdGESDetermination': 12},
        {'Id': 5, 'Feature': 'BirdsAll', 'IdGESDetermination': 13},
        {'Id': 9, 'Feature': 'Ghost', 'IdGESDetermination': 19},
    ])
    session.execute(art9_2018_marine_unit.insert(), [
        {'MarineReportingUnit': 'BAL-FI-1', 'IdGESDetermination': 10},
        {'MarineReportingUnit': 'BAL-FI-2', 'IdGESDetermination': 11},
        {'MarineReportingUnit': 'BAL-SE-1', 'IdGESDetermination': 13},
        {'MarineReportingUnit': 'BAL-GHOST', 'IdGESDetermination': 19},
    ])
    session.execute(mrus_2018.insert(), [
        {'thematicId': 'BAL-FI-1', 'rZoneId': 'BAL'},
        {'thematicId': 'BAL-FI-2', 'rZoneId': 'BAL'},
        {'thematicId': 'BAL-SE-1', 'rZoneId': 'BAL'},
    ])

    session.execute(imports.insert(), [
        {'MSFD9_Import_ID': 1, 'MSFD9_Import_ReportingCountry': 'DE         ',
         'MSFD9_Import_ReportingRegion': 'ANS        ',
         'MSFD9_Import_Time': datetime(2012, 7, 6, 11, 2, 18)},
        {'MSFD9_Import_ID': 2, 'MSFD9_Import_ReportingCountry': 'FR         ',
         'MSFD9_Import_ReportingRegion': 'MWE        ',
         'MSFD9_Import_Time': None},
    ])
    session.execute(descriptors.insert(), [
        {'MSFD9_Descriptor_ID': 10, 'MarineUnitID': 'DE_ANS',
         'ReportingFeature': 'D1', 'DescriptionGES': 'German description',
         'ReferencePointType': 'LimitReferencePoint',
         'MSFD9_Descriptors_Import': 1},
        {'MSFD9_Descriptor_ID': 11, 'MarineUnitID': 'DE_ANS',
         'ReportingFeature': '1.1', 'DescriptionGES': 'German description 2',
         'ReferencePointType': 'TargetReferencePoint',
         'MSFD9_Descriptors_Import': 1},
        {'MSFD9_Descriptor_ID': 12, 'MarineUnitID': 'FR_MWE',
         'ReportingFeature': 'D5', 'DescriptionGES': 'French description',
         'ReferencePointType': 'NotReported',
         'MSFD9_Descriptors_Import': 2},
    ])
    session.execute(features.insert(), [
        {'MSFD9_Descriptor': 10, 'FeaturesPressuresImpacts': 'BirdsAll',
         'FeatureType': 'Species group'},
        # the same feature listed twice for one descriptor must still count
        # as a single result row.
        {'MSFD9_Descriptor': 10, 'FeaturesPressuresImpacts': 'Acidification',
         'FeatureType': 'Pressures'},
        {'MSFD9_Descriptor': 10, 'FeaturesPressuresImpacts': 'Acidification',
         'FeatureType': 'Physical/chemical features'},
        {'MSFD9_Descriptor': 12, 'FeaturesPressuresImpacts': 'Nutrients',
         'FeatureType': 'Pressures'},
        # an underscore in a feature code is a literal character, not a LIKE
        # wildcard
        {'MSFD9_Descriptor': 12, 'FeaturesPressuresImpacts': 'BioDisturb_other',
         'FeatureType': 'Pressures'},
    ])
    session.commit()


class SqliteProviderMixin(object):
    """Point a provider at the seeded SQLite session."""

    def _get_session(self):
        return session


class P2024(SqliteProviderMixin, Article9Cycle2024Provider):
    mapper = art9_2024
    region_mru_table = mrus_2024


class P2018(SqliteProviderMixin, Article9Cycle2018Provider):
    component = art9_2018_component
    reported = reported_info
    determination = art9_2018_determination
    feature = art9_2018_feature
    marine_unit = art9_2018_marine_unit
    region_mru_table = mrus_2018


class P2012(SqliteProviderMixin, Article9Cycle2012Provider):
    descriptors = descriptors
    imports = imports
    features = features


# ---------------------------------------------------------------------------
# assertions
# ---------------------------------------------------------------------------
def options(provider, name):
    filters = {facet['name']: facet for facet in provider.build_filters()}
    return {option['value']: option for option in filters[name]['options']}


def test_registry():
    providers = available_providers()
    article9 = [
        p for p in providers
        if p['article'] == '9'
        and p['articleSlug'] == 'determination-of-good-environmental-status'
    ]
    assert {p['cycle'] for p in article9} == {'2012', '2018', '2024'}


def test_2024_multi_value_facets():
    provider = P2024(selections={}, page=0, page_size=10)
    components = options(provider, 'ges_component')
    # the cell 'D5C1; D5C2' contributes one option per token
    assert set(components) == {'D5C1', 'D5C2', 'D1C1'}
    assert components['D5C1']['count'] == 2
    assert components['D5C2']['count'] == 1

    feature_opts = options(provider, 'feature')
    assert set(feature_opts) == {'Nutrients', 'Contaminants', 'Birds_all'}
    assert feature_opts['Nutrients']['count'] == 2

    # an underscore is a literal character, not a LIKE wildcard
    assert P2024(selections={'feature': ['Birds_all']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 1

    # whole token matching: 'D5' must not match 'D5C1' / 'D5C2'
    assert P2024(selections={'ges_component': ['D5']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 0
    assert P2024(selections={'ges_component': ['D5C1']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 2
    assert P2024(selections={'feature': ['Contaminants']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 1


def test_2024_multi_cell_serialization():
    provider = P2024(selections={}, page=0, page_size=10)
    data = provider.build_data()
    row = next(
        r for r in data['rows'] if r['GEScomponent']['raw'] == 'D5C1; D5C2'
    )
    # every token is labelled, the raw value is kept as a tooltip
    assert row['GEScomponent']['text'].startswith('(Criteria) D5C1')
    assert 'D5C2 - ' in row['GEScomponent']['text']
    assert row['GEScomponent']['tooltip'] == 'D5C1; D5C2'
    # each token is also exposed separately so the frontend can bullet it
    assert len(row['GEScomponent']['items']) == 2
    assert row['GEScomponent']['text'] == ', '.join(
        row['GEScomponent']['items']
    )
    assert data['pagination']['total'] == 3


def test_2024_result_columns():
    provider = P2024(selections={}, page=0, page_size=10)
    columns = {c['key']: c for c in provider.build_data()['columns']}

    # the packed MRU column is renamed and marked as multi valued so the
    # frontend renders it as a bullet list, exactly like the features
    assert columns['Feature']['format'] == 'multi'
    assert columns['MarineReportingUnit']['label'] == (
        'Marine Reporting Unit(s)'
    )
    assert columns['MarineReportingUnit']['format'] == 'mru_multi'

    row = next(
        r for r in provider.build_data()['rows']
        if r['GEScomponent']['raw'] == 'D5C1; D5C2'
    )
    assert row['MarineReportingUnit']['items'] == ['ANS-DE-1', 'ANS-DE-2']


def test_2024_derived_region():
    provider = P2024(selections={}, page=0, page_size=10)
    regions = options(provider, 'region_subregions')
    assert set(regions) == {'ANS', 'MWE'}
    assert regions['ANS']['count'] == 2
    assert regions['MWE']['count'] == 1

    # filtering by the derived region keeps the rows whose packed MRU list
    # reaches it (whole token match, not substring)
    assert P2024(selections={'region_subregions': ['MWE']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 1

    data = provider.build_data()
    row = next(r for r in data['rows'] if r['CountryCode']['raw'] == 'DE')
    assert row['Region']['raw'] == 'ANS'


def test_2024_unsupported_facet_is_ignored():
    # a selection on an unknown facet must not break the query
    provider = P2024(selections={'unknown': ['x']}, page=0, page_size=10)
    assert provider.build_data()['pagination']['total'] == 3


def test_2024_determination_year_slider():
    # the determination date is stored with month precision ('YYYYMM'); the
    # range facet must slide over *years* (2024), never over the raw months
    facets = {f['name']: f for f in P2024().build_filters()}
    facet = facets['determination_date']
    assert facet['type'] == 'range'
    assert facet['label'] == 'Determination Date'
    assert facet['unit'] == 'year'
    assert facet['step'] == 1
    # a single reported year collapses the slider onto it
    assert (facet['min'], facet['max']) == (2024, 2024)

    # add two months of 2019: the bounds widen to whole years
    session.execute(art9_2024.insert(), [
        {'row_id': 90, 'CountryCode': 'FR', 'GEScomponent': 'D1C1',
         'Feature': 'Birds_all', 'MarineReportingUnit': 'MWE-FR-1',
         'DeterminationDate': '201911', 'UpdateTypeGES': 'New determination'},
        {'row_id': 91, 'CountryCode': 'FR', 'GEScomponent': 'D1C1',
         'Feature': 'Birds_all', 'MarineReportingUnit': 'MWE-FR-1',
         'DeterminationDate': '201903', 'UpdateTypeGES': 'New determination'},
    ])

    def total(selections):
        return P2024(selections=selections, page=0, page_size=10,
                     ).build_data()['pagination']['total']

    try:
        facet = {f['name']: f for f in P2024().build_filters()}[
            'determination_date'
        ]
        # year precision, not '201903' / '202401'
        assert (facet['min'], facet['max']) == (2019, 2024)
        assert (facet['selectedMin'], facet['selectedMax']) == (2019, 2024)

        # the whole range keeps every month of every year
        assert total({'determination_date': ['2019', '2024']}) == 3
        # a single year keeps all its months
        assert total({'determination_date': ['2019', '2019']}) == 2
        # an upper bound below a year's months still drops that year
        assert total({'determination_date': ['2019', '2020']}) == 2
        assert total({'determination_date': ['2020', '2024']}) == 1
        # the exclusive upper bound is one year past the selection
        assert total({'determination_date': ['2025', '2030']}) == 0

        # rows without a determination date: two of the five rows in the
        # table have no date at all, so a plain range would silently drop them
        assert total({}) == 5
        # the slider on its full range *with* the null toggle keeps everything
        assert total({'determination_date': ['2019', '2024', 'null']}) == 5
        # dropping the null toggle is exactly what hides the undated rows
        assert total({'determination_date': ['2019', '2024']}) == 3
        assert total({'determination_date': ['2019', '2019', 'null']}) == 4
        assert total({'determination_date': ['2019', '2019']}) == 2
        # the two bounds must stay ANDed with each other (a loose OR would let
        # the 2024 row through every window); only the undated rows are an
        # alternative to the whole window
        assert total({'determination_date': ['2020', '2024', 'null']}) == 3
        assert total({'determination_date': ['2020', '2024']}) == 1
        # an empty reported cell counts as "no value" too
        session.execute(art9_2024.insert(), [
            {'row_id': 92, 'CountryCode': 'DE', 'GEScomponent': 'D5C1',
             'Feature': 'Nutrients', 'MarineReportingUnit': 'ANS-DE-1',
             'DeterminationDate': ''},
        ])
        assert total({'determination_date': ['2019', '2024', 'null']}) == 6
        assert total({'determination_date': ['2019', '2024']}) == 3
        session.execute(art9_2024.delete().where(art9_2024.c.row_id == 92))

        # the toggle ships with its label, row count and default state
        payload = {f['name']: f for f in P2024().build_filters()}
        null_option = payload['determination_date']['nullOption']
        assert null_option['value'] == 'null'
        assert null_option['label'] == (
            'Include rows without a determination date'
        )
        assert null_option['count'] == 2
        assert null_option['selected'] is True
        # ... and reflects the selection once the user moves the slider
        hidden = {f['name']: f for f in P2024(
            selections={'determination_date': ['2019', '2024']},
            page=0, page_size=10,
        ).build_filters()}['determination_date']['nullOption']
        assert hidden['selected'] is False
        shown = {f['name']: f for f in P2024(
            selections={'determination_date': ['2019', '2024', 'null']},
            page=0, page_size=10,
        ).build_filters()}['determination_date']['nullOption']
        assert shown['selected'] is True
        # the count is cross filtered by the other facets, like an option count
        cross = {f['name']: f for f in P2024(
            selections={'feature': ['Birds_all']}, page=0, page_size=10,
        ).build_filters()}['determination_date']['nullOption']
        assert cross['count'] == 0

        # the slider bounds cross filter with the other facets
        narrowed = {f['name']: f for f in P2024(
            selections={'feature': ['Birds_all']}, page=0, page_size=10,
        ).build_filters()}['determination_date']
        assert (narrowed['min'], narrowed['max']) == (2019, 2024)
    finally:
        session.execute(
            art9_2024.delete().where(art9_2024.c.row_id.in_([90, 91]))
        )
        session.commit()


def test_2018_base_tables_and_grain():
    provider = P2018(selections={}, page=0, page_size=10)

    # only the latest reported file per (country, schema) is shown: the FI
    # component filed under the old import Id 1 is dropped
    components = options(provider, 'ges_component')
    assert set(components) == {'D5C1', 'D5C2', 'D1C1'}
    assert 'D9C9' not in components

    feature_opts = options(provider, 'feature')
    assert set(feature_opts) == {'Nutrients', 'Contaminants', 'BirdsAll'}
    # options are counted per determination row, not per expanded feature
    assert feature_opts['Nutrients']['count'] == 2
    assert feature_opts['BirdsAll']['count'] == 2
    assert 'Ghost' not in feature_opts

    assert P2018(selections={'feature': ['Contaminants']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 1
    # one row per determination (GES description), features and MRUs packed
    assert provider.build_data()['pagination']['total'] == 4


def test_2018_packs_features_and_mrus():
    provider = P2018(selections={}, page=0, page_size=10)
    data = provider.build_data()
    columns = {c['key']: c for c in data['columns']}

    # the child-table values are bullet lists under the renamed columns
    assert columns['Feature']['label'] == 'Feature(s)'
    assert columns['Feature']['format'] == 'multi'
    assert columns['MarineReportingUnit']['label'] == (
        'Marine Reporting Unit(s)'
    )
    assert columns['MarineReportingUnit']['format'] == 'mru_multi'

    # determination 10 (D5C1, FI) has two features and one MRU
    row = next(
        r for r in data['rows']
        if r['GESDescription']['raw'] == 'Good status'
        and r['GESComponent']['raw'] == 'D5C1'
        and r['CountryCode']['raw'] == 'FI'
    )
    assert row['Feature']['items'] == ['Contaminants', 'Nutrients (N, P)']
    assert row['MarineReportingUnit']['items'] == ['BAL-FI-1']

    # a determination with no marine unit still renders, with an empty cell
    det12 = next(
        r for r in data['rows'] if r['GESDescription']['raw'] == 'Good status 3'
    )
    assert det12['MarineReportingUnit']['empty'] is True
    assert det12['Feature']['items'] and len(det12['Feature']['items']) == 1


def test_2018_update_type_facet():
    provider = P2018(selections={}, page=0, page_size=10)
    updates = options(provider, 'update_type')
    assert updates['New determination']['count'] == 3
    assert updates['Same as last reported']['count'] == 1


def test_2018_determination_year_slider():
    # the 2018 determination date is also stored with month precision
    # ('YYYYMM'); the facet must slide over years, like the 2024 cycle
    facet = {f['name']: f for f in P2018().build_filters()}[
        'determination_date'
    ]
    assert facet['type'] == 'range'
    assert facet['label'] == 'Determination Date'
    assert facet['unit'] == 'year'
    assert facet['step'] == 1
    # one row reports 201806, three only the year 2024
    assert (facet['min'], facet['max']) == (2018, 2024)

    def total(selections):
        return P2018(selections=selections, page=0, page_size=10,
                     ).build_data()['pagination']['total']

    # the whole range keeps everything
    assert total({}) == 4
    assert total({'determination_date': ['2018', '2024']}) == 4
    # a single year keeps every month of it
    assert total({'determination_date': ['2024', '2024']}) == 3
    # the exclusive upper bound drops the later years
    assert total({'determination_date': ['2018', '2023']}) == 1
    assert total({'determination_date': ['2025', '2030']}) == 0

    # a component with no determination gets no date from the outer join, so
    # the facet offers the "keep undated rows" toggle, on by default
    null_option = facet['nullOption']
    assert null_option['value'] == 'null'
    assert null_option['label'] == (
        'Include rows without a determination date'
    )
    assert null_option['selected'] is True


def test_2018_derived_region():
    provider = P2018(selections={}, page=0, page_size=10)
    regions = options(provider, 'region_subregions')
    assert set(regions) == {'BAL'}
    # the determination without a marine reporting unit reaches no region
    assert regions['BAL']['count'] == 3

    data = provider.build_data()
    assert data['rows'][0]['Region']['raw'] == 'BAL'


def test_2012_trimmed_country_region_and_features():
    provider = P2012(selections={}, page=0, page_size=10)
    filters = {facet['name']: facet for facet in provider.build_filters()}

    # no update type on this cycle
    assert 'update_type' not in filters
    # padded database codes are trimmed on the wire
    assert set(o['value'] for o in filters['member_states']['options']) == {
        'DE', 'FR',
    }
    assert set(
        o['value'] for o in filters['region_subregions']['options']
    ) == {'ANS', 'MWE'}

    data = provider.build_data()
    assert data['pagination']['total'] == 3
    assert data['rows'][0]['Country']['text'] == 'Germany'

    # features live in a child table; selecting one keeps the descriptor row
    feature_opts = options(provider, 'feature')
    assert feature_opts['Acidification']['count'] == 1

    filtered = P2012(selections={'feature': ['Acidification']}, page=0,
                     page_size=10)
    assert filtered.build_data()['pagination']['total'] == 1
    # and narrows the reachable feature options through the other filters
    reachable = options(
        P2012(selections={'member_states': ['FR']}, page=0, page_size=10),
        'feature',
    )
    assert set(reachable) == {'Nutrients', 'BioDisturb_other'}

    # an underscore in a feature code is a literal character, not a LIKE
    # wildcard
    assert P2012(selections={'feature': ['BioDisturb_other']}, page=0,
                 page_size=10).build_data()['pagination']['total'] == 1


def test_2012_grouped_feature_cell():
    provider = P2012(selections={}, page=0, page_size=10)
    data = provider.build_data()
    columns = {c['key']: c for c in data['columns']}

    # a real, sortable, after-the-component column with the collapse hint.
    assert columns['Feature']['label'] == 'Feature(s)'
    assert columns['Feature']['format'] == 'grouped_multi'
    assert columns['Feature']['sortable'] is True
    assert columns['Feature']['maxItems'] == 10
    keys = [c['key'] for c in data['columns']]
    assert keys.index('Feature') == keys.index('ReportingFeature') + 1

    def by_component(component):
        for row in data['rows']:
            if row['ReportingFeature']['raw'] == component:
                return row

        raise AssertionError('no row for %r' % component)

    def label(code):
        return glossary_label(code)

    # features are grouped by FeatureType, ordered by label; the same feature
    # listed under two types is kept once per type.
    cell = by_component('D1')['Feature']
    assert cell['groups'] == [
        {'label': 'Physical/chemical features',
         'items': [label('Acidification')]},
        {'label': 'Pressures', 'items': [label('Acidification')]},
        {'label': 'Species group', 'items': [label('BirdsAll')]},
    ]
    assert cell['text'] == (
        'Physical/chemical features: Marine acidification; '
        'Pressures: Marine acidification; Species group: All birds'
    )
    # the raw codes stay available as the tooltip whenever they differ.
    assert cell['tooltip'] == cell['raw']
    assert cell['empty'] is False

    # comma packing inside a single value is split, and items are ordered by
    # their displayed label (BioDisturb_other before Nutrients).
    cell = by_component('D5')['Feature']
    assert cell['groups'] == [
        {'label': 'Pressures', 'items': [label('BioDisturb_other'),
                                         label('Nutrients')]},
    ]
    assert cell['text'] == (
        'Pressures: BioDisturb_other, Nutrients (N, P)'
    )

    # a descriptor without feature rows keeps its row and an empty cell.
    empty = by_component('1.1')['Feature']
    assert empty['empty'] is True
    assert empty['groups'] is None


def test_sort_direction():
    def first(sort, direction, key='CountryCode'):
        return P2018(
            selections={}, page=0, page_size=1,
            sort=sort, direction=direction,
        ).build_data()['rows'][0][key]['raw']

    # the user direction must win over the default order_by direction
    assert first('CountryCode', 'asc') == 'FI'
    assert first('CountryCode', 'desc') == 'SE'
    # sorting by a column that is not in order_by is primary
    assert first('GESComponent', 'asc', 'GESComponent') == 'D1C1'
    assert first('GESComponent', 'desc', 'GESComponent') == 'D5C2'


def test_date_columns_are_formatted():
    # the reported/determination date columns are full datetimes in the DB;
    # the table must show a readable day, not ``2018-07-06T11:02:18``
    data = P2024(selections={}, page=0, page_size=10).build_data()
    fr = next(r for r in data['rows'] if r['CountryCode']['raw'] == 'FR')
    assert fr['ReportingDate']['text'] == '2018 Jul 06'
    assert fr['ReportingDate']['raw'] == '2018 Jul 06'
    assert 'T' not in fr['ReportingDate']['text']
    # determination dates are reported as ``YYYYMM`` and shown as ``YYYY Mon``
    assert fr['DeterminationDate']['text'] == '2024 Jan'
    assert fr['DeterminationDate']['raw'] == '2024 Jan'

    p2018 = P2018(selections={}, page=0, page_size=10)
    rows = p2018.build_data()['rows']
    row = next(r for r in rows if not r['ReportingDate']['empty'])
    assert row['ReportingDate']['text'] == '2018 Jul 06'
    # the summary meta uses the same format
    assert p2018.build_data()['meta']['reportedDate'] == '2018 Jul 06'
    month = next(
        r for r in rows if r['DeterminationDate']['text'] == '2018 Jun'
    )
    assert month['DeterminationDate']['raw'] == '2018 Jun'

    row = P2012(selections={}, page=0, page_size=10).build_data()['rows'][0]
    assert row['ReportingDate']['text'] == '2012 Jul 06'


def test_mru_labels_in_article9_cells():
    # the MRU label lookup runs against GES_LABELS.mrus (the Article 4
    # publication); patch it so the assertion does not depend on live data.
    from wise.msfd.labels import GES_LABELS

    original = GES_LABELS.mrus
    labels = dict(original or {})
    labels.update({
        'BAL-FI-1': 'Northern Baltic Proper',
        'ANS-DE-1': 'German Bight',
        'ANS-DE-2': 'Dogger Bank',
        'DE_ANS': 'German North Sea',
    })
    GES_LABELS.mrus = labels

    try:
        # multi valued cell (2018/2024): one label per bullet
        row = P2018(selections={}, page=0, page_size=10).build_data()['rows'][0]
        assert row['MarineReportingUnit']['items'] == [
            'Northern Baltic Proper (BAL-FI-1)'
        ]

        rows = P2024(selections={}, page=0, page_size=10).build_data()['rows']
        packed = next(
            r for r in rows
            if r['MarineReportingUnit'].get('items')
            and len(r['MarineReportingUnit']['items']) > 1
        )
        assert packed['MarineReportingUnit']['items'] == [
            'German Bight (ANS-DE-1)', 'Dogger Bank (ANS-DE-2)'
        ]
        # the raw ids stay available as the tooltip
        assert packed['MarineReportingUnit']['tooltip'] == 'ANS-DE-1; ANS-DE-2'

        # single valued cell (2012)
        row = P2012(selections={}, page=0, page_size=10).build_data()['rows'][0]
        assert row['MarineUnitID']['text'] == 'German North Sea (DE_ANS)'
    finally:
        GES_LABELS.mrus = original


def test_reporting_period_is_static():
    for provider, text in (
        (P2024, '2024 reporting exercise'),
        (P2018, '2018 reporting exercise'),
        (P2012, '2012 reporting exercise'),
    ):
        data = provider(
            selections={}, page=0, page_size=1
        ).build_data()
        cell = data['rows'][0]['ReportingPeriod']
        assert cell['raw'] == text
        assert cell['text'] == text


def _cards(summary):
    return {c['key']: c for c in summary['cards']}


def _charts(summary):
    return {c['key']: c for c in summary['charts']}


def test_2024_summary():
    summary = P2024(selections={}, page=0, page_size=10).build_summary()
    cards = _cards(summary)
    charts = _charts(summary)

    # distinct tokens, not packed cells
    assert cards['mru_count']['value'] == 3
    assert cards['mru_count']['valueOf'] == 3
    assert cards['component_count']['value'] == 3
    assert cards['feature_count']['value'] == 3

    justifications = cards['justifications']
    assert justifications['value'] == 1
    assert justifications['valueOf'] == 3
    assert justifications['details'] == []

    updates = {
        p['label']: p['value'] for p in charts['update_type']['points']
    }
    assert updates == {
        'New determination': 2,
        'Modified from reported determination': 1,
    }
    justifications_chart = {
        p['label']: p['value']
        for p in charts['justification_distribution']['points']
    }
    assert justifications_chart == {
        'Justification for delay': 1,
        'Justification for non-use': 0,
    }

    # the cards cross filter with the facets
    filtered = P2024(
        selections={'ges_component': ['D1C1']}, page=0, page_size=10
    ).build_summary()
    filtered_cards = _cards(filtered)
    assert filtered_cards['mru_count']['value'] == 1
    assert filtered_cards['mru_count']['valueOf'] == 3
    assert filtered_cards['feature_count']['value'] == 1
    assert filtered_cards['justifications']['value'] == 0


def test_2018_summary():
    summary = P2018(selections={}, page=0, page_size=10).build_summary()
    cards = _cards(summary)
    charts = _charts(summary)

    assert cards['mru_count']['value'] == 3
    assert cards['component_count']['value'] == 3
    assert cards['feature_count']['value'] == 3

    justifications = cards['justifications']
    assert justifications['value'] == 1
    assert justifications['valueOf'] == 4
    assert justifications['details'] == []

    updates = {
        p['label']: p['value'] for p in charts['update_type']['points']
    }
    assert updates == {'New determination': 3, 'Same as last reported': 1}
    justifications_chart = {
        p['label']: p['value']
        for p in charts['justification_distribution']['points']
    }
    assert justifications_chart == {
        'Justification for delay': 0,
        'Justification for non-use': 1,
    }


def test_2012_summary():
    summary = P2012(selections={}, page=0, page_size=10).build_summary()
    cards = _cards(summary)
    charts = _charts(summary)

    assert cards['mru_count']['value'] == 2
    assert cards['component_count']['value'] == 3
    # features come from the child table and are de-duplicated
    assert cards['feature_count']['value'] == 4

    reference = cards['reference_points']
    assert reference['label'] == 'Determinations with a reference point'
    assert reference['value'] == 2
    assert reference['valueOf'] == 3
    assert reference['details'] == []

    points = {
        p['label']: p['value']
        for p in charts['reference_point_type']['points']
    }
    assert points == {
        'LimitReferencePoint': 1,
        'TargetReferencePoint': 1,
        'NotReported': 1,
    }
    # the GES component chart is replaced by the reference point chart, which
    # this cycle already carried, so 2012 exposes a single chart
    assert set(charts) == {'reference_point_type'}
    assert charts['reference_point_type']['title'] == (
        'Determinations by reference point type'
    )

    # feature facet narrows the reachable feature set; a descriptor that also
    # reports another feature keeps it, matching the multi-value facet counts
    filtered = P2012(
        selections={'feature': ['Acidification']}, page=0, page_size=10
    ).build_summary()
    assert _cards(filtered)['feature_count']['value'] == 2


def main():
    seed()
    tests = [value for name, value in sorted(globals().items())
             if name.startswith('test_') and callable(value)]
    failures = 0

    for test in tests:
        try:
            test()
            print('ok   - {}'.format(test.__name__))
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print('FAIL - {}: {}'.format(test.__name__, exc))

    print('\n{} passed, {} failed'.format(len(tests) - failures, failures))

    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
