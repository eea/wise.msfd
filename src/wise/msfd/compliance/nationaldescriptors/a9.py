# from collections import defaultdict

import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    PageTemplateFile as PageTemplate
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as ViewTemplate
from wise.msfd.data import get_report_data
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.utils import Item, ItemList, Node, RelaxedNode, Row

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class A9Item(Item):
    # list_tpl = PageTemplate('../../pt/list.pt')

    def __init__(self, node, descriptors):

        super(A9Item, self).__init__([])

        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        self.descriptors = descriptors

        self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text

        # descriptor entries with same ReportingFeature
        # can be for a different MarineUnitID
        self.siblings = []

        for d in self.descriptors:
            n = Node(d, nsmap=NSMAP)

            muid = n['w:MarineUnitID']

            if muid is None:
                continue

            feature = n['w:ReportingFeature/text()'][0]

            if feature != self.id:
                continue

            self.siblings.append(n)

        attrs = [
            ('Feature(s) reported [Feature]', self.feature),
            ('GES Component [Reporting feature]', self.ges_component),
            ('GES description', self.ges_description),
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

    def ges_description(self):
        v = self.g['w:DescriptionGES/text()']

        return v and v[0] or ''

    def threshold_value(self):
        m = {}

        for n in self.siblings:

            tv = n['w:ThresholdValue/text()']

            if not tv:
                continue

            muid = n['w:MarineUnitID/text()'][0]
            m[muid] = tv[0]

        res = [u'{} = {}'.format(k, m[k]) for k in sorted(m)]

        return ItemList(rows=res)

    def threshold_value_unit(self):
        v = self.g['w:ThresholdValueUnit/text()']

        return v and v[0] or ''

    def reference_point_type(self):
        v = self.g['w:ReferencePointType/text()']

        return v and v[0] or ''

    def baseline(self):
        v = self.g['w:Baseline/text()']

        return v and v[0] or ''

    def proportion(self):
        v = self.g['w:Proportion/text()']

        return v and v[0] or ''

    def assessment_method(self):
        v = self.g['w:AssessmentMethod/text()']

        return v and v[0] or ''

    def development_status(self):
        v = self.g['w:DevelopmentStatus/text()']

        return v and v[0] or ''


class Article9(BaseArticle2012):
    """ Article 9 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = ViewTemplate('pt/report-data-a9.pt')

    def __call__(self):
        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        descriptor_class = get_descriptor(self.descriptor)
        self.descriptor_label = descriptor_class.title

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

        muids = root.xpath('//w:MarineUnitID/text()', namespaces=NSMAP)
        muids = ', '.join(set(muids))

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]', [muids])
        ]

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
