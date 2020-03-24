import logging
import os
import tempfile
from collections import defaultdict

import requests

import sparql
from eea.cache import cache
from wise.msfd import db, sql, sql_extra

from .utils import current_date, timeit

logger = logging.getLogger('wise.msfd')


FILENAMES_MISSING_DB = {
    'PL': (
        ('BAL', 'Art8', 'MSFD8aFeatures_20150225_135158.xml'),
        ('BAL', 'Art9', 'MSFD9GES_20150130_111719.xml'),
        ('BAL', 'Art10', 'MSFD10TI_20160226_150132.xml')
    )
}


@db.use_db_session('2012')
def all_regions():
    """ Return a list of region ids
    """

    return db.get_unique_from_mapper(
        sql_extra.MSFD4GeographicalAreaID,
        'RegionSubRegions'
    )


@db.use_db_session('2012')
def countries_in_region(regionid):
    """ Return a list of (<countryid>, <marineunitids>) pairs
    """
    t = sql_extra.MSFD4GeographicalAreaID

    return db.get_unique_from_mapper(
        t,
        'MemberState',
        t.RegionSubRegions == regionid
    )


@db.use_db_session('2012')
def muids_by_country(regions=None):
    t = sql_extra.MSFD4GeographicalAreaID
    count, records = db.get_all_records(t)
    res = defaultdict(list)

    for rec in records:
        # filter MUIDs by region, used in regional descriptors A9 2012
        if regions and rec.RegionSubRegions not in regions:
            continue

        res[rec.MemberState].append(rec.MarineUnitID)

    return dict(**res)


@db.use_db_session('2012')
def _get_report_filename_art10_2012(country, region, article, descriptor):
    mc = sql.MSFD10Import

    count, item = db.get_item_by_conditions(
        mc,
        'MSFD10_Import_ID',
        mc.MSFD10_Import_ReportingCountry == country,
        mc.MSFD10_Import_ReportingRegion == region
    )

    # TODO: analyse cases when it returns more then one file

    if count != 1:
        logger.warning("Could not find precise report (count %s) "
                       "filename for %s %s %s", country, region, article,)

        raise ValueError

        # return None

    return item.MSFD10_Import_FileName


@db.use_db_session('2012')
def _get_report_filename_art8esa_2012(country, region, article):
    mc = sql.MSFD8cImport

    count, item = db.get_item_by_conditions(
        mc,
        'MSFD8c_Import_ID',
        mc.MSFD8c_Import_ReportingCountry == country,
        mc.MSFD8c_Import_ReportingRegion == region
    )

    if count != 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    return item.MSFD8c_Import_FileName


@db.use_db_session('2012')
def _get_report_filename_art3_4_2012_db(country, region, article, descriptor):
    """ This method is not used anymore, see _get_report_filename_art3_4_2012
    """
    mc = sql.MSFD4Import

    count, item = db.get_item_by_conditions(
        mc,
        'MSFD4_Import_ID',
        mc.MSFD4_Import_ReportingCountry == country,
        # mc.MSFD8c_Import_ReportingRegion == region
    )

    if count != 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    return item.MSFD4_Import_FileName


@db.use_db_session('2012')
def _get_report_filename_art7_2012_db(country, region, article, descriptor):
    mc = sql_extra.MSCompetentAuthority

    count, item = db.get_item_by_conditions(
        mc,
        'Import_Time',
        mc.C_CD == country,
        reverse=True
    )

    if count < 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    return item.Import_FileName


@db.use_db_session('2012')
def _get_report_filename_art9_2012(country, region, article, descriptor):
    mc = sql.MSFD9Import

    count, item = db.get_item_by_conditions(
        mc,
        'MSFD9_Import_ID',
        mc.MSFD9_Import_ReportingCountry == country,
        mc.MSFD9_Import_ReportingRegion == region
    )

    # TODO: analyse cases when it returns more then one file

    if count != 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    return item.MSFD9_Import_FileName


def _get_report_filename_art8_2012(country, region, article, descriptor):
    d = descriptor.split('.')[0]

    if d in ['D1', 'D4', 'D6']:
        base = 'MSFD8a'
    else:
        base = 'MSFD8b'

    mc = getattr(sql, base + 'Import')
    idcol = base + '_Import_ID'
    filecol = base + '_Import_FileName'
    countrycol = getattr(mc, base + '_Import_ReportingCountry')
    regcol = getattr(mc, base + '_Import_ReportingRegion')

    count, item = db.get_item_by_conditions(
        mc,
        idcol,
        countrycol == country,
        regcol == region
    )

    # TODO: analyse cases when it returns more then one file

    if count != 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    return getattr(item, filecol)


def get_report_filename(report_version,
                        country, region, article, descriptor):
    """ Return the filename for imported information

    :param report_version: report "version" year: 2012 or 2018
    :param country: country code, like: 'LV'
    :param region: region code, like: 'ANS'
    :param article: article code, like: 'art9'
    :param descriptor: descriptor code, like: 'D5'
    """

    if country in FILENAMES_MISSING_DB:
        filename = [
            x[2]
            for x in FILENAMES_MISSING_DB[country]
            if x[0] == region and x[1] == article
        ]

        return filename[0]

    # 'Art8': '8b',       # TODO: this needs to be redone for descriptor
    mapping = {
        '2012': {
            'Art3': _get_report_filename_art3_4_2012,
            'Art4': _get_report_filename_art3_4_2012,
            'Art7': _get_report_filename_art7_2012,
            'Art8esa': _get_report_filename_art8esa_2012,
            'Art8': _get_report_filename_art8_2012,
            'Art9': _get_report_filename_art9_2012,
            'Art10': _get_report_filename_art10_2012,
        },
        '2018': {
            'Art7': _get_report_filename_art7_2018,
            'Art3': _get_report_filename_art3_4_2018,
            'Art4': _get_report_filename_art3_4_2018,
        }
    }

    handler = mapping[report_version][article]

    return handler(country, region, article, descriptor)


@cache(lambda func, filename: func.__name__ + filename + current_date())
@timeit
def get_report_file_url(filename):
    """ Retrieve the CDR url based on query in ContentRegistry
    """

#     q = """
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
# PREFIX dc: <http://purl.org/dc/dcmitype/>
# PREFIX dcterms: <http://purl.org/dc/terms/>
#
# SELECT ?file
# WHERE {
# ?file a dc:Dataset .
# ?file dcterms:date ?date .
# FILTER regex(str(?file), '%s')
# }
# ORDER BY DESC(?date)
# LIMIT 1""" % filename

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>

SELECT ?file
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml'.
FILTER regex(str(?file), '/%s')
}
ORDER BY DESC(?date)
LIMIT 1""" % filename

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')

    logger.info("Getting filename with SPARQL: %s", filename)
    try:
        req = service.query(q)
        rows = req.fetchall()

        urls = []

        for row in rows:
            url = row[0].value
            splitted = url.split('/')

            filename_from_url = splitted[-1]

            if filename == filename_from_url:
                urls.append(url)

        assert len(urls) == 1
    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'filename url: %s', filename)

        raise

    logger.info("Got file with url: %s", urls[0])

    return urls[0]


@cache(lambda func, url: func.__name__ + url + current_date())
def get_factsheet_url(url):
    """ Returns the URL for the conversion that gets the "HTML Factsheet"
    """
    cdr = "http://cdr.eionet.europa.eu/Converters/run_conversion"\
        "?source=remote&file="

    base = url.replace('http://cdr.eionet.europa.eu/', '')
    base = base.replace('https://cdr.eionet.europa.eu/', '')

    resp = requests.get(url + '/get_possible_conversions')
    j = resp.json()
    ids = [x
           for x in j['remote_converters']

           if x['description'] == 'HTML Factsheet']

    if ids:
        return '{}{}&conv={}'.format(cdr, base, ids[0]['convert_id'])


@timeit
def get_xml_report_data(filename):
    if not filename:
        return ""

    xmldir = os.environ.get("MSFDXML")

    if not xmldir:
        xmldir = tempfile.gettempdir()

    assert '..' not in filename     # need better security?

    fpath = os.path.join(xmldir, filename)

    text = ''

    if filename in os.listdir(xmldir):
        with open(fpath) as f:
            text = f.read()

    if not text:
        # TODO: handle this problem:
        # https://cr.eionet.europa.eu/factsheet.action?uri=http%3A%2F%2Fcdr.eionet.europa.eu%2Fro%2Feu%2Fmsfd8910%2Fblkro%2Fenvux97qw%2FRO_MSFD10TI_20130430.xml&page1=http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23type
        url = get_report_file_url(filename)
        req = requests.get(url)
        text = req.content
        logger.info("Requesting XML file: %s", fpath)

        with open(fpath, 'wb') as f:
            f.write(text)
    else:
        logger.info("Using cached XML file: %s", fpath)

    assert text, "Report data could not be fetched %s" % url

    return text


@db.use_db_session('2012')
def country_ges_components(country_code):
    """ Get the assigned ges components for a country
    """

    t = sql.t_MSFD_19a_10DescriptiorsCriteriaIndicators
    count, res = db.get_all_records(
        t,
        t.c.MemberState == country_code,
    )

    cols = t.c.keys()
    recs = [
        {
            k: v for k, v in zip(cols, row)
        } for row in res
    ]

    return list(set([c['Descriptors Criterion Indicators'] for c in recs]))


def _get_report_filename_art3_4_2012(country, region, article, descriptor):
    schema = 'http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd'
    obligation = '608'

    return __get_report_filename_art3_4(country, region, schema, obligation)


def _get_report_filename_art3_4_2018(country, region, article, descriptor):
    schema = 'http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd'
    obligation = '760'

    return __get_report_filename_art3_4(country, region, schema, obligation)


@cache(lambda func, *args: func.__name__ + "_".join(args) + current_date())
@timeit
def __get_report_filename_art3_4(country, region, schema, obligation):
    """ Retrieve from CDR the latest filename
    for Article 7 competent authorities
    """

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT ?file
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml' .
?file terms:isPartOf ?isPartOf .
?file cr:xmlSchema ?schema .
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '%s')
FILTER (str(?schema) = '%s')
FILTER regex(str(?file), '%s')
}
ORDER BY DESC(?date)
LIMIT 1    
""" % (country.upper(), obligation, schema, region.upper())

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    filename = ''
    try:
        req = service.query(q)
        rows = req.fetchall()
        if not rows:
            return filename

        url = rows[0][0].value
        splitted = url.split('/')
        filename = splitted[-1]
    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'Article 7 country: %s', country)

        raise

    return filename


def _get_report_filename_art7_2012(country, region, article, descriptor):
    """ Retrieve from CDR the latest filename
    for Article 7 competent authorities
    """

    schema = 'http://water.eionet.europa.eu/schemas/dir200856ec/MSCA_1p0.xsd'

    return __get_report_filename_art7(country, schema)


def _get_report_filename_art7_2018(country, region, article, descriptor):
    schema = 'http://dd.eionet.europa.eu/schemas/MSFD/MSFDCA_1p0.xsd'

    return __get_report_filename_art7(country, schema)


@cache(lambda func, *args: func.__name__ + "".join(args) + current_date())
@timeit
def __get_report_filename_art7(country, schema):
    """ Retrieve from CDR the latest filename
    for Article 7 competent authorities
    """

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT ?file
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml' .
?file terms:isPartOf ?isPartOf .
?file cr:xmlSchema ?schema .
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '607')
FILTER (str(?schema) = '%s')
}
ORDER BY DESC(?date)
LIMIT 1    
""" % (country.upper(), schema)

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    filename = ''
    try:
        req = service.query(q)
        rows = req.fetchall()
        url = rows[0][0].value
        splitted = url.split('/')
        filename = splitted[-1]
    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'Article 7 country: %s', country)

        raise

    return filename


@cache(lambda func, *args: func.__name__ + "".join(args) + current_date())
@timeit
def get_all_report_filenames_art7(country):
    """ Retrieve from CDR the latest filename
    for Article 7 competent authorities
    """

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT distinct ?file
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml' .
?file terms:isPartOf ?isPartOf .
?file cr:xmlSchema ?schema .
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '607')
FILTER (str(?schema) IN ('http://dd.eionet.europa.eu/schemas/MSFD/MSFDCA_1p0.xsd', 
'http://water.eionet.europa.eu/schemas/dir200856ec/MSCA_1p0.xsd'))
}
ORDER BY DESC(?date)""" % (country.upper())

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    filenames = []

    try:
        req = service.query(q)
        rows = req.fetchall()

        for row in rows:
            url = row[0].value
            splitted = url.split('/')
            filename = splitted[-1]
            filenames.append(filename)

    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'Article 7 country: %s', country)

        raise

    return filenames
