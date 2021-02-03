from collections import defaultdict

import lxml.etree
from zope.interface import Attribute, Interface, implements

from Products.Five.browser.pagetemplatefile import PageTemplateFile
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.labels import GES_LABELS
from wise.msfd.utils import (fixedorder_sortkey, get_annot, ItemLabel,
                             TemplateMixin)

from .vocabulary import REGIONAL_DESCRIPTORS_REGIONS


class IReportField(Interface):
    """ A field definition for displaying a report table
    """

    converter = Attribute(u'Function to convert value for display')
    label_collection = Attribute(u'If value is a id, where to find label')
    section = Attribute(u"The section that the field belongs to")
    drop = Attribute(u'Should the field be dropped from displayed report?')
    merge = Attribute(u'Merge this field with identical values')
    startgroup = Attribute(u'This field starts a new column group')
    filter_values = Attribute(u'???')


class DummyReportField(TemplateMixin):
    template = PageTemplateFile('pt/report_field_header.pt')

    def __init__(self, proxy_obj):
        self.title = proxy_obj.title
        self.name = proxy_obj.name
        self.drop = False
        self.article = 'Art11'
        self.section = 'element'
        self.setlevel = None


class ReportField(TemplateMixin):
    """ An object reprezenting the field (row) definition in a report table
    """
    implements(IReportField)

    template = PageTemplateFile('pt/report_field_header.pt')

    def __init__(self, node, article):
        self.title = node.text
        self.name = node.get('name')
        self.article = article

        self.label_collection = node.get('label')
        self.converter = node.get('convert')
        self.filter_values = node.get('filter')
        self.section = node.get('section', '')

        self.drop = node.get('skip') == 'true'

        self.setlevel = node.get('setlevel')

        if self.setlevel:
            self.setlevel = int(self.setlevel)

        # Regional descriptors
        self.getrowdata = node.get('getrowdata')


class ReportDefinition(object):
    """ Parser class for a XML report definition file.

    For 2018, use report_2018_def.xml, for 2012 use report_2012_def.xml
    """

    def __init__(self, fpath, article):
        self.article = article
        self.doc = lxml.etree.parse(fpath)
        self.nodes = self.doc.find(self.article).getchildren()
        self._fields = [ReportField(n, article) for n in self.nodes]

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

    criterions = []

    # need to add D1 descriptor to the criterion lists too, CY reported data
    # on the generic D1 descriptor
    if 'D1.' in descriptor.id:
        criterions.append(get_descriptor('D1'))

    criterions.append(descriptor)
    criterions.extend(descriptor.sorted_criterions())

    for muidlist, dataset in data.items():
        # build a map of existing criterions, so that we detect missing ones

        # this proxy object will serve as template for new cloned columns,
        # to be able to show an empty column
        tplobj = None

        # colmap = {}
        colmap = defaultdict(list)
        new = []

        for col in dataset:
            # rewrite the GESComponent feature. TODO: move this functionality
            # to the Proxy2018 and XML file, with a getter

            # if col.GESComponent in colmap:
            #     continue

            if col.GESComponent.is_descriptor():
                colmap[col.GESComponent].append(col)
            else:
                col.GESComponent = descriptor[col.GESComponent.id]
                colmap[col.GESComponent].append(col)

            if tplobj is None:
                tplobj = col

        for c in criterions:
            if c in colmap:
                col = colmap[c]
            else:
                col = [tplobj.clone(GESComponent=c)]
            new.extend(col)

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
        _mru = ItemLabel('No MRUs', 'No MRUs')
        res[_mru].extend(rows_extra)

    return res


ASSESSORS_ANNOT_KEY = 'wise.msfd.assessors'


def get_assessors():
    annot = get_annot()
    value = annot.get(ASSESSORS_ANNOT_KEY, '')

    return value


def set_assessors(value):
    annot = get_annot()
    annot[ASSESSORS_ANNOT_KEY] = value


def ordered_regions_sortkey(region_id):
    """ Sorting function to sort regions by the order defined in vocabulary.py
    REGIONAL_DESCRIPTORS_REGIONS
    """

    regions = REGIONAL_DESCRIPTORS_REGIONS
    regions_order = []

    for region in regions:
        if not region.is_main:
            continue

        regions_order.extend(region.subregions)

    return fixedorder_sortkey(region_id, regions_order)
