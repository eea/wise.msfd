from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil

from ..base import BaseComplianceView
from .a8 import Article8, DESCRIPTORS
from .a910 import Article910
from .a10 import Article10
from .utils import row_to_dict


class ReportData2012(BaseComplianceView, BaseUtil):

    """ WIP on compliance tables
    """

    name = 'nat-desc-start'

    Art8 = Article8
    Art9 = Article910
    Art10 = Article910

    def get_criterias_list(self, descriptor):
        """ Get the list of criterias for the specified descriptor
        :param descriptor: 'D5'
        :return: (('D5', 'Eutrophication'), ('5.1.1', 'D5C1'),
            ('5.2.1', 'D5C2'), ... )
        """
        descriptor_class = DESCRIPTORS.get(descriptor, None)

        if descriptor_class:
            criterias_list = descriptor_class.criterias_order

            return criterias_list

        return []

    @property
    def muids(self):
        """ Get all Marine Units for a country
        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code
        )

        res = [row_to_dict(t, r) for r in res]
        muids = set([x['MarineUnitID'] for x in res])

        return sorted(muids)

    @property
    def colspan(self):
        return 42

    @db.use_db_session('session')
    def __call__(self):
        article_class = getattr(self, self.article)

        # TODO find another way to pass these
        article_class.country = self.country_code
        article_class.descriptor = self.descriptor
        article_class.article = self.article

        article_class.muids = self.muids
        article_class.colspan = self.colspan

        print "Will render report for ", self.article

        self.content = article_class(self, self.request)()

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
