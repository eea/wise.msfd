from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.Five.browser import BrowserView
from wise.msfd import db, sql, sql2018

from .utils import row_to_dict


class Article910(BrowserView):
    Art9 = Template('pt/compliance-a9.pt')
    Art10 = Template('pt/compliance-a10.pt')

    def get_environment_data(self, muids):
        """ Get all data from a table
        :param muids: ['LV-001', 'LV-002', ...]
        :return: table result
        """
        mc = sql.MSFD10Target
        descr_nr = self.descriptor[1:]
        count, res = db.get_all_records(
            mc,
            and_(
                mc.Topic == 'EnvironmentalTarget',
                mc.ReportingFeature.like('%{}%'.format(descr_nr)),
                mc.MarineUnitID.in_(muids)
            )
        )

        if res:
            return res[0]

        return []

    @property
    def country_name(self):
        """ Get country name based on country code
        :return: 'Latvia'
        """
        count, obj = db.get_item_by_conditions(
            sql.MSFD11CommonLabel,
            'ID',
            sql.MSFD11CommonLabel.value == self.country,
            sql.MSFD11CommonLabel.group == 'list-countries',
        )

        return obj.Text

    @property
    def regions(self):
        """ Get all regions and subregions for a country
        :return: ['BAL', 'ANS']
        """
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country
        )

        res = [row_to_dict(t, r) for r in res]
        regions = set([x['RegionSubRegions'] for x in res])

        return regions

    @property
    def descriptors(self):
        """ Get all descriptor codes
        :return: ['D1', 'D2', ..., 'D10', 'D11']
        """
        m = sql.MSFDFeaturesOverview
        res = db.get_unique_from_mapper(
            m, 'RFCode',
            m.FeatureType == 'GES descriptor'
        )

        return res

    def get_ges_descriptor_label(self, ges):
        """ Get the label(text) for a descriptor
        :param ges: 'D5'
        :return: 'D5 Eutrophication'
        """
        count, obj = db.get_item_by_conditions(
            sql.MSFD11CommonLabel,
            'ID',
            sql.MSFD11CommonLabel.value == ges,
            sql.MSFD11CommonLabel.group == 'list-MonitoringProgramme',
        )

        if obj:
            return obj.Text

    def get_ges_criterions(self, descriptor):
        """ Get all criterions(indicators) and the descriptor
            for a descriptor
        :param descriptor: 'D5'
        :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
        """
        nr = descriptor[1:]
        m = sql.MSFDFeaturesOverview
        res = db.get_unique_from_mapper(
            m, 'RFCode',
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
        criterion_labels[self.descriptor] = self.desc_label

        return criterion_labels

    def get_indicator_descriptors(self, muids, available_indicators):
        """ Get data based on Marine Units and available indicators
        :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        :param available_indicators: ['5.2.2-indicator 5.2C',
            '5.2.1- indicator 5.2B']
        :return: table result
        """
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
        # TODO: optimize this with a single function
        # and a single query (w/ JOIN)
        self.descs = {}

        for d in self.descriptors:
            self.descs[d] = self.get_ges_descriptor_label(d)
        self.desc_label = self.descs.get(self.descriptor,
                                         'Descriptor Not Found')

        self.criterions = self.get_ges_criterions(self.descriptor)

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

        template = getattr(self, self.article, None)
        self.content = template and template() or ""

        return self.content
