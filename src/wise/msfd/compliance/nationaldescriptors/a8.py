# from collections import defaultdict

import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql
from wise.msfd.data import get_report_data
# from wise.msfd.gescomponents import get_ges_criterions
from wise.msfd.utils import Item, Node, Row  # RelaxedNode,

from ..base import BaseArticle2012
from .utils import get_descriptors

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}

# TODO: this needs to take region into account


class A8Item(Item):

    def __init__(self, criterion, targets_indicators, country_code):
        super(A8Item, self).__init__([])

        self.criterion = criterion
        self.targets_indicators = targets_indicators
        self.country_code = country_code

        self.targets = []

        for ti in targets_indicators:
            targets = ti.targets_for_criterion(self.criterion)
            self.targets.extend(targets)

        attrs = [
            ('Description [Targets]', ''),
        ]

        for title, value in attrs:
            self[title] = value


class Article8(BaseArticle2012):
    """ Article 8 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a9.pt')

    def __call__(self):

        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        muids = xp('//w:MarineUnitID/text()')
        muids = ', '.join(set(muids))

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]', [muids]),
        ]

        # cols = [A8Item(gc, all_target_indicators, self.country_code)
        #         for gc in gcs]

        cols = []

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
                    values.append(inner[name])
                row = Row(name, values)
                self.rows.append(row)

            break       # only need the "first" row

        return self.template()
