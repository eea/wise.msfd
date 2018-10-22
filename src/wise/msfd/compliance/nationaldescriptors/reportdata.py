from collections import defaultdict
from copy import deepcopy
from datetime import datetime

from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from persistent.list import PersistentList
from plone.api import portal
from plone.dexterity.browser.add import DefaultAddForm
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil
from wise.msfd.search.base import EmbededForm
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView
from .a8 import DESCRIPTORS, Article8
from .a10 import Article10
from .a910 import Article910
from .utils import row_to_dict


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
    template = Template('../pt/comment-add-form.pt')

    def __init__(self, context, request):
        super(SnapshotSelectForm, self).__init__(context, request)

        snaps = getattr(context.context, 'snapshots', None)

        if snaps:
            default = snaps[-1][0]
        else:
            default = None

        dates = [SimpleTerm(x[0], x[0].isoformat(), x[0]) for x in snaps]

        fields = []

        field = Choice(
            title=u'Date of harvest',
            __name__='harvest_date',
            vocabulary=SimpleVocabulary(dates),
            required=False,
            default=default
        )

        fields.append(field)

        self.fields = Fields(*fields)

        self.update()
        self.updateWidgets()

        # self.widgets['harvest_date']
    @buttonAndHandler(u'Apply')
    def apply(self, action):
        pass

    @buttonAndHandler(u'Harvest new data')
    def harvest(self, action):
        data = self.context.get_data_from_db()
        self.context.context.snapshots.append((datetime.now(), data))

        # self.request.response.redirect('./@@view-report-data-2018')


class ReportData2018(BaseComplianceView):

    name = 'nat-desc-start'

    Art8 = Template('pt/nat-desc-report-data-multiple-muid.pt')
    Art9 = ''
    Art10 = ''

    view_names = {
        'Art8': 't_V_ART8_GES_2018',
        # TODO: do the other: 9, 10
    }

    def __init__(self, context, request):
        super(ReportData2018, self).__init__(context, request)

        self.subform = SnapshotSelectForm(self, request)

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

    def compare_data(self, res, prev_snap):

        return res != prev_snap

        is_changed = False

        if not prev_snap:
            return is_changed, res

        res_changed = deepcopy(res)

        for mru_row in res_changed:
            mru = mru_row[0]
            data = mru_row[1]
            prev_data = [x[1] for x in prev_snap if x[0] == mru][0]

            for val_name_row in data:
                val_name = val_name_row[0]
                values = val_name_row[1]
                prev_values = [x[1] for x in prev_data if x[0] == val_name][0]

                for indx in range(len(values)):
                    val = values[indx]
                    prev_val = prev_values[indx]

                    if val != prev_val:
                        values[indx] = [prev_val, val]
                        is_changed = True

        return is_changed, res_changed

    def get_data_from_db(self):
        data = self.get_data_from_view()

        g = defaultdict(list)

        for row in data:
            g[row.MarineReportingUnit].append(row)

        res = [(k, self.change_orientation(v)) for k, v in g.items()]
        # res[0][1][3][1][0] = 'DE_ANS'

        return res

    def get_snapshots(self):
        # self.context.snapshots = []
        snapshots = getattr(self.context, 'snapshots', [])

        if not snapshots:
            new_data = self.get_data_from_db()
            date = datetime.now()
            self.context.snapshots = PersistentList()
            self.context.snapshots.append((date, new_data))
            self.context.snapshots._p_changed = True

            return self.context.snapshots

        return snapshots

    def get_form(self):
        if not hasattr(self, 'subform'):
            form = SnapshotSelectForm(self, self.request)

            return form

        return self.subform

    @db.use_db_session('session_2018')
    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        self.new_data = self.get_data_from_db()
        snapshots = self.get_snapshots()
        last_snap = snapshots[-1]

        self.is_changed = self.compare_data(self.new_data, last_snap[1])

        # self.subform = self.get_form()

        print "Nr of snapshots: {}".format(len(snapshots))

        date_selected = self.subform.widgets['harvest_date'].value

        print "selected date: {}".format(date_selected)

        result = [x for x in snapshots if x[0].isoformat() == date_selected]

        # if self.is_changed:
        #     res = changes
            # self.context.snapshots.append(new_data)
        # else:
        #     res = self.new_data

        self.content = template(data=result,
                                title='2018 Member State Report')

        return self.index()



class ReportData2018_old(Form, BaseComplianceView):
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

    # def __init__(self, context, request):
    #     super(ReportData2018, self).__init__(context, request)
    #
    #     self.subform = RefreshForm(context, self.request)

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

    def compare_data(self, res, prev_snap):

        return res != prev_snap


        is_changed = False

        if not prev_snap:
            return is_changed, res

        res_changed = deepcopy(res)

        for mru_row in res_changed:
            mru = mru_row[0]
            data = mru_row[1]
            prev_data = [x[1] for x in prev_snap if x[0] == mru][0]

            for val_name_row in data:
                val_name = val_name_row[0]
                values = val_name_row[1]
                prev_values = [x[1] for x in prev_data if x[0] == val_name][0]

                for indx in range(len(values)):
                    val = values[indx]
                    prev_val = prev_values[indx]

                    if val != prev_val:
                        values[indx] = [prev_val, val]
                        is_changed = True

        return is_changed, res_changed

    def get_data_from_db(self):
        data = self.get_data_from_view()

        g = defaultdict(list)

        for row in data:
            g[row.MarineReportingUnit].append(row)

        res = [(k, self.change_orientation(v)) for k, v in g.items()]
        res[0][1][3][1][0] = 'DE_URL'

        return res

    def get_snapshots(self):
        # self.context.snapshots = []
        snapshots = getattr(self.context, 'snapshots', [])

        if not snapshots:
            new_data = self.get_data_from_db()
            date = datetime.now()
            self.context.snapshots = PersistentList()
            self.context.snapshots.append((date, new_data))
            self.context.snapshots._p_changed = True

            return self.context.snapshots

        return snapshots

    def get_form(self):
        if not hasattr(self, 'subform'):
            form = SnapshotSelectForm(self, self.request)

            return form

        return self.subform

    @db.use_db_session('session_2018')
    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        self.new_data = self.get_data_from_db()
        snapshots = self.get_snapshots()
        last_snap = snapshots[-1]

        self.is_changed = self.compare_data(self.new_data, last_snap[1])

        self.subform = self.get_form()

        print "Nr of snapshots: {}".format(len(snapshots))

        # print self.subform.form.data

        self.is_changed = self.compare_data(self.new_data, last_snap[1])

        # if self.is_changed:
        #     res = changes
            # self.context.snapshots.append(new_data)
        # else:
        #     res = self.new_data

        self.content = template(data=last_snap[-1],
                                title='2018 Member State Report')

        return self.index()
