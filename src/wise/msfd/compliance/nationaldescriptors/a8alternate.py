import logging
from collections import OrderedDict, defaultdict

from sqlalchemy.orm import aliased

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql  # , sql2018
from wise.msfd.utils import Item, ItemList, Row

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


class OrderedDefaultDict(OrderedDict):
    factory = list

    def __missing__(self, key):
        self[key] = value = self.factory()

        return value


class A8AlternateItem(Item):
    """
    """

    def __init__(self, descriptor, *args):
        super(A8AlternateItem, self).__init__()

        self.descriptor = descriptor
        self._args = args

        for title, value in self.get_values():
            self[title] = value

    @staticmethod
    def _get_mapper_pk(mapper):
        pk = mapper.__table__.primary_key.columns.values()[0]

        return pk

    @staticmethod
    def _get_table_fk(table):
        for col in table.c:
            if col.foreign_keys:
                return col

    @staticmethod
    def _get_mapper_fk(mapper):
        for col in mapper.__table__.columns.values():
            if col.foreign_keys:
                return col


class A8aGeneric(A8AlternateItem):
    """ Generic alternate implementation for Article 8a items
    """

    @classmethod
    def items(cls, descriptor, muids):
        sess = db.session()

        N = cls.primary_mapper
        P = cls.pres_mapper
        A = cls.ast_mapper
        I = cls.indic_mapper
        C = cls.crit_mapper
        # M = cls.metadata_table

        pk = cls._get_mapper_pk(N)
        # fk = cls._get_table_fk(M)

        # m_q = sess.query(M) \
        #     .join(N, pk == fk) \
        #     .filter(M.c.Topic == 'Assessment',
        #             M.c.MarineUnitID.in_(muids))\
        #     .distinct()

        print 'Started to query data!'

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
                .filter(N.MarineUnitID.in_(muids)) \
                .outerjoin(a_A)\
                .outerjoin(I)\
                .outerjoin(c_A)\
                .outerjoin(P) \
                .distinct()\
                .order_by(N.ReportingFeature, pk)
            # asd = q.statement.compile(compile_kwargs={"literal_binds": True})

            print 'Started to setup data!'
            print q.count()

            for item in q:
                print 'Will yield one item!'
                yield cls(descriptor, *item)

        # A8aPhysical only has the primary mapper, needs different query
        else:
            q = sess.query(N)\
                .select_from(N)\
                .filter(N.Topic != 'InfoGaps')\
                .filter(N.MarineUnitID.in_(muids)) \
                .order_by(N.Topic, pk)

            print q.count()

            for item in q:
                yield cls(descriptor, *(item, None, None, None, None))

    def _get_metadata(self, rec):
        t = self.metadata_table
        pk = self._get_mapper_pk(rec)
        fk = self._get_table_fk(t)

        _count, _res = db.get_all_records(
            t,
            fk == pk,
            t.c.Topic == 'Assessment',
        )

        if _res:
            return _res[0]

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


class A8bGeneric(A8AlternateItem):

    @classmethod
    def items(cls, descriptor, muids):
        sess = db.session()

        N = cls.primary_mapper
        A = cls.asses_mapper
        AI = cls.asses_ind_mapper
        AC = cls.asses_crit_mapper

        pk = cls._get_mapper_pk(N)

        print 'Started to query data!'

        filters = []
        filters.append(N.MarineUnitID.in_(muids))
        # TODO should we filter by cls.param_topics?
        filters.append(N.Topic != 'InfoGaps')

        # TODO should we filter by crit_topics?
        crit_topics = getattr(cls, 'crit_topics', None)

        if crit_topics:
            filters.append(A.Topic.in_(crit_topics))

        # Acidification does not have '_Assessment' tables

        if A:
            q = sess.query(N, A, AI, AC)\
                .select_from(N)\
                .filter(*filters)\
                .outerjoin(A)\
                .outerjoin(AI)\
                .outerjoin(AC)\
                .order_by(pk)

            print 'Started to setup data!'
            print q.count()

            for tup in q:
                print 'Will yield one item!'
                yield cls(descriptor, *tup)

        # special case for Acidification
        else:
            q = sess.query(N) \
                .select_from(N) \
                .filter(*filters) \
                .order_by(pk)

            print 'Started to setup data!'
            print q.count()

            for tup in q:
                print 'Will yield one item!'
                yield cls(descriptor, *(tup, None, None, None))

    def _topic_filter(self, topic, value, topics):
        if not value:
            return None

        if topic in topics:
            return value

        return None

    def _param_topic(self, rec):
        topic = rec.Topic
        topics = getattr(self, 'param_topics', None)

        return self._topic_filter(topic, topic, topics)

    def _metadata(self, rec):
        # return None

        t = self.metadata_table
        pk = self._get_mapper_pk(rec)
        fk = self._get_table_fk(t)

        _count, _res = db.get_all_records(
            t,
            fk == pk,
            t.c.Topic == 'Assessment',
        )
        meta = None

        if _res:
            meta = _res[0]

        return meta

    def _related_activities(self, rec):
        # return []

        sess = db.session()  # TODO: concurent ongoing sessions
        # will be a problem?

        A = self.activity_mapper
        AD = self.act_descr_mapper

        fk = self._get_mapper_fk(AD)
        pk = self._get_mapper_pk(rec)

        res = sess.query(A.Activity) \
            .join(AD) \
            .filter(fk == pk) \
            .distinct() \
            .all()
        related_activities = res and res[0] or []

        return related_activities

    def get_values(self):
        rec, asses, indic, crit = self._args
        self.MarineUnitID = rec.MarineUnitID

        meta = self._metadata(rec)
        related_activities = self._related_activities(rec)

        return [
            ('MarineReportingUnit', rec.MarineUnitID),
            ('GEScomponent', getattr(self, 'ges_comp', 'D5')),
            ('Feature', getattr(self, 'feature', 'N/A')),

            ('GESAchieved', getattr(self, 'ges_achiev', 'N/A')),
            ('AssessmentPeriod',
             meta and meta.AssessmentDateStart or rec.RecentTimeStart),
            ('AssessmentPeriod2',
             meta and meta.AssessmentDateEnd or rec.RecentTimeEnd),

            ('MethodUsed', meta and meta.MethodUsed),
            ('MethodSources', meta and meta.Sources),

            ('RelatedActivities', ItemList(rows=related_activities)),
            ('Criteria',
                getattr(self, 'criteria', crit and crit.CriteriaType)),
            ('CriteriaStatus',
                getattr(self, 'crit_stat', asses and asses.Status)),
            ('DescriptionCriteria',
                getattr(self, 'desc_crit', asses and asses.StatusDescription)),
            ('Element', getattr(self, 'element', 'N/A')),
            ('ElementStatus', getattr(self, 'elem_status', 'N/A')),
            ('Parameter', getattr(self, 'parameter', self._param_topic(rec))),

            ('ThresholdQualitative', indic and indic.ThresholdValue),
            ('ValueUnit', indic and indic.ThresholdValueUnit),
            ('ProportionThresholdValue', indic and indic.ThresholdProportion),
            ('ProportionValueAchieved', rec.SumInfo1),
            ('Trend', getattr(self, 'trend', asses and asses.StatusTrend)),
            ('ParameterAchieved', 'N/A'),
            ('DescriptionParameter', rec.Description),
        ]


class A8bAcidification(A8bGeneric):
    primary_mapper = sql.MSFD8bAcidification
    asses_mapper = None
    asses_ind_mapper = None
    asses_crit_mapper = None
    metadata_table = sql.t_MSFD8b_AcidificationMetadata

    activity_mapper = sql.MSFD8bAcidificationActivity
    act_descr_mapper = sql.MSFD8bAcidificationActivityDescription

    @property
    def ges_comp(self):
        return 'D4'

    @property
    def feature(self):
        return 'Acidification'

    @property
    def criteria(self):
        return 'No criteria associated'

    @property
    def crit_stat(self):
        return 'N/A'

    @property
    def desc_crit(self):
        return None

    @property
    def trend(self):
        rec = self._args[0]
        value = getattr(rec, 'TrendsRecent', None)

        return value


class A8bNIS(A8bGeneric):
    primary_mapper = sql.MSFD8bNI
    asses_mapper = sql.MSFD8bNISAssesment
    asses_ind_mapper = sql.MSFD8bNISAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bNISAssesmentCriterion
    metadata_table = sql.t_MSFD8b_NISMetadata

    activity_mapper = sql.MSFD8bNISActivity
    act_descr_mapper = sql.MSFD8bNISActivityDescription
    param_topics = ['LevelPressureEnvironment', 'ImpactPressureSeabedHabitats',
                    'ImpactPressureWaterColumn',
                    'ImpactPressureFunctionalGroup']

    @property
    def ges_comp(self):
        return 'D2'

    @property
    def feature(self):
        return 'PresBioIntroNIS'

    @property
    def element(self):
        m = sql.MSFD8aNISInventory
        _count, _res = db.get_all_records(
            m.ScientificName,
            m.MarineUnitID == self.MarineUnitID,
        )

        if _count:
            elements = ', '.join([x[0] for x in _res])

            return elements

        return None


class A8bExtractionFishShellfish(A8bGeneric):
    primary_mapper = sql.MSFD8bExtractionFishShellfish
    asses_mapper = sql.MSFD8bExtractionFishShellfishAssesment
    asses_ind_mapper = sql.MSFD8bExtractionFishShellfishAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bExtractionFishShellfishAssesmentCriterion
    metadata_table = sql.t_MSFD8b_ExtractionFishShellfishMetadata
    activity_mapper = sql.MSFD8bExtractionFishShellfishActivity
    act_descr_mapper = sql.MSFD8bExtractionFishShellfishActivityDescription

    crit_topics = ['Extraction3_1', 'ExtractionCommerciallyExpFish3_2or3_3',
                   'ExtractionCommerciallyExpShellfish3_2or3_3']

    param_topics = []

    @property
    def ges_comp(self):
        return 'D3'

    @property
    def feature(self):
        return 'FishCommercial'

    @property
    def element(self):
        return 'All commercial stocks'

    @property
    def parameter(self):
        indic = self._args[2]
        value = getattr(indic, 'GESIndicators', None)

        return value

    @property
    def desc_crit(self):
        return None

    @property
    def criteria(self):
        crit = self._args[3]
        value = getattr(crit, 'CriteriaType')
        topic = crit.Topic

        return self._topic_filter(value, topic, self.crit_topics)

    @property
    def crit_stat(self):
        asses = self._args[1]
        value = getattr(asses, 'Status')
        topic = asses.Topic

        return self._topic_filter(value, topic, self.crit_topics)


class A8bExtractionSeaweedMaerlOther(A8bGeneric):
    primary_mapper = sql.MSFD8bExtractionSeaweedMaerlOther
    asses_mapper = sql.MSFD8bExtractionSeaweedMaerlOtherAssesment
    asses_ind_mapper = sql.MSFD8bExtractionSeaweedMaerlOtherAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bExtractionSeaweedMaerlOtherAssesmentCriterion
    metadata_table = sql.t_MSFD8b_ExtractionSeaweedMaerlOtherMetadata
    activity_mapper = sql.MSFD8bExtractionSeaweedMaerlOtherActivity
    act_descr_mapper = sql.MSFD8bExtractionSeaweedMaerlOtherActivityDescription

    param_topics = ['LevelPressureOther', 'ImpactPressureExploitedSpecies',
                    'ImpactPressureFunctionalGroup',
                    'ImpactPressureSeabedHabitats']

    @property
    def ges_comp(self):
        return 'D3'

    @property
    def feature(self):
        return 'SeaweedMaerlOther'

    @property
    def element(self):
        return 'N/A'

    @property
    def desc_crit(self):
        return None


class A8bNutrient(A8bGeneric):
    primary_mapper = sql.MSFD8bNutrient
    asses_mapper = sql.MSFD8bNutrientsAssesment
    asses_ind_mapper = sql.MSFD8bNutrientsAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bNutrientsAssesmentCriterion
    metadata_table = sql.t_MSFD8b_NutrientsMetadata

    activity_mapper = sql.MSFD8bNutrientsActivity
    act_descr_mapper = sql.MSFD8bNutrientsActivityDescription
    param_topics = [
        'LevelPressureNConcentration', 'LevelPressureNLoad',
        'LevelPressureOConcentration', 'LevelPressureOLoad',
        'LevelPressurePConcentration', 'LevelPressurePLoad',
        'ImpactPressureSeabedHabitats', 'ImpactPressureWaterColumn'
    ]

    @property
    def ges_comp(self):
        return 'D5'

    @property
    def feature(self):
        return 'PresEnvEutrophi'


class A8bPhysicalDamage(A8bGeneric):
    primary_mapper = sql.MSFD8bPhysicalDamage
    asses_mapper = sql.MSFD8bPhysicalDamageAssesment
    asses_ind_mapper = sql.MSFD8bPhysicalDamageAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bPhysicalDamageAssesmentCriterion
    metadata_table = sql.t_MSFD8b_PhysicalDamageMetadata
    activity_mapper = sql.MSFD8bPhysicalDamageActivity
    act_descr_mapper = sql.MSFD8bPhysicalDamageActivityDescription

    param_topics = ['LevelPressure', 'ImpactsPressureSeabedHabitats']

    @property
    def ges_comp(self):
        return 'D6'

    @property
    def feature(self):
        return 'PresPhyDisturbSeabed'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class A8bPhysicalLoss(A8bGeneric):
    primary_mapper = sql.MSFD8bPhysicalLos
    asses_mapper = sql.MSFD8bPhysicalLossAssesment
    asses_ind_mapper = sql.MSFD8bPhysicalLossAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bPhysicalLossAssesmentCriterion
    metadata_table = sql.t_MSFD8b_PhysicalLossMetadata
    activity_mapper = sql.MSFD8bPhysicalLossActivity
    act_descr_mapper = sql.MSFD8bPhysicalLossActivityDescription

    param_topics = ['LevelPressure', 'ImpactsPressureSeabedHabitats']

    @property
    def ges_comp(self):
        return 'D6'

    @property
    def feature(self):
        return 'PresPhyLoss'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class A8bHydrologicalProcessess(A8bGeneric):
    primary_mapper = sql.MSFD8bHydrologicalProcess
    asses_mapper = sql.MSFD8bHydrologicalProcessesAssesment
    asses_ind_mapper = sql.MSFD8bHydrologicalProcessesAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bHydrologicalProcessesAssesmentCriterion
    metadata_table = sql.t_MSFD8b_HydrologicalProcessesMetadata
    activity_mapper = sql.MSFD8bHydrologicalProcessesActivity
    act_descr_mapper = sql.MSFD8bHydrologicalProcessesActivityDescription

    param_topics = [
        'LevelPressure', 'ImpactPressureSeabedHabitats',
        'ImpactPressureWaterColumn', 'ImpactPressureFunctionalGroup'
    ]

    @property
    def ges_comp(self):
        return 'D7'

    @property
    def feature(self):
        return 'PresEnvHydroChanges'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class A8bPollutantEvents(A8bGeneric):
    primary_mapper = sql.MSFD8bPollutantEvent
    asses_mapper = sql.MSFD8bPollutantEventsAssesment
    asses_ind_mapper = sql.MSFD8bPollutantEventsAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bPollutantEventsAssesmentCriterion
    metadata_table = sql.t_MSFD8b_PollutantEventsMetadata
    activity_mapper = sql.MSFD8bPollutantEventsActivity
    act_descr_mapper = sql.MSFD8bPollutantEventsActivityDescription

    crit_topics = [
        'PollutionEvents8_2_2', 'PollutionEventsFunctionalGroups8_2_2',
        'PollutionEventsSeabedHabitats8_2_2'
    ]
    param_topics = [
        'LevelPressure', 'LevelPressureContaminant',
        'ImpactPressureSeabedHabitats', 'ImpactFunctionalGroup'
    ]

    @property
    def ges_comp(self):
        return 'D8'

    @property
    def feature(self):
        return 'PresEnvAcuPolluEvents'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'

    @property
    def criteria(self):
        crit = self._args[3]
        value = getattr(crit, 'CriteriaType')
        topic = crit.Topic

        return self._topic_filter(value, topic, self.crit_topics)

    @property
    def crit_stat(self):
        asses = self._args[1]
        value = getattr(asses, 'Status')
        topic = asses.Topic

        return self._topic_filter(value, topic, self.crit_topics)

    @property
    def desc_crit(self):
        asses = self._args[1]
        value = getattr(asses, 'StatusDescription')
        topic = asses.Topic

        return self._topic_filter(value, topic, self.crit_topics)


class A8bHazardousSubstances(A8bGeneric):
    primary_mapper = sql.MSFD8bHazardousSubstance
    asses_mapper = sql.MSFD8bHazardousSubstancesAssesment
    asses_ind_mapper = sql.MSFD8bHazardousSubstancesAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bHazardousSubstancesAssesmentCriterion
    metadata_table = sql.t_MSFD8b_HazardousSubstancesMetadata
    activity_mapper = sql.MSFD8bHazardousSubstancesActivity
    act_descr_mapper = sql.MSFD8bHazardousSubstancesActivityDescription

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'

    @property
    def criteria(self):
        crit = self._args[3]
        value = getattr(crit, 'CriteriaType')
        topic = crit.Topic

        return self._topic_filter(value, topic, self.crit_topics)

    @property
    def crit_stat(self):
        asses = self._args[1]
        value = getattr(asses, 'Status')
        topic = asses.Topic

        return self._topic_filter(value, topic, self.crit_topics)

    @property
    def desc_crit(self):
        asses = self._args[1]
        value = getattr(asses, 'StatusDescription')
        topic = asses.Topic

        return self._topic_filter(value, topic, self.crit_topics)


class A8bHazardousSubstancesD8(A8bHazardousSubstances):
    crit_topics = [
        'HazardousSubstances8_1', 'HazardousSubstancesFunctionalGroups8_1',
        'HazardousSubstancesFunctionalGroups8_2',
        'HazardousSubstancesSeabedHabitats8_2'
    ]
    param_topics = [
        'LevelPressureEnvironment', 'LevelPressureAir',
        'LevelPressureFunctionalGroups', 'LevelPressureLand',
        'LevelPressureSea', 'ImpactPressureSeabedHabitats',
        'ImpactFunctionalGroup'
    ]

    @property
    def ges_comp(self):
        return 'D8'

    @property
    def feature(self):
        return 'PresInputCont'


class A8bHazardousSubstancesD9(A8bHazardousSubstances):
    crit_topics = ['HazardousSubstancesFishSeafood9_1']
    param_topics = ['ImpactlPressureFishSeafood']

    @property
    def ges_comp(self):
        return 'D9'

    @property
    def feature(self):
        return 'PresEnvContSeafood'


class A8bMicrobialPathogens(A8bGeneric):
    primary_mapper = sql.MSFD8bMicrobialPathogen
    asses_mapper = sql.MSFD8bMicrobialPathogensAssesment
    asses_ind_mapper = sql.MSFD8bMicrobialPathogensAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bMicrobialPathogensAssesmentCriterion
    metadata_table = sql.t_MSFD8b_MicrobialPathogensMetadata
    activity_mapper = sql.MSFD8bMicrobialPathogensActivity
    act_descr_mapper = sql.MSFD8bMicrobialPathogensActivityDescription

    param_topics = [
        'LevelPressureBathingHigher', 'LevelPressureBathingLower',
        'LevelPressureOther', 'LevelPressureShellfishHigher',
        'LevelPressureShellfishLower', 'ImpactPressureShellfish'
    ]

    @property
    def ges_comp(self):
        return 'D9'

    @property
    def feature(self):
        return 'PresBioIntroMicroPath'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class A8bLitter(A8bGeneric):
    primary_mapper = sql.MSFD8bLitter
    asses_mapper = sql.MSFD8bLitterAssesment
    asses_ind_mapper = sql.MSFD8bLitterAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bLitterAssesmentCriterion
    metadata_table = sql.t_MSFD8b_LitterMetadata
    activity_mapper = sql.MSFD8bLitterActivity
    act_descr_mapper = sql.MSFD8bLitterActivityDescription

    param_topics = [
        'LevelPressureSeabed', 'LevelPressureShore', 'LevelPressureWater',
        'ImpactPressureSeabedHabitats', 'ImpactFunctionalGroup',
        'ImpactPressureWaterColumn'
    ]

    @property
    def ges_comp(self):
        return 'D10'

    @property
    def feature(self):
        return 'PresInputLitter'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class A8bNoise(A8bGeneric):
    primary_mapper = sql.MSFD8bNoise
    asses_mapper = sql.MSFD8bNoiseAssesment
    asses_ind_mapper = sql.MSFD8bNoiseAssesmentIndicator
    asses_crit_mapper = sql.MSFD8bNoiseAssesmentCriterion
    metadata_table = sql.t_MSFD8b_NoiseMetadata
    activity_mapper = sql.MSFD8bNoiseActivity
    act_descr_mapper = sql.MSFD8bNoiseActivityDescription

    param_topics = [
        'LevelPressureImpulsive', 'LevelPressureContinuous',
        'ImpactPressureFunctionalGroups'
    ]

    @property
    def ges_comp(self):
        return 'D11'

    @property
    def feature(self):
        return 'PresInputSound'

    @property
    def element(self):
        return 'N/A'

    @property
    def elem_status(self):
        return 'N/A'


class Article8Alternate(BaseArticle2012):
    template = Template('pt/report-data-a8.pt')
    help_text = """ """

    implementations = {
        'D1': [
            A8aSpecies,
            A8aFunctional,
        ],
        'D1/D6': [
            A8aHabitat
        ],
        'D2': [
            A8bNIS,
        ],
        'D3': [
            A8bExtractionFishShellfish,
            A8bExtractionSeaweedMaerlOther,
        ],
        'D4': [
            A8aEcosystem,
            A8aPhysical,
            A8bAcidification,
        ],
        'D5': [
            A8bNutrient,
        ],
        'D6': [
            A8bPhysicalDamage
        ],
        'D7': [
            A8bHydrologicalProcessess
        ],
        'D8': [
            A8bPollutantEvents,
            A8bHazardousSubstancesD8
        ],
        'D9': [
            A8bHazardousSubstancesD9,
            A8bMicrobialPathogens
        ],
        'D10': [
            A8bLitter
        ],
        'D11': [
            A8bNoise
        ],
    }

    def setup_data(self):
        # descriptor = get_descriptor(self.descriptor)
        # ok_ges_ids = descriptor.all_ids()
        descriptor = self.descriptor

        if descriptor.startswith('D1.'):
            descriptor = 'D1'       # TODO: handle other cases

        self.rows = defaultdict(list)

        # {muid: {field_name: [values, ...], ...}
        res = defaultdict(lambda: OrderedDefaultDict())
        muids = {m.id: m for m in self.muids}

        for Klass in self.implementations[descriptor]:
            print 'Started Klass: %s' % (Klass.__name__)

            # Klass = self.implementations[descriptor][0]

            # count, res = db.get_all_records(
            #     Impl.mapper,
            #     Impl.mapper.MarineUnitID.in_(self.muids)
            # )

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
