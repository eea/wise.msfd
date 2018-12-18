# -*- coding: utf-8 -*-

import csv
import json
from collections import namedtuple

from pkg_resources import resource_filename

from wise.msfd import db, sql2018


# GES criterias have been used in 2010/2012 reports and then revamped for 2018
# reports. As such, some exist in 2010 that didn't exist in 2018, some exist
# for 2018 that didn't exist for 2010 and they have changed their ids between
# the two reporting exercises.

Criterion2012 = namedtuple('Criterion2012', ['id', 'title'])
Feature = namedtuple('Feature', ['name', 'label', 'descriptors'])
Parameter = namedtuple('Parameter', ['name', 'unit', 'criterias'])


class Descriptor:
    """ A descriptor representation
    """

    def __init__(self, id=None, title=None, criterions=None):
        self.id = id
        self.title = title
        self.criterions = criterions or []

    def all_ids(self):
        res = set()
        res.add(self.id)

        if self.id == 'D6':
            res.add('D6/D1')

        if self.id == 'D4':
            res.add('D4/D1')

        # if self.id.startswith('D1.'):
        #     res.add('D1')

        for crit in self.criterions:
            for cid in crit.all_ids():
                res.add(cid)

        return res


class Criterion(object):
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

    def __init__(self, id, title, alternatives=None):
        self._id = id
        self._title = title
        self.alternatives = alternatives or []  # Criterion2012 objects

        # self.descriptors = descriptors or []
        # # belongs to these descriptors

    def __repr__(self):
        title = self.title.encode('ascii', 'replace')
        title = title.replace('?', '-')

        return "<Criterion {}>".format(title)

    def is_2018_exclusive(self):
        return not self.alternatives

    def is_2012_exclusive(self):
        return not self._id

    @property
    def id(self):
        return self._id or self.alternatives[0][0]

    @property
    def title(self):
        alter = self.alternatives

        if not alter:
            return u"{} {}".format(self._id, self._title)

        if not self._id:
            id, title = alter[0]

            return u"{} {}".format(id, title)

        alter_ids = len(alter) == 0 and alter[0][0] \
            or u', '.join([a[0] for a in alter])

        return u"{} ({}) {}".format(
            self._id,
            alter_ids,
            self._title,
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


def parse_ges_components():
    # Node: this method is not used, it doesn't offer a way to map old
    # criterias to new criterias
    # {
    #   "code": "1.1.3",
    #   "label": "(Indicator(old)) Area covered by the species (for
    #   sessile/benthic species)",
    #   "descriptor": "D1"
    # },
    gcomps = TERMSLIST['GESComponents']

    # {
    #   "code": "5.2",
    #   "label": "(Criteria(old)) Direct effects of nutrient enrichment",
    #   "descriptor": "D5"
    # },
    gcrits = TERMSLIST['GESCriterias']

    # {
    #   "code": "D1.1",
    #   "label": "(Descriptor) D1 - Biodiversity - birds"
    # },
    gdescs = TERMSLIST['GESDescriptors']

    descriptors = {d['label']: Descriptor(d['code'], d['label'])
                   for d in gdescs}
    descriptors['D1'] = Descriptor('D1', 'D1 - Biodiversity')
    criterions = {}

    for c in (gcomps + gcrits):
        if c['code'] not in criterions:
            c = Criterion(c['code'], c['label'], [])
            descriptors[c['descriptor']].criterions.add(c)
            criterions[c['code']] = c
        else:
            c = criterions[c['code']]
            descriptors[c['descriptor']].criterions.add(c)

    return descriptors, criterions


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
            descriptor = Descriptor(b1, b2, [])
            descriptors[descriptor.id] = descriptor

            continue

        if b1 in criterions:
            criterion = criterions[b1]
            descriptors[descriptor.id].criterions.append(criterion)
        else:
            criterion = Criterion(id=b1, title=b2)

            criterions[criterion.id] = criterion
            descriptors[descriptor.id].criterions.append(criterion)

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
    d_sorted = sorted(descriptors, key=lambda d: float(d[0].replace('D', '')))

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
            return c


def parse_codelists_file():
    """ Parse the msfd2018-codelists.json file
    """
    jsonf = resource_filename('wise.msfd',
                              'data/msfd2018-codelists.json')
    with open(jsonf) as f:
        d = json.load(f)

    return d


TERMSLIST = parse_codelists_file()


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


# def parse_features():
#     res = {}
#
#     FEATURES = TERMSLIST['ReferenceFeature']        # FeaturesSmart
#
#     for fr in FEATURES:
#         feature = fr['Feature']
#
#         if feature in res:
#             continue
#
#         descs = set([f['GEScomponent']
#                      .replace('D6/D1', 'D6').replace('D4/D1', 'D4')
#
#                      for f in FEATURES
#
#                      if f['Feature'] == feature])
#
#         res[feature] = Feature(feature, descs)
#
#     return res


def parse_features():
    res = {}

    FEATURES = TERMSLIST['FeaturesSmart']        #

    for fr in FEATURES:
        code = fr['code']
        label = fr['label']

        if code in res:
            continue

        descs = set([f['descriptor']
                     .replace('D6/D1', 'D6').replace('D4/D1', 'D4')

                     for f in FEATURES

                     if f['code'] == code])

        res[code] = Feature(code, label, descs)

    return res


FEATURES = parse_features()


def get_features(descriptor_code=None):
    if descriptor_code is None:
        return FEATURES.values()

    return [f
            for f in FEATURES.values()

            if descriptor_code in f.descriptors]


@db.use_db_session('2018')
def get_indicator_labels():
    mc = sql2018.IndicatorsIndicatorAssessmentTarget
    count, res = db.get_all_records(
        mc
    )
    labels = {}

    for row in res:
        code = row.IndicatorCode
        label = row.IndicatorTitle
        labels[code] = label

    # import pdb; pdb.set_trace()
    return labels


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


class LabelCollection(object):
    """ A convenience wrapper over multiple structures with labels

    Needed because ReferenceFeature does not contain all features
    """

    feature_labels = _parse_labels('Features')
    pressure_labels = _parse_labels('Pressures')
    parameter_labels = _parse_labels('Parameters')
    threshold_sources_labels = _parse_labels('ThresholdSources')
    units_labels = _parse_labels('Units')
    elementcode_sources_labels = _parse_labels('ElementCodeSources')
    ges_criterias_labels = _parse_labels('GESCriterias')
    ges_components_labels = _parse_labels('GESComponents')
    indicators_labels = get_indicator_labels()

    def get(self, collection_name, name):
        label_dict = getattr(self, collection_name, None)

        if not label_dict:
            return name

        label = label_dict.get(name, name)

        return label


LABELS = LabelCollection()
