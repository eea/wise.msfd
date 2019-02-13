import logging
import time
from collections import OrderedDict, namedtuple
from datetime import datetime
from HTMLParser import HTMLParser
from io import BytesIO

from lxml.etree import fromstring
from zope.interface import implements
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

import xlsxwriter
from eea.cache import cache
from plone.app.layout.viewlets.common import TitleViewlet as BaseTitleViewlet
from plone.memoize import volatile
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018  # sql,
from wise.msfd.base import BaseUtil
from wise.msfd.compliance.interfaces import IReportDataView
from wise.msfd.compliance.utils import REPORT_DEFS, get_sorted_fields
from wise.msfd.data import (get_factsheet_url, get_report_data,
                            get_report_file_url, get_report_filename)
from wise.msfd.gescomponents import (GES_LABELS, get_descriptor, get_features,
                                     get_parameters)
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (ItemLabel, ItemList, change_orientation,
                             consolidate_data)
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView
from .a8 import Article8, Article8Alternate
from .a9 import Article9, Article9Alternate
from .a10 import Article10, Article10Alternate

# from persistent.list import PersistentList
# from six import string_types
# from .utils import row_to_dict

logger = logging.getLogger('wise.msfd')

NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


ReportingInformation = namedtuple('ReportingInformation',
                                  ['report_date', 'reporters'])


def get_reportdata_key(func, self, *args, **kwargs):
    """ Reportdata template rendering cache key generation
    """

    if 'nocache' in self.request.form:
        raise volatile.DontCache

    muids = ",".join([m.id for m in self.muids])
    region = getattr(self, 'country_region_code', ''.join(self.regions))

    res = '_cache_' + '_'.join([self.report_year,
                                self.country_code,
                                region,
                                self.descriptor,
                                self.article,
                                muids])
    res = res.replace('.', '').replace('-', '')

    return res


def serialize_rows(rows):
    """ Return a cacheable result of rows, this is used when
    downloading the report data as excel

    :param rows: view.rows
    :return: dict in format {mru : data, ...} where
        'mru': marine unit id, representing the worksheet title
        'data': list of tuples in format [(row_title, raw_data), ...]
        'raw_data' list of unicode values [u'GES 5.1', u'GES 5.2', ...]
    """

    if isinstance(rows, list):
        rows = {'Report data': rows}

    res = {}

    for mru, data in rows.items():
        raw_data = []

        for row in data:
            title = row.title
            raw_values = []

            for v in row.raw_values:
                if isinstance(v, str):
                    parser = HTMLParser()
                    v = parser.unescape(v.decode('utf-8'))

                if not isinstance(v, basestring):
                    if not v:
                        v = ''
                    else:
                        v = v.__repr__()

                        if isinstance(v, str):
                            v = v.decode('utf-8')

                raw_values.append(unicode(v))

            raw_data.append((title, raw_values))

        res[mru] = raw_data

    return res


class ReportData2012(BaseComplianceView, BaseUtil):
    """ WIP on compliance tables
    """
    implements(IReportDataView)

    year = report_year = '2012'
    section = 'national-descriptors'

    @property
    def help_text(self):
        klass = self.article_implementations[self.article]

        return klass.help_text

    @property
    def article_implementations(self):
        res = {
            'Art8': Article8,
            'Art9': Article9,
            'Art10': Article10,
        }

        return res

    def get_criterias_list(self, descriptor):
        """ Get the list of criterias for the specified descriptor

        :param descriptor: 'D5'
        :return: (('D5', 'Eutrophication'),
                  ('5.1.1', 'D5C1'),
                  ('5.2.1', 'D5C2'), ... )

        # TODO: the results here need to be augumented by L_GESComponents
        """

        result = [
            (descriptor, self.descriptor_label)
        ]

        criterions = get_descriptor(descriptor).criterions

        for crit in criterions:
            for alt in crit.alternatives:
                title = '{} ({}) {}'.format(crit._id or '', alt[0], alt[1])
                indicator = alt[0]

                result.append((indicator, title))

        return result

    def get_report_view(self):
        logger.info("Rendering 2012 report for: %s %s %s %s",
                    self.country_code, self.descriptor, self.article,
                    ",".join([x.id for x in self.muids]))

        klass = self.article_implementations[self.article]

        view = klass(self, self.request, self.country_code,
                     self.country_region_code, self.descriptor, self.article,
                     self.muids)

        return view

    @cache(get_reportdata_key, dependencies=['translation'])
    def get_report_data(self):
        view = self.get_report_view()
        rendered_view = view()

        # get cacheable raw values
        rows = serialize_rows(view.rows)

        return rendered_view, rows

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file

        return get_report_filename('2012',
                                   self.country_code,
                                   self.country_region_code,
                                   art or self.article,
                                   self.descriptor)

    def data_to_xls(self, data, report_header):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        # add worksheet with report header data
        worksheet = workbook.add_worksheet(unicode('Report header'))

        for i, (wtitle, wdata) in enumerate(report_header.items()):
            wtitle = wtitle.title().replace('_', ' ')

            if isinstance(wdata, tuple):
                wdata = wdata[1]

            worksheet.write(i, 0, wtitle)
            worksheet.write(i, 1, wdata)

        for wtitle, wdata in data.items():  # add worksheet(s) with report data
            if not wdata:
                continue

            worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

            for i, row in enumerate(wdata):
                row_label = row[0]
                worksheet.write(i, 0, row_label)
                row_values = row[1]

                for j, v in enumerate(row_values):
                    worksheet.write(i, j + 1, v)

        workbook.close()
        out.seek(0)

        return out

    def download(self, report_data, report_header):
        xlsio = self.data_to_xls(report_data, report_header)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join([self.country_code,
                          self.country_region_code,
                          self.article,
                          self.descriptor])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    @db.use_db_session('2012')
    def __call__(self):
        # if self.descriptor.startswith('D1.'):       # map to old descriptor
        #     # self._descriptor = 'D1'               # this hardcodes D1.x
        #                                             # descriptors to D1
        #     assert self.descriptor == 'D1'

        if 'translate' in self.request.form:
            report_view = self.get_report_view()
            report_view.auto_translate()

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        print("Will render report for: %s" % self.article)
        self.filename = filename = self.get_report_filename()
        factsheet = None

        source_file = ('File not found', None)

        if filename:
            url = get_report_file_url(filename)

            if url:
                try:
                    factsheet = get_factsheet_url(url)
                except Exception:
                    logger.exception("Error in getting HTML Factsheet URL %s",
                                     url)
            else:
                logger.warning("No factsheet url, filename is: %r", filename)

            source_file = (filename, url + '/manage_document')

        rep_info = self.get_reporting_information()

        report_header_data = OrderedDict(
            title="{}'s 2012 Member State Report for {} / {} / {}".format(
                self.country_name,
                self.country_region_name,
                self.descriptor,
                self.article
            ),
            report_by=rep_info.reporters,
            source_file=source_file,
            factsheet=factsheet,
            # TODO: do the report_due by a mapping with article: date
            report_due='2012-10-15',
            report_date=rep_info.report_date,
            help_text=self.help_text,
        )
        report_header = self.report_header_template(**report_header_data)

        report_data, report_data_rows = self.get_report_data()
        trans_edit_html = self.translate_view()()
        self.report_html = report_header + report_data + trans_edit_html

        if 'download' in self.request.form:

            return self.download(report_data_rows, report_header_data)

        return self.index()

    def get_reporting_information(self):
        # The MSFD<ArtN>_ReportingInformation tables are not reliable (8b is
        # empty), so we try to get the information from the reported XML files.

        default = ReportingInformation('Member State', '2013-04-30')

        if not self.filename:
            return default

        text = get_report_data(self.filename)
        root = fromstring(text)

        reporters = root.xpath('//w:ReportingInformation/w:Name/text()',
                               namespaces=NSMAP)
        date = root.xpath('//w:ReportingInformation/w:ReportingDate/text()',
                          namespaces=NSMAP)

        try:
            res = ReportingInformation(date[0], ', '.join(set(reporters)))
        except Exception:
            logger.exception('Could not get reporting info for %s, %s, %s',
                             self.article, self.descriptor, self.country_code
                             )
            res = default

        return res


class ReportData2012Like2018(ReportData2012):
    """ An alternative implementation, mapping data like the 2018 views
    """
    @property
    def article_implementations(self):
        res = {
            'Art8': Article8Alternate,
            'Art9': Article9Alternate,
            'Art10': Article10Alternate,
        }

        return res


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

        self.request.response.redirect('./@@view-report-data-2018')


class Proxy2018(object):
    """ A proxy wrapper that uses XML definition files to 'translate' elements
    """

    def __init__(self, obj, article, extra=None):
        self.__o = obj       # the proxied object
        self.nodes = REPORT_DEFS['2018'][article].get_elements()

        if not extra:
            extra = {}

        self.extra = extra

        for node in self.nodes:
            name = node.get('name')
            value = getattr(self.__o, name, extra.get(name, None))

            if not value:
                continue

            attrs = node.attrib
            label_name = attrs.get('label', None)

            if not label_name:
                continue

            as_list = attrs.get('as-list', 'false')

            if as_list == 'true':
                vals = set(value.split(','))

                res = [
                    ItemLabel(
                        v,
                        GES_LABELS.get(label_name, v),
                    )

                    for v in vals
                ]

                setattr(self, name, ItemList(rows=res))
            else:
                title = GES_LABELS.get(label_name, value)
                setattr(self, name, ItemLabel(value, title))

    def __getattr__(self, name):
        return getattr(self.__o, name, self.extra.get(name, None))

    def __iter__(self):
        return iter(self.__o)


class ReportData2018(BaseComplianceView):
    implements(IReportDataView)

    report_year = '2018'        # used by cache key
    year = '2018'       # used in report definition and translation
    section = 'national-descriptors'
    help_texts = {
        'Art8': """
The data is retrieved from the MSFD2018_production.V_ART8_GES_2018 database
view, filtered by country code and ges component ids. If the current Descriptor
starts with 'D1.', we also append the 'D1' descriptor to the GES Component ids.

We use this table for the list of GES Components and the descriptor that they
belong to:

https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv
""",
        'Art9': """
The data is retrieved from the MSFD2018_production.V_ART9_GES_2018 database
view, filtered by country code and ges component ids. If the current Descriptor
starts with 'D1.', we also append the 'D1' descriptor to the GES Component ids.

We use this table for the list of GES Components and the descriptor that they
belong to:

https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv
""",
        'Art10': """
The data is retrieved from the MSFD2018_production.V_ART10_Targets_2018
database view. Because the GESComponent column is not reliable (the Netherlands
reported using the 1.1.3 GESComponent for all their records), we filter the
data using the Parameters and Features available for the current descriptor.

We use this file for the Descriptor to Parameters and Features association
table:

https://svn.eionet.europa.eu/repositories/Reportnet/Dataflows/MarineDirective/MSFD2018/Webforms/msfd2018-codelists.json
""",
    }

    @property
    def help_text(self):
        return self.help_texts[self.article]

    BLACKLIST = (       # used in templates to filter fields
        'CountryCode',
        'ReportingDate',
        'ReportedFileLink',
        'Region',
        'MarineReportingUnit'
    )

    Art8 = Template('pt/report-data-multiple-muid.pt')
    Art9 = Template('pt/report-data-multiple-muid.pt')
    Art10 = Template('pt/report-data-multiple-muid.pt')
    # Art9 = Template('pt/report-data-single-muid.pt')

    subform = None      # used for the snapshot selection form

    def get_data_from_view_Art8(self):
        # TODO this is not used
        # exclude = REPORT_2018.get_group_by_fields(self.article)
        # exclude,

        t = sql2018.t_V_ART8_GES_2018

        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        muids = [x.id for x in self.muids]
        conditions = [
            t.c.CountryCode == self.country_code,
            t.c.GESComponent.in_(all_ids),
            t.c.Element.isnot(None),
            t.c.MarineReportingUnit.in_(muids),
        ]

        count, res = db.get_all_records_ordered(
            t,
            'Criteria',
            *conditions
        )
        print "Res count", count
        # import pdb
        # pdb.set_trace()

        data = [Proxy2018(row, self.article) for row in res]

        return data

    def get_data_from_view_Art10(self):
        t = sql2018.t_V_ART10_Targets_2018

        # descr_class = get_descriptor(self.descriptor)
        # all_ids = list(descr_class.all_ids())
        #
        # if self.descriptor.startswith('D1.'):
        #     all_ids.append('D1')
        # TODO check conditions for other countries beside NL
        # conditions = [t.c.GESComponents.in_(all_ids)]

        conditions = []
        params = get_parameters(self.descriptor)
        p_codes = [p.name for p in params]
        conditions.append(t.c.Parameter.in_(p_codes))

        features = set([f.name for f in get_features(self.descriptor)])

        count, res = db.get_all_records_ordered(
            t,
            'GESComponents',
            t.c.CountryCode == self.country_code,
            *conditions
        )

        out = []

        for row in res:
            feats = set(row.Features.split(','))

            if feats.intersection(features):
                out.append(row)

        data = [Proxy2018(row, self.article) for row in out]

        return data

    def get_data_from_view_Art9(self):

        t = sql2018.t_V_ART9_GES_2018

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        # TODO: this needs to be analysed, what to do about D1?

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        count, r = db.get_all_records_ordered(
            t,
            'GESComponent',
            t.c.CountryCode == self.country_code,
            t.c.GESComponent.in_(all_ids)
        )

        data = [Proxy2018(row, self.article) for row in r]

        return data

    @db.use_db_session('2018')
    def get_data_from_db(self):
        data = getattr(self, 'get_data_from_view_' + self.article)()

        definition = REPORT_DEFS['2018'][self.article]
        group_by_fields = definition.get_group_by_fields()

        # this consolidates the data, filtering duplicates
        # list of ((name, label), values)
        good_data = consolidate_data(data, group_by_fields)

        res = []

        for mru, rows in good_data.items():
            _fields = rows[0]._fields
            sorted_fields = get_sorted_fields('2018', self.article, _fields)
            _data = change_orientation(rows, sorted_fields)

            for row in _data:
                (fieldname, label), row_data = row
                row[0] = (fieldname, label)

                if fieldname not in group_by_fields:
                    continue

                # TODO: this needs to be refactored into a function, to allow
                # easier understanding of code

                # rewrite some rows with list of all possible values
                all_values = [
                    getattr(x, fieldname)

                    for x in data

                    if (x.MarineReportingUnit == mru) and
                    (getattr(x, fieldname) is not None)
                ]
                seen = []
                uniques = []

                # if the values are unicode

                if isinstance(all_values[0], (unicode, str)):
                    row[1] = [', '.join(set(all_values))] * len(row_data)

                    continue

                # if the values are ItemList types, make the values unique

                for item in all_values:
                    item_label_class = item.rows[0]
                    name = item_label_class.name

                    if name in seen:
                        continue

                    seen.append(name)
                    uniques.append(item_label_class)

                row[1] = [ItemList(rows=uniques)] * len(row_data)

            # TODO: this needs to be redone to take advantage of smart
            # self.muids
            mru_label = GES_LABELS.get('mrus', mru)

            if mru_label != mru:
                mru_label = u"{} ({})".format(mru_label, unicode(mru))

            res.append((ItemLabel(mru, mru_label), _data))

        return sorted(res, key=lambda r: r[0])      # sort by MarineUnitiD

    def get_snapshots(self):
        """ Returns all snapshots, in the chronological order they were created
        """
        # TODO: fix this. I'm hardcoding it now to always use generated data
        db_data = self.get_data_from_db()
        snapshot = (datetime.now(), db_data)

        return [snapshot]

        # snapshots = getattr(self.context, 'snapshots', None)
        #
        # if snapshots is None:
        #     self.context.snapshots = PersistentList()
        #
        #     db_data = self.get_data_from_db()
        #     snapshot = (datetime.now(), db_data)
        #
        #     self.context.snapshots.append(snapshot)
        #     self.context.snapshots._p_changed = True
        #
        #     self.context._p_changed = True
        #
        #     return self.context.snapshots
        #
        # return snapshots

    def get_report_data(self):
        """ Returns the data to display in the template

        Returns a list of "rows (tuples of label: data)"
        """

        snapshots = self.get_snapshots()
        self.subform.update()
        fd, errors = self.subform.extractData()
        date_selected = fd['sd']

        data = snapshots[-1][1]

        if date_selected:
            filtered = [x for x in snapshots if x[0] == date_selected]

            if filtered:
                date, data = filtered[0]
            else:
                raise ValueError("Snapshot doesn't exist at this date")

        return data

    def get_muids_from_data(self, data):
        if isinstance(data[0][0], (unicode, str)):
            all_muids = sorted(set([x[0] for x in data]))

            return ', '.join(all_muids)

        all_muids = [x[0] for x in data]
        seen = []
        muids = []

        for muid in all_muids:
            name = muid.name

            if name in seen:
                continue

            seen.append(name)
            muids.append(muid)

        return ItemList(rows=muids)

    @db.use_db_session('2018')
    def get_report_metadata(self):
        """ Returns metadata about the reported information
        """
        t = sql2018.ReportedInformation
        schema = {
            'Art8': 'ART8_GES',
            'Art9': 'ART9_GES',
            'Art10': 'ART10_Targets',
        }[self.article]
        count, item = db.get_item_by_conditions(
            t,
            'ReportingDate',
            t.CountryCode == self.country_code,
            t.Schema == schema,
            reverse=True,
        )
        return item

    @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2018 report data: %s %s %s %s",
                    self.country_code, self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()
        report = self.get_report_metadata()
        report_by = u"{} / {} / {}".format(
            report.ContactOrganisation,
            report.ContactName,
            report.ContactMail,
        )

        report_header = self.report_header_template(
            title="{}'s 2018 Member State Report for {} / {} / {}".format(
                self.country_name,
                self.country_region_name,
                self.descriptor,
                self.article
            ),
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by=report_by,
            source_file=report.ReportedFileLink,
            report_due='2018-10-15',
            report_date=report.ReportingDate,
            help_text=self.help_text
        )

        template = getattr(self, self.article, None)

        return template(data=data, report_header=report_header)

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        for wtitle, wdata in data:
            worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

            for i, (row_label, row_values) in enumerate(wdata):
                worksheet.write(i, 0, row_label)

                for j, v in enumerate(row_values):
                    worksheet.write(i, j + 1, unicode(v or ''))

        workbook.close()
        out.seek(0)

        return out

    def download(self):
        xlsdata = self.get_report_data()

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join([self.country_code,
                          self.country_region_code,
                          self.article,
                          self.descriptor])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def auto_translate(self):
        data = self.get_report_data()
        # report_def = REPORT_DEFS[self.year][self.article]
        # translatables = report_def.get_translatable_fields()
        translatables = self.TRANSLATABLES
        seen = set()

        for table in data:
            muid, table_data = table

            for row in table_data:
                (name, label), cells = row
                if name in translatables:
                    for value in cells:
                        if value not in seen:
                            retrieve_translation(self.country_code, value)
                            seen.add(value)

        return ''

    def __call__(self):

        self.content = ''
        template = getattr(self, self.article, None)

        if not template:
            return self.index()

        self.subform = self.get_form()

        if 'download' in self.request.form:
            return self.download()

        if 'translate' in self.request.form:
            return self.auto_translate()

        trans_edit_html = self.translate_view()()

        t = time.time()
        logger.debug("Started rendering of report data")

        # self.muids = []
        report_html = self.render_reportdata()

        delta = time.time() - t
        logger.info("Rendering report data took: %s, %s/%s/%s/%s",
                    delta, self.article, self.descriptor,
                    self.country_region_code, self.country_code)

        self.report_html = report_html + trans_edit_html

        return self.index()

    def get_form(self):

        if not self.subform:
            form = SnapshotSelectForm(self, self.request)
            self.subform = form

        return self.subform


class TitleViewlet(BaseTitleViewlet, BaseComplianceView):

    @property
    def page_title(self):
        params = {
            'country': self.country_name,
            'region': self.country_region_code,
            'article': self.article,
            'descriptor': self.descriptor,
            'year': self.view.report_year,
        }

        return (u"{article} report - {country} / {region} / {descriptor}"
                "/ {year}".format(**params))
