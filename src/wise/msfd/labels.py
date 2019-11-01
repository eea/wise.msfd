
from collections import defaultdict

import csv
import json
import logging

from lxml.etree import parse
from pkg_resources import resource_filename

from . import db, sql, sql2018, sql_extra

COMMON_LABELS = {}                        # vocabulary of labels

# MSFD Search engine
# Labels used to override the default db column name into a
# user friendly text
DISPLAY_LABELS = {
    'MSFD4_Import_ReportingCountry': "Country",
    'AssessmentsPeriod': 'Assessment Period',
    'UniqueCode': 'Measure code',
    # Article 4
    'thematicId': 'Identifier',
    'nameTxtInt': 'Name in English',
    'nameText': 'Name in the national language',
    'spZoneType': 'Zone type',
    'legisSName': 'Legislation short name'
}

logger = logging.getLogger('wise.msfd')


def _extract_from_csv():
    labels = {}
    csv_f = resource_filename('wise.msfd',
                              'data/MSFDreporting_TermLists.csv')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in csv_file:
            if row[0] in labels.keys():
                logger.debug("Duplicate label in csv file: %s", row[0])

            labels[row[0]] = row[1]

    return labels


def _extract_ktm():
    labels = {}
    csv_f = resource_filename('wise.msfd',
                              'data/KTM.csv')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in csv_file:
            if row[0] in labels.keys():
                logger.debug("Duplicate label in csv file: %s", row[0])

            labels[row[0]] = row[2]

    return labels


def _extract_from_xsd(fpath):
    labels = {}

    # """ Read XSD files and populates a vocabulary of term->label

    # Note: there labels are pretty ad-hoc defined in the xsd file as
    # documentation tags, so this method is imprecise.
    # """

    lines = []
    xsd_f = resource_filename('wise.msfd', fpath)

    e = parse(xsd_f)

    for node in e.xpath('//xs:documentation',
                        namespaces={'xs': "http://www.w3.org/2001/XMLSchema"}):
        text = node.text.strip()
        lines.extend(text.split('\n'))

    for line in lines:

        line = line.strip()

        for splitter in ['=', '\t']:
            eqpos = line.find(splitter)

            if eqpos == -1:
                continue

            if ' ' in line[:eqpos]:
                continue

            label, title = line.split(splitter, 1)

            # if label in COMMON_LABELS:
            #     logger = logging.getLogger('tcpserver')
            #     logger.warning("Duplicate label in xsd file: %s", label)

            labels[label] = title

    return labels


@db.use_db_session('2012')
def get_human_labels():

    t = sql.t_MSFDCommon
    human_labels = {}
    count, rows = db.get_all_records(t)
    for row in rows:
        human_labels[row.Description] = row.value

    return human_labels


####################################
# CODE MOVED FROM gescomponents.py #
####################################


def parse_codelists_file():
    """ Parse the msfd2018-codelists.json file
    """
    jsonf = resource_filename('wise.msfd',
                              'data/msfd2018-codelists.json')
    with open(jsonf) as f:
        d = json.load(f)

    return d


TERMSLIST = parse_codelists_file()


def get_label(value, label_collection):
    """ Get the human version of a database 'shortcode' (a string id) """

    if label_collection:
        trans = GES_LABELS.get(label_collection, value)

        if trans != value:
            return trans

    return COMMON_LABELS.get(value, value)


def _parse_labels(label_name):
    res = {}

    features = TERMSLIST[label_name]

    for fr in features:
        code = fr['code']
        label = fr['label']

        if code in res:
            continue

        res[code] = label

    return res


@db.use_db_session('2018')
def get_indicator_labels():
    mc = sql2018.IndicatorsIndicatorAssessment
    count, res = db.get_all_records(
        mc
    )
    labels = {}

    for row in res:
        code = row.IndicatorCode
        label = row.IndicatorTitle

        if label:
            labels[code] = label

    return labels


@db.use_db_session('2018')
def get_indicator_urls():
    mc = sql2018.IndicatorsIndicatorAssessment
    count, res = db.get_all_records(
        mc
    )
    urls = {}

    for row in res:
        code = row.IndicatorCode
        url = row.UniqueReference

        if url:
            urls[code] = url

    return urls


@db.use_db_session('2018')
def get_mru_labels():
    # for faster query only get these fields
    needed = ('MarineReportingUnitId', 'Description', 'nameTxtInt', 'nameText')
    mc = sql2018.MarineReportingUnit
    mc_cols = [getattr(mc, x) for x in needed]

    count, res = db.get_all_specific_columns(
        mc_cols
    )
    labels = {}

    for row in res:
        code = row.MarineReportingUnitId
        label_main = row.Description
        label_int = row.nameTxtInt
        label_txt = row.nameText
        label = label_main or label_int or label_txt

        if label:
            labels[code] = label

    return labels


@db.use_db_session('2018')
def get_target_labels():
    needed = ('TargetCode', 'Description')
    mc = sql2018.ART10TargetsTarget
    mc_cols = [getattr(mc, x) for x in needed]

    count, res = db.get_all_specific_columns(
        mc_cols
    )
    labels = {}

    for row in res:
        code = row.TargetCode
        label = row.Description
        labels[code] = label

    return labels


@db.use_db_session('2012')
def get_environmental_targets():
    mc = sql.MSFD10Target
    mc_join = sql.MSFD10Import
    count, res = db.get_all_records_join(
        [mc.ReportingFeature, mc.Description,
         mc.MarineUnitID,
         mc_join.MSFD10_Import_ReportingCountry],
        mc_join,
        mc.Topic == 'EnvironmentalTarget'
    )
    labels = defaultdict(dict)

    for row in res:
        code = row.ReportingFeature
        label = row.Description
        # country_code = row.MSFD10_Import_ReportingCountry
        mru = row.MarineUnitID

        mru_labels = labels[mru]
        mru_labels[code] = label

    return labels


class LabelCollection(object):
    """ A convenience wrapper over multiple structures with labels

    Needed because ReferenceFeature does not contain all features
    """

    features = _parse_labels('Features')
    pressures = _parse_labels('Pressures')
    parameters = _parse_labels('Parameters')
    threshold_sources = _parse_labels('ThresholdSources')
    units = _parse_labels('Units')
    element_sources = _parse_labels('ElementSources')
    elementcode_sources = _parse_labels('ElementCodeSources')
    ges_criterias = _parse_labels('GESCriterias')
    ges_components = _parse_labels('GESComponents')
    indicators = get_indicator_labels()
    indicators_url = get_indicator_urls()
    mrus = get_mru_labels()
    targets = get_target_labels()
    ktms = _extract_ktm()
    env_targets = get_environmental_targets()

    def get(self, collection_name, name):
        label_dict = getattr(self, collection_name, None)

        if not label_dict:
            return name

        label = label_dict.get(name, name)

        return label


GES_LABELS = LabelCollection()


def get_common_labels():
    labels = {}
    labels.update(_extract_from_csv())
    labels.update(_extract_from_xsd('data/MSCommon_1p0.xsd'))
    labels.update(_extract_from_xsd('data/MSCommon_1p1.xsd'))
    labels.update(get_human_labels())

    # We should use the labels from msfd2018-codelists.json
    # they look better and there are more labels
    labels.update(getattr(GES_LABELS, 'features'))
    labels.update(getattr(GES_LABELS, 'ges_components'))
    labels.update(getattr(GES_LABELS, 'ges_criterias'))

    # TODO there are keys with empty values, find out from where it comes
    filtered = {k: v for k, v in labels.items() if k}

    return filtered


COMMON_LABELS = get_common_labels()
