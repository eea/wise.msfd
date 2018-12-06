# -*- coding: utf-8 -*-

import csv
from collections import namedtuple

from pkg_resources import resource_filename

# GES criterias have been used in 2010/2012 reports and then revamped for 2018
# reports. As such, some exist in 2010 that didn't exist in 2018, some exist
# for 2018 that didn't exist for 2010 and they have changed their ids between
# the two reporting exercises.


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

        for crit in self.criterions:
            for cid in crit.all_ids():
                res.add(cid)

        return res


Criterion2012 = namedtuple('Descriptor', ['id', 'title'])


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

    def __init__(self, id, title, descriptors=None, alternatives=None):
        self._id = id
        self._title = title
        self.descriptors = descriptors or []    # belongs to these descriptors
        self.alternatives = alternatives or []  # Criterion2012 objects

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

    def belongs_to_descriptor(self, descriptor_id):
        for descriptor in self.descriptors:
            if descriptor.id == descriptor_id:
                return True

        return False

    def all_ids(self):

        return set([self.id] + [x[0] for x in self.alternatives])

    def has_alternative(self, id):
        return any([x.id == id for x in self.alternatives])


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
        else:
            criterion = Criterion(id=b1, title=b2, descriptors=[descriptor])
            criterions[b1] = criterion

            descriptors[descriptor.id].criterions.append(criterion)

        # TODO: redo this for 2012 exclusive
        # if b3 and (not criterion.has_alternative(b3)):
        #     crit = Criterion2012(*b3.split(' ', 1))
        #     criterion.alternatives.append(crit)

    return descriptors, criterions


GES_DESCRIPTORS, GES_CRITERIONS = parse_ges_extended_format()


def get_descriptor(descriptor=None):
    """ Returns a Descriptor object, that has criterions attached

    :param get_descriptor: descriptor id, ex D5
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
