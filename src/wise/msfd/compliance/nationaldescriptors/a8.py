import logging
from collections import defaultdict

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql2018  # sql,
from wise.msfd.data import country_ges_components, get_report_data
from wise.msfd.gescomponents import Criterion, get_ges_criterions
from wise.msfd.utils import Item, Node, Row  # RelaxedNode,

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}

# TODO: this needs to take regions into account

# a criterion is either a Descriptor (2018 concept), a Criteria or an Indicator


class Descriptor(Criterion):
    """ Override the default Criterion to offer a nicer title
    (doesn't duplicate code)
    """

    @property
    def title(self):
        return self._title


class A8Item(Item):
    """ A column in the 2012 Art8 assessment.

    It is created with a focus on individual <Indicator> tags, as that is the
    most basic unit in the report columns
    """

    def __init__(self, report, indicator_assessment, country_code,
                 marine_unit_id, criterion):

        super(A8Item, self).__init__([])

        self.country_code = country_code
        self.criterion = criterion
        self.marine_unit_id = marine_unit_id

        # How to handle multiple reports?
        self.report = report
        self.indicator_assessment = indicator_assessment

        self['CriteriaType [GESComponent]'] = self.criterion.title

        attrs = [
            ('Topic', self.topic),
            # ('[Parameter]', self.parameter),
            ('ThresholdValue', self.threshold_value),
        ]

        for title, handler in attrs:
            self[title] = self.handle_missing_assessment(handler)

    def handle_missing_assessment(self, handler):
        if self.indicator_assessment is None:
            return ''

        return handler()

    def threshold_value(self):
        return self.indicator_assessment['c:ThresholdValue/text()'][0]

    def topic(self):
        return self.indicator_assessment.topic


class IndicatorAssessment(Node):
    """ A wrapper over <Indicators> nodes
    """

    @property
    def assessment(self):
        # the AssessmentPI node

        return Node(self.node.getparent().getparent(), NSMAP)

    @property
    def topic(self):
        topic = self.assessment['w:Topic/text()']

        return topic and topic[0] or ''     # empty if descriptor column


class ReportTag(Node):
    def __init__(self, node, nsmap):
        super(ReportTag, self).__init__(node, nsmap)

        self.marine_unit_id = self['w:MarineUnitID/text()'][0]

    @property
    def criterias(self):
        return self['w:AssessmentPI/w:Assessment/c:Criterias/'
                    'c:Criteria/c:CriteriaType/text()']

    @property
    def indicators(self):
        return self['w:AssessmentPI/w:Assessment/c:Indicators/'
                    'c:Indicator/text()']

    @property
    def descriptor(self):
        # Used to filter the report based on intended descriptor

        for crit in (self.criterias + self.indicators):
            if crit.startswith('D'):
                return crit

            if '.' in crit:
                # this means that only D1 is supported, 1.1, etc are not
                # supported. For 2012, I think this is fine??

                return 'D' + crit.split('.', 1)[0]

    @property
    def report_type(self):      # TODO: this needs check
        tag = self.node.tag.replace(self.node.nsmap[None] + '{}', '')

        return tag

    def indicator_assessments(self, criterion):
        res = []

        indicators = [IndicatorAssessment(n, NSMAP)
                      for n in self['.//c:Indicators']]

        for crit_id in criterion.all_ids():
            for n_i in indicators:
                crit = n_i['c:Indicator/text()'][0]

                if crit == crit_id:
                    res.append(n_i)

        return res


class Article8(BaseArticle2012):
    """ Article 8 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a8.pt')

    def filtered_ges_components(self):
        m = self.descriptor.replace('D', '')

        gcs = country_ges_components(self.country_code)

        # TODO: handle D10, D11     !!

        return [self.descriptor] + [g for g in gcs if g.startswith(m)]

    @db.use_db_session('2018')
    def descriptor_criterion(self):
        mc = sql2018.LGESComponent
        count, res = db.get_all_records(
            mc,
            mc.GESComponent == 'Descriptor'
        )
        descriptors = [(x.Code.split('/')[0], x.Description) for x in res]
        descriptors = dict(descriptors)

        return Descriptor(self.descriptor, descriptors[self.descriptor])

    def __call__(self):

        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        # TODO: should use declared set of marine unit ids
        muids = sorted(set(xp('//w:MarineUnitID/text()')))
        self.muids = muids

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]', [', '.join(set(muids))]),
        ]

        # TODO: these are tags for article 8b, needs also for 8a
        tags = [
            'PhysicalLoss',
            'PhysicalDamage',
            'Noise',
            'Litter',
            'HydrologicalProcesses',
            'HazardousSubstances',
            'PollutionEvents',
            'Nutrients',
            'MicrobialPathogens',
            'NIS',
            'ExtractionofFishShellfish',
            'Acidification',
        ]

        # each of the following report tags can appear multiple times, once per
        # MarineUnitID. Each one can have multiple <AssessmentPI>,
        # for specific topics. An AssessmentPI can have multiple indicators

        report_map = defaultdict(list)

        for name in tags:
            nodes = xp('//w:' + name)

            for node in nodes:
                rep = ReportTag(node, NSMAP)

                if rep.descriptor == self.descriptor:
                    report_map[rep.marine_unit_id].append(rep)

        ges_crits = [self.descriptor_criterion()]
        ges_crits.extend(get_ges_criterions(self.descriptor))

        # a bit confusing code, we have multiple sets of rows, grouped in
        # report_data under the marine unit id key.
        report_data = {}

        # TODO: use reported list of muids per country,from database

        for muid in muids:
            if muid not in report_map:
                logger.warning("MarineUnitID not reported: %s, %s, Article 8",
                               muid, self.descriptor)
                report_data[muid] = []

                continue

            m_reps = report_map[muid]

            assert len(m_reps) < 2, "Multiple reports for same MarineUnitID?"
            report = m_reps[0]

            # TODO: redo this, it needs to be done per indicator
            # join the criterions with their corresponding assessments
            gc_as = zip(ges_crits,
                        [report.indicator_assessments(gc) for gc in ges_crits])

            report = m_reps[0]
            cols = []

            for gc, assessments in gc_as:
                if not assessments:     # if there are no assessments for the
                                        # criterion, just show it
                    item = A8Item(report,
                                  None, self.country_code, muid, gc)
                    cols.append(item)

                    continue

                for assessment in assessments:
                    item = A8Item(report,
                                  assessment, self.country_code, muid, gc)
                    cols.append(item)

            rows = []

            for col in cols:
                for name in col.keys():
                    values = []

                    for inner in cols:
                        values.append(inner[name])
                    row = Row(name, values)
                    rows.append(row)

                break       # only need the "first" row
            report_data[muid] = rows

            break       # debug, only handle first muid

        self.rows = report_data

        return self.template()
