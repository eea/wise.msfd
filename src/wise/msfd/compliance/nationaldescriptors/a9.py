# from collections import defaultdict

import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as ViewTemplate
from wise.msfd import db
from wise.msfd.data import get_report_data
from wise.msfd.gescomponents import (criteria_from_gescomponent, get_criterion,
                                     get_descriptor, is_descriptor,
                                     sorted_by_criterion)
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow,
                             RelaxedNode, Row)

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class A9Item(Item):
    def __init__(self, parent, node, descriptors, muids):

        super(A9Item, self).__init__([])

        self.parent = parent
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
            ('GES descriptor, criterion or indicator [GEScomponent]',
             self.criterion),
            ('Marine reporting unit(s)', lambda: muids),
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

    def criterion(self):

        crit = criteria_from_gescomponent(self.id)

        if is_descriptor(crit):
            return get_descriptor(crit).title

        crit = get_criterion(crit)

        return crit.title

    def feature(self):
        # TODO: this needs more work, to aggregate with siblings
        res = set()

        all_nodes = [s.node for s in self.siblings]

        for n in all_nodes:
            fpi = n.xpath('w:Features/w:FeaturesPressuresImpacts/text()',
                          namespaces=NSMAP)

            for x in fpi:
                res.add(x)

        labels = [ItemLabel(k, COMMON_LABELS.get(k, k))
                  for k in res]

        return ItemList(labels)

    def ges_component(self):
        return self.id

    def ges_description(self):
        v = self.g['w:DescriptionGES/text()']

        return v and v[0] or ''

    def threshold_value(self):
        values = {}

        for n in self.siblings:

            tv = n['w:ThresholdValue/text()']

            if not tv:
                continue

            muid = n['w:MarineUnitID/text()'][0]

            # filter values according to region's marine unit ids

            if muid not in self.parent.muids:
                continue

            values[muid] = tv[0]

        rows = []
        count, mres = db.get_marine_unit_id_names(values.keys())
        muid_labels = dict(mres)

        for muid in sorted(values.keys()):
            name = u'{} = {}'.format(muid, values[muid])
            title = u'{} = {}'.format(muid_labels[muid], values[muid])

            label = ItemLabel(name, title)
            rows.append(label)

        return ItemList(rows=rows)

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

    # TODO: add MethodUsed


class Article9(BaseArticle2012):
    """ Article 9 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = ViewTemplate('pt/report-data-a9.pt')
    help_text = """
    - we identify the filename for the original XML file, by looking at the
      MSFD10_Imports table. This is the same file that you can find in the
      report table header on this page.

    - we download this file from CDR and parse it.

    - we take all the <Descriptors> tag in the file and we filter them by
      converting the ReportingFeature to the closest criteria or indicator,
      then matching the available criterias for the current descriptor. We use
      this table to match criterias to descriptors:

      https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv

    - because the descriptor records are repeated (one time for each marine
      unit id), we take only the first one for each marine unit id, for each
      ReportingFeature tag. We build result columns from those.
"""

    def setup_data(self, filename=None):
        if not filename:
            filename = self.context.get_report_filename()
        text = get_report_data(filename)

        if not text:
            self.rows = []

            return self.template()

        root = fromstring(text)

        descriptor_class = get_descriptor(self.descriptor)
        self.descriptor_label = descriptor_class.title

        def x(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        def filter_descriptors(nodes, descriptor):
            res = []

            for d in nodes:
                rf = x('w:ReportingFeature/text()', d)[0]
                rf = criteria_from_gescomponent(rf)

                if rf in descriptor_class.all_ids():
                    res.append(d)

            return res

        # these are the records we are interested in
        descriptors = filter_descriptors(x('//w:Descriptors'),
                                         self.descriptor)

        # the xml file is a collection of records that need to be agregated
        # in order to "simplify" their information. For example, the
        # ThresholdValues need to be shown for all MarineUnitIds, but the
        # grouping criteria is the "GES Component"

        cols = []
        seen = []

        muids = root.xpath('//w:MarineUnitID/text()', namespaces=NSMAP)

        count, res = db.get_marine_unit_id_names(list(set(muids)))

        labels = [ItemLabel(m, t) for m, t in res if m in self.muids]
        muids = ItemList(labels)

        for node in descriptors:
            col_id = node.find('w:ReportingFeature', namespaces=NSMAP).text

            if col_id in seen:
                continue

            item = A9Item(self, node, descriptors, muids)
            cols.append(item)
            seen.append(item.id)

        self.rows = []

        sorted_ges_c = sorted_by_criterion([c.ges_component() for c in cols])

        def sort_func(col):
            return sorted_ges_c.index(col.ges_component())

        sorted_cols = sorted(cols, key=sort_func)
        self.cols = list(sorted_cols)

        for col in sorted_cols:
            for name in col.keys():
                values = []

                for inner in sorted_cols:
                    values.append(inner[name])

                values = [self.context.translate_value(name, value=v)
                          for v in values]
                row = RawRow(name, values)
                self.rows.append(row)

            break       # only need the "first" row

        # straight rendering of all extracted items
        # for item in cols:
        #     for k, v in item.items():
        #         self.rows.append(Row(k, [v]))

    def __call__(self, filename=None):
        self.setup_data(filename)

        return self.template()
