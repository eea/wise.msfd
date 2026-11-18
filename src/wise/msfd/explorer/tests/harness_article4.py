# pylint: skip-file
"""Article 4 / 2024 explorer harness.

Exercises the 2024 provider end to end against an in-memory SQLite database
seeded with representative rows. It covers the switch to the reporting table
(``data.ART4_GEO_GeographicalBoundaries``) joined to the MRU publication for
the area, the ``desigEnd`` cut-off (past designations hidden, open ended ones
kept), the ``MarineReportingUnitIdOld`` column and the country-scoped size
join.

Run it inside the backend container, where the package (and its label data)
imports:

    docker exec -i marine-backend-p6 /app/bin/python \
        -m wise.msfd.explorer.tests.harness_article4
"""
from __future__ import absolute_import

from sqlalchemy import (Column, Float, MetaData, Table, Unicode,
                        create_engine)
from sqlalchemy.orm import sessionmaker

from wise.msfd.explorer.providers.article4_2024 import (
    Article4Cycle2024Provider)
from wise.msfd.explorer.providers.registry import (
    PROVIDERS,
    available_providers,
)

metadata = MetaData()

boundaries = Table(
    'ART4_GEO_GeographicalBoundaries', metadata,
    Column('CountryCode', Unicode(2), primary_key=True),
    Column('MarineReportingUnitId', Unicode, primary_key=True),
    Column('MarineReportingUnitIdOld', Unicode),
    Column('MarineReportingUnitName', Unicode),
    Column('RegionSubRegion', Unicode),
    Column('legisSName', Unicode),
    Column('nameText', Unicode),
    Column('desigEnd', Unicode),
)

publication = Table(
    'MarineReportingUnit_Publication', metadata,
    Column('MarineReportingUnitId', Unicode, primary_key=True),
    Column('countryCode', Unicode(2), primary_key=True),
    Column('sizeValue', Float),
)

engine = create_engine('sqlite://')
metadata.create_all(engine)
session = sessionmaker(bind=engine)()


def seed():
    session.execute(boundaries.insert(), [
        # designation already ended: must be hidden
        {'CountryCode': 'DE', 'MarineReportingUnitId': 'DE-1',
         'MarineReportingUnitIdOld': 'DE-1-old',
         'MarineReportingUnitName': 'Ended designation',
         'RegionSubRegion': 'ANS', 'legisSName': 'WFD',
         'nameText': 'Alt', 'desigEnd': '2020-01-01'},
        # ongoing designation: visible
        {'CountryCode': 'DE', 'MarineReportingUnitId': 'DE-2',
         'MarineReportingUnitIdOld': 'DE-2-old',
         'MarineReportingUnitName': 'Open designation',
         'RegionSubRegion': 'ANS', 'legisSName': 'WFD',
         'nameText': 'Neu', 'desigEnd': '2030-01-01'},
        # empty end date: open ended, visible
        {'CountryCode': 'DE', 'MarineReportingUnitId': 'DE-3',
         'MarineReportingUnitIdOld': None,
         'MarineReportingUnitName': 'No end date',
         'RegionSubRegion': 'BAL', 'legisSName': 'MSFD',
         'nameText': None, 'desigEnd': ''},
        # null end date, and the same id in another country: both kept
        # blank (single space) legislation: must not become a facet option
        {'CountryCode': 'FR', 'MarineReportingUnitId': 'DE-3',
         'MarineReportingUnitIdOld': None,
         'MarineReportingUnitName': 'No end date',
         'RegionSubRegion': 'MWE', 'legisSName': ' ',
         'nameText': None, 'desigEnd': None},
    ])
    session.execute(publication.insert(), [
        {'MarineReportingUnitId': 'DE-2', 'countryCode': 'DE',
         'sizeValue': 100.0},
        {'MarineReportingUnitId': 'DE-3', 'countryCode': 'DE',
         'sizeValue': 5.0},
        # same MRU id as DE-3 but a different country: must not cross over
        {'MarineReportingUnitId': 'DE-3', 'countryCode': 'FR',
         'sizeValue': 999.0},
    ])
    session.commit()


class P2024(Article4Cycle2024Provider):
    boundaries = boundaries
    publication = publication

    def _get_session(self):
        return session


def facet_by_name(provider, name):
    filters = {facet['name']: facet for facet in provider.build_filters()}
    return filters[name]


def data(selections=None, page=0, page_size=10):
    return P2024(
        selections=selections or {}, page=page, page_size=page_size
    ).build_data()


def rows(selections=None):
    return data(selections)['rows']


def test_registry_lists_the_cycle():
    assert ('4', '2024') in [
        (p['article'], p['cycle']) for p in available_providers()
    ]


def test_every_provider_declares_its_groups_once():
    """Every facet of every provider sits in a group, and the facets of one
    group are declared together, so the filters payload reads in the order the
    Frontend renders it (no group split over two places)."""
    for provider in PROVIDERS:
        keys = [
            facet.group.key if facet.group else None
            for facet in provider.facets
        ]
        label = '{} {}'.format(provider.article, provider.cycle)

        assert None not in keys, label

        runs = [key for index, key in enumerate(keys)
                if index == 0 or keys[index - 1] != key]

        assert len(runs) == len(set(runs)), (label, keys)


def test_past_designations_are_hidden():
    result = data()
    assert result['pagination']['total'] == 3, result['pagination']

    mru_ids = [
        row['MarineReportingUnitId']['raw'] for row in result['rows']
    ]
    assert 'DE-1' not in mru_ids, mru_ids
    # the same id in two countries is kept twice (one row each)
    assert mru_ids.count('DE-3') == 2, mru_ids


def test_id_old_column_is_present():
    columns = {column['key']: column for column in data()['columns']}
    assert 'MarineReportingUnitIdOld' in columns
    assert columns['MarineReportingUnitIdOld']['label'] == (
        'Marine Reporting Unit ID (old)'
    )
    by_id = {row['MarineReportingUnitId']['raw']: row for row in rows()}
    assert by_id['DE-2']['MarineReportingUnitIdOld']['raw'] == 'DE-2-old'


def test_area_comes_from_the_publication_of_the_same_country():
    areas = {
        row['MarineReportingUnitId']['raw']: row['Area']['raw']
        for row in rows()
    }
    # DE-3 exists in DE (5) and FR (999): the join must not cross the two.
    # dict keeps the last of the duplicate id, so check the full list too.
    assert sorted(
        (row['MarineReportingUnitId']['raw'], float(row['Area']['raw']))
        for row in rows()
    ) == [('DE-2', 100.0), ('DE-3', 5.0), ('DE-3', 999.0)], areas


def test_area_facet_uses_the_joined_size():
    area = facet_by_name(data_provider(), 'area')
    assert area['min'] == 5.0, area
    assert area['max'] == 999.0, area


def test_area_filter_narrows_the_rows():
    found = rows({'area': ['500', '2000']})
    assert len(found) == 1, found
    assert found[0]['MarineReportingUnitId']['raw'] == 'DE-3'
    assert float(found[0]['Area']['raw']) == 999.0


def test_summary_ignores_ended_designations():
    summary = P2024(
        selections={}, page=0, page_size=10
    ).build_summary()
    cards = {card['key']: card for card in summary['cards']}
    assert cards['mru_count']['value'] == 3, cards['mru_count']
    assert round(cards['total_area']['value'], 2) == 1104.0, cards


def test_blank_legislation_is_not_a_facet_option():
    legislation = facet_by_name(data_provider(), 'legislation')
    values = [option['value'] for option in legislation['options']]
    assert values == ['MSFD', 'WFD'], values


def test_facets_travel_with_their_group():
    """The Filters panel bands the facets by group, so every facet must ship
    one (see ``providers/groups.py``) and the provider must declare the facets
    band by band (the frontend keeps the declaration order inside a band)."""
    filters = data_provider().build_filters()
    groups = [facet['group'] for facet in filters]

    assert all(group and group['key'] and group['label'] for group in groups), \
        groups
    assert [facet['name'] for facet in filters] == [
        'member_states', 'region_subregions', 'area', 'mru_id', 'mru_name',
        'legislation',
    ]
    assert [group['key'] for group in groups] == [
        'location', 'location', 'unit', 'unit', 'unit', 'legislation',
    ]
    # the bands are sorted by this in the frontend, so it must be a number
    assert all(isinstance(group['order'], int) for group in groups), groups


def data_provider():
    return P2024(selections={}, page=0, page_size=10)


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
