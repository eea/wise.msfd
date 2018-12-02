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

        attrs = [
            ('Analysis [Feature]', self.analysis),
            ('[Element]', lambda: 'Row not implemented'),
            ('CriteriaType [GESComponent]', lambda: self.criterion.title),
            ('Topic', self.topic),
            ('[Parameter]', lambda: 'Row not implemented'),
            ('ThresholdValue', self.threshold_value),
            ('SumInfo1 [ValueAchieved]', self.suminfo1),
            ('SumInfo1Unit/ThresholdValueUnit [ValueUnit]', self.suminfo1_tv),
            ('[ProportionThresholdValue]', lambda: 'Row not implemented'),

            # TODO: check fields

            ('Status [CriteriaStatus]', self.as_status),
            ('StatusTrend', self.as_status_trend),
            ('StatusConfidence', self.as_status_confidence),
            ('StatusDescription [DescriptionCriteria]',
             self.as_status_description),
            ('Limitations (DesciptionElement)', self.limitations),
            ('RecentTimeStart/RecentTimeEnd/AssessmentDateStart/'
             'AssessmentDateEnd [AssessmentPeriod]', self.recent_time_start),

            ('LevelPressureOverall: Description', self.lpo_description),
            ('LevelPressureOverall: SumInfo1 [proportion of area subject '
             'to nutrient enrichment]', self.lpo_suminfo1),
            ('LevelPressureOverall: SumInfo1Confidence', self.lpo_confidence),

            # TODO: this needs to be done in a generic mode.
            # LevelPressure<PressureID>
            # ImpactPressure<PressureID>

            ('LevelPressureN/P/OLoad: Description', self.pres_description),
            ('LevelPressureN/P/OLoad: SumInfo1 [input load of '
             'nitrogen/phosphorus/organic matter]', self.pres_sum1),
            ('LevelPressureN/P/OLoad: SumInfo1Unit', self.pres_unit),
            ('LevelPressureN/P/OLoad: SumInfo1Confidence',
             self.pres_confidence),
            ('LevelPressureN/P/OLoad: TrendsRecent', self.pres_trend_recent),
            ('LevelPressureN/P/OLoad: TrendsFuture', self.pres_trend_future),

            ('Activities: Description', self.activity_description),
            ('ActivityType', self.activity_type),
            ('InfoGaps', self.info_gaps),
        ]

        for title, handler in attrs:
            self[title] = self.handle_missing_assessment(handler)

    def info_gaps(self):
        v = self.report['w:Analysis/w:InfoGaps/text()']

        return v and v[0] or ''

    def activity_description(self):
        x = self.report['w:Analysis/w:Activities/w:Description/text()']

        return x and x[0] or ''

    def activity_type(self):
        nodes = self.report['w:Analysis/w:Activities/'
                            'w:Activity/w:ActivityType/text()']

        return ', '.join(nodes)

    def lpo_confidence(self):
        x = 'w:Analysis/w:LevelPressureOverall/w:SumInfo1Confidence/text()'
        v = self.report[x]

        if v:
            return v[0]

    def lpo_description(self):
        x = 'w:Analysis/w:LevelPressureOverall/w:Description/text()'
        v = self.report[x]

        if v:
            return v[0]

    def lpo_suminfo1(self):
        x = 'w:Analysis/w:LevelPressureOverall/w:SumInfo1/text()'
        v = self.report[x]

        if v:
            return v[0]

    def recent_time_start(self):
        v = self.report["w:Metadata[contains(./w:Topic/text(),"
                        "'AnalysisCharactTrend')]"]

        if v:
            v = Node(v[0], NSMAP)

            return '{} - {}'.format(v['w:AssessmentStartDate/text()'][0],
                                    v['w:AssessmentEndDate/text()'][0])

    def limitations(self):
        return self.related_assessment.Limitations

    def as_status(self):
        ia = self.indicator_assessment
        v = ia['ancestor::w:Assessment/c:Status/text()']

        return v and v[0] or ''

    def as_status_trend(self):
        ia = self.indicator_assessment
        v = ia['ancestor::w:Assessment/c:StatusTrend/text()']

        return v and v[0] or ''

    def as_status_confidence(self):
        ia = self.indicator_assessment
        v = ia['ancestor::w:Assessment/c:StatusConfidence/text()']

        return v and v[0] or ''

    def as_status_description(self):
        ia = self.indicator_assessment
        v = ia['ancestor::w:Assessment/c:StatusDescription/text()']

        return v and v[0] or ''

    @property
    def analysis_tag(self):
        # TODO: I don't think this is well implemented. It doesn't fit the
        # specification Excel file

        # the Analysis -> LevelPressureNLoad tag
        _type = self.analysis()

        nodes = self.report['.//w:' + _type]

        if nodes:
            return Node(nodes[0], NSMAP)

    def pres_confidence(self):
        tag = self.analysis_tag

        if tag:
            v = self.analysis_tag['w:SumInfo1Confidence/text()']

            return v and v[0] or ''

    def pres_trend_recent(self):
        tag = self.analysis_tag

        if tag:
            v = self.analysis_tag['w:TrendsRecent/text()']

            return v and v[0] or ''

    def pres_trend_future(self):
        tag = self.analysis_tag

        if tag:
            v = self.analysis_tag['w:TrendsFuture/text()']

            return v and v[0] or ''

    def pres_sum1(self):
        # search for the Analysis > X tag that correspunds to this analysis

        tag = self.analysis_tag

        if tag:
            return self.analysis_tag['w:SumInfo1/text()'][0]

    def pres_description(self):
        tag = self.analysis_tag

        if tag:
            return self.analysis_tag['w:Description/text()'][0]

    def pres_unit(self):
        tag = self.analysis_tag

        if tag:
            v = self.analysis_tag['w:SumInfo1Unit/text()']

            return v and v[0] or ''

    def suminfo1_tv(self):
        # {'Description': u'Latvijas liel\u0101ko upju .',
        #  'FutureTimeEnd': None,
        #  'FutureTimeStart': None,
        #  'Limitations': None,
        #  'MSFD8b_Nutrients_ID': 990,
        #  'MSFD8b_Nutrients_Import': 53,
        #  'MarineUnitID': u'BAL- LV- AA- 001',
        #  'RecentTimeEnd': None,
        #  'RecentTimeStart': None,
        #  'SumInfo1': u'Nov\u0113rt\u0113jums attiecas ',
        #  'SumInfo1Confidence': u'Moderate',
        #  'SumInfo1Unit': u'tonnas/gad\u0101',
        #  'Topic': u'LevelPressureNLoad',
        #  'TrendsFuture': u'Unknown_NotAssessed',
        #  'TrendsRecent': u'Unknown_NotAssessed',
        # return self.related_assessment.SumInfo0Unit

        tv = self.indicator_assessment['c:ThresholdValueUnit/text()']

        return tv and tv[0] or ''

    def handle_missing_assessment(self, handler):
        if handler.__name__ == '<lambda>':      # don't handle lambdas
            return handler()

        if self.indicator_assessment is None:
            return ''

        return handler()

    def threshold_value(self):
        return self.indicator_assessment['c:ThresholdValue/text()'][0]

    def topic(self):
        return self.indicator_assessment.topic

    def suminfo1(self):
        return self.related_assessment.SumInfo1

    def analysis(self):
        return self.related_assessment.Topic

    @property
    def related_assessment(self):
        """ Locate the imported assessment in the database

        :returns: SQLAlchemy object, like MSFD8bNutrient instance
        """
        # The problem is that there appears to be a missing link that connects
        # the indicator assessment to the real <Analysis> tag in the XML file
        # We use the database to bypass this problem
        dbitem = self.indicator_assessment.database_assessment()
        rep_type = self.report.report_type

        if rep_type.endswith('s'):      # quick hack, should get a mapping
            rep_type = rep_type[:-1]

        return getattr(dbitem, 'MSFD8b_{}'.format(rep_type))


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

    @property
    def report_type(self):
        node = self.node.xpath('../../..')[0]
        tag = node.tag.split('}')[1]

        return tag

    @property
    def marine_unit_id(self):
        return self['ancestor::*/w:MarineUnitID/text()'][0]

    @db.use_db_session('2012')
    def database_assessment(self):
        # TODO: this needs to avoid database caching
        name = 'MSFD8b{}Assesment'.format(self.report_type)
        mc = getattr(sql, name)
        count, res = db.get_all_records(
            mc,
            mc.Topic == self.topic,
            mc.MarineUnitID == self.marine_unit_id
        )

        if count > 1:
            raise ValueError("Multiple assessments")

        return res[0]


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
        return self.node.tag.split('}')[1]

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

    template = Template('pt/report-data-a8-new.pt')

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
