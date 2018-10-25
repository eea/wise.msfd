from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from sqlalchemy import or_

from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView
from .a8 import DESCRIPTORS, Article8
from .a910 import Article910
from .utils import row_to_dict

# from wise.msfd.search.base import EmbededForm
# from .a10 import Article10


class ReportData2012(BaseComplianceView, BaseUtil):

    """ WIP on compliance tables
    """

    name = 'nat-desc-start'

    header_template = Template('pt/report-data-2012-header.pt')

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

    @property
    def country_name(self):
        """ Get country name based on country code
        :return: 'Latvia'
        """
        res = db.get_unique_from_mapper(
            sql.MSFD11CommonLabel,
            'Text',
            sql.MSFD11CommonLabel.value == self.country_code,
            sql.MSFD11CommonLabel.group == 'list-countries',
        )

        if not res:
            return ''

        return res[0]

    @property
    def regions(self):
        """ Get all regions and subregions for a country
        :return: ['BAL', 'ANS']
        """
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code
        )

        res = [row_to_dict(t, r) for r in res]
        regions = set([x['RegionSubRegions'] for x in res])

        return regions

    @property
    def desc_label(self):
        """ Get the label(text) for a descriptor
        :return: 'D5 Eutrophication'
        """
        res = db.get_unique_from_mapper(
            sql.MSFD11CommonLabel,
            'Text',
            sql.MSFD11CommonLabel.value == self.descriptor,
            sql.MSFD11CommonLabel.group == 'list-MonitoringProgramme',
        )

        if not res:
            return ''

        return res[0]

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

        self.content = self.header_template() + \
            article_class(self, self.request)()

        return self.index()


class SnapshotSelectForm(Form):
    template = Template('../pt/inline-form.pt')
    # method = 'GET'
    _updated = False

    @property
    def fields(self):
        snaps = getattr(self.context.context, 'snapshots', [])

        if snaps:
            default = snaps[-1][0]
        else:
            default = None

        dates = [SimpleTerm(x[0], x[0].isoformat(), x[0]) for x in snaps]

        field = Choice(
            title=u'Date of harvest',
            __name__='sd',
            vocabulary=SimpleVocabulary(dates),
            required=False,
            default=default
        )

        return Fields(field)

    def update(self):
        if not self._updated:
            Form.update(self)
            self._updated = True

    @buttonAndHandler(u'View snapshot', name='view')
    def apply(self, action):
        print "apply pushed"

        return

    # TODO: make a condition for this button
    @buttonAndHandler(u'Harvest new data', name='harvest')
    def harvest(self, action):
        data = self.context.get_data_from_db()

        self.context.context.snapshots.append((datetime.now(), data))
        print "harvesting data"

        self.request.response.redirect('./@@view-report-data-2018')


class ReportData2018(BaseComplianceView):

    name = 'nat-desc-start'

    Art8 = Template('pt/nat-desc-report-data-multiple-muid.pt')
    Art9 = Template('pt/nat-desc-report-data-multiple-muid.pt')
    Art10 = Template('pt/nat-desc-report-data-multiple-muid.pt')

    view_names = {
        'Art8': 't_V_ART8_GES_2018_All',
        'Art9': 't_V_ART9_GES_2018',
        'Art10': 't_V_ART10_Targets_2018'
    }

    subform = None

    def get_data_from_view_art8(self):

        view_name = self.view_names[self.article]
        t = getattr(sql2018, view_name)

        count, res = db.get_all_records_ordered(
            t,
            'Criteria',
            t.c.CountryCode == self.country_code,
            t.c.GESComponent == self.descriptor,
        )

        return res

    def get_data_from_view_art10(self):

        view_name = self.view_names[self.article]
        t = getattr(sql2018, view_name)

        # TODO update conditions
        count, res = db.get_all_records_ordered(
            t,
            'GESComponents',
            t.c.CountryCode == self.country_code,
            t.c.GESComponents.like('{}%'.format(self.descriptor)),
        )

        return res

    def get_data_from_view_art9(self):

        view_name = self.view_names[self.article]
        t = getattr(sql2018, view_name)

        count, r = db.get_all_records_ordered(
            t,
            'GESComponent',
            t.c.CountryCode == self.country_code,
            or_(t.c.GESComponent.like('{}%'.format(self.descriptor)),
                t.c.GESComponent.like('{}%'.format(self.descriptor[1]))),
        )

        res = r

        # for row in r:
        #     row_changed = list(row)
        #
        #     features = row.Features
        #     features = features.split(',')
        #     features = set(features)
        #
        #     import pdb; pdb.set_trace()
        #
        #     row_changed[indx] = ', '.join(features)
        #
        #     res.append(row_changed)

        return res

    def change_orientation(self, data):
        """ From a set of results, create labeled list of rows
        """
        res = []
        row0 = data[0]

        for name in row0._fields:
            values = [getattr(row, name) for row in data]

            # if len(set(values)) == 1:
            #     values = set(values)

            res.append([name, values])

        return res

    @db.use_db_session('session_2018')
    def get_data_from_db(self):
        get_data_method = getattr(self, 'get_data_from_view_'
                                        + self.article.lower())

        data = get_data_method()

        g = defaultdict(list)

        for row in data:
            g[row.MarineReportingUnit].append(row)

        res = [(k, self.change_orientation(v)) for k, v in g.items()]
        # res[0][1][3][1][0] = 'REGION 56'

        res = sorted(res, key=lambda r: r[0])

        return res

    def get_snapshots(self):
        """ Returns all snapshots, in the chronological order they were created
        """

        snapshots = getattr(self.context, 'snapshots', None)

        if snapshots is None:
            self.context.snapshots = PersistentList()

            db_data = self.get_data_from_db()
            snapshot = (datetime.now(), db_data)

            self.context.snapshots.append(snapshot)
            self.context.snapshots._p_changed = True

            self.context._p_changed = True

            return self.context.snapshots

        return snapshots

    def get_form(self):

        if not self.subform:
            form = SnapshotSelectForm(self, self.request)
            self.subform = form

        return self.subform

    def get_data(self):
        """ Returns the data to display in the template
        """

        snapshots = self.get_snapshots()
        self.subform.update()
        fd, errors = self.subform.extractData()
        date_selected = fd['sd']

        data = snapshots[-1][1]

        if date_selected:
            print date_selected
            filtered = [x for x in snapshots if x[0] == date_selected]

            if filtered:
                date, data = filtered[0]
            else:
                raise ValueError("Snapshot doesn't exist at this date")

        return data

    # @db.use_db_session('session_2018')
    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        # self.db_data = self.get_data_from_db()

        self.subform = self.get_form()

        data = self.get_data()
        self.content = template(data=data, title='2018 Member State Report')

        return self.index()
