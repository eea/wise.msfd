# from collections import defaultdict

import logging
import os
import tempfile

import requests
from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.utils import Item, Row

from ..base import BaseArticle2012
from .utils import get_descriptors

logger = logging.getLogger('wise.msfd')

NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class Node(object):
    """ A wrapper over the lxml etree to simplify syntax
    """

    def __init__(self, node):
        self.node = node

    def __getitem__(self, name):
        assert name.startswith('w:')        # this is just a reminder for devel

        return self.node.find(name, namespaces=NSMAP)

    def relax(self):
        return RelaxedNode(self.node)


class Empty(object):
    """ A "node" with empty text
    """

    @property
    def text(self):
        return ''


class RelaxedNode(Node):
    """ A "relaxed" version of the node getter.

    It never returns None from searches
    """

    def __getitem__(self, name):
        n = super(RelaxedNode, self).__getitem__(name)

        if n is None:
            return Empty()

        return n


N = Node        # alias for shorter names


class A9Item(Item):

    def __init__(self, node, descriptors):

        super(A9Item, self).__init__([])

        self.node = node
        self.g = RelaxedNode(node)

        self.descriptors = descriptors

        self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text

        # descriptor entries with same ReportingFeature
        # can be for a different MarineUnitID
        self.siblings = []

        for d in self.descriptors:
            n = Node(d)

            muid = n['w:MarineUnitID']

            if muid is None:
                continue

            feature = n['w:ReportingFeature'].text

            if feature != self.id:
                continue

            self.siblings.append(n)

        attrs = [
            ('Feature(s) reported [Feature]', self.feature),
            ('GES Component [Reporting feature]', self.ges_component),
            ('Threshold value(s)', self.threshold_value),
            ('Threshold value unit', self.threshold_value_unit),
            ('Reference point type', self.reference_point_type),
            ('Baseline', self.baseline),
            ('Proportion', self.proportion),
            ('Assessment method', self.assessment_method),
            ('Development status', self.development_status),
        ]

        for title, getter in attrs:
            self[title] = getter()

    def feature(self):
        # TODO: this needs more work, to aggregate with siblings
        res = []

        all_nodes = [s.node for s in self.siblings]

        for n in all_nodes:
            fpi = n.xpath('w:Features/w:FeaturesPressuresImpacts/text()',
                          namespaces=NSMAP)
            res.extend(fpi)

        return ', '.join(set(res))

    def ges_component(self):
        return self.id

    def threshold_value(self):
        m = {}

        for n in self.siblings:

            tv = n['w:ThresholdValue']

            if tv is None:
                continue

            muid = n['w:MarineUnitID'].text
            m[muid] = tv.text

        res = ['{} = {}'.format(k, v) for (k, v) in m.items()]

        return "\n".join(res)

    def threshold_value_unit(self):
        return self.g['w:ThresholdValueUnit'].text

    def reference_point_type(self):
        return self.g['w:ReferencePointType'].text

    def baseline(self):
        return self.g['w:Baseline'].text

    def proportion(self):
        return self.g['w:Proportion'].text

    def assessment_method(self):
        return self.g['w:AssessmentMethod'].text

    def development_status(self):
        return self.g['w:DevelopmentStatus'].text


class Article9(BaseArticle2012):
    """ Article 9 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a9.pt')

    def __call__(self):
        tmpdir = tempfile.gettempdir()
        filename = self.context.get_report_filename()
        assert '..' not in filename     # need better security?

        fpath = os.path.join(tmpdir, filename)

        if filename in os.listdir(tmpdir):
            with open(fpath) as f:
                text = f.read()
            logger.info("Using cached XML file: %s", fpath)
        else:
            url = self.context.get_report_file_url(filename)
            req = requests.get(url)
            text = req.content
            logger.info("Requesting XML file: %s", fpath)

            with open(fpath, 'wb') as f:
                f.write(text)

        root = fromstring(text)

        self.descriptor_label = dict(get_descriptors())[self.descriptor]

        def x(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        def filter_descriptors(nodes, descriptor):
            res = []
            m = descriptor.replace('D', '')

            for d in nodes:
                rf = x('w:ReportingFeature/text()', d)[0]

                if rf == descriptor or rf.startswith(m):
                    res.append(d)

            return res

        # these are the records we are interested in
        descriptors = filter_descriptors(x('//w:Descriptors'),
                                         self.descriptor)

        # the xml files is a collection of records that need to be agregated
        # in order to "simplify" their information. For example, the
        # ThresholdValues need to be shown for all MarineUnitIds, but the
        # grouping criteria is the "GES Component"

        cols = []
        seen = []

        for node in descriptors:
            col_id = node.find('w:ReportingFeature', namespaces=NSMAP).text

            if col_id in seen:
                continue

            item = A9Item(node, descriptors)
            cols.append(item)
            seen.append(item.id)

        self.rows = []

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
                    values.append(inner[name])
                row = Row(name, values)
                self.rows.append(row)

            break       # only need the "first" row

        # straight rendering of all extracted items
        # for item in cols:
        #     for k, v in item.items():
        #         self.rows.append(Row(k, [v]))

        return self.template()
