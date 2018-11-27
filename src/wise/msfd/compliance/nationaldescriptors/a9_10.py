from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018, sql_extra
from wise.msfd.gescomponents import get_ges_criterions
from wise.msfd.utils import Row, TableHeader

from ..base import BaseArticle2012
from .utils import row_to_dict


class Article9(BaseArticle2012):
    """ Article 9 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a9.pt')

    def row_marine_unit_ids(self):
        muids = ', '.join(self.muids)

        return Row('Reporting area(s) [MarineUnitID]', [muids])

    def row_gescomponents(self):
        result = [(self.descriptor, self.descriptor_label)]

        for crit in self.criterias:
            for alt in crit.alternatives:
                title = '{} ({}) {}'.format(crit._id or '', alt[0], alt[1])
                indicator = alt[0]

                result.append((indicator, title))

        values = [x[1] for x in result]

        return Row('GES component [Reporting feature]', values)

    # def row_gesdescriptions(self):
    #     values = get_indicator_descriptors(self.muids,
    #                                        self.indicators_map.keys())
    #
    #     return Row('GES description [DescriptionGES]', values)

    def __call__(self):
        self.criterias = get_ges_criterions(self.descriptor)
        self.descriptor_label = dict(get_descriptors())[self.descriptor]

        # criterions = get_all_criterions(self.descriptor)

        # self.indicators_map = get_indicators_with_feature_pressures(
        #     self.muids, criterions
        # )

        self.rows = [
            self.row_marine_unit_ids(),
            self.row_gescomponents(),
            self.row_gescomponent_indicators(),
            # self.row_gesdescriptions(),
        ]

        return self.template()


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a10.pt')

    def get_gescomponents(self):
        return Row('[GEScomponent]', [x[1] for x in self.labeled_criterias])

    def get_marine_unit_ids(self):
        return Row('MarineUnitID', [', '.join(self.muids)])

    def get_indicator_descriptors(self):
        values = get_indicator_descriptors(self.muids,
                                           self.indicators_map.keys())

        return Row('GES description [DescriptionGES]', values)

    def __call__(self):

        self.labeled_criterias = self.context.get_criterias_list(
            self.descriptor
        )
        criterions = get_all_criterions(self.descriptor)

        self.indicators_map = get_indicators_with_feature_pressures(
            criterions
        )

        self.rows = [
            self.get_marine_unit_ids(),
            self.get_gescomponents(),
            self.get_indicator_descriptors(),
        ]

        return self.template()


@db.use_db_session('2012')
def get_criterion_labels(criterions, descriptor, descriptor_label):
    """ Get all labels for the criterions

    :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    :return: [('5.1', '5.1: Nutrients levels'),
              ('5.1.2', '5.1.2: Nutrient ratios (silica'),
              (...)]
    """

    count, res = db.get_all_records(
        sql.MSFD11CommonLabel,
        sql.MSFD11CommonLabel.value.in_(criterions),
        sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
                                         'list-GESCriteria')),
    )

    criterion_labels = dict([(x.value, x.Text) for x in res])
    # add D5 criterion to the criterion lists too
    criterion_labels[descriptor] = descriptor_label

    return criterion_labels


@db.use_db_session('2018')
def get_descriptors():
    """ Get a list of (code, description) descriptors
    """

    mc = sql2018.LGESComponent
    count, res = db.get_all_records(
        mc,
        mc.GESComponent == 'Descriptor'
    )
    descriptors = [(x.Code.split('/')[0], x.Description) for x in res]

    return descriptors


@db.use_db_session('2012')
def get_indicator_descriptors(muids, available_indicators):
    """ Get data based on Marine Units and available indicators

    :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
    :param available_indicators: ['5.2.2-indicator 5.2C',
                                  '5.2.1- indicator 5.2B']
    :return: table result
    """
    # TODO: sort the results based on ascending muid?
    count, res = db.get_all_records(
        sql.MSFD9Descriptor,
        sql.MSFD9Descriptor.MarineUnitID.in_(muids),
        sql.MSFD9Descriptor.ReportingFeature.in_(available_indicators)
    )

    return res


@db.use_db_session('2012')
def get_indicators_with_feature_pressures(muids, criterions):
    """ Get a dict with all indicators and their corresponding features

    :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
    :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    :return: {'5.2.2-indicator 5.2C': ['Transparency', 'InputN_Psubst'],
             {'5.2.1- indicator 5.2B': ['InputN_Psubst',
                                        'FunctionalGroupOther'],
              ...}
    """

    t = sql.t_MSFD9_Features
    count, res = db.get_all_records(
        t,
        t.c.MarineUnitID.in_(muids),
    )
    res = [row_to_dict(t, r) for r in res]

    indicators = defaultdict(set)

    for row in res:
        rf = row['ReportingFeature']
        indicators[rf].add(row['FeaturesPressuresImpacts'])

    res = {}

    for k, v in indicators.items():
        flag = False

        for crit in criterions:
            if k.startswith(crit):
                flag = True

        if flag:
            res[k] = v

    return res


@db.use_db_session('2012')
def get_all_criterions(descriptor):
    """ Get all criterions(indicators) + descriptor, for a descriptor

    :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    """
    nr = descriptor[1:]
    m = sql.MSFDFeaturesOverview
    res = db.get_unique_from_mapper(
        m,
        'RFCode',
        or_(
            and_(m.RFCode.like('{}.%'.format(nr)),
                 m.FeatureType == 'GES criterion',),
            and_(m.RFCode.like('{}'.format(descriptor)),
                 m.FeatureType == 'GES descriptor')
        ),
        m.FeatureRelevant == 'Y',
        m.FeatureReported == 'Y',
    )

    return res
