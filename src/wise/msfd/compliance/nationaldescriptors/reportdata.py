from collections import defaultdict  # , namedtuple

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil

from ..base import BaseComplianceView
from .a8 import Article8
from .a10 import Article10
from .utils import row_to_dict

# from wise.msfd.base import BaseUtil, EmbededForm, MainFormWrapper
# from wise.msfd.gescomponents import get_ges_criterions
# from z3c.form.field import Fields
# from z3c.form.form import Form


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
        count, obj = db.get_item_by_conditions(
            sql.MSFD11CommonLabel,
            'ID',
            sql.MSFD11CommonLabel.value == self.country,
            sql.MSFD11CommonLabel.group == 'list-countries',
        )

        return obj.Text

    def get_regions(self):
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country
        )

        res = [row_to_dict(t, r) for r in res]
        regions = set([x['RegionSubRegions'] for x in res])

        return regions

    def get_ges_descriptors(self):
        m = sql.MSFDFeaturesOverview
        res = db.get_unique_from_mapper(
            m, 'RFCode',
            m.FeatureType == 'GES descriptor'
        )

        return res

    def get_ges_descriptor_label(self, ges):
        count, obj = db.get_item_by_conditions(
            sql.MSFD11CommonLabel,
            'ID',
            sql.MSFD11CommonLabel.value == ges,
            sql.MSFD11CommonLabel.group == 'list-MonitoringProgramme',
        )

        if obj:
            return obj.Text

    def get_marine_unit_ids(self):
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country
        )

        res = [row_to_dict(t, r) for r in res]
        muids = set([x['MarineUnitID'] for x in res])

        return sorted(muids)

    def get_ges_criterions(self, descriptor):
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
        # returns a dict key Indicator, value: list of feature pressures
        # {u'5.2.2-indicator 5.2C': set([u'Transparency', u'InputN_Psubst']),
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
        count, res = db.get_all_records(
            sql.MSFD11CommonLabel,
            sql.MSFD11CommonLabel.value.in_(criterions),
            sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
                                             'list-GESCriteria')),
        )

        return [(x.value, x.Text) for x in res]

    def get_indicator_descriptors(self, muids, available_indicators):
        count, res = db.get_all_records(
            sql.MSFD9Descriptor,
            sql.MSFD9Descriptor.MarineUnitID.in_(muids),
            sql.MSFD9Descriptor.ReportingFeature.in_(available_indicators)
        )

        return res

    def get_ges_descriptions(self, indicators):
        res = {}

        for indic in indicators:
            res[indic.ReportingFeature] = indic.DescriptionGES

        return res

    def get_descriptors_for_muid(self, muid):
        return sorted(
            [x for x in self.indicator_descriptors if x.MarineUnitID == muid],
            key=lambda o: o.ReportingFeature
        )

    @db.use_db_session('session')
    def __call__(self):
        # threadlocals.session_name = 'session'

        # data = self.get_flattened_data(self)

        self.country = self.country_code
        # self.country = self._country_folder.getId().upper()
        # self.descriptor = self._descriptor_folder.getId().upper()
        # self.article = self._article_assessment.getId().capitalize()

        if not self.country:
            return ''

        # descriptor = 'D5'
        # descriptor_prefix = descriptor[1:]

        self.country_name = self.get_country_name()
        self.regions = self.get_regions()

        # TODO: optimize this with a single function and a single query (w/
        # JOIN)
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

        self.criterion_labels = dict(
            self.get_criterion_labels(self.criterions)
        )
        # add D5 criterion to the criterion lists too
        self.criterion_labels.update({self.descriptor: self.desc_label})

        self.indicator_descriptors = self.get_indicator_descriptors(
            self.muids, self.indic_w_p.keys()
        )

        # indicator_ids = self.indics.keys()
        # res = self.get_ges_descriptions(self.indicators)
        # self.ges_descriptions = {k: v
        #                          for k, v in res.items()
        #                          if k in indicator_ids}

        # TODO create a function for this
        self.crit_lab_indics = defaultdict(list)

        for crit_lab in self.criterion_labels.keys():
            self.crit_lab_indics[crit_lab] = []

            for ind in self.indic_w_p.keys():
                norm_ind = ind.split('-')[0]

                if crit_lab == norm_ind:
                    self.crit_lab_indics[crit_lab].append(ind)

            if not self.crit_lab_indics[crit_lab]:
                self.crit_lab_indics[crit_lab].append('')
        self.crit_lab_indics[u'GESOther'] = ['']

        self.colspan = len([item
                            for sublist in self.crit_lab_indics.values()

                            for item in sublist])

        # Article 8 stuff
        # self.art8data = self.get_data_reported('BAL- LV- AA- 001',
        # self.descriptor)

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

        # data = self.context.context.get_flattened_data(self)
        #
        # def d(k):
        #     return data.get(k, None)
        #
        # article = d('article')
        #
        # member_state = d('member_state')
        # descriptor = d('descriptor')
        # marine_unit_ids = d('marine_unit_ids')
        # feature = d('feature_reported')

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
