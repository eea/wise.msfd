from collections import defaultdict

import lxml.etree

from Products.Five.browser.pagetemplatefile import PageTemplateFile
from wise.msfd.gescomponents import GES_LABELS
from wise.msfd.utils import ItemLabel, TemplateMixin


class ReportField(TemplateMixin):
    """ An object reprezenting the field (row) definition in a report table
    """
    template = PageTemplateFile('pt/report_field_header.pt')

    def __init__(self, node):
        self.title = node.text
        self.name = node.get('name')

        self.label_collection = node.get('label')
        self.converter = node.get('convert')

        self.group = node.get('group')

        self.drop = node.get('skip') == 'true'
        self.merge = node.get('merge') == 'true'


class ReportDefinition(object):
    """ Parser class for a XML report definition file.

    For 2018, use report_2018_def.xml, for 2012 use report_2012_def.xml
    """

    def __init__(self, fpath, article):
        self.article = article
        self.doc = lxml.etree.parse(fpath)
        self.nodes = self.doc.find(self.article).getchildren()
        self._fields = [ReportField(n) for n in self.nodes]

    def get_fields(self):
        return self._fields

    def get_translatable_fields(self):
        res = [
            x.get('name')

            for x in self.nodes

            if x.attrib.get('translate', 'false') == 'true'
        ]

        return res


def _resort_fields(reportdef, fields):
    """ field = name from DB
        title = title/label showed in the template

    :param fields: ['Feature', 'GESComponents', 'Element', 'TargetCode', ...]
    :param article: 'Art8'
    :return: [('<fieldname>', <title'), ...
              ('Feature', 'Feature'), ('GESComponents', ''GESComponents),
        ... , ('TargetCode', 'RelatedTargets')]
    """
    elements = reportdef.get_elements()

    labels = []

    for x in elements:
        if x.attrib.get('skip', 'false') == 'true':
            continue

        name = x.get('name')
        label = x.text.strip()

        labels.append((name, label))

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

    for muidlist, dataset in data.items():
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

        data[muidlist] = new


def group_by_mru(data):
    """ Group data by mru

    It returns a dict where the keys are ItemLabels of the MRU and values are
    list of rows for that mru
    """

    if not data:
        return {}

    res = defaultdict(list)

    mrus = {}
    # rows with empty MRU field are added to all MRUs
    # This case applies for Art9, when justification for delay is reported
    rows_extra = []

    for row in data:
        if not row.MarineReportingUnit:     # skip rows without muid
            rows_extra.append(row)
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

    for mru in res.keys():
        for row in rows_extra:
            res[mru].append(row)

    # Special case for Art9, when no real data is reported besides
    # justification for delay
    if not res and rows_extra:
        res['No MRUs'].extend(rows_extra)

    return res
