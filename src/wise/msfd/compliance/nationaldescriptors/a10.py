import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    PageTemplateFile as PageTemplate
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql
from wise.msfd.data import country_ges_components, get_report_data
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.utils import Item, Node, Row

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}

# TODO: this needs to take region into account


class A10Item(Item):
    list_tpl = PageTemplate('../../pt/list.pt')

    def __init__(self, criterion, targets_indicators, country_code):
        super(A10Item, self).__init__([])

        self.criterion = criterion
        self.targets_indicators = targets_indicators
        self.country_code = country_code

        self.targets = []

        for ti in targets_indicators:
            targets = ti.targets_for_criterion(self.criterion)
            self.targets.extend(targets)

        feature_pressures = self.get_feature_pressures()

        attrs = [
            ('Description [Targets]', self.description()),
            ('Threshold value [TargetValue]', self.threshold_value()),
            ('Reference point type',
             self.pick('w:ReferencePointType/text()')),
            ('Baseline', self.pick('w:Baseline/text()')),
            ('Proportion', self.pick('w:Proportion/text()')),
            ('AssessmentMethod', self.pick('w:AssessmentMethod/text()')),
            ('Development status', self.pick('w:DevelopmentStatus/text()')),
            ('Type of target/indicator', self.pick('w:Type/text()')),
            ('Timescale', self.pick('w:TimeScale/text()')),
            ('Interim or GES target', self.pick('w:InterimGESTarget/text()')),
            ('Compatibility with existing targets/indicators',
             self.pick('w:CompatibilityExistingTargets/text()')),

        ]

        for name in [
                'Physical/chemical features',
                'Predominant habitats',
                'Functional group',
                'Pressures'
        ]:
            attrs.append((name, ", ".join(feature_pressures[name])))

        for title, value in attrs:
            self[title] = value

    @property
    def is_descriptor(self):
        return self.criterion.startswith('D')

    @db.use_db_session('2012')
    def _get_ges_description(self):
        # TODO: cache this info
        t = sql.t_MSFD_16a_9Detailed
        count, res = db.get_all_records(
            t.c.DescriptionGES,
            t.c.MemberState == self.country_code,
            t.c.ListOfGES == self.criterion,
        )

        for row in res:
            return row[0]       # there are multiple records, one for each MUID

    @db.use_db_session('2012')
    def get_feature_pressures(self):
        t = sql.t_MSFD_19b_10PhysicalChemicalFeatures
        target = self.pick('w:Feature/text()')

        # TODO: this needs to take region into account
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code,
            t.c.Targets == target,
            # TODO: region here
            # t.c['Marine region/subregion'] == 'BAL'
        )

        cols = t.c.keys()
        recs = [{k: v for k, v in zip(cols, row)} for row in res]

        _types = {
            'Functional group': set(),
            'Pressures': set(),
            'Predominant habitats': set(),
            'Physical/chemical features': set()
        }

        for rec in recs:
            t = rec['FeatureType']
            s = _types[t]

            if rec['FeaturesPressures'] == 'FunctionalGroupOther':
                s.add('FunctionalGroupOther')
                s.add(rec['OtherExplanation'])
            else:
                s.add(rec['FeaturesPressures'])

        return _types

    def description(self):
        if not self.criterion.startswith('D'):
            return self._get_ges_description()

        for ti in self.targets_indicators:
            for target in ti.targets_for_descriptor(self.criterion):
                desc = target['w:Description/text()']

                if desc:
                    return desc[0]

        return ""

    def threshold_value(self):
        m = {}

        for target in self.targets:
            m[target.marine_unit_id] = target['w:ThresholdValue/text()'][0]

        res = []

        for k in sorted(m):
            res.append('{} = {}'.format(k, m[k]))

        # TODO: return a List() here

        return self.list_tpl(rows=res)

    def pick(self, xpath):
        """ For values which are repeated across all targets nodes, try to find
        one with a positive value
        """

        if not self.is_descriptor:
            return ''

        for target in self.targets:
            v = target[xpath]

            if v:
                return v[0]

        return ''

    def set_pick(self, xpath):
        """ Just like pick, but return all distinct values
        """

        if not self.is_descriptor:
            return ''

        res = []

        for target in self.targets:
            res.extend(target[xpath])

        return set(res) or ''

    def reference_point_type(self):
        # for which MarineUnitID do we show information?

        return self.pick('')


class Target(Node):
    """ Wraps a <Target> node
    """
    def __init__(self, marine_unit_id, node, nsmap):
        super(Target, self).__init__(node, nsmap)
        self.marine_unit_id = marine_unit_id

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

        return [self.descriptor] + self['w:DesriptorCriterionIndicators/'
                                        'w:DesriptorCriterionIndicator/text()']


class TargetsIndicators(Node):
    """ A <TargetsIndicators> wrapper.

    There is one TargetsIndicators node for each MarineUnitID.
    It has multiple <Targets> nodes, one for each set of "descriptors"
    """

    def __init__(self, node):
        super(TargetsIndicators, self).__init__(node, NSMAP)
        self.id = self['w:MarineUnitID/text()'][0]
        self.targets = [Target(self.id, n, NSMAP)
                        for n in self['w:Targets']]

    def targets_for_descriptor(self, descriptor):
        return [t for t in self.targets if t.descriptor == descriptor]

    def targets_for_criterion(self, criterion):
        return [t for t in self.targets if criterion in t.criterions]


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a10.pt')

    def filtered_ges_components(self):
        m = self.descriptor.replace('D', '')

        gcs = country_ges_components(self.country_code)

        # TODO: handle D10, D11     !!

        return [self.descriptor] + [g for g in gcs if g.startswith(m)]

    def __call__(self):

        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        muids = xp('//w:MarineUnitID/text()')
        muids = ', '.join(sorted(set(muids)))

        gcs = self.filtered_ges_components()

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]', [muids]),
            Row('DescriptorCriterionIndicator', gcs),
        ]

        descriptor_class = get_descriptor(self.descriptor)
        self.descriptor_label = descriptor_class.title
        # ges_components = get_ges_criterions(self.descriptor)

        # wrap the target per MarineUnitID
        all_target_indicators = [TargetsIndicators(node)
                                 for node in xp('w:TargetsIndicators')]
        cols = [A10Item(gc, all_target_indicators, self.country_code)
                for gc in gcs]

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
                    values.append(inner[name])
                row = Row(name, values)
                self.rows.append(row)

            break       # only need the "first" row

        return self.template()
