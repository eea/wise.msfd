# from collections import defaultdict

import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql
from wise.msfd.data import get_report_data
from wise.msfd.gescomponents import get_ges_criterions
from wise.msfd.utils import Item, Node, RelaxedNode, Row

from ..base import BaseArticle2012
from .utils import get_descriptors

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class A10Item(Item):

    def __init__(self):

        super(A10Item, self).__init__([])

        self.node = node
        self.g = RelaxedNode(node)

        self.descriptors = descriptors

        self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text


class Target(Node):

    @property
    def descriptor(self):

        for dci in self['w:DesriptorCriterionIndicators/'
                        'w:DesriptorCriterionIndicator/text()']:

            if dci.startswith('D'):
                return dci

            if '.' in dci:
                # this means that only D1 is supported, 1.1, etc are not
                # supported. For 2012, I think this is fine??

                return 'D' + dci.split('.', 1)[0]

    @property
    def criterions(self):
        return self['w:DesriptorCriterionIndicators/'
                    'w:DesriptorCriterionIndicator/text()']


class MarineTarget(Node):
    def __init__(self, node):
        super(MarineTarget, self).__init__(node)
        self.id = self['w:MarineUnitID/text()']
        self.targets = [Target(n) for n in self['w:Targets']]

    def targets_for_descriptor(self, descriptor):
        return [t for t in self.targets if t.descriptor == descriptor]


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a9.pt')

    def _ges_components(self):
        t = sql.t_MSFD_19a_10DescriptiorsCriteriaIndicators
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code,
        )
        import pdb; pdb.set_trace()

        return res

    def filtered_ges_components(self):
        m = self.descriptor.replace('D', '')

        gcs = self._ges_components()

        return [self.descriptor] + [g for g in gcs if g.startswith(m)]

    def __call__(self):

        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        muids = xp('//w:MarineUnitID/text()')
        muids = ', '.join(set(muids))

        gcs = self.filtered_ges_components()

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]', [muids]),
            Row('DescriptorCriterionIndicator', [gcs]),
        ]

        self.descriptor_label = dict(get_descriptors())[self.descriptor]
        # ges_components = get_ges_criterions(self.descriptor)

        targets = xp('TargetsIndicators')

        # wrap the target per MarineUnitID
        w_targets = [MarineTarget(node) for node in targets]
        cols = [A10Item(gc, w_targets) for gc in gcs]

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
