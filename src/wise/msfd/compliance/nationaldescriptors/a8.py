import logging
from collections import defaultdict

from lxml.etree import fromstring
from sqlalchemy.orm import aliased
from sqlalchemy.orm.relationships import RelationshipProperty

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql  # , sql2018
from .data import REPORT_DEFS
from wise.msfd.data import get_report_data
from wise.msfd.gescomponents import Criterion, get_criterion, get_descriptor
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import Item, ItemLabel, ItemList, Node, RawRow, Row

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
            ('Baseline', self.row_baseline()),
            ('Status', self.row_status()),
            ('Status Description', self.row_status_description()),
            ('Status Trend', self.row_status_trend()),
            ('Status Confidence', self.row_status_confidence()),
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
            ('GES component', self.row_criteria_type()),
            ('Feature', self.column_type),
            ('Assessment Topic', self.row_assessment_topic()),
            ('Element', self.row_element()),
            ('Element 2', self.row_element2()),
            ('ImpactType [Parameter]', 'Row not implemented'),
            ('ThresholdValue', self.row_threshold_value()),
            ('Value achieved', 'Row not implemented'),
            ('Threshold value/Value unit',
             self.row_threshold_value_unit()),
            ('Proportion threshold value', self.row_proportion_threshold()),
            ('Proportion value achieved', 'Row not implemented'
                                          '(same values as Input load)'),

            ('Status of criteria/indicator', self.row_assessment_status()),
            ('Status trend', self.row_assessment_status_trend()),
            ('Status confidence', self.row_assessment_status_confidence()),
            ('Description (status of criteria/indicator)',
             self.row_status_description()),
            ('Limitations', self.db_record.Limitations),
            ('Assessment period', self.assessment_period()),

            ('Description', self.db_record.Description),
            ('Input load', self.db_record.SumInfo1),
            ('Load unit', self.row_record_suminfo1_unit()),
            ('Confidence', label(self.db_record.SumInfo1Confidence)),
            ('Trends (recent)', label(self.db_record.TrendsRecent)),
            ('Trends (future)', label(self.db_record.TrendsFuture)),

            ('Description (activities)', self.row_activity_description()),
            ('Activity type', self.row_activity_types()),
            ('Information gaps', self.row_infogaps()),
            # ('Debug', self.debug()),
        ]

        for title, value in attrs:
            self[title] = value

    def assessment_period(self):
        xpath = "parent::*/preceding-sibling::w:Metadata" \
                "[w:Topic/text() = 'AnalysisCharactTrend']"
        meta = self.node[xpath]

        if not meta:
            return ''

        metadata_node = Node(meta[0], NSMAP)

        start = metadata_node['w:AssessmentStartDate/text()']
        end = metadata_node['w:AssessmentEndDate/text()']

        if start and end:
            res = '-'.join((start[0], end[0]))

            return res

    def row_proportion_threshold(self):
        if self.indicator:
            return self.indicator.ThresholdProportion

    def row_element(self):
        suminfo2 = self.node['w:SumInformation2/w:SumInfo2']

        if not suminfo2:
            return ''

        res = ', '.join([x.text for x in suminfo2])

        return res

    def row_element2(self):
        other = self.node['w:SumInformation2/w:Other/text()']

        if not other:
            return ''

        return other[0]

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
    help_text = """
    - we identify the filename for the original XML file, by looking at the
        MSFD10_Imports table. This is the same file that you can find in the
        report table header on this page.

    - we download this file from CDR and parse it.

    - we try to match the type of file to one of two implementation: Article8a
      and Article8b.

    - We extract all "main" tags from the file and filter those tags that have
      matching criterias to the current descriptor, by using theis table:

      https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv

      We use the <Indicator> tag plus the <CriteriaType> tag to determine which
      parent main tag is ok for current descriptor.

      For Article8b we lookup the imported assessment in the database MarineDB,
      to be able to provide the related indicators. For each such indicator
      which we generate a table column.
    """

    def setup_data(self):

        filename = self.context.get_report_filename()
        text = get_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        # TODO: should use declared set of marine unit ids
        xml_muids = sorted(set(xp('//w:MarineUnitID/text()')))

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]',
                [', '.join(set(xml_muids))]),
        ]

        # each of the following report tags can appear multiple times, once per
        # MarineUnitID. Each one can have multiple <AssessmentPI>,
        # for specific topics. An AssessmentPI can have multiple indicators

        report_map = defaultdict(list)
        root_tags = get_report_tags(root)

        ReportTag = None

        # basic algorthim to detect what type of report it is
        article = self.article

        if 'Nutrients' in root_tags:
            ReportTag = ReportTag8b
            article = 'Art8b'

        elif 'FunctionalGroupFeatures' in root_tags:
            ReportTag = ReportTag8a
            article = 'Art8a'

        if ReportTag is None:
            logger.warning("Unhandled report type?")
            self.rows = []

            return self.template()

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        for name in root_tags:
            nodes = xp('//w:' + name)

            for node in nodes:
                try:
                    rep = ReportTag(node, NSMAP)
                except:
                    import pdb
                    pdb.set_trace()

                # import pdb; pdb.set_trace()
                # TODO for D7(maybe for other descriptors too)
                # find a way to match the node with the descriptor
                # because all reported criterias and indicators are GESOther

                if rep.matches_descriptor(self.descriptor):
                    report_map[rep.marine_unit_id].append(rep)

        descriptor = get_descriptor(self.descriptor)
        ges_crits = [descriptor] + list(descriptor.criterions)

        # a bit confusing code, we have multiple sets of rows, grouped in
        # report_data under the marine unit id key.
        report_data = {}

        # TODO: use reported list of muids per country,from database

        for muid in xml_muids:
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

                # if i > 0:       # add a splitter row, to separate reports
                #     rows.append(Row('', ''))

                cols = report.columns(ges_crits)

                for col in cols:
                    for name in col.keys():
                        values = []

                        for inner in cols:
                            values.append(inner[name])
                        translated_values = [
                            self.context.translate_value(name, value=v)
                            for v in values
                        ]
                        row = RawRow(name, translated_values, values)
                        rows.append(row)

                    break       # only need the "first" row, for headers

            report_data[muid] = rows

        res = {}

        # filter the results to show only region's marine unit ids
        # TODO: this should use self.context.muids
        # count, muids_t = db.get_marine_unit_id_names(self.muids)
        # muid_labels = dict(muids_t)
        muids = {m.id: m for m in self.muids}

        for k, v in report_data.items():
            res[muids[k]] = v

        # self.muids = sorted(res.keys())
        self.rows = res

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


class A8AlternateItem(Item):
    """
    """

    def __init__(self, descriptor, *args):
        super(A8AlternateItem, self).__init__()

        self.descriptor = descriptor
        self._args = args

        for title, value in self.get_values():
            self[title] = value


class A8aGeneric(A8AlternateItem):
    """ Generic alternate implementation for Article 8a items
    """

    @property
    def pk(self):
        N = self.primary_mapper
        pk = N.__table__.primary_key.columns.values()[0]
        return pk.name

    @classmethod
    def items(cls, descriptor, muids):
        sess = db.session()

        N = cls.primary_mapper
        P = cls.pres_mapper
        A = cls.ast_mapper
        I = cls.indic_mapper
        C = cls.crit_mapper

        pk = N.__table__.primary_key.columns.values()[0]

        if P:
            # .filter(A.Topic == cls.ast_topic)
            a_q = sess.query(A).join(N).subquery()
            a_A = aliased(A, alias=a_q, adapt_on_names=True)

            # .filter(A.Topic.in_(cls.criteria_types))\
            c_q = sess.query(C).join(A).subquery()
            c_A = aliased(C, alias=c_q, adapt_on_names=True)

            # TODO how to filter by topics
            # .filter(N.Topic.in_(cls.ast_topic + cls.criteria_types))\
            q = sess.query(N, P, a_A, I, c_A)\
                .select_from(N) \
                .filter(N.Topic != 'InfoGaps')\
                .filter(N.MarineUnitID.in_(muids))\
                .outerjoin(a_A)\
                .outerjoin(I)\
                .outerjoin(c_A)\
                .outerjoin(P)\
                .order_by(N.ReportingFeature, pk)

            for item in q:
                yield cls(descriptor, *item)

        # A8aPhysical only has the primary mapper, needs different query
        else:
            q = sess.query(N)\
                .select_from(N)\
                .filter(N.Topic != 'InfoGaps')\
                .filter(N.MarineUnitID.in_(muids))\
                .order_by(N.Topic, pk)

            for item in q:
                yield cls(descriptor, *(item, None, None, None, None))

        print q.count()

    def _get_metadata(self, rec):
        t = self.metadata_table
        pk = getattr(rec, self.pk)
        fk = self._get_table_fk(t)

        _count, _res = db.get_all_records(
            t,
            fk == pk,
            t.c.Topic == 'Assessment',
        )

        if _res:
            return _res[0]

    def _get_table_fk(self, table):
        for col in table.c:
            for fk in col.foreign_keys:
                return fk

    def get_pressures(self, rec):
        if rec is None:
            return []
        res = set()

        for name in ['Pressure1', 'Pressure2', 'Pressure3']:
            v = getattr(rec, name)
            res.add(v)

        return list(sorted(res))

    def _filter_by_topics(self, topic_type, *args):
        topic, value = args
        topics = getattr(self, topic_type)
        if topic in topics:
            return value

        return None

    def get_conditional_value(self, method_name, default_val):
        topic = self._args[0].Topic
        get_method = getattr(self, method_name, None)
        if get_method:
            return get_method(topic, default_val)

        return default_val

    def get_values(self):
        rec, pres, ast, indic, crit = self._args
        self.MarineUnitID = rec.MarineUnitID
        meta = self._get_metadata(rec)

        return [
            ('MarineReportingUnit', rec.MarineUnitID),

            ('GEScomponent', self.get_conditional_value(
                'ges_comp', 'D1')
             ),
            ('Feature', self.get_conditional_value(
                'feature', getattr(rec, 'ReportingFeature', None))
             ),
            ('GESachieved', self.get_conditional_value(
                'ges_achiev', getattr(rec, 'Summary1', None))
             ),
            ('AssessmentPeriod', meta and meta.AssessmentDateStart
                or getattr(rec, 'RecentTimeStart', None)),
            ('AssessmentPeriod2', meta and meta.AssessmentDateEnd
                or getattr(rec, 'RecentTimeEnd', None)),
            ('MethodUsed', meta and meta.MethodUsed),
            ('MethodSources', meta and meta.Sources),

            ('RelatedPressures', ItemList(rows=self.get_pressures(pres))),
            # ('RelatedActivities', ItemList(rows=related_activities)),
            #
            ('Criteria', self.get_conditional_value(
                'criteria', getattr(crit, 'CriteriaType', None))
             ),
            # TODO? ????
            ('CriteriaStatus', self.get_conditional_value(
                'crit_status', getattr(ast, 'Status', None))
             ),
            ('DescriptionCriteria', self.get_conditional_value(
                'desc_crit', getattr(ast, 'StatusDescription', None))
             ),
            ('Element', self.get_conditional_value(
                'element', getattr(rec, 'ReportingFeature', None))
             ),
            ('ElementSource', self.get_conditional_value(
                'elem_source',
                getattr(rec, 'SourceClassificationListAuthority', None))
             ),
            ('DescriptionElement', self.get_conditional_value(
                'descr_elem', getattr(ast, 'StatusDescription', None))
             ),
            ('ElementStatus', self.get_conditional_value(
                'elem_status', getattr(ast, 'Status', None))
             ),
            ('Parameter', self.get_conditional_value('param', rec.Topic)),
            ('ThresholdQualitative', indic and indic.ThresholdValue),
            ('ValueUnit', indic and indic.ThresholdValueUnit),
            ('ProportionThresholdValue', indic and indic.ThresholdProportion),

            # ('ProportionValueAchieved', rec.SumInfo1),
            ('Trend', self.get_conditional_value(
                'trend', getattr(ast, 'TrendStatus', None))
             ),
            ('ParameterAchieved', 'N/A'),
            ('DescriptionParameter', self.get_conditional_value(
                'desc_param', None)
             ),
        ]


class A8aSpecies(A8aGeneric):
    primary_mapper = sql.MSFD8aSpecy
    pres_mapper = sql.MSFD8aSpeciesPressuresImpact
    ast_mapper = sql.MSFD8aSpeciesStatusAssessment
    indic_mapper = sql.MSFD8aSpeciesStatusIndicator
    crit_mapper = sql.MSFD8aSpeciesStatusCriterion

    metadata_table = sql.t_MSFD8a_SpeciesMetadata

    criteria_types = ['Distribution', 'Population', 'Condition']
    ast_topic = ['SpeciesOverall', ]     # Overall

    def feature(self, *args):
        return 'SppAll'

    def ges_achiev(self, *args):
        return 'N/A'

    def descr_elem(self, *args):
        return self._filter_by_topics('ast_topic', *args)

    def elem_status(self, *args):
        return self._filter_by_topics('ast_topic', *args)

    def criteria(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def crit_status(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def desc_crit(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def param(self, *args):
        return self._filter_by_topics('criteria_types', *args)


class A8aFunctional(A8aGeneric):
    primary_mapper = sql.MSFD8aFunctional
    pres_mapper = sql.MSFD8aFunctionalPressuresImpact
    ast_mapper = sql.MSFD8aFunctionalStatusAssessment
    indic_mapper = sql.MSFD8aFunctionalStatusIndicator
    crit_mapper = sql.MSFD8aFunctionalStatusCriterion

    metadata_table = sql.t_MSFD8a_FunctionalMetadata

    criteria_types = ['SpeciesComposition', 'Abundance']
    summary_topics = ['FuncGroupOverall']

    def element(self, *args):
        return 'N/A'

    def elem_source(self, *args):
        return None

    def elem_status(self, *args):
        return 'N/A'

    def ges_achiev(self, *args):
        return self._filter_by_topics('summary_topics', *args)

    def criteria(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def crit_status(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def desc_crit(self, *args):
        return self._filter_by_topics('criteria_types', *args)

    def param(self, *args):
        return self._filter_by_topics('criteria_types', *args)


class A8aHabitat(A8aGeneric):
    primary_mapper = sql.MSFD8aHabitat
    pres_mapper = sql.MSFD8aHabitatPressuresImpact
    ast_mapper = sql.MSFD8aHabitatStatusAssessment
    indic_mapper = sql.MSFD8aHabitatStatusIndicator
    crit_mapper = sql.MSFD8aHabitatStatusCriterion

    metadata_table = sql.t_MSFD8a_HabitatMetadata

    element_topics = ('HabitatOverall',)
    criteria_topics = ('Distribution', 'Extent', 'Condition')
    param_topics = ('Distribution', 'Extent', 'Condition')

    def ges_comp(self, *args):
        return 'D1/D6'

    def feature(self, *args):
        return 'HabAll'

    def descr_elem(self, *args):
        return self._args[0].Description

    def elem_status(self, *args):
        return self._filter_by_topics('element_topics', *args)

    def criteria(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def crit_status(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def desc_crit(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def param(self, *args):
        return self._filter_by_topics('param_topics', *args)


class A8aEcosystem(A8aGeneric):
    primary_mapper = sql.MSFD8aEcosystem
    pres_mapper = sql.MSFD8aEcosystemPressuresImpact
    ast_mapper = sql.MSFD8aEcosystemStatusAssessment
    indic_mapper = sql.MSFD8aEcosystemStatusIndicator
    crit_mapper = sql.MSFD8aEcosystemStatusCriterion

    metadata_table = sql.t_MSFD8a_EcosystemMetadata

    elem_status_topics = ('EcosystemOverall',)
    criteria_topics = ('Structure', 'Productivity', 'Proportion', 'Abundance')

    def ges_comp(self, *args):
        return 'D4'

    def feature(self, *args):
        return 'EcosystemFoodWeb'

    def ges_achiev(self, *args):
        return 'N/A'

    def elem_source(self, *args):
        return None

    def descr_elem(self, *args):
        return self._args[0].Description

    def elem_status(self, *args):
        return self._filter_by_topics('elem_status_topics', *args)

    def criteria(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def crit_status(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def desc_crit(self, *args):
        return self._filter_by_topics('criteria_topics', *args)

    def param(self, *args):
        return self._filter_by_topics('criteria_topics', *args)


class A8aPhysical(A8aGeneric):
    # this type only has primary table and metadata
    primary_mapper = sql.MSFD8aPhysical
    pres_mapper = None
    ast_mapper = None
    indic_mapper = None
    crit_mapper = None

    metadata_table = sql.t_MSFD8a_PhysicalMetadata

    def ges_comp(self, *args):
        return 'D4'

    def feature(self, *args):
        return 'PhyHydroCharacAll'

    def ges_achiev(self, *args):
        return 'N/A'

    def element(self, *args):
        return 'N/A'

    def elem_status(self, *args):
        return 'N/A'

    def criteria(self, *args):
        return 'No criteria associated'

    def crit_status(self, *args):
        return 'N/A'

    def trend(self, *args):
        return self._args[0].TrendsRecent

    def desc_param(self, *args):
        return self._args[0].Description


class A8bNutrient(A8AlternateItem):

    @classmethod
    def items(cls, descriptor, muids):
        sess = db.session()

        I = sql.MSFD8bNutrientsAssesmentIndicator
        A = sql.MSFD8bNutrientsAssesment
        AC = sql.MSFD8bNutrientsAssesmentCriterion
        N = sql.MSFD8bNutrient

        q = sess.query(N, A, I, AC)\
            .select_from(N)\
            .filter(N.MarineUnitID.in_(muids))\
            .outerjoin(A)\
            .outerjoin(I)\
            .outerjoin(AC)\
            .order_by(N.MSFD8b_Nutrients_ID)

        for tup in q:
            yield cls(descriptor, *tup)

    def get_values(self):

        rec, assessment, indic, crit = self._args
        self.MarineUnitID = rec.MarineUnitID

        t = sql.t_MSFD8b_NutrientsMetadata
        _count, _res = db.get_all_records(
            t,
            t.c.MSFD8b_Nutrients_ID == rec.MSFD8b_Nutrients_ID,
            t.c.Topic == 'Assessment',
        )
        meta = None
        if _res:
            meta = _res[0]

        sess = db.session()     # TODO: concurent ongoing sessions
        # will be a problem?

        A = sql.MSFD8bNutrientsActivity
        AD = sql.MSFD8bNutrientsActivityDescription
        res = sess\
            .query(A.Activity)\
            .join(AD)\
            .filter(AD.MSFD8b_Nutrients == rec.MSFD8b_Nutrients_ID)\
            .distinct()\
            .all()
        related_activities = res and res[0] or []

        return [
            ('MarineReportingUnit', rec.MarineUnitID),
            ('GEScomponent', 'D5'),
            ('Feature', 'PresEnvEutrophi'),

            ('AssessmentPeriod',
             meta and meta.AssessmentDateStart or rec.RecentTimeStart),
            ('AssessmentPeriod2',
             meta and meta.AssessmentDateEnd or rec.RecentTimeEnd),

            ('MethodUsed', meta and meta.MethodUsed),
            ('MethodSources', meta and meta.Sources),

            ('RelatedActivities', ItemList(rows=related_activities)),

            ('Criteria', crit and crit.CriteriaType),
            ('CriteriaStatus',
             crit and crit.MSFD8b_Nutrients_Assesment1.Status),
            ('DescriptionCriteria',
             crit and crit.MSFD8b_Nutrients_Assesment1.StatusDescription),
            ('Element', 'N/A'),
            ('ElementStatus', 'N/A'),
            ('Parameter', rec.Topic),

            ('ThresholdQualitative', indic and indic.ThresholdValue),
            ('ValueUnit', indic and indic.ThresholdValueUnit),
            ('ProportionThresholdValue', indic and indic.ThresholdProportion),

            ('ProportionValueAchieved', rec.SumInfo1),
            ('ParameterAchieved', 'N/A'),
            ('DescriptionParameter', rec.Description),
        ]


class Article8Alternate(BaseArticle2012):
    template = Template('pt/report-data-a8.pt')
    help_text = """ """

    implementations = {
        'D1': [
            A8aSpecies,
            A8aFunctional,
            A8aHabitat,
            A8aEcosystem,
            A8aPhysical
        ],
        'D1/D6': [],
        'D2': [],
        'D3': [],
        'D4': [],
        'D5': [
            A8bNutrient,
        ],
        'D6': [],
        'D7': [],
        'D8': [],
        'D9': [],
        'D10': [],
        'D11': [],
    }

    def setup_data(self):
        # descriptor = get_descriptor(self.descriptor)
        # ok_ges_ids = descriptor.all_ids()
        descriptor = self.descriptor

        if descriptor.startswith('D1.'):
            descriptor = 'D1'       # TODO: handle other cases

        self.rows = defaultdict(list)

        # {muid: {field_name: [values, ...], ...}
        res = defaultdict(lambda: defaultdict(list))
        muids = {m.id: m for m in self.muids}

        for Klass in self.implementations[descriptor]:

            by_muid = defaultdict(list)

            for item in Klass.items(self.descriptor, muids.keys()):
                by_muid[item.MarineUnitID].append(item)

            for muid, cols in by_muid.items():
                rows = []

                if not cols:
                    continue

                for name in cols[0].keys():
                    values = [c[name] for c in cols]
                    res[muid][name].extend(values)

        for muid, rows in res.items():
            for name, values in rows.items():
                row = Row(name, values)
                self.rows[muids[muid]].append(row)

    def __call__(self):
        self.setup_data()

        return self.template()
