from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql_extra
from wise.msfd.utils import CompoundRow, Row, TableHeader

from ..base import BaseArticle2012
from .utils import row_to_dict


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a10.pt')

    def get_gescomponents(self):
        return Row('[GEScomponent]', [x[1] for x in self.criterias])

    def get_marine_unit_ids(self):
        return Row('MarineUnitID', [', '.join(self.muids)])

    def __call__(self):
        self.criterias = self.context.get_criterias_list(self.descriptor)
        self.rows = [
            self.get_marine_unit_ids(),
            self.get_gescomponents(),
        ]

        return self.template()


class Article910(BaseArticle2012):
    """
    """

    Art9 = Template('pt/report-data-a9.pt')
    Art10 = Template('pt/report-data-a10.pt')

    # Art 10 methods
    @property
    def get_environment_data(self):
        """ Get all data from a table
        :return: table result
        """
        mc = sql.MSFD10Target
        descr_nr = self.descriptor[1:]
        count, res = db.get_all_records(
            mc,
            and_(
                mc.Topic == 'EnvironmentalTarget',
                mc.ReportingFeature.like('%{}%'.format(descr_nr)),
                mc.MarineUnitID.in_(self.muids)
            )
        )

        if res:
            return res[0]

        return []

    # Art 9 methods
    @property
    def criterions(self):
        """ Get all criterions(indicators) and the descriptor
            for a descriptor
        :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
        """
        nr = self.descriptor[1:]
        m = sql.MSFDFeaturesOverview
        res = db.get_unique_from_mapper(
            m, 'RFCode',
            or_(
                and_(m.RFCode.like('{}.%'.format(nr)),
                     m.FeatureType == 'GES criterion',),
                and_(m.RFCode.like('{}'.format(self.descriptor)),
                     m.FeatureType == 'GES descriptor')
            ),
            m.FeatureRelevant == 'Y',
            m.FeatureReported == 'Y',
        )

        return res

    def get_indicators_with_feature_pressures(self, muids, criterions):
        """ Get a dict with all indicators and their corresponding features
        :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
        :return: {'5.2.2-indicator 5.2C': ['Transparency', 'InputN_Psubst'],
        {'5.2.1- indicator 5.2B': ['InputN_Psubst', 'FunctionalGroupOther'],
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

    def get_criterion_labels(self, criterions):
        """ Get all labels for the criterions
        :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
        :return: [('5.1', '5.1: Nutrients levels'),
            ('5.1.2', '5.1.2: Nutrient ratios (silica'), (...)]
        """
        count, res = db.get_all_records(
            sql.MSFD11CommonLabel,
            sql.MSFD11CommonLabel.value.in_(criterions),
            sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
                                             'list-GESCriteria')),
        )

        criterion_labels = dict([(x.value, x.Text) for x in res])
        # add D5 criterion to the criterion lists too
        criterion_labels[self.descriptor] = self.context.desc_label

        return criterion_labels

    def get_indicator_title(self, value):

        return value

    def get_marine_unit_id_title(self, muid):
        t = sql_extra.MSFD4GeographicalAreaID
        res = db.get_unique_from_mapper(
            t,
            'MarineUnits_ReportingAreas',
            t.MarineUnitID == muid,
        )

        assert len(res) == 1

        if res:
            title = u'{} - {}'.format(muid, res[0])
        else:
            title = muid

        return title

    def get_indicator_descriptors(self, muids, available_indicators):
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

    @property
    def crit_lab_indics(self):
        """ Get all criterions with their reported indicators
        :return: {'5.1': [],
            '5.1.1': ['5.1.1-indicator 5.1A', '5.1.1-indicator 5.1B']
            , ...}
        """
        crit_lab_indics = defaultdict(list)

        for crit_lab in self.criterion_labels.keys():
            crit_lab_indics[crit_lab] = []

            for ind in self.indic_w_p.keys():
                norm_ind = ind.split('-')[0]

                if crit_lab == norm_ind:
                    crit_lab_indics[crit_lab].append(ind)

            if not crit_lab_indics[crit_lab]:
                crit_lab_indics[crit_lab].append('')

        crit_lab_indics[u'GESOther'] = ['']

        return crit_lab_indics

    @property
    def colspan(self):
        colspan = len([item
                       for sublist in self.crit_lab_indics.values()

                       for item in sublist])

        return colspan

    def setup_data(self):
        # {u'5.2.2-indicator 5.2C': set([u'Transparency', u'InputN_Psubst']),
        self.indic_w_p = self.get_indicators_with_feature_pressures(
            self.muids, self.criterions
        )

        self.criterion_labels = self.get_criterion_labels(
            self.criterions
        )

        self.indicator_descriptors = self.get_indicator_descriptors(
            self.muids, self.indic_w_p.keys()
        )

    def __call__(self):
        self.setup_data()

        t_impl = getattr(self, self.article, None)

        self.content = t_impl and t_impl() or ""

        return self.content
