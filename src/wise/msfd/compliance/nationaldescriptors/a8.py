# from collections import defaultdict

import logging
from collections import defaultdict

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.data import country_ges_components, get_report_data
from wise.msfd.gescomponents import Criterion, get_ges_criterions
from wise.msfd.utils import Item, Node, Row  # RelaxedNode,

from ..base import BaseArticle2012
from .utils import get_descriptors

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}

# TODO: this needs to take region into account

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

    It corresponds to the <AssessmentPI> tags in the report
    """

    def __init__(self, reports, country_code, marine_unit_id, criterion):
        super(A8Item, self).__init__([])

        self.country_code = country_code
        self.criterion = criterion
        self.marine_unit_id = marine_unit_id

        # How to handle multiple reports?
        self.reports = reports

        attrs = [
            # ('Indicator [RelatedIndicator]', self.criterion.title),
            ('CriteriaType [GESComponent]', self.criterion.title)
        ]

        for title, value in attrs:
            self[title] = value

        for report in self.reports:
            print report.assessments

        import pdb; pdb.set_trace()


class Assessment(Node):
    """ A wrapper over <AssessmentPI> nodes
    """

    @property
    def indicators(self):
        return self['w:Indicators/w:Indicator/text()']


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

    @property
    def assessments(self):
        res = defaultdict(list)

        for node in self['w:AssessmentPI/w:Assessment']:
            n = Assessment(node, NSMAP)

            for codes in n['c:Indicators/c:Indicator/text()']:
                for code in codes:
                    res[code].append(n)

        return res

    def assessments_for_indicator(self, indicator):
        return [a for a in self.assessments if indicator in a.indicators]


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
        reports = []

        for name in tags:
            nodes = xp('//w:' + name)

            for node in nodes:
                reports.append(ReportTag(node, NSMAP))

        filtered_reports = [rep for rep in reports
                            if rep.descriptor == self.descriptor]

        report_map = defaultdict(list)      # reports, grouped by MarineUnitID

        for report in filtered_reports:
            report_map[report.marine_unit_id].append(report)

        gcs = [self.descriptor_criterion()] + \
            get_ges_criterions(self.descriptor)

        # a bit confusing code, we have multiple sets of rows, grouped in
        # report_data under the marine unit id key
        report_data = {}

        for muid in muids:      # TODO: use reported list of muids per country,
                                # from database
            m_reps = report_map[muid]
            cols = [A8Item(m_reps, self.country_code, muid, gc) for gc in gcs]

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

        self.rows = report_data

        return self.template()
