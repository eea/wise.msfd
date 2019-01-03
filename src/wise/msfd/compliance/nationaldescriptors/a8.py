import logging
from collections import defaultdict

from lxml.etree import fromstring
from sqlalchemy.orm.relationships import RelationshipProperty

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql  # , sql2018
from wise.msfd.data import get_report_data
from wise.msfd.gescomponents import Criterion, get_criterion, get_descriptor
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.utils import Item, ItemLabel, ItemList, Node, Row

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


MAPPER_CLASSES = {
    # 'Ecosystem': sql.MSFD8aEcosystemStatusAssessment,
    # 'ExtractionSeaweedMaerlOther': sql.MSFD8bExtractionSeaweedMaerlOther
    # 'Functional': sql.MSFD8aFunctionalStatusAssessment,
    # 'Habitat': sql.MSFD8aHabitatStatusAssessment,
    # 'Other': sql.MSFD8aOtherStatusAssessment,
    # 'Species': sql.MSFD8aSpeciesStatus,

    'ExtractionofFishShellfish': sql.MSFD8bExtractionFishShellfish,
    'HazardousSubstances': sql.MSFD8bHazardousSubstance,
    'HydrologicalProcesses': sql.MSFD8bHydrologicalProcess,
    'Litter': sql.MSFD8bLitter,
    'MicrobialPathogens': sql.MSFD8bMicrobialPathogen,
    'NIS': sql.MSFD8bNI,
    'Noise': sql.MSFD8bNoise,
    'Nutrients': sql.MSFD8bNutrient,
    'PhysicalDamage': sql.MSFD8bPhysicalDamage,
    'PhysicalLoss': sql.MSFD8bPhysicalLos,
    'PollutantEvents': sql.MSFD8bPollutantEvent,
}

ASSESSMENT_MAPPER_CLASSES = {
    # 'Ecosystem': sql.MSFD8aEcosystemStatusAssessment,
    # 'Functional': sql.MSFD8aFunctionalStatusAssessment,
    # 'Habitat': sql.MSFD8aHabitatStatusAssessment,
    # 'Other': sql.MSFD8aOtherStatusAssessment,
    # 'Physical': sql.MSFD8aPhysicalStatusAssessment,
    # 'Species': sql.MSFD8aSpeciesStatusAssessment,

    'ExtractionSeaweedMaerlOther':
    sql.MSFD8bExtractionSeaweedMaerlOtherAssesment,
    'ExtractionofFishShellfish': sql.MSFD8bExtractionFishShellfishAssesment,
    'HazardousSubstances': sql.MSFD8bHazardousSubstancesAssesment,
    'HydrologicalProcesses': sql.MSFD8bHydrologicalProcessesAssesment,
    'Litter': sql.MSFD8bLitterAssesment,
    'MicrobialPathogens': sql.MSFD8bMicrobialPathogensAssesment,
    'NIS': sql.MSFD8bNISAssesment,
    'Noise': sql.MSFD8bNoiseAssesment,
    'Nutrients': sql.MSFD8bNutrientsAssesment,
    'PhysicalDamage': sql.MSFD8bPhysicalDamageAssesment,
    'PhysicalLoss': sql.MSFD8bPhysicalLossAssesment,
    'PollutantEvents': sql.MSFD8bPollutantEventsAssesment,
}

# map from XML Analysis/<X> node name to DB column topic string
ASSESSMENT_TOPIC_MAP = {
    "ImpactspressureWater": "ImpactPressureWaterColumn",
    "ImpactspressureSeabed": "ImpactPressureSeabedHabitats",
}


def tag_name(node):
    return node.tag.split('}')[1]

# TODO: this needs to take regions into account


def get_introspected_relationship(mc):
    """ Find out which of the attributes of mapper is a Relationship

    Note: this is very optimistic, may need adjustments
    """

    for name in dir(mc):
        if name.startswith('_'):
            continue

        v = getattr(mc, name)

        if not v:
            continue

        if isinstance(v.prop, RelationshipProperty):
            return v


def get_db_assessment(mc, db_record):
    """ For a given <ImpactPressureExploitedShellfish> matching db record,
    locate the matching <Assessment> record

    :returns: SQLAlchemy object, like MSFD8bNutrientAssessment instance
    """

    rel = get_introspected_relationship(mc)
    count, res = db.get_all_records(
        mc,
        rel == db_record,
        raw=True,
        order_by=mc.__mapper__.primary_key[0].desc()
    )

    if count >= 2:
        logger.warning("Multiple assessments for record? Investigate")

    if count > 0:
        return res[0]


def get_related_indicators(assessment):
    """ Return the related indicator based on introspected relationships
    """

    if assessment is None:
        return

    mc_name = assessment.__class__.__name__ + 'Indicator'
    mc = getattr(sql, mc_name)
    rel = get_introspected_relationship(mc)
    count, res = db.get_all_records(
        mc,
        rel == assessment,
        raw=True
    )

    return res


class Descriptor(Criterion):
    """ Override the default Criterion to offer a nicer title
    (doesn't duplicate code)
    """

    @property
    def title(self):
        return self._title


class A8aItem(Item):
    """ A column in the 2012 Art8 assessment.
    """

    def __init__(self, **kw):
        super(A8aItem, self).__init__([])

        for k, v in kw.items():
            setattr(self, k, v)

        # tn = tag_name(self.node)
        # self.column_type = ASSESSMENT_TOPIC_MAP.get(tn, tn)

        self.node = Node(self.node, NSMAP)

        sn = self.node['ancestor::w:Status'][0]
        asn = self.node['ancestor::w:AssessmentStatus'][0]
        rfn = sn.getparent()  # a node like FunctionalGroups

        self.reporting_feature = Node(rfn, NSMAP)
        self.assessment_status = Node(asn, NSMAP)

        attrs = [
            ('Topic', self.row_topic()),
            ('Reporting Feature', self.row_reporting_feature()),
            ('Indicator', self.row_indicator()),
            ('Threshold Value', self.row_threshold_value()),
            ('Threshold Unit', self.row_threshold_value_unit()),
            ('Threshold Proportion', self.row_threshold_value_proportion()),
            ('Baseline', self.row_baseline),
            ('Status', self.row_status),
            ('Status Description', self.row_status_description),
            ('Status Trend', self.row_status_trend),
            ('Status Confidence', self.row_status_confidence),
        ]

        for title, value in attrs:
            self[title] = value

    def row_topic(self):
        v = self.assessment_status['parent::*/w:Topic/text()'][0]

        return ItemLabel(v, COMMON_LABELS.get(v, v))

    def row_status(self):
        status = self.assessment_status['c:Status/text()']

        if status:
            return status[0]

    def row_status_description(self):
        status = self.assessment_status['c:StatusDescription/text()']

        if status:
            return status[0]

    def row_status_trend(self):
        status = self.assessment_status['c:StatusTrend/text()']

        if status:
            return status[0]

    def row_status_confidence(self):
        status = self.assessment_status['c:StatusConfidence/text()']

        if status:
            return status[0]

    def row_reporting_feature(self):
        return self.reporting_feature['w:ReportingFeature/text()'][0]

    def row_indicator(self):
        return self.node['c:Indicator/text()'][0]

    def row_threshold_value(self):
        tv = self.node['c:ThresholdValue/text()']

        if tv:
            return tv[0]

    def row_threshold_value_unit(self):
        tvu = self.node['c:ThresholdValueUnit/text()']

        if tvu:
            return tvu[0]

    def row_threshold_value_proportion(self):
        p = self.node['c:ThresholdProportion/text()']

        if p:
            return p[0]

    def row_baseline(self):
        b = self.node['c:Baseline/text()']

        if b:
            return b[0]


class A8bItem(Item):
    """ A column in the 2012 Art8 assessment.
    """

    def __init__(self, **kw):
        super(A8bItem, self).__init__([])

        for k, v in kw.items():
            setattr(self, k, v)

        tn = tag_name(self.node)

        self.node = Node(self.node, NSMAP)

        self.column_type = ASSESSMENT_TOPIC_MAP.get(tn, tn)
        label = self.value_to_label

        attrs = [
            ('Analysis [Feature]', self.column_type),
            ('Assessment Topic', self.row_assessment_topic()),
            ('[Element]', 'Row not implemented'),
            ('CriteriaType [GESComponent]', self.row_criteria_type),
            ('[Parameter]', 'Row not implemented'),
            ('ThresholdValue', self.row_threshold_value()),
            ('SumInfo1Unit/ThresholdValueUnit [ValueUnit]',
             self.row_threshold_value_unit()),
            ('[ProportionThresholdValue]', 'Row not implemented'),

            ('Status [CriteriaStatus]', self.row_assessment_status()),
            ('StatusTrend', self.row_assessment_status_trend()),
            ('StatusConfidence', self.row_assessment_status_confidence()),
            ('StatusDescription [DescriptionCriteria]',
             self.row_status_description()),
            ('Limitations [DescriptionElement]', self.db_record.Limitations),

            ('Description', self.db_record.Description),
            ('SumInfo1', self.db_record.SumInfo1),
            ('SumInfo1Unit', self.row_record_suminfo1_unit),
            ('SumInfo1Confidence', label(self.db_record.SumInfo1Confidence)),
            ('TrendsRecent', label(self.db_record.TrendsRecent)),
            ('TrendsFuture', label(self.db_record.TrendsFuture)),

            ('RecentTimeStart / RecentTimeEnd / '
             'AssessmentDateStart / AssessmentDateEnd [AssessmentPeriod]',
             'Row not implemented'),

            ('Activities: Description', self.row_activity_description()),
            ('ActivityType', self.row_activity_types()),
            ('InfoGaps', self.row_infogaps()),
            # ('Debug', self.debug()),
        ]

        for title, value in attrs:
            self[title] = value

    def value_to_label(self, value):
        if value in COMMON_LABELS:
            return ItemLabel(value, COMMON_LABELS[value])
        else:
            return value

    def row_record_suminfo1_unit(self):
        # PhysicalLos doesn't have SumInfo1Unit

        return getattr(self.db_record, 'SumInfo1Unit', None)

    def row_assessment_status_confidence(self):
        if self.assessment:
            return self.assessment.StatusConfidence

    def row_assessment_status(self):
        if self.assessment:
            return self.assessment.Status

    def row_assessment_status_trend(self):
        if self.assessment:
            return self.assessment.StatusTrend

    def row_status_description(self):
        if self.assessment:
            return self.assessment.StatusDescription

    def row_infogaps(self):
        text = self.node['parent::*/w:InfoGaps/text()']

        if text:
            return text[0]

    def row_activity_description(self):
        text = self.node['parent::*/w:Activities/w:Description/text()']

        if text:
            return text[0]

    def row_activity_types(self):
        x = 'parent::*/w:Activities/w:Activity/w:ActivityType/text()'

        v = set(self.node[x])
        labels = [ItemLabel(a, COMMON_LABELS.get(a, a)) for a in v]

        return ItemList(labels)

    def row_criteria_type(self):
        if self.indicator:
            ges_id = self.indicator.GESIndicators
            ges_other = ""

            if ges_id == 'GESOther':
                # TODO: is this valid for all indicators?
                ges_id = self.indicator.OtherIndicatorDescription
                ges_other = "GESOther: "

            criterion = get_criterion(ges_id)

            if criterion is None:
                logger.warning('Could not find ges: %s from indicator', ges_id)

                return ges_other + ges_id

            return ges_other + criterion.title

    def row_threshold_value(self):
        if self.indicator:
            return self.indicator.ThresholdValue

    def row_threshold_value_unit(self):
        if self.indicator:
            return self.indicator.ThresholdValueUnit

    def row_assessment_topic(self):
        if self.assessment:
            v = self.assessment.Topic

            return ItemLabel(v, COMMON_LABELS.get(v, v))

    def debug(self):
        import pdb
        pdb.set_trace()


def get_db_record(report_type, marine_unit_id, topic):
    """ Locate the corresponding dbrecord for this report
    """
    mc = MAPPER_CLASSES[report_type]
    muid = marine_unit_id

    count, res = db.get_all_records(
        mc,
        mc.MarineUnitID == muid,
        mc.Topic == topic,
        raw=True
    )

    if count != 1:
        import pdb
        pdb.set_trace()
    assert count == 1, "Matching record not found"

    return res[0]


class ReportTag8a(Node):
    """ Handle a <FunctionalGroupFeatures> or <HabitatFeatures> tag
    """

    def __init__(self, node, nsmap):
        super(ReportTag8a, self).__init__(node, nsmap)

        self.marine_unit_id = self['w:MarineUnitID/text()'][0]

    def matches_descriptor(self, descriptor):
        descriptor = get_descriptor(descriptor)
        self_crits = set(self.criterias)

        return bool(self_crits.intersection(descriptor.all_ids()))

    @property
    def criterias(self):
        res = self['.//w:AssessmentStatus/c:Criterias'
                   '/c:Criteria/c:CriteriaType/text()']

        return res

    @property
    def indicators(self):
        res = self['.//w:AssessmentStatus/c:Criterias'
                   '/c:Indicators/c:Indicator/text()']

        return res

    def columns(self, criterion):
        res = []

        for node in self['.//w:Status/w:AssessmentStatus/c:Indicators']:
            item = A8aItem(report=self, node=node)
            res.append(item)

        return res

    def __repr__(self):
        return "<ReportTag8a for {}>".format(tag_name(self.node))


class ReportTag8b(Node):
    """ Handle a (for ex) <PhysicalLoss> or <Nutrients> tag
    """

    def __init__(self, node, nsmap):
        super(ReportTag8b, self).__init__(node, nsmap)

        self.marine_unit_id = self['w:MarineUnitID/text()'][0]

    @property
    def criterias(self):
        return self['w:AssessmentPI/w:Assessment/c:Criterias/'
                    'c:Criteria/c:CriteriaType/text()']

    @property
    def indicators(self):
        return self['w:AssessmentPI/w:Assessment/c:Indicators/'
                    'c:Indicator/text()']

    def matches_descriptor(self, descriptor):
        descriptor = get_descriptor(descriptor)
        self_crits = set(self.indicators + self.criterias)

        return bool(self_crits.intersection(descriptor.all_ids()))

    @property
    def report_type(self):      # TODO: this needs check
        return tag_name(self.node)

    def columns(self, criterion):
        res = []

        blacklist = [       # TODO: decide how to handle these
            'InfoGaps',
            'Activities',
        ]

        for node in self['w:Analysis/*']:

            tn = tag_name(node)

            if tn in blacklist:
                continue
            topic = ASSESSMENT_TOPIC_MAP.get(tn, tn)

            db_record = get_db_record(
                self.report_type,
                self.marine_unit_id,
                topic
            )

            mc_assessment = ASSESSMENT_MAPPER_CLASSES[self.report_type]
            assessment = get_db_assessment(mc_assessment, db_record)

            assessment_indicators = get_related_indicators(assessment)

            # TODO: this is specific to 8b
            kw = dict(report=self,
                      node=node,            # the LevelPressureOLoad like node
                      db_record=db_record,  # the tag as recorded in db
                      assessment=assessment,  # its attached db assessment
                      indicator=None,         # its attached db indicator
                      )

            if not assessment_indicators:
                kwargs = kw.copy()
                res.append(A8bItem(**kwargs))
            else:
                for indicator in assessment_indicators:
                    kwargs = kw.copy()
                    kwargs['indicator'] = indicator

                    res.append(A8bItem(**kwargs))

        return res


def get_report_tags(root):
    """ Get a list of "main" tags in the report XML file
    """
    blacklist = [
        'ReportingInformation',
        'Country',
        'Region',
    ]

    res = set()

    for node in root.iterchildren():
        tn = tag_name(node)

        if tn in blacklist:
            continue
        res.add(tn)

    return res


class Article8(BaseArticle2012):
    """ Article 8 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a8.pt')

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

        # each of the following report tags can appear multiple times, once per
        # MarineUnitID. Each one can have multiple <AssessmentPI>,
        # for specific topics. An AssessmentPI can have multiple indicators

        report_map = defaultdict(list)
        root_tags = get_report_tags(root)

        ReportTag = None

        # basic algorthim

        if 'Nutrients' in root_tags:
            ReportTag = ReportTag8b

        elif 'FunctionalGroupFeatures' in root_tags:
            ReportTag = ReportTag8a

        if ReportTag is None:
            logger.warning("Unhandled report type?")
            self.rows = []

            return self.template()

        for name in root_tags:
            nodes = xp('//w:' + name)

            for node in nodes:
                rep = ReportTag(node, NSMAP)

                # import pdb; pdb.set_trace()
                # TODO for D7(maybe for other descriptors too)
                # find a way to match the node with the descriptor
                # because all reported criterias and indicators are GESOther

                if rep.matches_descriptor(self.descriptor):
                    report_map[rep.marine_unit_id].append(rep)

        descriptor = get_descriptor(self.descriptor)
        ges_crits = [descriptor] + descriptor.criterions

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

            if len(m_reps) > 1:
                logger.warning("Multiple report tags for this "
                               "marine unit id: %r", m_reps)

            rows = []

            for i, report in enumerate(m_reps):

                if i > 0:       # add a splitter row, to separate reports
                    rows.append(Row('', ''))

                cols = report.columns(ges_crits)

                for col in cols:
                    for name in col.keys():
                        values = []

                        for inner in cols:
                            values.append(inner[name])
                        row = Row(name, values)
                        rows.append(row)

                    break       # only need the "first" row, for headers

            report_data[muid] = rows

        self.rows = report_data

        return self.template()
