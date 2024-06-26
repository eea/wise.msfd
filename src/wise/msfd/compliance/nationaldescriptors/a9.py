#pylint: skip-file
# from collections import defaultdict

from __future__ import absolute_import
import logging
from collections import defaultdict

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as ViewTemplate
from wise.msfd import db, sql
from wise.msfd.data import get_xml_report_data
from wise.msfd.gescomponents import (criteria_from_gescomponent,
                                     get_descriptor, get_ges_component,
                                     sorted_by_criterion)
from wise.msfd.labels import COMMON_LABELS, get_label
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow,
                             RelaxedNode, Row, natural_sort_key, to_html)

from ..base import BaseArticle2012
import six

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class DummyNode(object):
    def __init__(self, crit):
        # <MarineUnitID>{}</MarineUnitID>

        self.node = """
<Descriptors xmlns="http://water.eionet.europa.eu/schemas/dir200856ec">
    <ReportingFeature>{}</ReportingFeature>
</Descriptors>""".format(crit)

    def __call__(self):
        return self.node


class A9Item(Item):
    def __init__(self, parent, node, descriptors, muids):

        super(A9Item, self).__init__([])

        self._muids = muids.rows
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
            ('GES component', self.criterion),
            ('Method used', self.method_used),
            ('Marine reporting units', lambda: muids),
            ('Feature', self.feature),
            ('Criterion/indicator', self.ges_component),
            ('GES description', self.ges_description),
            ('Threshold values', self.threshold_value),
            ('Threshold value unit', self.threshold_value_unit),
            ('Proportion of area to achieve threshold value', self.proportion),
            ('Reference point type', self.reference_point_type),
            ('Baseline', self.baseline),
            ('Assessment method', self.assessment_method),
            ('Development status', self.development_status),
        ]

        for title, getter in attrs:
            self[title] = getter()

    def method_used(self):
        root = self.node.getroottree()
        method_node = root.find('w:Metadata/w:MethodUsed', namespaces=NSMAP)
        text = getattr(method_node, 'text', '')

        return to_html(text)

    def criterion(self):
        crit = criteria_from_gescomponent(self.id)
        ges_comp = get_ges_component(crit)

        if not hasattr(ges_comp, 'alternatives'):
            return ges_comp

        criterion_2012 = [x for x in ges_comp.alternatives if x.id == crit]

        if criterion_2012:
            c = criterion_2012[0]

            return "{} {}".format(c.id, c.title)

        return ges_comp.title

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
        count, mres = db.get_marine_unit_id_names(list(values.keys()))
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

        if not isinstance(filename, tuple):
            filename = [filename]

        def filter_descriptors(nodes, descriptor):
            res = []

            for d in nodes:
                rf = x('w:ReportingFeature/text()', d)[0]
                rf = criteria_from_gescomponent(rf)

                if rf in all_ids:
                    res.append(d)

            return res

        descriptor_class = get_descriptor(self.descriptor)
        all_ids = descriptor_class.all_ids()
        self.descriptor_label = descriptor_class.title

        if self.descriptor.startswith('D1.'):
            all_ids.add('D1')

        _cols = []
        _muids = []

        for fname in filename:
            text = get_xml_report_data(fname)

            if not text:
                self.rows = []

                return self.template()

            root = fromstring(text)

            def x(xpath, node=root):
                return node.xpath(xpath, namespaces=NSMAP)

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
            muid_ids = [y.id for y in self.muids]

            labels = [
                ItemLabel(m, t or m)
                for m, t in res
                if m in muid_ids
            ]

            # special case for PL where marine_unit_ids are not imported into DB
            # therefore we cannot get the labels for them
            if muids and not labels:
                labels = [ItemLabel(m, m) for m in set(muids)]

            self.muids_labeled = sorted(
                labels, key=lambda l: natural_sort_key(l.name)
            )
            _muids.extend(labels)
            muids = ItemList(labels)

            for node in descriptors:
                col_id = node.find('w:ReportingFeature', namespaces=NSMAP).text

                if col_id in seen:
                    continue

                item = A9Item(self, node, descriptors, muids)
                cols.append(item)
                seen.append(item.id)

            _cols.extend(cols)

        _muids = ItemList(_muids)
        # insert missing criterions
        self.insert_missing_criterions(descriptor_class, _cols, _muids)

        self.rows = []
        sorted_ges_c = sorted_by_criterion([c.ges_component() for c in _cols])

        def sort_func(col):
            return sorted_ges_c.index(col.ges_component())

        sorted_cols = sorted(_cols, key=sort_func)
        self.cols = list(sorted_cols)

        for col in sorted_cols:
            for name in col.keys():
                values = []

                for inner in sorted_cols:
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

        # straight rendering of all extracted items
        # for item in cols:
        #     for k, v in item.items():
        #         self.rows.append(Row(k, [v]))

    def auto_translate(self):
        # report_def = REPORT_DEFS[self.year][self.article]
        # translatables = report_def.get_translatable_fields()

        self.setup_data()

        translatables = self.context.TRANSLATABLES
        seen = set()

        for item in self.cols:
            for k in translatables:
                value = item[k]
                if not isinstance(value, six.string_types):
                    continue

                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        return ''

    def insert_missing_criterions(self, descriptor_class, cols, muids):
        criterions = descriptor_class.criterions
        reported_crits = [
            # needs split by '-' because of LV criterions
            x.ges_component().split('-')[0]
            for x in cols
        ]

        for crit in criterions:
            if crit.is_2018_exclusive():
                continue

            for crit2012 in crit.alternatives:
                crit_id = crit2012.id
                if crit_id in reported_crits:
                    continue

                dn = DummyNode(crit2012.id)
                dummy_node = fromstring(dn())

                item = A9Item(self, dummy_node, [], muids)
                cols.append(item)

    def __call__(self, filename=None):
        self.setup_data(filename)

        return self.template()


class A9AlternateItem(Item):
    """
    """

    def __init__(self, descriptor_item):
        super(A9AlternateItem, self).__init__()
        di = self.descriptor_item = descriptor_item

        attrs = [
            ('GES component', di.ReportingFeature),
            # Proportion not needed in 2018
            # ('Proportion', di.Proportion),
            ('Features', self.features()),
            ('GES description', di.DescriptionGES),
            # ('Justification for non-use of criterion',
            #     'Row not implemented (not mapped to 2012)'),
            # ('Justification for delay in setting EU/regional requirements',
            #     'Row not implemented (not mapped to 2012)'),
            # ('Determination date',
            #     'Row not implemented (not mapped to 2012)'),
            # ('Update type',
            #     'Row not implemented (not mapped to 2012)'),
        ]

        for title, value in attrs:
            self[title] = value

    def features(self):
        t = sql.t_MSFD9_Features
        count, res = db.get_all_records(
            t,
            t.c.MSFD9_Descriptor == self.descriptor_item.MSFD9_Descriptor_ID
        )
        vals = list(set([x.FeatureType for x in res] +
                        [x.FeaturesPressuresImpacts for x in res]))
        # return vals       # remove code below when properly integrated

        rows = [ItemLabel(v, get_label(v, 'features')) for v in vals]
        return ItemList(rows=rows)


class Article9Alternate(BaseArticle2012):
    """
    """
    template = ViewTemplate('pt/report-data-a8.pt')
    help_text = """ """

    @db.use_db_session('2012')
    def setup_data(self):
        t = sql.MSFD9Descriptor
        muids = {m.id: m for m in self.muids}
        count, res = db.get_all_records(
            t,
            t.MarineUnitID.in_(list(muids.keys())),
        )

        by_muid = defaultdict(list)
        descriptor = get_descriptor(self.descriptor)
        ok_ges_ids = descriptor.all_ids()

        for desc_item in res:
            ges_id = criteria_from_gescomponent(desc_item.ReportingFeature)

            if ges_id not in ok_ges_ids:
                continue
            item = A9AlternateItem(desc_item)
            by_muid[desc_item.MarineUnitID].append(item)

        self.rows = {}

        for muid, cols in by_muid.items():
            rows = []

            if not cols:
                continue

            for name in cols[0].keys():
                values = [c[name] for c in cols]
                row = Row(name, values)
                rows.append(row)

            self.rows[muids[muid]] = rows

    def __call__(self):
        self.setup_data()

        return self.template()
