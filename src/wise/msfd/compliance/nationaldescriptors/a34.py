import logging
from collections import defaultdict

from lxml.etree import fromstring
from sqlalchemy.orm.relationships import RelationshipProperty

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql  # , sql2018
from wise.msfd.data import get_xml_report_data
from wise.msfd.gescomponents import (Criterion, MarineReportingUnit,
                                     get_criterion, get_descriptor)
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow,
                             RelaxedNode, Row, natural_sort_key, to_html)

from ..base import BaseArticle2012
from .data import REPORT_DEFS

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


class A34Item(Item):
    def __init__(self, parent, node):

        super(A34Item, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        # self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text

        self.siblings = []

        attrs = [
            ('Member state description', lambda: 'No data'),
            ('Region / subregion', lambda: 'No data'),
            ('Subdivisions', lambda: 'No data'),
            ('Marine reporting units description', lambda: 'No data'),
            ('Member state', lambda: 'No data'),
            ('Area type', lambda: 'No data'),
            ('MRU ID', lambda: 'No data'),
            ('Marine reporting unit,', lambda: 'No data'),
        ]

        for title, getter in attrs:
            self[title] = getter()

    def method_used(self):
        root = self.node.getroottree()
        method_node = root.find('w:Metadata/w:MethodUsed', namespaces=NSMAP)
        text = getattr(method_node, 'text', '')

        return to_html(text)

    def feature(self):
        # TODO: this needs more work, to aggregate with siblings
        res = set()

        all_nodes = [s.node for s in self.siblings]

        for n in all_nodes:
            fpi = n.xpath('w:Features/w:FeaturesPressuresImpacts/text()',
                          namespaces=NSMAP)

            for x in fpi:
                res.add(x)

        labels = [ItemLabel(k, COMMON_LABELS.get(k, k) or k)
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


class Article34(BaseArticle2012):
    # TODO not implemented, copy of Article 8
    """ Article 3 & 4 implementation

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a3-4.pt')
    help_text = ""

    def setup_data(self):
        filename = self.context.get_report_filename()
        text = get_xml_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        # basic algorthim to detect what type of report it is
        article = self.article

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        cols = []
        # TODO get nodes from XML
        nodes = [1, 2, 3]

        for node in nodes:
            item = A34Item(self, node)
            cols.append(item)

        self.rows = []

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
                    values.append(inner[name])

                raw_values = []
                vals = []
                for v in values:
                    raw_values.append(v)
                    vals.append(self.context.translate_value(
                        name, v, self.country_code))

                # values = [self.context.translate_value(name, value=v)
                #           for v in values]

                row = RawRow(name, vals, raw_values)
                self.rows.append(row)

            break       # only need the "first" row

        self.cols = cols

    def __call__(self):
        self.setup_data()

        return self.template()

    def auto_translate(self):
        self.setup_data()
        translatables = self.context.TRANSLATABLES
        seen = set()

        for table in self.rows.items():
            muid, table_data = table

            for row in table_data:
                if not row:
                    continue
                if row.title not in translatables:
                    continue

                for value in row.raw_values:
                    if not isinstance(value, basestring):
                        continue
                    if value not in seen:
                        retrieve_translation(self.country_code, value)
                        seen.add(value)

        return ''
