from collections import defaultdict

import lxml.etree

from wise.msfd.gescomponents import GES_LABELS
from wise.msfd.utils import ItemLabel


class ReportDefinition(object):
    """ Parser class for a XML report definition file.

    For 2018, use report_2018_def.xml, for 2012 use report_2012_def.xml
    """

    def __init__(self, fpath, article):
        self.article = article
        self.doc = lxml.etree.parse(fpath)
        self.nodes = self.doc.find(self.article).getchildren()

    def get_elements(self):
        return self.nodes

    def get_group_by_fields(self):
        res = [
            x.get('name')

            for x in self.nodes

            if x.attrib.get('exclude', 'false') == 'true'
        ]

        return res

    def get_translatable_fields(self):
        res = [
            x.get('name')

            for x in self.nodes

            if x.attrib.get('translate', 'false') == 'true'
        ]

        return res


def _get_sorted_fields(reportdef, fields):
    """ field = name from DB
        title = title/label showed in the template

    :param fields: ['Feature', 'GESComponents', 'Element', 'TargetCode', ...]
    :param article: 'Art8'
    :return: [('<fieldname>', <title'), ...
              ('Feature', 'Feature'), ('GESComponents', ''GESComponents),
        ... , ('TargetCode', 'RelatedTargets')]
    """
    elements = reportdef.get_elements()

    labels = [
        (x.get('name'), x.text.strip())

        for x in elements

        if x.attrib.get('skip', 'false') == 'false'
    ]

    if not labels:
        final = [(x, x) for x in fields]

        return final

    diff = set(fields) - set([x.get('name') for x in elements])
    final = [(x, x) for x in diff]

    final.extend(labels)

    return final


def insert_missing_criterions(data, descriptor):
    """ For Art9 we want to show a row for all possible GESComponents,
    regardless if the MS has reported on that or not

    :param data: a map of <muid>: list of rows
    :param descriptor: a Descriptor instance

    This function will change in place the provided data
    """

    criterions = [descriptor] + descriptor.sorted_criterions()

    for muid, dataset in data.items():
        # build a map of existing criterions, so that we detect missing ones

        # this proxy object will serve as template for new cloned columns,
        # to be able to show an empty column
        tplobj = None
        colmap = {}
        new = []

        for col in dataset:
            # rewrite the GESComponent feature. TODO: move this functionality
            # to the Proxy2018 and XML file, with a getter
            col.GESComponent = descriptor[col.GESComponent]
            colmap[col.GESComponent] = col

            if tplobj is None:
                tplobj = col

        for c in criterions:
            if c in colmap:
                col = colmap[c]
            else:
                col = tplobj.clone(GESComponent=c)
            new.append(col)

        data[muid] = new


def group_by_mru(data):
    """ Group data by mru

    It returns a dict where the keys are ItemLabels of the MRU and values are
    list of rows for that mru
    """

    if not data:
        return {}

    res = defaultdict(list)

    mrus = {}

    for row in data:
        if not row.MarineReportingUnit:     # skip rows without muid
            continue

        mru = row.MarineReportingUnit

        if mru not in mrus:
            mru_label = GES_LABELS.get('mrus', mru)

            if mru_label != mru:
                mru_label = u"{} ({})".format(mru_label, unicode(mru))

            mru_item = ItemLabel(mru, mru_label)
            mrus[mru] = mru_item
        else:
            mru_item = mrus[mru]

        res[mru_item].append(row)

    return res
