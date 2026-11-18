# pylint: skip-file
"""Article 19.3 "Datasets used" explorer harness.

Exercises the four Article 19.3 information-type providers end to end against
an in-memory SQLite database seeded with representative rows, so the risky
logic (the dataset/indicator grain, packed context cells, the 2018
latest-import cut,
the 2020 descriptor-by-code mapping, the derived regions and the trimmed 2012
country) is covered without a database server. The live 2024 source is not
reachable from the development environment, which is why the harness feeds all
four providers the same way.

Run it inside the backend container, where the package (and its label data)
imports:

    docker exec -i marine-backend-p6 /app/bin/python \
        -m wise.msfd.explorer.tests.harness_article19
"""
from __future__ import absolute_import

from datetime import datetime

from sqlalchemy import (Column, Date, DateTime, Integer, MetaData, Table,
                        Unicode, create_engine)
from sqlalchemy.orm import sessionmaker

from wise.msfd.explorer.providers.article19_2012 import (
    Article19Cycle2012Provider)
from wise.msfd.explorer.providers.article19_2018 import (
    Article19Cycle2018Provider)
from wise.msfd.explorer.providers.article19_2020 import (
    Article19Cycle2020Provider)
from wise.msfd.explorer.providers.article19_2024 import (
    Article19Cycle2024Provider)
from wise.msfd.explorer.providers.registry import available_providers

# ---------------------------------------------------------------------------
# schema + fixtures
# ---------------------------------------------------------------------------
metadata = MetaData()

# -- Article 19.3 / 2024 (data.Indicators_*) ---------------------------------
data_datasets = Table(
    'data_Indicators_Datasets', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('URL', Unicode),
    Column('MD_URL', Unicode),
    Column('SnapshotId', Integer),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
)

data_assessment = Table(
    'data_Indicators_IndicatorAssessment', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('IndicatorTitle', Unicode),
    Column('SourceAssessmentIndicator', Unicode),
    Column('ReportingMethodIndicator', Unicode),
    Column('UniqueReference', Unicode),
    Column('RelatedTargets', Unicode),
    Column('DatasetVoidReason', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('RegionalAssessmentArea', Unicode),
    Column('SnapshotId', Integer),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
)

data_feature = Table(
    'data_Indicators_Feature', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('SnapshotId', Integer),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
)

# -- Article 19.3 / 2018 (Indicators_*) --------------------------------------
ind_dataset = Table(
    'Indicators_Dataset', metadata,
    Column('Id', Integer, primary_key=True),
    Column('URL', Unicode),
    Column('MD_URL', Unicode),
    Column('IdIndicatorAssessment', Integer),
)

ind_assessment = Table(
    'Indicators_IndicatorAssessment', metadata,
    Column('Id', Integer, primary_key=True),
    Column('IndicatorCode', Unicode),
    Column('IndicatorTitle', Unicode),
    Column('IdReportedInformation', Integer),
)

ind_ges = Table(
    'Indicators_Feature_GESComponent', metadata,
    Column('Id', Integer, primary_key=True),
    Column('GESComponent', Unicode),
    Column('IdIndicatorAssessment', Integer),
)

ind_feature = Table(
    'Indicators_Feature_Feature', metadata,
    Column('Feature', Unicode, primary_key=True),
    Column('IdGESComponent', Integer, primary_key=True),
)

ind_mru = Table(
    'Indicators_MarineUnit', metadata,
    Column('MarineReportingUnit', Unicode, primary_key=True),
    Column('IdIndicatorAssessment', Integer, primary_key=True),
)

reported_info = Table(
    'ReportedInformation', metadata,
    Column('Id', Integer, primary_key=True),
    Column('CountryCode', Unicode(2)),
    Column('Schema', Unicode),
    Column('ReportingDate', Date),
)

# -- Article 19.3 / 2020 (ART11_*) -------------------------------------------
art11_programme = Table(
    'ART11_Programmes_MonitoringProgramme', metadata,
    Column('Id', Integer, primary_key=True),
    Column('ProgrammeCode', Unicode),
    Column('ProgrammeName', Unicode),
    Column('IdReportedInformation', Integer),
)

art11_data_access = Table(
    'ART11_Programmes_MonitoringProgramme_DataAccess', metadata,
    Column('Id', Integer, primary_key=True),
    Column('DataAccess', Unicode),
    Column('IdMonitoringProgramme', Integer),
)

art11_mru = Table(
    'ART11_Programmes_MonitoringProgramme_MarineReportingUnit', metadata,
    Column('Id', Integer, primary_key=True),
    Column('MarineReportingUnit', Unicode),
    Column('IdMonitoringProgramme', Integer),
)

art11_strategy = Table(
    'ART11_Strategies_MonitoringStrategy', metadata,
    Column('Id', Integer, primary_key=True),
    Column('Descriptor', Unicode),
)

art11_strategy_mp = Table(
    'ART11_Strategies_MonitoringStrategy_MonitoringProgrammes', metadata,
    Column('Id', Integer, primary_key=True),
    Column('MonitoringProgrammes', Unicode),
    Column('IdMonitoringStrategy', Integer),
)

# -- Article 19.3 / 2012 -----------------------------------------------------
metadata_features = Table(
    'MetadataFeatures', metadata,
    Column('IdMetadataArt19_3', Integer),
    Column('MarineUnitID', Unicode),
    Column('ReportingFeature', Unicode),
    Column('DatasetRecord', Unicode),
    Column('DatasetLink', Unicode),
    Column('MetadataStandard', Unicode),
    Column('DateStamp', Unicode),
    Column('Language', Unicode),
)

metadata_art193 = Table(
    'MetadataArt19_3', metadata,
    Column('Id', Integer, primary_key=True),
    Column('Country', Unicode(11)),
    Column('Region', Unicode(11)),
)

# -- Article 4 MRU publications, used to derive the region -------------------
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

geographical_areas_2012 = Table(
    'MSFD4_GegraphicalAreasID', metadata,
    Column('MarineUnitID', Unicode, primary_key=True),
    Column('RegionSubRegions', Unicode(3)),
)

engine = create_engine('sqlite://')
metadata.create_all(engine)
session = sessionmaker(bind=engine)()


def seed():
    # -- 2024 -------------------------------------------------------------
    session.execute(data_datasets.insert(), [
        {'CountryCode': 'DE', 'IndicatorCode': 'IND1',
         'URL': 'http://ds1', 'MD_URL': 'http://md1',
         'ReportingDate': datetime(2024, 1, 15)},
        {'CountryCode': 'DE', 'IndicatorCode': 'IND1',
         'URL': 'http://ds2', 'MD_URL': 'http://md2',
         'ReportingDate': datetime(2024, 1, 15)},
        {'CountryCode': 'FR', 'IndicatorCode': 'IND2',
         'URL': 'http://ds3', 'MD_URL': None,
         'ReportingDate': datetime(2024, 2, 1)},
        # a dataset whose assessment has no feature rows
        {'CountryCode': 'SE', 'IndicatorCode': 'IND4',
         'URL': 'http://ds4', 'MD_URL': None,
         'ReportingDate': datetime(2024, 4, 1)},
    ])
    session.execute(data_assessment.insert(), [
        {'CountryCode': 'DE', 'IndicatorCode': 'IND1',
         'IndicatorTitle': 'Indicator One',
         'SourceAssessmentIndicator': 'National; HELCOM',
         'ReportingMethodIndicator': 'Type A',
         'UniqueReference': 'https://ref.example/ind1',
         'RelatedTargets': '1',
         'DatasetVoidReason': None,
         'MarineReportingUnit': 'ANS-DE-1; ANS-DE-2',
         'RegionalAssessmentArea': 'ANS',
         'ReportingDate': datetime(2024, 1, 15)},
        {'CountryCode': 'FR', 'IndicatorCode': 'IND2',
         'IndicatorTitle': 'Indicator Two',
         'SourceAssessmentIndicator': 'OSPAR',
         'ReportingMethodIndicator': 'Type B1',
         'UniqueReference': 'https://ref.example/ind2',
         'RelatedTargets': '1; 2',
         'DatasetVoidReason': 'Data-NotElectronic',
         'MarineReportingUnit': 'MWE-FR-1',
         'RegionalAssessmentArea': 'MWE; MWE-FR',
         'ReportingDate': datetime(2024, 2, 1)},
        # an assessment with no dataset rows and no feature rows: it must
        # still surface, with empty dataset / feature cells
        {'CountryCode': 'DE', 'IndicatorCode': 'IND3',
         'IndicatorTitle': 'Indicator Three',
         'SourceAssessmentIndicator': 'National',
         'ReportingMethodIndicator': 'Type C',
         'UniqueReference': 'https://ref.example/ind3',
         'RelatedTargets': None,
         'DatasetVoidReason': 'Data-InPrep',
         'MarineReportingUnit': 'ANS-DE-1',
         'RegionalAssessmentArea': 'ANS',
         'ReportingDate': datetime(2024, 3, 1)},
        # an assessment with a dataset but no feature rows
        {'CountryCode': 'SE', 'IndicatorCode': 'IND4',
         'IndicatorTitle': 'Indicator Four',
         'SourceAssessmentIndicator': 'HELCOM',
         'ReportingMethodIndicator': 'Type D',
         'UniqueReference': 'https://ref.example/ind4',
         'RelatedTargets': None,
         'DatasetVoidReason': None,
         'MarineReportingUnit': 'MWE-SE-1',
         'RegionalAssessmentArea': None,
         'ReportingDate': datetime(2024, 4, 1)},
    ])
    session.execute(data_feature.insert(), [
        {'CountryCode': 'DE', 'IndicatorCode': 'IND1',
         'GEScomponent': 'D5C1; D5C2',
         'Feature': 'Nutrients; Contaminants'},
        {'CountryCode': 'FR', 'IndicatorCode': 'IND2',
         'GEScomponent': 'D1C1', 'Feature': 'Birds_all'},
    ])
    session.execute(mrus_2024.insert(), [
        {'MarineReportingUnitId': 'ANS-DE-1', 'RegionSubRegion': 'ANS'},
        {'MarineReportingUnitId': 'ANS-DE-2', 'RegionSubRegion': 'ANS'},
        {'MarineReportingUnitId': 'MWE-FR-1', 'RegionSubRegion': 'MWE'},
        {'MarineReportingUnitId': 'MWE-SE-1', 'RegionSubRegion': 'MWE'},
    ])

    # -- 2018 -------------------------------------------------------------
    session.execute(reported_info.insert(), [
        {'Id': 5, 'CountryCode': 'FI', 'Schema': 'MSFD_Art8',
         'ReportingDate': datetime(2018, 7, 6)},
        {'Id': 1, 'CountryCode': 'FI', 'Schema': 'MSFD_Art8',
         'ReportingDate': None},
        {'Id': 2, 'CountryCode': 'SE', 'Schema': 'MSFD_Art8',
         'ReportingDate': None},
        {'Id': 3, 'CountryCode': 'DE', 'Schema': 'MSFD_Art11',
         'ReportingDate': datetime(2020, 1, 1)},
    ])
    session.execute(ind_assessment.insert(), [
        {'Id': 1, 'IndicatorCode': 'IND1', 'IndicatorTitle': 'Indicator One',
         'IdReportedInformation': 5},
        {'Id': 2, 'IndicatorCode': 'IND2', 'IndicatorTitle': 'Indicator Two',
         'IdReportedInformation': 2},
        # filed under the old FI import; must never surface
        {'Id': 9, 'IndicatorCode': 'IND9', 'IndicatorTitle': 'Ghost',
         'IdReportedInformation': 1},
    ])
    session.execute(ind_dataset.insert(), [
        {'Id': 1, 'URL': 'http://ds1', 'MD_URL': 'http://md1',
         'IdIndicatorAssessment': 1},
        {'Id': 2, 'URL': 'http://ds2', 'MD_URL': None,
         'IdIndicatorAssessment': 1},
        {'Id': 3, 'URL': 'http://ds3', 'MD_URL': 'http://md3',
         'IdIndicatorAssessment': 2},
        {'Id': 9, 'URL': 'http://ds9', 'MD_URL': None,
         'IdIndicatorAssessment': 9},
    ])
    session.execute(ind_ges.insert(), [
        {'Id': 10, 'GESComponent': 'D5C1', 'IdIndicatorAssessment': 1},
        {'Id': 11, 'GESComponent': 'D1C1', 'IdIndicatorAssessment': 2},
        {'Id': 19, 'GESComponent': 'D9C9', 'IdIndicatorAssessment': 9},
    ])
    session.execute(ind_feature.insert(), [
        {'Feature': 'Nutrients', 'IdGESComponent': 10},
        {'Feature': 'Contaminants', 'IdGESComponent': 10},
        {'Feature': 'BirdsAll', 'IdGESComponent': 11},
        {'Feature': 'Ghost', 'IdGESComponent': 19},
    ])
    session.execute(ind_mru.insert(), [
        {'MarineReportingUnit': 'BAL-FI-1', 'IdIndicatorAssessment': 1},
        {'MarineReportingUnit': 'BAL-FI-2', 'IdIndicatorAssessment': 1},
        {'MarineReportingUnit': 'BAL-SE-1', 'IdIndicatorAssessment': 2},
        {'MarineReportingUnit': 'BAL-GHOST', 'IdIndicatorAssessment': 9},
    ])

    # -- 2020 -------------------------------------------------------------
    session.execute(art11_programme.insert(), [
        {'Id': 100, 'ProgrammeCode': 'MP1', 'ProgrammeName': 'Programme One',
         'IdReportedInformation': 3},
        {'Id': 101, 'ProgrammeCode': 'mp2', 'ProgrammeName': 'Programme Two',
         'IdReportedInformation': 2},
    ])
    session.execute(art11_data_access.insert(), [
        {'Id': 1, 'DataAccess': 'http://data1', 'IdMonitoringProgramme': 100},
        {'Id': 2, 'DataAccess': 'http://data2', 'IdMonitoringProgramme': 100},
        {'Id': 3, 'DataAccess': 'http://data3', 'IdMonitoringProgramme': 101},
    ])
    session.execute(art11_mru.insert(), [
        {'Id': 1, 'MarineReportingUnit': 'ANS-DE-1',
         'IdMonitoringProgramme': 100},
        {'Id': 2, 'MarineReportingUnit': 'MWE-SE-1',
         'IdMonitoringProgramme': 101},
    ])
    session.execute(art11_strategy.insert(), [
        {'Id': 200, 'Descriptor': 'D5'},
        {'Id': 201, 'Descriptor': 'D1'},
        {'Id': 202, 'Descriptor': 'D11'},
    ])
    session.execute(art11_strategy_mp.insert(), [
        # programme codes are matched case insensitively
        {'Id': 1, 'MonitoringProgrammes': 'MP1',
         'IdMonitoringStrategy': 200},
        {'Id': 2, 'MonitoringProgrammes': 'MP1',
         'IdMonitoringStrategy': 202},
        {'Id': 3, 'MonitoringProgrammes': 'mp2',
         'IdMonitoringStrategy': 201},
    ])

    # -- region mappings --------------------------------------------------
    session.execute(mrus_2018.insert(), [
        {'thematicId': 'BAL-FI-1', 'rZoneId': 'BAL'},
        {'thematicId': 'BAL-FI-2', 'rZoneId': 'BAL'},
        {'thematicId': 'BAL-SE-1', 'rZoneId': 'BAL'},
        {'thematicId': 'ANS-DE-1', 'rZoneId': 'ANS'},
        {'thematicId': 'MWE-SE-1', 'rZoneId': 'MWE'},
    ])

    # -- 2012 -------------------------------------------------------------
    session.execute(metadata_art193.insert(), [
        {'Id': 1, 'Country': 'DE         ', 'Region': 'ANS'},
        {'Id': 2, 'Country': 'FR         ', 'Region': 'MWE'},
    ])
    session.execute(metadata_features.insert(), [
        {'IdMetadataArt19_3': 1, 'MarineUnitID': 'DE_ANS',
         'ReportingFeature': 'D1', 'DatasetRecord': 'Record A',
         'DatasetLink': 'http://a', 'MetadataStandard': 'ISO19115',
         'DateStamp': '20120101', 'Language': 'en'},
        {'IdMetadataArt19_3': 1, 'MarineUnitID': 'DE_ANS',
         'ReportingFeature': 'D5', 'DatasetRecord': 'Record B',
         'DatasetLink': 'http://b', 'MetadataStandard': 'ISO19115',
         'DateStamp': '20120102', 'Language': 'en'},
        {'IdMetadataArt19_3': 2, 'MarineUnitID': 'FR_MWE',
         'ReportingFeature': 'D5', 'DatasetRecord': 'Record C',
         'DatasetLink': None, 'MetadataStandard': 'ISO19115',
         'DateStamp': '20120103', 'Language': 'fr'},
    ])
    session.execute(geographical_areas_2012.insert(), [
        {'MarineUnitID': 'DE_ANS', 'RegionSubRegions': 'ANS'},
        {'MarineUnitID': 'FR_MWE', 'RegionSubRegions': 'MWE'},
    ])

    session.commit()


class SqliteProviderMixin(object):
    """Point a provider at the seeded SQLite session."""

    def _get_session(self):
        return session


class P2024(SqliteProviderMixin, Article19Cycle2024Provider):
    dataset = data_datasets
    assessment = data_assessment
    feature = data_feature
    region_mru_table = mrus_2024


class P2018(SqliteProviderMixin, Article19Cycle2018Provider):
    dataset = ind_dataset
    assessment = ind_assessment
    ges_component = ind_ges
    feature = ind_feature
    marine_unit = ind_mru
    reported = reported_info
    region_mru_table = mrus_2018


class P2020(SqliteProviderMixin, Article19Cycle2020Provider):
    data_access = art11_data_access
    programme = art11_programme
    marine_unit = art11_mru
    strategy = art11_strategy
    strategy_programme = art11_strategy_mp
    reported = reported_info
    region_mru_table = mrus_2018


class P2012(SqliteProviderMixin, Article19Cycle2012Provider):
    features = metadata_features
    metadata = metadata_art193
    region_mru_table = geographical_areas_2012


# ---------------------------------------------------------------------------
# assertions
# ---------------------------------------------------------------------------
def options(provider, name):
    filters = {facet['name']: facet for facet in provider.build_filters()}
    return {option['value']: option for option in filters[name]['options']}


def total(provider):
    return provider.build_data()['pagination']['total']


def test_registry():
    providers = available_providers()
    article19 = [
        p for p in providers
        if p['article'] == '19.3' and p['articleSlug'] == 'datasets-used'
    ]
    assert {p['cycle'] for p in article19} == {
        '2012', '2018', '2020', '2024'
    }


def test_2024_indicator_grain_and_packing():
    provider = P2024(selections={}, page=0, page_size=10)

    # one row per reported indicator (CountryCode, IndicatorCode); the datasets
    # are packed into the URL / MD_URL cells
    assert total(provider) == 4

    rows = provider.build_data()['rows']

    ind1 = next(
        r for r in rows
        if r['CountryCode']['raw'] == 'DE'
        and r['IndicatorCode']['raw'] == 'IND1'
    )
    # the two filed datasets are concatenated, not one row each
    assert ind1['URL']['raw'] == 'http://ds1;http://ds2'
    assert ind1['URL']['items'] == ['http://ds1', 'http://ds2']
    assert ind1['MD_URL']['raw'] == 'http://md1;http://md2'
    assert ind1['IndicatorTitle']['text'] == 'Indicator One'
    assert set(
        ind1['GEScomponent']['raw'].replace(' ', '').split(';')
    ) == {'D5C1', 'D5C2'}
    assert set(
        ind1['Feature']['raw'].replace(' ', '').split(';')
    ) == {'Contaminants', 'Nutrients'}
    assert ind1['InformationType']['text'] == '2024 Article 8'

    # the assessment metadata fields are carried onto the indicator row
    assert ind1['SourceAssessmentIndicator']['raw'] == 'National; HELCOM'
    assert ind1['ReportingMethodIndicator']['raw'] == 'Type A'
    assert ind1['UniqueReference']['raw'] == 'https://ref.example/ind1'
    assert ind1['RelatedTargets']['raw'] == '1'
    assert ind1['MarineReportingUnit']['raw'] == 'ANS-DE-1; ANS-DE-2'
    fr = next(r for r in rows if r['CountryCode']['raw'] == 'FR')
    assert fr['DatasetVoidReason']['raw'] == 'Data-NotElectronic'
    assert set(
        fr['RegionalAssessmentArea']['raw'].replace(' ', '').split(';')
    ) == {'MWE', 'MWE-FR'}


def test_2024_missing_dataset_and_feature_data():
    provider = P2024(selections={}, page=0, page_size=10)
    rows = provider.build_data()['rows']

    # assessment with no dataset: kept once, dataset cells empty, context and
    # the assessment's own reporting date still present
    ind3 = next(
        r for r in rows
        if r['CountryCode']['raw'] == 'DE'
        and r['IndicatorCode']['raw'] == 'IND3'
    )
    assert ind3['URL']['raw'] is None
    assert ind3['URL']['empty'] is True
    assert ind3['GEScomponent']['empty'] is True
    assert ind3['Feature']['empty'] is True
    assert ind3['SourceAssessmentIndicator']['raw'] == 'National'
    assert ind3['DatasetVoidReason']['raw'] == 'Data-InPrep'
    assert ind3['Region']['raw'] == 'ANS'
    assert ind3['ReportingDate']['empty'] is False

    # dataset whose assessment has no feature rows: kept, feature cells empty
    ind4 = next(
        r for r in rows
        if r['CountryCode']['raw'] == 'SE'
        and r['IndicatorCode']['raw'] == 'IND4'
    )
    assert ind4['URL']['raw'] == 'http://ds4'
    assert ind4['GEScomponent']['empty'] is True
    assert ind4['Feature']['empty'] is True
    assert ind4['SourceAssessmentIndicator']['raw'] == 'HELCOM'


def test_multi_columns_collapse_at_ten():
    # every format='multi' column declares maxItems=10 so the frontend can
    # collapse long lists with a "Show N more" control
    columns = {c['key']: c for c in P2024(
        selections={}, page=0, page_size=1).build_columns()}

    for key in ('GEScomponent', 'Feature', 'URL', 'MD_URL',
                'RelatedTargets', 'RegionalAssessmentArea'):
        assert columns[key]['maxItems'] == 10, key

    # the 2018 datasets / features collapse the same way
    columns_2018 = {c['key']: c for c in P2018(
        selections={}, page=0, page_size=1).build_columns()}

    for key in ('URL', 'MD_URL', 'GESComponent', 'Feature'):
        assert columns_2018[key]['format'] == 'multi', key
        assert columns_2018[key]['maxItems'] == 10, key

    assert columns_2018['MarineReportingUnit']['format'] == 'mru_multi'

    # non multi columns keep the default (no collapse)
    assert columns['CountryCode']['maxItems'] is None


def test_2024_facets_and_region():
    provider = P2024(selections={}, page=0, page_size=10)

    # IND1 + the dataset-less IND3 assessment
    assert options(provider, 'member_states')['DE']['count'] == 2

    components = options(provider, 'ges_component')
    assert set(components) == {'D5C1', 'D5C2', 'D1C1'}
    assert components['D5C1']['count'] == 1

    regions = options(provider, 'region_subregions')
    assert set(regions) == {'ANS', 'MWE'}
    # IND1 + the dataset-less IND3
    assert regions['ANS']['count'] == 2
    # IND2 + IND4 (the dataset with no feature rows)
    assert regions['MWE']['count'] == 2

    assert total(P2024(
        selections={'ges_component': ['D5C1']}, page=0, page_size=10
    )) == 1
    assert total(P2024(
        selections={'region_subregions': ['MWE']}, page=0, page_size=10
    )) == 2

    data = provider.build_data()
    de = next(r for r in data['rows'] if r['CountryCode']['raw'] == 'DE')
    assert de['Region']['raw'] == 'ANS'


def test_2018_latest_import_cut_and_two_hop_features():
    provider = P2018(selections={}, page=0, page_size=10)

    # one row per indicator assessment; the ghost assessment under the old FI
    # import is dropped
    assert total(provider) == 2
    assert set(options(provider, 'member_states')) == {'FI', 'SE'}

    feature_opts = options(provider, 'feature')
    assert set(feature_opts) == {'Nutrients', 'Contaminants', 'BirdsAll'}
    assert 'Ghost' not in feature_opts

    # filtering by a feature keeps the matching assessment (one row), and the
    # datasets of that assessment stay packed into it
    assert total(P2018(
        selections={'feature': ['Contaminants']}, page=0, page_size=10
    )) == 1

    rows = provider.build_data()['rows']
    fi = next(r for r in rows if r['CountryCode']['raw'] == 'FI')
    # both datasets of the assessment are packed into one row
    assert fi['URL']['raw'] == 'http://ds1;http://ds2'
    assert fi['URL']['items'] == ['http://ds1', 'http://ds2']
    assert fi['MD_URL']['raw'] == 'http://md1'
    assert fi['GESComponent']['raw'] == 'D5C1'
    assert fi['Feature']['raw'] == 'Contaminants;Nutrients'
    assert set(fi['MarineReportingUnit']['raw'].split(';')) == {
        'BAL-FI-1', 'BAL-FI-2'
    }
    assert fi['InformationType']['text'] == '2018 Article 8'


def test_2018_derived_region():
    provider = P2018(selections={}, page=0, page_size=10)
    regions = options(provider, 'region_subregions')
    assert set(regions) == {'BAL'}
    # one row per indicator assessment
    assert regions['BAL']['count'] == 2

    rows = provider.build_data()['rows']
    assert all(r['Region']['raw'] == 'BAL' for r in rows)


def test_2020_descriptor_by_code_and_case():
    provider = P2020(selections={}, page=0, page_size=10)

    # one row per data-access reference
    assert total(provider) == 3

    descriptors = options(provider, 'descriptor')
    assert set(descriptors) == {'D5', 'D11', 'D1'}
    # the mixed-case programme code 'mp2' still resolves its descriptor
    assert descriptors['D1']['count'] == 1
    assert descriptors['D5']['count'] == 2

    assert total(P2020(
        selections={'descriptor': ['D5']}, page=0, page_size=10
    )) == 2

    rows = provider.build_data()['rows']
    mp1 = next(r for r in rows if r['DataAccess']['raw'] == 'http://data1')
    assert mp1['Descriptor']['raw'] == 'D11;D5'
    assert mp1['ProgrammeCode']['raw'] == 'MP1'
    # the URL must reach the frontend as plain text: the shared
    # ``DataAccess`` transform emits ``<ul>`` HTML and, applied to a single
    # URL string, would iterate it character by character.
    assert mp1['DataAccess']['text'] == 'http://data1'
    assert '<' not in mp1['DataAccess']['text']
    assert mp1['InformationType']['text'] == (
        '2020 Article 11 Monitoring programmes'
    )


def test_2020_derived_region():
    provider = P2020(selections={}, page=0, page_size=10)
    regions = options(provider, 'region_subregions')
    assert set(regions) == {'ANS', 'MWE'}
    assert regions['ANS']['count'] == 2
    assert regions['MWE']['count'] == 1


def test_2012_trimmed_country_and_region():
    provider = P2012(selections={}, page=0, page_size=10)

    assert total(provider) == 3

    countries = options(provider, 'member_states')
    assert set(countries) == {'DE', 'FR'}
    assert countries['DE']['count'] == 2

    regions = options(provider, 'region_subregions')
    assert set(regions) == {'ANS', 'MWE'}
    assert regions['ANS']['count'] == 2

    rows = provider.build_data()['rows']
    de = next(r for r in rows if r['DatasetRecord']['raw'] == 'Record A')
    assert de['CountryCode']['text'] == 'Germany'
    assert de['Region']['raw'] == 'ANS'
    assert de['ReportingFeature']['raw'] == 'D1'
    assert de['InformationType']['text'] == '2012 Article 19.3'


def test_2012_has_only_common_facets():
    provider = P2012(selections={}, page=0, page_size=10)
    names = {facet['name'] for facet in provider.build_filters()}
    assert names == {'member_states', 'region_subregions'}


def test_information_type_is_static():
    for provider, text in (
        (P2024, '2024 Article 8'),
        (P2020, '2020 Article 11 Monitoring programmes'),
        (P2018, '2018 Article 8'),
        (P2012, '2012 Article 19.3'),
    ):
        cell = provider(
            selections={}, page=0, page_size=1
        ).build_data()['rows'][0]['InformationType']
        assert cell['raw'] == text
        assert cell['text'] == text


def test_sort_direction():
    def first(provider, sort, direction, key):
        return provider(
            selections={}, page=0, page_size=1,
            sort=sort, direction=direction,
        ).build_data()['rows'][0][key]['raw']

    assert first(P2024, 'CountryCode', 'asc', 'CountryCode') == 'DE'
    assert first(P2024, 'CountryCode', 'desc', 'CountryCode') == 'SE'
    # sorting by the derived region is ignored (not mapped) and falls back to
    # the default ordering instead of failing
    assert first(P2024, 'Region', 'desc', 'CountryCode') == 'DE'


def test_link_and_descriptor_helpers():
    from wise.msfd.explorer.providers.summary import LINK_RE, descriptors_in

    # a link starts with a scheme or a bare www. host; the placeholders the
    # member states file in the link fields are not links
    assert LINK_RE.match('http://x')
    assert LINK_RE.match('Https://doi.org/10.17895/ices.advice')
    assert LINK_RE.match('www.nodc.ro')
    assert not LINK_RE.match('Metadata not available')
    assert not LINK_RE.match('nvt')
    assert not LINK_RE.match('Planned for 15 February 2019')

    assert descriptors_in('D5C1; D5C2') == ['D5']
    assert descriptors_in('D6/D1') == ['D6', 'D1']
    assert descriptors_in('D1.2') == ['D1']
    assert descriptors_in('D10C1') == ['D10']
    assert descriptors_in(u'D1B') == ['D1']
    assert descriptors_in('NotRelevant') == []
    assert descriptors_in('1.4.1') == []
    assert descriptors_in(None) == []


def summary(provider_cls, selections=None):
    return provider_cls(
        selections=selections or {}, page=0, page_size=10
    ).build_summary()


def cards(payload):
    return {card['key']: card for card in payload['cards']}


def charts(payload):
    return {chart['key']: chart for chart in payload['charts']}


def test_summary_2024():
    payload = summary(P2024)
    card = cards(payload)

    assert list(card) == ['records', 'dataset_links', 'metadata_links',
                          'descriptors', 'countries']
    assert card['records']['value'] == 4
    # IND1 packs two dataset links and two metadata links in one cell each;
    # IND3 files neither, IND4 a dataset but no metadata link
    assert (card['dataset_links']['value'],
            card['dataset_links']['valueOf']) == (4, 4)
    assert (card['metadata_links']['value'],
            card['metadata_links']['valueOf']) == (2, 2)
    assert card['descriptors']['value'] == 2
    assert card['countries']['value'] == 3

    # links are attributed to every descriptor the indicator covers
    points = charts(payload)['descriptor_distribution']['points']
    assert [point['value'] for point in points] == [1, 2]
    assert points[0]['label'].startswith('D1')
    assert points[1]['label'].startswith('D5')
    assert 'country_distribution' in charts(payload)

    # the void reason chart only counts indicators carrying a reason
    reasons = charts(payload)['void_reason']['points']
    assert sum(point['value'] for point in reasons) == 2


def test_summary_2018():
    card = cards(summary(P2018))

    # the ghost indicator filed under the superseded import is never counted
    assert card['records']['value'] == 2
    assert (card['dataset_links']['value'],
            card['dataset_links']['valueOf']) == (3, 3)
    assert (card['metadata_links']['value'],
            card['metadata_links']['valueOf']) == (2, 2)
    assert card['descriptors']['value'] == 2
    assert card['descriptors']['valueOf'] == 2


def test_summary_2020():
    payload = summary(P2020)
    card = cards(payload)

    # 2020 reports no dataset / metadata file at all: one data access card
    assert 'metadata_links' not in card
    assert card['dataset_links']['label'] == 'Data access links'
    assert (card['dataset_links']['value'],
            card['dataset_links']['valueOf']) == (3, 3)
    assert card['descriptors']['value'] == 3
    assert card['countries']['value'] == 2

    points = charts(payload)['descriptor_distribution']['points']
    assert [point['value'] for point in points] == [1, 2, 2]


def test_summary_2012():
    payload = summary(P2012)
    card = cards(payload)

    # 2012 has a single dataset link column and no GES descriptor
    assert list(card) == ['records', 'dataset_links', 'countries']
    assert card['records']['value'] == 3
    assert (card['dataset_links']['value'],
            card['dataset_links']['valueOf']) == (2, 2)
    assert card['countries']['value'] == 2

    standard = charts(payload)['metadata_standard']['points']
    assert standard == [{'label': 'ISO19115', 'value': 3}]


def test_summary_honours_selection():
    card = cards(summary(P2018, {'member_states': ['SE']}))

    assert card['records']['value'] == 1
    assert card['dataset_links']['value'] == 1
    assert card['descriptors']['value'] == 1
    # the denominator ignores the selection
    assert card['countries']['valueOf'] == 2


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
