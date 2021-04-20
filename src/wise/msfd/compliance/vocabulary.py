# -*- coding: utf-8 -*-
from collections import defaultdict, namedtuple
from datetime import datetime

from persistent.list import PersistentList
from pkg_resources import resource_filename
from pyexcel_xlsx import get_data

from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from wise.msfd import db, sql2018


REPORTING_HISTORY_ENV = PersistentList()


ASSESSED_ARTICLES = (
    ('Art3', 'Art. 3(1) Marine waters',),
    ('Art4', 'Art. 4/2017 Decision: Marine regions, subregions, '
     'and subdivisions '),
    ('Art5', 'Art. 5(2)', ),
    ('Art6', 'Art. 6 Regional cooperation', ),
    ('Art7', 'Art. 7 Competent authorities', ),
    ('Art8', 'Art. 8 Initial assessment (and Art. 17 updates)', ),
    ('Art9', 'Art. 9 Determination of GES (and Art. 17 updates) ', ),
    ('Art10', 'Art. 10 Environmental targets (and Art. 17 updates)', ),
    ('Art11', 'Art. 11 Monitoring programmes (and Art. 17 updates)', ),
    ('Art13', 'Art. 13 Programme of measures (and Art. 17 updates)', ),
    ('Art14', 'Art. 14 Exceptions (and Art. 17 updates)', ),
    ('Art18', 'Art. 18 Interim report on programme of measures', ),
    ('Art19_3', 'Art. 19(3) Access to data', ),
)


# TODO: sort this vocabulary (somehow)
GES_DESCRIPTORS = (
    ('D1', 'D1 Biodiversity'),
    ('D1 Birds', 'D1 Biodiversity – birds'),
    ('D1 Cephalopods', 'D1 Biodiversity –  cephalopods'),
    ('D1 Fish', 'D1 Biodiversity – fish'),
    ('D1 Mammals', 'D1 Biodiversity – mammals'),
    ('D1 Pelagic habitats', 'D1 Biodiversity – pelagic habitats'),
    ('D1 Reptiles', 'D1 Biodiversity – reptiles'),
    ('D2', 'D2 Non-indigenous species'),
    ('D3', 'D3 Commercial fish and shellfish'),
    ('D4/D1', 'D4 - Food webs / D1 Biodiversity - ecosystems'),
    ('D5', 'D5 Eutrophication'),
    ('D6/D1', 'D6 - Sea-floor integrity / D1 Biodiversity - benthic habitats'),
    ('D7', 'D7 Hydrographical changes'),
    ('D8', 'D8 Contaminants'),
    ('D9', 'D9 Contaminants in seafood'),
    ('D10', 'D10 Marine litter'),
    ('D11', 'D11 Energy, incl. underwater noise'),
)


@db.use_db_session('2018')
def get_all_countries():
    count, res = db.get_all_records(
        sql2018.LCountry
    )
    countries = [(x.Code, x.Country) for x in res]

    return countries


def vocab_from_pairs(pairs):
    """ Build a zope.schema vocabulary from pairs of (value(token), title)
    """
    terms = []

    for val, title in pairs:
        term = SimpleTerm(val, val, title)
        terms.append(term)

    return SimpleVocabulary(terms)


def vocab_from_list(values):
    return SimpleVocabulary([SimpleTerm(x, x, x) for x in values])


descriptors_vocabulary = vocab_from_pairs(GES_DESCRIPTORS)
articles_vocabulary = vocab_from_pairs(ASSESSED_ARTICLES)


REGIONS = {
    "ABI": "NE Atlantic: Bay of Biscay & Iberian Coast",
    "ACS": "NE Atlantic: Celtic Seas",
    "AMA": "NE Atlantic: Macaronesia",
    "ANS": "NE Atlantic: Greater North Sea",
    # , incl. Kattegat & English Channel
    "BAL": "Baltic Sea",
    "BLK": "Black Sea",
    "MAD": "Mediterranean: Adriatic Sea",
    "MAL": "Mediterranean: Aegean-Levantine Sea",
    "MIC": "Mediterranean: Ionian Sea & Central Mediterranean Sea",
    "MWE": "Mediterranean: Western Mediterranean Sea"
}


REGIONS_SIMPLIFIED = {
    'North East Atlantic': ('ABI', 'ACS', 'AMA', 'ANS'),
    'West Mediterranean': ('MWE',),
    # 'MWE' is added to Mediterranean region because the 2012 assessments
    # for Spain are done for Mediterranean level
    'Mediterranean': ('MAD', 'MAL', 'MIC', 'MWE'),
    'Baltic Sea': ('BAL',),
    'North Sea': ('ANS',),
    'Black Sea': ('BLK',),
}

Region = namedtuple('Region', ['code', 'title', 'subregions',
                               'countries', 'is_main'])

REGIONAL_DESCRIPTORS_REGIONS = [
    # Main regions
    Region('BAL', 'Baltic Sea', ('BAL',),
           ('FI', 'EE', 'LV', 'LT', 'PL', 'DE', 'DK', 'SE'), True),
    Region('ATL', 'North East Atlantic Ocean', ('ABI', 'ACS', 'AMA', 'ANS',),
           ('SE', 'DK', 'DE', 'NL', 'BE', 'FR', 'UK', 'IE', 'ES', 'PT'), True),
    Region('MED', 'Mediterranean Sea', ('MAD', 'MAL', 'MIC', 'MWE'),
           ('UK', 'ES', 'FR', 'IT', 'MT', 'SI', 'HR', 'EL', 'CY'), True),
    Region('BLK', 'Black Sea', ('BLK',), ('BG', 'RO'), True),
    # Sub regions
    Region('ANS', 'NE Atlantic: Greater North Sea', ('ANS',),
           ('SE', 'DK', 'DE', 'NL', 'BE', 'FR', 'UK'), False),
    Region('ACS', 'NE Atlantic: Celtic Seas', ('ACS',),
           ('UK', 'IE', 'FR'), False),
    Region('ABI', 'NE Atlantic: Bay of Biscay & Iberian Coast', ('ABI',),
           ('FR', 'ES', 'PT'), False),
    Region('AMA', 'NE Atlantic: Macaronesia', ('AMA',),
           ('ES', 'PT'), False),
    Region('MWE', 'Mediterranean: Western Mediterranean Sea', ('MWE',),
           ('UK', 'ES', 'FR', 'IT'), False),
    Region('MAD', 'Mediterranean: Adriatic Sea', ('MAD',),
           ('IT', 'SI', 'HR', 'EL'), False),
    Region('MIC', 'Mediterranean: Ionian Sea & Central Mediterranean Sea',
           ('MIC',), ('IT', 'MT', 'EL'), False),
    Region('MAL', 'Mediterranean: Aegean-Levantine Sea', ('MAL',),
           ('EL', 'CY'), False),
]

ReportingHistoryENVRow = namedtuple(
    'ReportingHistoryENVRow',
    ['Sort', 'Year', 'MSFDArticle', 'TaskProduct', 'ReportType',
     'DateDue', 'DateReceived', 'CountryCode', 'FileName',
     'CIRCABC', 'WISE', 'ARES', 'LocationURL', 'Comments']
)


def get_msfd_reporting_history_from_file(file):
    res = PersistentList()
    sheets = get_data(file)
    env_data = sheets['ENV']

    indx_date_due = env_data[0].index('DateDue')
    indx_date_received = env_data[0].index('DateReceived')

    for row in env_data:
        row = [
            isinstance(x, basestring) and x.strip() or x
            for x in row
        ]
        while len(row) < 14:
            row.append('')

        date_due = row[indx_date_due]
        date_received = row[indx_date_received]

        if isinstance(date_due, datetime):
            row[indx_date_due] = date_due.date()

        if isinstance(date_received, datetime):
            row[indx_date_received] = date_received.date()

        res.append(ReportingHistoryENVRow(*row[:14]))

    return res


def parse_reporting_history_env():
    file_loc = resource_filename(
        'wise.msfd', 'data/MSFDReportingHistory_Local.xlsx'
    )

    with open(file_loc, 'rb') as file:
        res = get_msfd_reporting_history_from_file(file)

    REPORTING_HISTORY_ENV = res

    return res


@db.use_db_session('2018')
def get_regions_for_country(country_code):
    t = sql2018.MarineReportingUnit
    regions = db.get_unique_from_mapper(
        t,
        'Region',
        t.CountryCode == country_code
    )

    # blacklist main/generic regions as they do not have reported data
    # but they appear in the database. Countries affected: ES, IE, PT, IT
    blacklist = ['NotReported', 'ATL', 'MED']

    return [(code, REGIONS.get(code, code))
            for code in regions

            if code and code not in blacklist]


def make_subregions(d):
    """ switches direction of REGIONS_SIMPLIFIED

    Returns dict like: {
        'ABI': 'North East Atlantic',
    }
    """

    r = defaultdict(list)

    for k, vs in d.items():
        for v in vs:
            r[v].append(k)

    return r


SUBREGIONS_TO_REGIONS = make_subregions(REGIONS_SIMPLIFIED)
