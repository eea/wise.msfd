# pylint: skip-file
"""data.py"""
from __future__ import absolute_import
import csv
import logging
import os
import re
import tempfile
from collections import defaultdict
from datetime import datetime

import requests
from pkg_resources import resource_filename

import sparql
from eea.cache import cache
from wise.msfd import db, sql, sql_extra, sql2018

from six.moves import zip
from .utils import current_date, timeit


logger = logging.getLogger('wise.msfd')


ART13_FIX_FILENAME = re.compile(r'^[0-9]{2}\-')


FILENAMES_MISSING_DB_ALL = {
    'PL': (
        ('BAL', 'Art8', 'MSFD8aFeatures_20150225_135158.xml'),
        ('BAL', 'Art9', 'MSFD9GES_20150130_111719.xml'),
        ('BAL', 'Art10', 'MSFD10TI_20160226_150132.xml')
    ),
    'MT': (
        ('MIC', 'Art8', 'MSFD8aFeatures_20131105_121510.xml'),
        ('MIC', 'Art9', 'MSFD9GES_20131105_121546.xml'),
        ('MIC', 'Art10', 'MSFD10TI_20140502_095401.xml')
    ),
    'ES': (
        ('ABI', 'Art8', ('ABIES-NOR_MSFD8aFeatures_20130430.xml',
                         'ABIES-SUD_MSFD8aFeatures_20130513.xml')),
        ('ABI', 'Art9', ('ABIES-NOR_MSFD9GES_20121210.xml',
                         'ABIES-SUD_MSFD9GES_20121210.xml')),
        ('ABI', 'Art10', ('ABIES-NOR_MSFD10TI.xml',
                          'ABIES-SUD_MSFD10TI.xml')),
        ('AMA', 'Art8', 'AMAES_MSFD8aFeatures_20131004.xml'),
        ('AMA', 'Art9', 'AMAES_MSFD9GES_20121210.xml'),
        ('AMA', 'Art10', 'AMAES_MSFD10TI_20130412.xml'),
        ('MWE', 'Art8', ('MWEES-ESAL_MSFD8aFeatures_20130517.xml',
                         'MWEES-LEBA_MSFD8aFeatures_20130624.xml')),
        ('MWE', 'Art9', ('MWEES-ESAL_MSFD9GES_20121210.xml',
                         'MWEES-LEBA_MSFD9GES_20121210.xml')),
        ('MWE', 'Art10', ('MWEES-ESAL_MSFD10TI.xml',
                          'MWEES-LEBA_MSFD10TI.xml')),
    ),
    'HR': (
        ('MAD', 'Art8', 'MADHR_MSFD8aFeatures_20130610.xml'),
        ('MAD', 'Art9', 'MADHR_MSFD9GES_20141014.xml'),
        ('MAD', 'Art10', 'MADHR_MSFD10TI_20141014.xml'),
    ),
}

FILENAMES_MISSING_DB_8b = {
    'ES': (
        ('ABI', 'Art8', ('ABIES-NOR_MSFD8bPressures_20121015.xml',
                         'ABIES-SUD_MSFD8bPressures_20130722.xml')),
        ('AMA', 'Art8', 'AMAES_MSFD8bPressures_20121015.xml'),
        ('MWE', 'Art8', ('MWEES-ESAL_MSFD8bPressures_20130726.xml',
                         'MWEES-LEBA_MSFD8bPressures_20121015.xml')),
    ),
    'MT': (
        ('MIC', 'Art8', 'MSFD8bPressures_20140826_082900.xml'),
    ),
    'HR': (
        ('MAD', 'Art8', 'MADHR_MSFD8bPressures_20130610.xml'),
    )
}


def _extract_pdf_assessments():
    """_extract_pdf_assessments"""
    data = []
    csv_f = resource_filename('wise.msfd',
                              'data/pdf_assessments.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter='\t', quotechar='|')

        for row in csv_file:
            data.append(row)

    return data


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
    """muids_by_country"""
    t = sql_extra.MSFD4GeographicalAreaID
    _, records = db.get_all_records(t)
    res = defaultdict(list)

    for rec in records:
        # filter MUIDs by region, used in regional descriptors A9 2012

        if regions and rec.RegionSubRegions not in regions:
            continue

        res[rec.MemberState].append(rec.MarineUnitID)

    return dict(**res)


@db.use_db_session('2012')
def _get_report_filename_art10_2012(country, region, article, descriptor):
    """_get_report_filename_art10_2012"""
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
def _get_report_filename_art8esa_2012(country, region, article, descriptor):
    """_get_report_filename_art8esa_2012"""
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
    """_get_report_filename_art7_2012_db"""
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
    """_get_report_filename_art9_2012"""
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
    """_get_report_filename_art8_2012"""
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


def _get_report_fileurl_art11_2014(country, region, article, descriptor):
    """_get_report_fileurl_art11_2014"""
    # return [
    #     'https://cdr.eionet.europa.eu/de/eu/msfd_mp/balde/envvfjbwg/BALDE_MSFD11Mon_20141105.xml',
    #     'https://cdr.eionet.europa.eu/de/eu/msfd_mp/balde/envu58cfw/BALDE_MSFD11MonSub_BALDE_Sub_099_20141015.xml'
    # ]

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
?file schema:restricted ?restricted.
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '611')
FILTER (str(?schema) = 'http://dd.eionet.europa.eu/schemas/MSFD11Mon/MSFD11MonSub_1p0.xsd'
|| str(?schema) = 'http://dd.eionet.europa.eu/schemas/MSFD11Mon/MSFD11Mon_1p1.xsd')
#FILTER regex(str(?file), '/%s')
#FILTER (?restricted = 0)
}
ORDER BY DESC(?date)
""" % (country.upper(), region.lower())

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')

    logger.info("Getting fileurl Art11 with SPARQL: %s - %s",
                country, region)
    try:
        req = service.query(q)
        rows = req.fetchall()

        urls = []

        for row in rows:
            url = row[0].value
            # splitted = url.split('/')

            # filename_from_url = splitted[-1]

            urls.append(url)

    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'Art11: %s - %s', country, region)

        raise

    return urls


def get_report_fileurl_art131418_2016(filename, country, region, article):
    """get_report_fileurl_art131418_2016"""
    schemas_mapping = {
        'Art13': 'http://dd.eionet.europa.eu/schemas/MSFD13/MSFD13_1p0.xsd',
        'Art14': 'http://dd.eionet.europa.eu/schemas/MSFD13/MSFD13_1p0ex.xsd',
        'Art18': 'http://dd.eionet.europa.eu/schemas/MSFD13/ART18.xsd'
    }

    obligation_mapping = {
        'Art13': '612',
        'Art14': '612',
        'Art18': '661'
    }

    schema = schemas_mapping[article]
    obligation = obligation_mapping[article]

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
?file schema:restricted ?restricted.
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '%s')
FILTER (str(?schema) = '%s')
FILTER regex(str(?file), '/%s')
#FILTER (?restricted = 0)
}
ORDER BY DESC(?date)
""" % (country.upper(), obligation, schema, filename)

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')

    logger.info("Getting fileurl %s with SPARQL: %s - %s",
                article, country, region)
    try:
        req = service.query(q)
        rows = req.fetchall()

        urls = []

        for row in rows:
            url = row[0].value

            urls.append(url)

    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         '%s: %s - %s', article, country, region)

        raise
    
    if urls:
        return urls[0]

    return ''
    

@db.use_db_session('2012')
def _get_report_filename_art13_2016(country, region, article, descriptor):
    """_get_report_filename_art13_2016"""
    mc = sql.MSFD13Import

    count, items = db.get_all_records(
        mc,
        mc.MemberStates == country,
        mc.Region == region,
        mc.Description == 'Success'
    )

    file_names = []
    
    for item in items:
        file_name = item.FileName

        if 'Exception' in file_name:
            continue

        if 'exemptions' in file_name:
            continue

        if file_name:
            file_name = ART13_FIX_FILENAME.sub('', file_name)

        file_names.append(file_name)

    # TODO: analyse cases when it returns more then one file
    if len(file_names) > 1:
        logger.warning("More filenames found for %s %s %s",
                       country, region, article,)

        return file_names[0]

    if not file_names:
        logger.warning("Could not find filename for %s %s %s",
                       country, region, article,)

        return None

    return file_names[0]


@db.use_db_session('2012')
def _get_report_filename_art14_2016(country, region, article, descriptor):
    """_get_report_filename_art14_2016"""
    mc = sql.MSFD13Import

    count, items = db.get_all_records(
        mc,
        mc.MemberStates == country,
        mc.Region == region,
        mc.Description == 'Success'
    )

    file_names = []
    
    for item in items:
        file_name = item.FileName

        if 'Measure' in file_name:
            continue
        
        if 'Mesure' in file_name:
            continue
        
        if file_name:
            file_name = ART13_FIX_FILENAME.sub('', file_name)

        file_names.append(file_name)

    # TODO: analyse cases when it returns more then one file
    if len(file_names) > 1:
        logger.warning("More filenames found for %s %s %s",
                       country, region, article,)

        return file_names[0]

    if not file_names:
        logger.warning("Could not find filename for %s %s %s",
                       country, region, article,)

        return None

    return file_names[0]


@db.use_db_session('2018')
def _get_report_filename_art18_2018(country, region, article, descriptor):
    """_get_report_filename_art18_2018"""
    mc = sql2018.ReportedInformation

    count, items = db.get_all_records(
        mc,
        mc.CountryCode == country,
        mc.Schema == 'ART18'
    )

    # file_names = []
    
    # TODO: analyse cases when it returns more then one file
    if len(items) != 1:
        logger.warning("Could not find report filename for %s %s %s",
                       country, region, article,)

        return None

    file_name = items[0].ReportedFileLink.split('/')[-1]

    return file_name


def get_report_filename(report_version,
                        country, region, article, descriptor):
    """ Return the filename for imported information

    :param report_version: report "version" year: 2012 or 2018
    :param country: country code, like: 'LV'
    :param region: region code, like: 'ANS'
    :param article: article code, like: 'art9'
    :param descriptor: descriptor code, like: 'D5'
    """
    d = descriptor.split('.')[0]

    if article != 'Art8':
        filenames = FILENAMES_MISSING_DB_ALL
    elif d in ['D1', 'D4', 'D6']:
        filenames = FILENAMES_MISSING_DB_ALL
    else:
        filenames = FILENAMES_MISSING_DB_8b

    if country in filenames:
        filename = [
            x[2]

            for x in filenames[country]

            if x[0] == region and x[1] == article
        ]
        if filename:
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
        '2014': {
            'Art11': _get_report_fileurl_art11_2014,
        },
        '2016': {
            'Art13': _get_report_filename_art13_2016,
            'Art14': _get_report_filename_art14_2016,
        },
        '2018': {
            'Art7': _get_report_filename_art7_2018,
            'Art3': _get_report_filename_art3_4_2018,
            'Art4': _get_report_filename_art3_4_2018,
            'Art18': _get_report_filename_art18_2018,
        }
    }

    handler = mapping[report_version][article]

    return handler(country, region, article, descriptor)


@cache(lambda func, filename, country_code: 
        func.__name__ + filename + country_code + current_date())
@timeit
def get_report_file_url(filename, country_code=''):
    """ Retrieve the CDR url based on query in ContentRegistry
    """

    if 'http' in filename:
        # already a url

        return filename

    country_filter = ''

    if country_code:
        country_filter = "FILTER (?notation = '{}')".format(country_code)

    if country_code in ('EL', 'GR'):
        country_filter = "FILTER (?notation in ('GR', 'EL'))"

    if country_code in ('LT', ):
        if ',' in filename:
            filename = filename.replace(',', '%2C')

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT ?file
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml'.
?file terms:isPartOf ?isPartOf .
?isPartOf schema:locality ?locality .
?locality core:notation ?notation
FILTER regex(str(?file), '/%s')
%s
}
ORDER BY DESC(?date)
LIMIT 1""" % (filename, country_filter)

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

    if resp.status_code in (401, 503):
        return url

    j = resp.json()
    ids = [x
           for x in j['remote_converters']

           if x['description'] == 'HTML Factsheet']

    if ids:
        return '{}{}&conv={}'.format(cdr, base, ids[0]['convert_id'])


@timeit
def get_xml_report_data(filename, country_code=''):
    """get_xml_report_data"""
    if not filename:
        return ""

    url = ''

    if 'http' in filename:      # this is a URL, not a filename
        url = filename
        filename = url.rsplit('/', 1)[-1]

    xmldir = os.environ.get("MSFDXML")

    if not xmldir:
        xmldir = tempfile.gettempdir()

    if country_code:
        xmldir = "{}/{}".format(xmldir, country_code)

        if not os.path.isdir(xmldir):
            os.mkdir(xmldir)

    assert '..' not in filename     # need better security?

    filename = filename.replace('%2C', ',')
    fpath = os.path.join(xmldir, filename)
    text = ''

    if filename in os.listdir(xmldir):
        with open(fpath, 'rb') as f:
            text = f.read()

    if not text:
        # TODO: handle this problem:
        # https://cr.eionet.europa.eu/factsheet.action?uri=http%3A%2F%2Fcdr.eionet.europa.eu%2Fro%2Feu%2Fmsfd8910%2Fblkro%2Fenvux97qw%2FRO_MSFD10TI_20130430.xml&page1=http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23type

        if not url:
            url = get_report_file_url(filename, country_code)

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
    _, res = db.get_all_records(
        t,
        t.c.MemberState == country_code,
    )

    cols = list(t.c.keys())
    recs = [
        {
            k: v for k, v in zip(cols, row)
        } for row in res
    ]

    return list(set([c['Descriptors Criterion Indicators'] for c in recs]))


def _get_report_filename_art3_4_2012(country, region, article, descriptor):
    """_get_report_filename_art3_4_2012"""
    schema = 'http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd'
    obligation = '608'

    return __get_report_filename_art3_4(country, region, schema, obligation)


def _get_report_filename_art3_4_2018(country, region, article, descriptor):
    """_get_report_filename_art3_4_2018"""
    schema = 'http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd'
    obligation = '760'

    return __get_report_filename_art3_4(country, region, schema, obligation)


@cache(lambda func, *args: func.__name__ + "_".join(args) + current_date())
@timeit
def __get_report_filename_art3_4(country, region, schema, obligation):
    """ Retrieve from CDR the latest filename for Article 3/4
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
            logger.warning("Filename not found for query: %s", q)
            return filename

        url = rows[0][0].value
        splitted = url.split('/')
        filename = splitted[-1]
    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'Article 3/4 country: %s', country)

        raise

    return filename


def _get_report_filename_art7_2012(country, region, article, descriptor):
    """ Retrieve from CDR the latest filename

    for Article 7 competent authorities
    """

    schema = 'http://water.eionet.europa.eu/schemas/dir200856ec/MSCA_1p0.xsd'

    return __get_report_filename_art7(country, schema)


def _get_report_filename_art7_2018(country, region, article, descriptor):
    """_get_report_filename_art7_2018"""
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
def get_all_report_filenames(country, article):
    """get_all_report_filenames"""
    ART3 = ('http://dd.eionet.europa.eu/schemas/MSFD/MSFD4Geo_2p0.xsd',
            'http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd',
            'http://cdr.eionet.europa.eu/se/eu/msfd8910/msfd4geo/envunbs3a/MSFD4Geo_2p0.xsd')
    ART7 = ('http://dd.eionet.europa.eu/schemas/MSFD/MSFDCA_1p0.xsd',
            'http://water.eionet.europa.eu/schemas/dir200856ec/MSCA_1p0.xsd')
    schemas = {
        'art7': "str(?schema) IN %s" % str(ART7),      # tuple hack
        'art3': "str(?schema) IN %s" % str(ART3),
        'art4': "str(?schema) IN %s" % str(ART3),
    }
    obligations = {
        'art3': "?obligationNr IN ('608', '759', '760')",
        'art4': "?obligationNr IN ('608', '759', '760')",
        'art7': "?obligationNr IN ('607', '608')",
    }

    schema = schemas[article.lower()]

    obligation = obligations[article.lower()]

    if country.lower() == 'el':
        country = 'GR'

    if country.lower() == 'uk':
        country = 'GB'

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
?file schema:restricted ?restricted.
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
#FILTER (str(?restricted) = 'false')
FILTER (?notation = '%s')
#FILTER (%s)
FILTER (%s)
}
ORDER BY DESC(?date)
""" % (country.upper(), obligation, schema, )       # region.upper()

# disabled filter on the obligation, as 4GEO files are reported along other
# obligations too
# FILTER regex(str(?file), '%s')

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    urls = []

    try:
        req = service.query(q)
        rows = req.fetchall()

        for row in rows:
            url = row[0].value

            if url not in urls:
                urls.append(url)

    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         '%s country: %s', article, country)

        raise

    if article.lower() in ('art3', 'art4'):
        if country.upper() == 'IT':
            urls.insert(1, 'https://cdr.eionet.europa.eu/it/eu/msfd_art17/'
                '2018reporting/spatialdata/envxd9fqa/IT_MSFD4Geo_20181220.xml')

        if country.upper() == 'LT':
            urls.append("https://cdr.eionet.europa.eu/lt/eu/msfd_art17/"
                        "2018reporting/spatialdata/envxosfwq/LT_MSFD4Geo.xml")

        # if country.upper() == 'PT':
        #     urls.append("https://cdr.eionet.europa.eu/pt/eu/msfd_art17/"
        #                 "2018reporting/spatialdata/envxuw4ba/PT_MSFD_4GEO_version_2_2019.08.09.xml")

    return urls


def _to_datetime(date_string):
    """_to_datetime"""
    d = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    return d


@timeit
def get_envelope_release_date(file_url):
    """get_envelope_release_date"""
    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>

SELECT ?released
WHERE {
?file terms:date ?date .
?file cr:mediaType 'text/xml'.
?file terms:isPartOf ?part .
?part schema:released ?released .
FILTER (str(?file) = '%s')
}
ORDER BY DESC(?date)
LIMIT 1
""" % file_url

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')

    try:
        req = service.query(q)
        rows = req.fetchall()

        if not rows:
            released = 0

            return released

        released = rows[0][0].value

    except:
        logger.exception('Got an error in querying SPARQL endpoint for '
                         'file_url: %s', file_url)

        raise

    release_date = _to_datetime(released)
    
    return release_date


def get_text_reports_2018(country_code):
    if country_code == 'EL':
        country_code = 'GR'

    if country_code == 'UK':
        country_code = 'GB'

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT distinct ?file, ?released
WHERE {
?file terms:date ?date .
#?file cr:mediaType 'text/xml' .
?file terms:isPartOf ?isPartOf .
?isPartOf schema:released ?released .
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '761')
}
ORDER BY DESC(?date)
""" % country_code

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    res = []

    try:
        req = service.query(q, timeout=30)
        rows = req.fetchall()

        for row in rows:
            file_url = row[0].value
            release_date = _to_datetime(row[1].value)

            res.append((file_url, release_date))

    except:
        logger.exception('Got an error in querying SPARQL endpoint when '
                         'getting text reports for: %s', country_code)

        raise

    return res

def get_gis_reports_2018(country_code):
    """get_gis_reports_2018"""
    if country_code == 'EL':
        country_code = 'GR'

    q = """
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX terms: <http://purl.org/dc/terms/>
PREFIX schema: <http://rod.eionet.europa.eu/schema.rdf#>
PREFIX core: <http://www.w3.org/2004/02/skos/core#>

SELECT distinct ?file, ?released
WHERE {
?file terms:date ?date .
#?file cr:mediaType 'text/xml' .
?file terms:isPartOf ?isPartOf .
?isPartOf schema:released ?released .
?isPartOf schema:locality ?locality .
?isPartOf schema:obligation ?obligation .
?obligation core:notation ?obligationNr .
?locality core:notation ?notation .
FILTER (?notation = '%s')
FILTER (?obligationNr = '760')
}
ORDER BY DESC(?date)
""" % country_code

    service = sparql.Service('https://cr.eionet.europa.eu/sparql')
    res = []

    try:
        req = service.query(q, timeout=30)
        rows = req.fetchall()

        for row in rows:
            file_url = row[0].value
            release_date = _to_datetime(row[1].value)

            res.append((file_url, release_date))

    except:
        logger.exception('Got an error in querying SPARQL endpoint when '
                         'getting text reports for: %s', country_code)

        raise

    return res
