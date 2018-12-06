import logging
from collections import defaultdict

from lxml.etree import fromstring
from sqlalchemy.orm.relationships import RelationshipProperty

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
# from wise.msfd.compliance import a8_utils
from wise.msfd.data import country_ges_components, get_report_data
from wise.msfd.gescomponents import Criterion, get_criterion, get_descriptor
from wise.msfd.utils import Item, Node, Row  # RelaxedNode,

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
    )

    assert count < 2, "Multiple assessments for record? Investigate"

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


class A8Item(Item):
    """ A column in the 2012 Art8 assessment.
    """

    def __init__(self, **kw):
        super(A8Item, self).__init__([])

        for k, v in kw.items():
            setattr(self, k, v)

        tn = tag_name(self.node)

        self.node = Node(self.node, NSMAP)

        self.column_type = ASSESSMENT_TOPIC_MAP.get(tn, tn)

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
            ('SumInfo1Confidence', self.db_record.SumInfo1Confidence),
            ('TrendsRecent', self.db_record.TrendsRecent),
            ('TrendsFuture', self.db_record.TrendsFuture),

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

        return ", ".join(set(self.node[x]))

    def row_criteria_type(self):
        if self.indicator:
            ges_id = self.indicator.GESIndicators

            if ges_id == 'GESOther':
                # TODO: is this valid for all indicators?
                ges_id = self.indicator.OtherIndicatorDescription

            criterion = get_criterion(ges_id)

            if criterion is None:
                logger.warning('Could not find ges: %s from indicator', ges_id)

            return criterion.title

    def row_threshold_value(self):
        if self.indicator:
            return self.indicator.ThresholdValue

    def row_threshold_value_unit(self):
        if self.indicator:
            return self.indicator.ThresholdValueUnit

    def row_assessment_topic(self):
        if self.assessment:
            return self.assessment.Topic

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
                res.append(A8Item(**kwargs))
            else:
                for indicator in assessment_indicators:
                    kwargs = kw.copy()
                    kwargs['indicator'] = indicator

                    res.append(A8Item(**kwargs))

        return res


def get_report_tags(root):
    wrapped = Node(root, NSMAP)
    tag_names = wrapped['w:ReportingInformation/w:ReportingFeature/text()']

    return [t for t in tag_names if ' ' not in t]


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
            mc.GESComponent == 'Descriptor',
            raw=True,
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

        # each of the following report tags can appear multiple times, once per
        # MarineUnitID. Each one can have multiple <AssessmentPI>,
        # for specific topics. An AssessmentPI can have multiple indicators

        report_map = defaultdict(list)

        for name in get_report_tags(root):
            nodes = xp('//w:' + name)

            for node in nodes:
                rep = ReportTag(node, NSMAP)

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
                import pdb; pdb.set_trace()

            assert len(m_reps) < 2, "Multiple reports for same MarineUnitID?"
            report = m_reps[0]

            cols = report.columns(ges_crits)

            rows = []

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
