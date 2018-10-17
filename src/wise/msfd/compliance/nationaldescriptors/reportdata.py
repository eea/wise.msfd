from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil

from ..base import BaseComplianceView
from .a8 import Article8
from .a10 import Article10
from .utils import row_to_dict


class ReportData2012(BaseComplianceView, Article8, Article10, BaseUtil):

    """ WIP on compliance tables
    """

    name = 'nat-desc-start'

    # art3 = ViewPageTemplateFile('../pt/compliance-a10.pt')
    Art8 = Template('pt/compliance-a8.pt')
    Art9 = Template('pt/compliance-a9.pt')
    Art10 = Template('pt/compliance-a10.pt')

    # def __init__(self, context, request):
    #     super(Report2012, self).__init__(context, request)

    def get_country_name(self):
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

    def get_regions(self):
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

    def get_ges_descriptors(self):
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

    def get_marine_unit_ids(self):
        """ Get all Marine Units for a country
        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country
        )

        res = [row_to_dict(t, r) for r in res]
        muids = set([x['MarineUnitID'] for x in res])

        return sorted(muids)

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

    def get_criterions_indics(self):
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

    def get_colspan(self):
        colspan = len([item
                       for sublist in self.crit_lab_indics.values()
                       for item in sublist])

        return colspan

    def setup_data(self):
        self.country_name = self.get_country_name()
        self.regions = self.get_regions()

        # TODO: optimize this with a single function
        # and a single query (w/ JOIN)
        self.descriptors = self.get_ges_descriptors()
        self.descs = {}

        for d in self.descriptors:
            self.descs[d] = self.get_ges_descriptor_label(d)
        self.desc_label = self.descs.get(self.descriptor,
                                         'Descriptor Not Found')

        self.muids = self.get_marine_unit_ids()

        self.criterions = self.get_ges_criterions(self.descriptor)

        # {u'5.2.2-indicator 5.2C': set([u'Transparency', u'InputN_Psubst']),
        self.indic_w_p = self.get_indicators_with_feature_pressures(
            self.muids, self.criterions
        )

        self.criterion_labels = self.get_criterion_labels(self.criterions)

        self.indicator_descriptors = self.get_indicator_descriptors(
            self.muids, self.indic_w_p.keys()
        )

        self.crit_lab_indics = self.get_criterions_indics()

        self.colspan = self.get_colspan()

    @db.use_db_session('session')
    def __call__(self):
        self.country = self.country_code

        if not self.country:
            return ''

        self.setup_data()

        print "Will render report for ", self.article

        template = getattr(self, self.article, None)
        self.content = template and template() or ""

        return self.index()


class ReportData2018(BaseComplianceView):
    """ TODO: get code in this
    """
    name = 'nat-desc-start'

    Art8 = Template('pt/nat-desc-report-data-multiple-muid.pt')
    Art9 = ''
    Art10 = ''

    view_names = {
        'Art8': 't_V_ART8_GES_2018',
        # TODO: do the other: 9, 10
    }

    def get_data_from_view(self):

        view_name = self.view_names[self.article]
        t = getattr(sql2018, view_name)

        count, res = db.get_all_records(
            t,
            t.c.CountryCode == self.country_code,
            t.c.GESComponent == self.descriptor,
            # t.c.MarineReportingUnit.in_(marine_unit_ids),
            # t.c.Feature.in_(feature),
        )

        return res

    def change_orientation(self, data):
        """ From a set of results, create labeled list of rows
        """
        res = []
        row0 = data[0]

        for name in row0._fields:
            values = [getattr(row, name) for row in data]
            res.append([name, values])

        return res

    @db.use_db_session('session_2018')
    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        data = self.get_data_from_view()

        g = defaultdict(list)

        for row in data:
            g[row.MarineReportingUnit].append(row)

        res = [(k, self.change_orientation(v)) for k, v in g.items()]
        # data = self.change_orientation(data)

        self.content = template(data=res, title='2018 Member State Report')

        return self.index()
