# -*- coding: utf-8 -*-

import csv

from pkg_resources import resource_filename

# GES criterias have been used in 2010/2012 reports and then revamped for 2018
# reports. As such, some exist in 2010 that didn't exist in 2018, some exist
# for 2018 that didn't exist for 2010 and they have changed their ids between
# the two reporting exercises.


class Criterion(object):
    """ A container for a GES criterion information
    """

    _id = None      # id for the 2018 version
    _title = None   # title for the 2018 version
    _alternatives = None

    def __init__(self, id, title, alternatives=None):
        self._id = id
        self._title = title
        self.alternatives = alternatives or []        # tuples of (id, title)

    def __repr__(self):
        return "<Criterion {}>".format(self.title)

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
            return "{} {}".format(self._id, self._title)

        if not self._id:
            id, title = alter[0]

            return "{} {}".format(id, title)

        alter_ids = len(alter) == 0 and alter[0][0] \
            or ', '.join([a[0] for a in alter])

        return "{} ({}) {}".format(
            self._id,
            alter_ids,
            self._title,
        )

    @property
    def descriptor(self):
        """ Returns the descriptor as a D<n> id
        """

        if self._id:        # 2018 version
            return self._id.split('C')[0]

        id = self.alternatives[0][0]    # 2012 version

        return 'D' + id.split('.')[0]

    def all_ids(self):

        return [self.id] + [x[0] for x in self.alternatives]


def parse_ges_terms():
    csv_f = resource_filename('wise.msfd',
                              'data/ges_terms.tsv')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter='\t')
        rows = list(csv_file)

    res = []

    for row in rows:
        if len(row) != 4:
            continue
        bits = [b.strip() for b in row]

        b1, b2, b3, b4 = bits

        id_2012 = None
        title_2012 = None
        id_2018 = None
        title_2018 = None

        if b1.startswith('D'):
            # new style criterions. Ex:
            # D6C5	D6C5 Benthic habitat condition	38	6.2.3 Proportion of ...
            id_2018 = b1
            title_2018 = b2.split(' ', 1)[1]

            if b4[0].isdigit():
                # we also have the old criterion
                id_2012 = b4.split(' ', 1)[0]
                title_2012 = b4.split(' ', 1)[1]
            else:
                # add it as GESOther if b4 is '-'
                id_2012 = 'GESOther'
                title_2012 = b4

            # if the criterion has already been defined, annotate that one

            seen = False

            for crit in res:
                if id_2018 and (crit.id == id_2018):
                    # already seen this criterion, let's append the title
                    seen = True
                    crit.alternatives.append((id_2012, title_2012))

            if not seen:
                crit = Criterion(id_2018, title_2018)

                if id_2012:
                    crit.alternatives.append((id_2012, title_2012))

                res.append(crit)

            continue

        if b1[0].isdigit():
            # old style criterions. Ex:
            # 5.3	5.3 Indirect effects of nutrient enrichment	52	Y
            id_2012 = b1
            title_2012 = b2.split(' ', 1)[1]

            crit = Criterion(None, None)
            crit.alternatives.append((id_2012, title_2012))
            res.append(crit)

    return res


GES_CRITERIONS = parse_ges_terms()


def get_ges_criterions(descriptor=None):
    """ Returns a list of Criterion objects
    """

    if not descriptor:
        return GES_CRITERIONS

    return [c for c in GES_CRITERIONS if c.descriptor == descriptor]
