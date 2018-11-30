import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import or_
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BaseUtil
from wise.msfd.data import get_report_file_url, get_report_filename
from wise.msfd.gescomponents import get_ges_criterions
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView
from .a8 import Article8
from .a9 import Article9
from .a10 import Article10
from .utils import row_to_dict

logger = logging.getLogger('wise.msfd')


class ReportData2012(BaseComplianceView, BaseUtil):
    """ WIP on compliance tables
    """

    section = 'national-descriptors'

    article_implementations = {
        'Art8': Article8,
        'Art9': Article9,
        'Art10': Article10,
    }

    def get_criterias_list(self, descriptor):
        """ Get the list of criterias for the specified descriptor

        :param descriptor: 'D5'
        :return: (('D5', 'Eutrophication'),
                  ('5.1.1', 'D5C1'),
                  ('5.2.1', 'D5C2'), ... )
        """

        result = [
            (descriptor, self.descriptor_label)
        ]

        criterions = get_ges_criterions(descriptor)

        for crit in criterions:
            for alt in crit.alternatives:
                title = '{} ({}) {}'.format(crit._id or '', alt[0], alt[1])
                indicator = alt[0]

                result.append((indicator, title))

        return result

    @property
    def muids(self):
        """ Get all Marine Units for a country

        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """
        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code,
            t.c.RegionSubRegions == self.country_region_code,
        )

        res = [row_to_dict(t, r) for r in res]
        muids = set([x['MarineUnitID'] for x in res])

        return sorted(muids)

    def get_article_report_implementation(self):
        klass = self.article_implementations[self.article]

        return klass(self, self.request, self.country_code, self.descriptor,
                     self.article, self.muids, self.colspan)

    def get_report_filename(self):
        # needed in article report data implementations, to retrieve the file
        return get_report_filename('2012',
                                   self.country_code,
                                   self.country_region_code,
                                   self.article,
                                   self.descriptor)

    @db.use_db_session('2012')
    def __call__(self):
        print "Will render report for ", self.article
        filename = self.get_report_filename()

        if filename:
            url = get_report_file_url(filename)
            source_file = (filename, url + '/manage_document')
        else:
            source_file = ('File not found', None)

        self.report_header = self.report_header_template(
            title="{}'s 2012 Member State Report for {} / {} / {}".format(
                self.country_name,
                self.country_region_code,
                self.descriptor,
                self.article
            ),
            # TODO: find out how to get info about who reported
            report_by='Member State',
            source_file=source_file,
            # TODO: do the report_due by a mapping with article: date
            report_due='2012-10-15',
            # TODO get info about report date from _ReportingInformation?? or
            # find another source
            report_date='2013-04-30'
        )

        self.report_data = self.get_article_report_implementation()()

        return self.index()


class SnapshotSelectForm(Form):
    template = Template('../pt/inline-form.pt')
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
        return

    # TODO: make a condition for this button
    @buttonAndHandler(u'Harvest new data', name='harvest')
    def harvest(self, action):
        data = self.context.get_data_from_db()

        self.context.context.snapshots.append((datetime.now(), data))
        print "harvesting data"

        self.request.response.redirect('./@@view-report-data-2018')


class ReportData2018(BaseComplianceView):

    section = 'national-descriptors'

    BLACKLIST = (
        'CountryCode',
        'ReportingDate',
        'ReportedFileLink',
        'Region',
        'MarineReportingUnit'
    )

    Art8 = Template('pt/nat-desc-report-data-multiple-muid.pt')
    Art9 = Template('pt/nat-desc-report-data-single-muid.pt')
    Art10 = Template('pt/nat-desc-report-data-multiple-muid.pt')

    view_names = {
        'Art8': 't_V_ART8_GES_2018',
        'Art9': 't_V_ART9_GES_2018',
        'Art10': 't_V_ART10_Targets_2018'
    }

    subform = None

    def get_data_from_view_art8(self):

        # TODO: the data here should be filtered by muids in region

        view_name = self.view_names[self.article]
        t = getattr(sql2018, view_name)

        count, res = db.get_all_records_ordered(
            t,
            'Criteria',
            t.c.CountryCode == self.country_code,
            t.c.GESComponent.like('{}%'.format(self.descriptor)),
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

        return r

    def change_orientation(self, data):
        """ From a set of results, create labeled list of rows
        """
        def make_distinct(col_name, col_data):
            if col_name not in ('Features', ):
                return col_data

            if not col_data:
                return ''

            splitted = col_data.split(',')
            distinct = ', '.join(sorted(set(splitted)))

            return distinct

        res = []
        row0 = data[0]

        for name in row0._fields:
            values = [make_distinct(name, getattr(row, name)) for row in data]

            res.append([name, values])

        return res

    @db.use_db_session('2018')
    def get_data_from_db(self):
        get_data_method = getattr(
            self,
            'get_data_from_view_' + self.article.lower()
        )

        data = get_data_method()

        g = defaultdict(list)

        for row in data:
            if not row.MarineReportingUnit:
                # skip rows without muid, they can't help us

                continue
            g[row.MarineReportingUnit].append(row)

        res = [(k, self.change_orientation(v)) for k, v in g.items()]

        res = sorted(res, key=lambda r: r[0])

        return res

    def get_snapshots(self):
        """ Returns all snapshots, in the chronological order they were created
        """

        # snapshots = getattr(self.context, 'snapshots', None)
        snapshots = None
        # TODO: fix this. I'm hardcoding it now to always use generated data

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

    def get_muids_from_data(self, data):
        muids = [x[0] for x in data]

        muids = sorted(set(muids))

        result = ', '.join(muids)

        return result

    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        self.subform = self.get_form()
        data = self.get_data()

        report_date = ''
        source_file = ['To be addedd...', '.']

        # TODO: check validity of data

        if data and data[0][1]:
            for row in data[0][1]:
                if row[0] == 'ReportingDate':
                    report_date = row[1][0]

                if row[0] == 'ReportedFileLink':
                    source_file[1] = row[1][0] + '/manage_document'
                    source_file[0] = row[1][0].split('/')[-1]

        self.report_header = self.report_header_template(
            title="{}'s 2018 Member State Report for {} / {} / {}".format(
                self.country_name,
                self.country_region_code,
                self.descriptor,
                self.article
            ),
            # TODO: find out how to get info about who reported
            report_by='Member State',
            source_file=source_file,
            report_due='2018-10-15',
            report_date=report_date
        )

        trans_edit_html = self.translate_view()()
        self.report_data = template(data=data) + trans_edit_html

        return self.index()
