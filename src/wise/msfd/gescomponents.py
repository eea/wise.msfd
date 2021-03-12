# -*- coding: utf-8 -*-

from eea.cache import cache

import csv
import logging
import re
from collections import namedtuple

import lxml.etree
from pkg_resources import resource_filename

from wise.msfd import db, sql, sql2018, sql_extra
from wise.msfd.labels import COMMON_LABELS, TERMSLIST
from wise.msfd.utils import (ItemLabel, _parse_files_in_location,
                             get_element_by_id, natural_sort_key, timeit)

logger = logging.getLogger('wise.msfd')

# GES criterias have been used in 2010/2012 reports and then revamped for 2018
# reports. As such, some exist in 2010 that didn't exist in 2018, some exist
# for 2018 that didn't exist for 2010 and they have changed their ids between
# the two reporting exercises.

Criterion2012 = namedtuple('Criterion2012', ['id', 'title'])
Feature = namedtuple('Feature', ['name', 'label', 'descriptors', 'theme'])
Feature_2018 = namedtuple('Feature', ['name', 'label', 'subject', 'theme'])
Parameter = namedtuple('Parameter', ['name', 'unit', 'criterias'])

DESC_RE = re.compile(r'^D\d(\.\d|\d)?$')
CRIT_2018_RE = re.compile(r'^D\d[0,1]?C\d$')       # ex: D10C5
CRIT_2012_RE = re.compile(r'^\d[0,1]?\.\d$')        # ex: 4.1
INDICATOR_2012_RE = re.compile(r'^\d[0,1]?\.\d\.\d$')       # ex: 10.1.1
NOTHEME = u'No theme'

DESCRIPTOR_TYPES = [
    ("Pressure-based descriptors", ['D2', 'D5', 'D7', 'D8', 'D9', 'D10',
                                    'D11']),
    ("State-based descriptors", ['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5',
                                 'D3', 'D1.6', 'D6', 'D4'])
]


class ElementDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        self.definition = node.text.strip()


class DummyMSD:
    def __init__(self):
        self.id = object()
        self.definition = ''


class MetodologicalStandardDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        self.definition = node.text.strip()


class CriteriaAssessmentDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        defn = node.find('definition')
        self.definition = defn.text.strip()

        prim = node.get('primary', 'false')

        if prim.lower() in ['false', 'true']:
            # acts as a star
            self._primary_for_descriptors = bool(['false', 'true'].index(prim))
        else:
            # parse the primary definition to identify descriptors
            descriptors = prim.split(' ')
            self._primary_for_descriptors = descriptors

        self.elements = []

        for eid in node.xpath('uses-element/@href'):
            el = get_element_by_id(root, eid)
            self.elements.append(ElementDefinition(el, root))

        msid = node.xpath('uses-methodological-standard/@href')[0]
        mel = get_element_by_id(root, msid)
        self.methodological_standard = MetodologicalStandardDefinition(
            mel, root
        )

    @property
    def title(self):
        if self._primary_for_descriptors:
            primary = True
        else:
            primary = False

        return u"{} - {}".format(self.id,
                                 primary and 'Primary' or 'Secondary')


def parse_elements_file(fpath):
    # Note: this parsing is pretty optimistic that there's a single descriptor
    # in the file. Keep that true
    res = []

    try:
        root = lxml.etree.parse(fpath).getroot()
    except:
        logger.exception('Could not parse file: %s', fpath)

        return

    desc_id = root.get('id')

    for critn in root.iterchildren('criteria'):

        crit = CriteriaAssessmentDefinition(critn, root)
        res.append(crit)

    return desc_id, res


def get_descriptor_elements(location):
    """ Parse the descriptor elements in a location and build a mapping struct

    The location argument should be a path relative to wise.msfd package.
    The return data is used to build the automatic forms.
    """
    def check_filename(fname):
        return fname.endswith('_elements.xml')

    return _parse_files_in_location(location,
                                    check_filename, parse_elements_file)


DESCRIPTOR_ELEMENTS = get_descriptor_elements(
    'compliance/nationaldescriptors/data'
)


class Descriptor(ItemLabel):
    """ A descriptor representation
    """

    def __init__(self, id=None, title=None, criterions=None):
        self.id = id
        self.title = title
        assert isinstance(self.title, unicode)
        self.name = self.title
        self.criterions = criterions or set()

    def is_descriptor(self):
        return True

    @property
    def template_vars(self):
        # ItemLabel support
        title = self.id

        if title.startswith('D1.'):
            # if D1.1, return "D1-B"
            bits = self.title.split(' ')
            b2 = bits[1].strip()
            major = b2[0].strip()
            # title = u"D1&#8209;" + major[0].upper()     # non-breaking hyphen
            title = u"D1-" + major.upper()  # non-breaking hyphen

        return {
            'title': title,
            'name': self.title,
        }

    def all_ids(self):
        res = set()
        res.add(self.id)

        if self.id == 'D6':
            res.add('D6/D1')

        if self.id == 'D4':
            res.add('D4/D1')

        # TODO why it is commented
        # if self.id.startswith('D1.'):
        #     res.add('D1')

        for crit in self.criterions:
            for cid in crit.all_ids():
                res.add(cid)

        return res

    def sorted_criterions(self):
        crits = {c.id: c for c in self.criterions}
        # ids = crits.keys()

        s = sorted_by_criterion(crits.keys())

        return [crits[x] for x in s]

    def __getitem__(self, crit_id):
        for crit in self.criterions:
            if crit.id == crit_id:
                return crit
        raise KeyError


class Criterion(ItemLabel):
    """ A container for a GES criterion information

    A criterion is a somewhat confusing concept. In 2012 reporting, the
    Criteria were used, which had assigned Indicators. In 2018, the Descriptor
    concept has been introduced, which has Indicators. So, the "virtual"
    hierarchy is Descriptor > Criteria > Indicator.

    A criterion can be either of Descriptor, Criteria, Indicator.

    NOTE: there is a criterion that is 2012 exclusive, we don't include it in
    data: 1.3.2 Population genetic structure
    """

    _id = None      # id for the 2018 version
    _title = None   # title for the 2018 version
    _alternatives = None
    _main_id = None

    @property
    def template_vars(self):
        # ItemLabel support
        # title = self._title or self.id
        #
        # if self._main_id and self._main_id != self.id:
        #     title = u"{} ({})".format(title, self._main_id)

        return {
            'title': self.id,
            'name': self.title,
        }

    def is_descriptor(self):
        return False

    def __init__(self, id, title, descriptor):
        self.alternatives = []  # Criterion2012 objects

        self._id = id
        self.id = self.name = self._id or self.alternatives[0][0]
        self._title = title
        self.descriptor = descriptor

        crit_defs = [x
                     for x in DESCRIPTOR_ELEMENTS[self.descriptor]

                     if x.id == self.id]

        if crit_defs:
            self.__dict__.update(crit_defs[0].__dict__)
        else:
            self.elements = []
            self.definition = ''
            self.methodological_standard = DummyMSD()
            self._primary = False
            # self._primary_for_descriptors = []

    def __str__(self):
        return self.title

    def __repr__(self):
        title = self.title.encode('ascii', 'replace')
        title = title.replace('?', '-')

        return "<Criterion {}>".format(title)

    def is_2018_exclusive(self):
        return not self.alternatives

    def is_2012_exclusive(self):
        return not self._id

    @property
    def title(self):
        alter = self.alternatives

        if not alter:
            return self._title
            # return u"{} {}".format(self._id, self._title)

        if not self._id:
            # id, title = alter[0]

            return alter[0][1]      # u"{} {}".format(id, title)

        alter_ids = len(alter) == 0 and alter[0][0] \
            or u', '.join(sorted(set([a[0] for a in alter])))

        # if self._main_id and self._main_id != self.id:
        #     return u"{} ({})".format(
        #         self._title,
        #         alter_ids,
        #     )

        return u"{} ({})".format(
            self._title,
            alter_ids,
        )

    # def belongs_to_descriptor(self, descriptor_id):
    #     for descriptor in self.descriptors:
    #         if descriptor.id == descriptor_id:
    #             return True
    #
    #     return False

    def all_ids(self):

        return set([self.id] + [x[0] for x in self.alternatives])

    def has_alternative(self, id):
        return any([x.id == id for x in self.alternatives])

    def is_primary(self, descriptor):
        if hasattr(self, '_primary'):
            return self._primary

        if self._primary_for_descriptors in [True, False]:
            return self._primary_for_descriptors
        else:
            return getattr(descriptor, 'id', descriptor).lower() in \
                [d.lower() for d in self._primary_for_descriptors]


def parse_ges_extended_format():
    csv_f = resource_filename('wise.msfd',
                              'data/ges_terms.csv')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter='\t')
        rows = list(csv_file)

    rows = rows[1:]     # skip header

    descriptors = {}
    criterions = {}
    descriptor = None

    for row in rows:
        if not row:
            continue

        if not row[0].strip():
            continue

        bits = [b.strip() for b in row]

        if len(bits) == 1:      # allow for editing with vim
            bits.extend(['', ''])

        if len(bits) == 2:
            bits.append('')

        b1, b2, b3 = bits

        if b1.startswith('D') and ('C' not in b1):
            # it's a descriptor label
            descriptor = Descriptor(b1, b2.decode('utf-8'))
            descriptors[descriptor.id] = descriptor

            continue

        if b1 in criterions:
            criterion = criterions[b1]
            descriptors[descriptor.id].criterions.add(criterion)
        else:
            criterion = Criterion(id=b1, title=b2, descriptor=descriptor.id)

            criterions[criterion.id] = criterion
            descriptors[descriptor.id].criterions.add(criterion)

        if b3 and (not criterion.has_alternative(b3)):
            crit = Criterion2012(*b3.split(' ', 1))
            criterion.alternatives.append(crit)
            # criterions[crit.id] = crit
            # descriptors[descriptor.id].criterions.append(criterion)

    return descriptors, criterions


GES_DESCRIPTORS, GES_CRITERIONS = parse_ges_extended_format()


def get_all_descriptors():
    """ Returns all descriptors in the following format

    :return: (('D1', 'D1 - Biodiversity'),
             ('D1.1', 'D1 - Biodiversity – birds'),
             ... )
    """

    descriptors = [(v.id, v.title) for k, v in GES_DESCRIPTORS.items()]
    d_sorted = sorted(descriptors, key=lambda d: natural_sort_key(d[0]))

    return d_sorted


def get_descriptor(descriptor=None):
    """ Returns a Descriptor object, that has criterions attached

    :param descriptor: descriptor id, ex D5
    """

    if descriptor == 'D6/D1':
        descriptor = 'D6'

    if descriptor == 'D4/D1':
        descriptor = 'D4'

    return GES_DESCRIPTORS[descriptor]

    # if not descriptor:
    #     return GES_CRITERIONS
    #
    # return [c for c in GES_CRITERIONS if c.descriptor == descriptor]


def get_criterion(ges_id):
    """ Get the first matched criterion for given ges id

    :param ges_id: criterion id (ex: D1, D5C1 or 5.1.1)
    """

    for c in GES_CRITERIONS.values():
        if ges_id in c.all_ids():
            c._main_id = ges_id

            return c


def get_ges_component(ges_id):
    if ges_id.upper() == 'D6/D1':
        ges_id = 'D6'
    elif ges_id.upper() == 'D4/D1':
        ges_id = 'D4'

    if is_descriptor(ges_id):
        return get_descriptor(ges_id)

    crit = get_criterion(ges_id)

    if crit is None:
        logger.warning("Criterion not found: %s", ges_id)

        return None

    return crit


def parse_parameters():
    res = {}

    for par in TERMSLIST['ReferenceParameter']:
        name = par['Parameter']

        if name not in res:
            unit = par['Unit']
            criterias = set([p['Criteria']
                             for p in TERMSLIST['ReferenceParameter']

                             if p['Parameter'] == name])
            param = Parameter(name, unit, criterias)
            res[name] = param

    return res


PARAMETERS = parse_parameters()


def get_parameters(descriptor_code=None):

    if descriptor_code is None:
        return PARAMETERS.values()

    descriptor = get_descriptor(descriptor_code)
    crit_ids = set(descriptor.all_ids())
    res = []

    for p in PARAMETERS.values():
        if p.criterias.intersection(crit_ids):
            res.append(p)

    return res


# TODO: move all label related code to labels.py
@db.use_db_session('2012')
def parse_features_from_db_2012():
    res = {}

    mc = sql_extra.MSFD9Feature
    count, data = db.get_all_records(mc)

    for row in data:
        code = row.FeaturesPressuresImpacts
        label = ''
        theme = row.FeatureType or NOTHEME

        res[code] = Feature(code, label, '', theme)

    return res


FEATURES_DB_2012 = parse_features_from_db_2012()


@db.use_db_session('2018')
def parse_features_from_db_2018():
    res = {}

    mc = sql2018.LFeature
    count, data = db.get_all_records(mc)

    for row in data:
        code = row.Code.strip()
        label = row.Feature
        theme = row.Theme or NOTHEME
        if theme.endswith(','):
            theme = theme.strip(',')

        subject = row.Subject

        res[code] = Feature_2018(code, label, subject, theme)

    return res


FEATURES_DB_2018 = parse_features_from_db_2018()


FEATURES_ORDER = [
    'BirdsGrazing',
    'BirdsWading',
    'BirdsSurfaceFeeding',
    'BirdsPelagicFeeding',
    'BirdsBenthicFeeding',
    'MamCetacSmall',
    'MamCetacDeepDiving',
    'MamCetacBaleenWhales',
    'MamSeals',
    'RepTurtles',
    'FishCoastal',
    'FishPelagicShelf',
    'FishDemersalShelf',
    'FishDeepSea',
    'FishCommercial',
    'CephaCoastShelf',
    'CephaDeepSea',
    'HabBenBHT',
    'HabBenOther',
    'HabPelBHT',
    'HabPelOther',
    'CharaPhyHydro',
    'CharaChem',
    'EcosysCoastal',
    'EcosysShelf',
    'EcosysOceanic',
    'PresEnvNISnew',
    'PresEnvNISestablished',
    'PresEnvBycatch',
    'PresEnvHydroChanges',
    'PresPhyDisturbSeabed',
    'PresPhyLoss',
    'PresEnvEutrophi',
    'PresEnvContNonUPBTs',
    'PresEnvContUPBTs',
    'PresEnvContSeafood',
    'PrevEnvAdvEffectsSppHab',
    'PresEnvAcuPolluEvents',
    'PresEnvLitter',
    'PresEnvLitterMicro',
    'PresEnvLitterSpp',
    'PresEnvSoundImpulsive',
    'PresEnvSoundContinuous',
    'PresBioIntroNIS',
    'PresBioIntroMicroPath',
    'PresBioIntroGenModSpp',
    'PresBioCultHab',
    'PresBioDisturbSpp',
    'PresBioExtractSpp',
    'PresInputNut',
    'PresInputOrg',
    'PresInputCont',
    'PresInputLitter',
    'PresInputSound',
    'PresInputOthEnergy',
    'PresInputWater',
    'ActivRestrucLandClaim',
    'ActivRestrucCanalisation',
    'ActivRestrucCoastDef',
    'ActivRestrucOffshStruc',
    'ActivRestrucSeabedMorph',
    'ActivExtrNonLivingMinerals',
    'ActivExtrNonLivingOilGas',
    'ActivExtrNonLivingSalt',
    'ActivExtrNonLivingWater',
    'ActivProdEnerRenew',
    'ActivProdEnerNonRenew',
    'ActivProdEnerCables',
    'ActivExtrLivingFishHarv',
    'ActivExtrLivingFishProcess',
    'ActivExtrLivingPlantHarv',
    'ActivExtrLivingHunt',
    'ActivCultivAquaculMarine',
    'ActivCultivAquaculFreshwa',
    'ActivCultivAgri',
    'ActivCultivFores',
    'ActivTranspInfras',
    'ActivTranspShip',
    'ActivTranspAir',
    'ActivTranspLand',
    'ActivUrbIndUrban',
    'ActivUrbIndIndustrial',
    'ActivUrbIndWaste',
    'ActivTourismInfras',
    'ActivTourismActiv',
    'ActivMilitary',
    'ActivResearch',
]


SUBJECT_2018_ORDER = [
    'Structure, functions and processes of marine ecosystems',
    'Anthropogenic pressures on the marine environment',
    'Pressure levels and impacts in marine environment',
    'Uses and human activities in or affecting the marine environment',
    'Ecosystem services',
]

THEMES_2018_ORDER = [
    'Species',
    'Habitats',
    'Ecosystems, including food webs',
    'Biological',
    'Physical',
    'Physical and hydrological',
    'Chemical',
    'Substances, litter and energy',
    'Nutrition',
    'Materials',
    'Energy',
    'Mediation of waste, toxics and other nuisances',
    'Mediation of flows',
    'Maintenance of physical, chemical, biological conditions',
    'Underpinning and/or enhancing physical and intellectual interactions',
    'Underpinning and/or enhancing spiritual, symbolic and other interactions',
    'Physical restructuring of rivers, coastline or seabed (water management)',
    'Extraction of non-living resources',
    'Production of energy',
    'Extraction of living resources',
    'Cultivation of living resources',
    'Transport',
    'Urban and industrial uses',
    'Tourism and leisure',
    'Security/defence',
    'Education and research',
    'No theme',
]

# Anthropogenic features are declared in the correct order
ANTHROPOGENIC_FEATURES_SHORT_NAMES = [
    ('PresAll', 'All pressures'),
    # Biological features
    ('PresBioAll', 'All biological pressures'),
    ('PresBioIntroNIS', 'Input or spread of non-indigenous species'),
    ('PresBioIntroMicroPath', 'Input of microbial pathogens'),
    ('PresBioIntroGenModSpp', 'Input of genetically modified species '
                              'and translocation'),
    ('PresBioCultHab', 'Loss of, or change to, natural biological communities '
                       'due to cultivation of animal or plant species'),

    ('PresBioDisturbSpp', 'Disturbance of species due to human presence'),
    ('PresBioExtractSpp', 'Extraction of, or mortality/injury to, '
                          'wild species'),
    # Physical features
    ('PresPhyAll', 'All physical pressures'),
    ('PresPhyDisturbSeabed', 'Physical disturbance to seabed'),
    ('PresPhyLoss', 'Physical loss of the seabed'),
    ('PresPhyHydroCond', 'Changes to hydrological conditions'),
    # Substances, litter and energy features
    ('PresInputAll', 'All pressures related to inputs of substances, '
                     'litter and energy'),
    ('PresInputNut', 'Input of nutrients'),
    ('PresInputOrg', 'Input of organic matter'),
    ('PresInputCont', 'Input of other substances'),
    ('PresInputLitter', 'Input of litter'),
    ('PresInputSound', 'Input of anthropogenic sound'),
    ('PresInputOthEnergy', 'Input of other forms of energy'),
    ('PresInputWater', 'Input of water'),
]


def parse_features():
    res = {}

    FEATURES = TERMSLIST['FeaturesSmart']        #

    for fr in FEATURES:
        code = fr['code']
        label = fr['label']

        if code in res:
            continue

        descs = set([f['descriptor']
                     .replace('D6/D1', 'D6')
                     .replace('D4/D1', 'D4')

                     for f in FEATURES

                     if f['code'] == code])

        theme = FEATURES_DB_2018[code].theme

        res[code] = Feature(code, label, descs, theme)

    # this is missing from FeaturesSmart, features assigned to multiple
    # descriptors
    res['HabAll'] = Feature('HabAll', 'All habitats', set(['D1.6', 'D6']),
                            FEATURES_DB_2018['BirdsAll'].theme)
    res['HabOther'] = Feature('HabOther', 'Other habitat types',
                              set(['D1.6', 'D6']),
                              FEATURES_DB_2018['HabOther'].theme)
    res['PhyHydroCharacAll'] = Feature(
        'PhyHydroCharacAll', 'All physical and hydrological characteristics',
        set(['D1.6', 'D6']), FEATURES_DB_2018['PhyHydroCharacAll'].theme)
    res['Temperature'] = Feature(
        'Temperature', 'Temperature',
        set(['D1.6', 'D6']), FEATURES_DB_2018['Temperature'].theme)
    res['Ice'] = Feature(
        'Ice', 'Ice',
        set(['D1.6', 'D6']), FEATURES_DB_2018['Ice'].theme)
    res['Waves'] = Feature(
        'Waves', 'Wave regime',
        set(['D1.6', 'D6']), FEATURES_DB_2018['Waves'].theme)
    res['Currents'] = Feature(
        'Currents', 'Current regime',
        set(['D1.6', 'D6']), FEATURES_DB_2018['Currents'].theme)
    res['OrganicCarbon'] = Feature(
        'OrganicCarbon', 'Organic carbon',
        set(['D1.6', 'D6']), FEATURES_DB_2018['OrganicCarbon'].theme)
    res['OrganicCarbon'] = Feature(
        'OrganicCarbon', 'Organic carbon',
        set(['D1.6', 'D6']), FEATURES_DB_2018['OrganicCarbon'].theme)
    res['pH'] = Feature(
        'pH', 'pH',
        set(['D1.6', 'D6']), FEATURES_DB_2018['pH'].theme)
    res['PresBioDisturbSpp'] = Feature(
        'PresBioDisturbSpp',
        'Disturbance of species (e.g. where they breed, rest and feed) '
        'due to human presence',
        set(['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5']),
        FEATURES_DB_2018['PresBioDisturbSpp'].theme)
    res['PresBioExtractSpp'] = Feature(
        'PresBioExtractSpp',
        'Extraction of, or mortality/injury to, wild species '
        '(by commercial and recreational fishing and other activities)',
        set(['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5']),
        FEATURES_DB_2018['PresBioExtractSpp'].theme)
    res['PresPhyAll'] = Feature(
        'PresPhyAll',
        'All physical pressures',
        set(['D1.6', 'D6']),
        FEATURES_DB_2018['PresPhyAll'].theme)
    res['PresPhyHydroCond'] = Feature(
        'PresPhyHydroCond',
        'Changes to hydrological conditions',
        set(['D1.6', 'D6']),
        FEATURES_DB_2018['PresPhyHydroCond'].theme)
    res['PresEnvHydroChanges'] = Feature(
        'PresEnvHydroChanges',
        'Hydrographical changes',
        set(['D1.6', 'D6']),
        FEATURES_DB_2018['PresEnvHydroChanges'].theme)

    return res


FEATURES = parse_features()


@cache(lambda func, *args: func.__name__ + args[0], lifetime=1800)
def get_features(descriptor_code=None):
    if descriptor_code is None:
        return FEATURES.values()

    return [f
            for f in FEATURES.values()

            if descriptor_code in f.descriptors]


def is_descriptor(value):
    return bool(DESC_RE.match(value))


def sorted_by_criterion(ids):
    """ Sort/group a list of criterion ids
    """

    descriptors = set()         # ex: D1.1
    criterias_2018 = set()      # ex: D1C5
    criterias_2012 = set()      # ex: 5.1
    indicators = set()          # ex: 5.1.1
    criterions = set()          # ex: 1.2.1-indicator 5.2B
    others = set()

    for id in ids:
        if id in GES_DESCRIPTORS:
            descriptors.add(id)

            continue

        if CRIT_2018_RE.match(id):
            criterias_2018.add(id)

            continue

        if CRIT_2012_RE.match(id):
            criterias_2012.add(id)

            continue

        if INDICATOR_2012_RE.match(id):
            indicators.add(id)

            continue

        if 'indicator' in id:        # TODO: this needs to be normalized
            criterions.add(id)

            continue

        others.add(id)

    res = []
    res.extend(sorted(descriptors, key=lambda d: d.replace('D', '')))
    res.extend(sorted(criterias_2018))      # TODO: sort for double digit

    criterions_2012 = criterias_2012.union(indicators)
    res.extend(sorted(criterions_2012))

    res.extend(sorted(criterions, key=lambda k: k.replace(' ', '')))
    res.extend(sorted(others))

    # print(res)

    return res


def sorted_criterions(crits):
    """ Given a list of criterias, returns the same list, sorted by criteria id
    """

    cm = {c.id: c for c in crits}
    s = sorted_by_criterion(cm.keys())

    return [cm[k] for k in s]


def criteria_from_gescomponent(text):
    """ Given a ges component id, such as '4.3.1.- indicators 4.3A',
    return the matching indicator or criteria (or even descriptor, if provided
    with a descriptor such as D1.1
    """
    crit = text.split('-', 1)[0]

    if crit.endswith('.'):      # there is an
        crit = crit[:-1]

    return crit


class MarineReportingUnit(ItemLabel):
    """ A labeled MarineReportingUnit container
    """

    def __init__(self, id, title):
        self.name = self.id = id
        self.title = title


@db.use_db_session('2012')
def _muids_2012(country, region):
    t = sql.t_MSFD4_GegraphicalAreasID
    count, res = db.get_all_records(
        (t.c.MarineUnitID,
         t.c.MarineUnits_ReportingAreas),
        t.c.MemberState == country,
        t.c.RegionSubRegions == region,
        # There are some MRUs with empty MarineUnits_ReportingAreas
        # we should not exclude these, they are used in the reports
        # ex: ../se/ans/d2/art9/@@view-report-data-2012 ANS-SE-SR-Nordsjon
        # t.c.MarineUnits_ReportingAreas.isnot(None),
    )
    # r[0] = MarineUnitID, r[1] = MarineUnits_ReportingAreas
    res = [MarineReportingUnit(r[0], r[1] or r[0]) for r in res]

    return sorted(res)


@db.use_db_session('2018')
def _muids_2018(country, region):
    # this method needs "raw" access because the shapefile column slows things
    t = sql2018.MarineReportingUnit

    sess = db.session()
    q = sess\
        .query(t.MarineReportingUnitId, t.nameTxtInt, t.Description)\
        .filter(
            t.CountryCode == country,
            t.Region == region,
            # t.MarineReportingUnitId.isnot(None),
            # t.localId.isnot(None),      # TODO: this suits NL, check others
        )

    res = [MarineReportingUnit(m.MarineReportingUnitId,
                               m.nameTxtInt or m.Description)

           for m in q]

    return sorted(res)


@cache(lambda func, *args: '-'.join((func.__name__, args[0], args[1],
                                     args[2])), lifetime=1800)
def get_marine_units(country, region, year=None):
    """ Get a list of ``MarineReportingUnit`` objects
    """

    if year in ('2012', '2014'):
        return _muids_2012(country, region)
    elif year == '2018':
        return _muids_2018(country, region)

    raise NotImplementedError
