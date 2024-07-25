# pylint: skip-file
from __future__ import absolute_import
from collections import defaultdict

import csv
import json
import logging

from lxml.etree import parse
from pkg_resources import resource_filename

from . import db, sql, sql2018

COMMON_LABELS = {}                        # vocabulary of labels

# Collection of label fixes, where the description/title for a value
# is not appropriate
LABEL_FIX = {
    "ANS": "NE Atlantic: Greater North Sea",
    "CY": 'Cyprus',
    "CZ": 'Czechia',
    'D4': '(Descriptor) D4 - Food webs',
    'D6': '(Descriptor) D6 - Sea-floor integrity'
}

# MSFD Search engine
# Labels used to override the default db column name into a
# user friendly text
DISPLAY_LABELS = {
    'ALL': {
        'SpatialDistribution1': 'Spatial distribution',
        'Habitat_FunctionalGroup': 'Habitat functional group',
        'Sum2Confidence': 'Summary 2 confidence',
        'Sum1Confidence': 'Summary confidence',
        'Impact5': 'Impact 5',
        'Impact4': 'Impact 4',
        'Impact3': 'Impact 3',
        'Impact2': 'Impact 2',
        'Impact1': 'Impact',
        'MSFD8a_Ecosystem1': 'MSFD8a ecosystem',
        'Pressure3Rank': 'Pressure 3 rank',
        'Pressure3': 'Pressure 3',
        'Pressure2Rank': 'Pressure 2 rank',
        'Pressure2': 'Pressure 2',
        'Pressure1Rank': 'Pressure rank',
        'Pressure1': 'Pressure',
        'Summary2': 'Summary 2',
        'Summary1': 'Summary',
        'URL_CA': 'URL',
        'CityNL': 'City (national language)',
        'CompetentAuthorityNameNL': 
            'Competent authority name (national language)',
        'GESachieved': 'GES achieved',
        'GEScomponent': 'GES component',
        'CBAreference': 'CBA reference',
        'CBA': 'Cost-benefit analysis (CBA)',
        'CEA': 'Cost-effectiveness analysis (CEA)',
        'CEAreference': 'CEA reference',
        'SpatialScopeGeographicZones': 'Spatial scope, geographic zones',
        'LinkToExistingPolicies': 'Link to existing policies',
        'KTM': 'Key types of measures (KTM)',
        'RelevantFeaturesFromMSFDAnnexIII':
            'Relevant features from MSFD Annex III',
        'RelevantGESDescriptors': 'Relevant GES descriptors',
        'RelevantEnvironmentalTargets': 'Relevant environmental targets',
        'RBDCode': 'River Basin District code (WFD)',
        'RelevantKTMs': 'Relevant Key types of measures (KTM)',
        'RelationshipToCA': 'Relationship to CA',
        'Q4e_ProgrammeID': 'Programme ID',
        'Q5f_DescriptionGES': 'Description GES',
        'Q5g_GapFillingDateGES': 'Gap filling date GES',
        'Q5h_PlansGES': 'Plans GES',
        'Q4g_SubProgrammeID': 'Sub programme ID',
        'Q10c_INSPIREStandard': 'INSPIRE standard',
        'MSFD11_Q5d_AdequacyForAssessmentGE': 'Adequacy for assessment GES',
        'MSFD11_Q6b_AdequacyForAssessmentTarget':
            'Adequacy for assessment target',
        'MSFD11_Q7e_AdequacyForAssessmentMeasure':
            'Adequacy for assessment measure',
        'AdequateUnderstandingGES': 'Adequate understanding GES',
        'Q5b_RelevantGESIndicators': 'Relevant GES indicators',
        'Q5a_RelevantGESCriteria': 'Relevant GES criteria',
        'GESDescriptorsCriteriaIndicators':
            'GES descriptors criteria indicators',
        'InterimGESTarget': 'Interim GES target',
        'MSCACode': 'MSCA code',
        'NACECode': 'NACE code',
        'Element2Code': 'Element2 code',
        'Element2CodeSource': 'Element2 code source',
        'GESComponent': 'GES component',
        'GESDescription': 'GES description',
        'GESExtentAchieved': 'GES extent achieved',
        'GESExtentUnit': 'GES extent unit',
        'GESExtentThreshold': 'GES extent threshold',
        'GESAchieved': 'GES achieved',
        'MSFD4_Import_ReportingCountry': "Country",
        'AssessmentsPeriod': 'Assessment period',
        'UniqueCode': 'Measure code',
        # Article 4
        'rZoneId': 'Region',
        'thematicId': 'Identifier',
        'nameTxtInt': 'Name in English',
        'nameText': 'Name in the national language',
        'spZoneType': 'Zone type',
        'legisSName': 'Legislation short name',
        'Area': 'Area (km2)',
        # Article 19.3
        'MarineUnitID': 'Marine Reporting unit'
    },
    'MSFD13_2016': {
        'UniqueCode': 'Measure code',
        'Name': 'Measure name'
    },
    'MSFD14_2016': {
        'UniqueCode': 'Exception code',
        'Name': 'Exception name'
    }
}

logger = logging.getLogger('wise.msfd')


def _extract_from_csv():
    """_extract_from_csv"""
    labels = {}
    csv_f = resource_filename('wise.msfd',
                              'data/MSFDreporting_TermLists.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in csv_file:
            if row[0] in list(labels.keys()):
                logger.debug("Duplicate label in csv file: %s", row[0])

            labels[row[0]] = row[1]

    return labels


def _extract_ktm():
    """_extract_ktm"""
    labels = {}
    csv_f = resource_filename('wise.msfd',
                              'data/KTM.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in csv_file:
            if row[0] in list(labels.keys()):
                logger.debug("Duplicate label in csv file: %s", row[0])

            label = row[2].strip('"')
            labels[row[0]] = label

    return labels


def _parse_art11_2020_labels():
    """_parse_art11_2020_labels"""
    labels = defaultdict(dict)
    csv_f = resource_filename('wise.msfd',
                              'data/MSFD_Art11_2020_Enumerations_v3_2.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=';', quotechar='"')

        for row in csv_file:
            label_type = row[0]
            code = row[1]
            label = row[2]

            labels[label_type][code] = label

    return labels


def _extract_from_xsd(fpath):
    """_extract_from_xsd"""
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

            code, label = line.split(splitter, 1)

            # if label in COMMON_LABELS:
            #     logger = logging.getLogger('tcpserver')
            #     logger.warning("Duplicate label in xsd file: %s", label)

            labels[code] = label

    return labels


@db.use_db_session('2012')
def get_human_labels():
    """get_human_labels"""
    t = sql.t_MSFDCommon
    human_labels = {}
    count, rows = db.get_all_records(t)
    for row in rows:
        label = row.Description
        code = row.value

        if not label:
            continue

        human_labels[code] = label

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
    """_parse_labels"""
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
    """get_indicator_labels"""
    mc = sql2018.IndicatorsIndicatorAssessment
    _, res = db.get_all_records(
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
    """get_indicator_urls"""
    mc = sql2018.IndicatorsIndicatorAssessment
    _, res = db.get_all_records(
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
    """get_mru_labels"""
    # for faster query only get these fields
    needed = ('MarineReportingUnitId', 'Description', 'nameTxtInt', 'nameText')
    mc = sql2018.MarineReportingUnit
    mc_cols = [getattr(mc, x) for x in needed]

    _, res = db.get_all_specific_columns(
        mc_cols
    )
    labels = {}

    for row in res:
        code = row.MarineReportingUnitId
        description = row.Description
        text_int = row.nameTxtInt
        text = row.nameText

        # check if text is empty string or 'NULL'(as string)
        if text in ('NULL', '', ' '):
            text = None

        # 'text' has the most readable label
        # 'text_int' second option when text is empty,
        # in most cases text_int is the same as 'text'
        # description last option, most of the time same as the MRU code
        label = text or text_int or description

        if label:
            labels[code] = label

    return labels


@db.use_db_session('2018')
def get_target_labels():
    """get_target_labels"""
    needed = ('TargetCode', 'Description')
    mc = sql2018.ART10TargetsTarget
    mc_cols = [getattr(mc, x) for x in needed]

    _, res = db.get_all_specific_columns(
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
    """get_environmental_targets"""
    mc = sql.MSFD10Target
    mc_join = sql.MSFD10Import
    _, res = db.get_all_records_join(
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

    countries = _parse_labels('Countries')
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
    art11_conventions = _parse_art11_2020_labels()['DirectivesConventions']
    art11_parameters = _parse_art11_2020_labels()['Parameter']
    art11_monitor_method = _parse_art11_2020_labels()['MonitoringMethod']
    art11_features = _parse_art11_2020_labels()['Feature']
    nace_codes = _parse_labels('NACECodesAll')

    def get(self, collection_name, name):
        """get"""
        label_dict = getattr(self, collection_name, None)

        if not label_dict:
            return name

        label = label_dict.get(name, name)

        return label


GES_LABELS = LabelCollection()


def get_common_labels():
    """get_common_labels"""
    labels = {}
    # The following labels were disabled because it contains
    # imprecise/non-sense labels ex. 'Good' = 'e.g. based on extensive surveys'
    # Other	= 'Please specify in comment'

    # labels.update(_extract_from_xsd('data/MSCommon_1p0.xsd'))
    # labels.update(_extract_from_xsd('data/MSCommon_1p1.xsd'))
    # labels.update(get_human_labels())

    labels.update(_extract_from_csv())
    labels.update(LABEL_FIX)

    # We should use the labels from msfd2018-codelists.json
    # they look better and there are more labels
    labels.update(getattr(GES_LABELS, 'features'))
    labels.update(getattr(GES_LABELS, 'ges_components'))
    labels.update(getattr(GES_LABELS, 'ges_criterias'))

    # there are keys with empty values, find out from where it comes
    filtered = {k: v for k, v in labels.items() if k and v}

    return filtered


COMMON_LABELS = get_common_labels()
