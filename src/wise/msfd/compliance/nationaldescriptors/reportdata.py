import logging
from collections import OrderedDict, defaultdict, namedtuple
from datetime import datetime
from HTMLParser import HTMLParser
from io import BytesIO

from lxml.etree import fromstring
from sqlalchemy import or_
from zope.interface import implements
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

import xlsxwriter
from eea.cache import cache
from plone.memoize import volatile
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018  # sql,
from wise.msfd.base import BaseUtil
from wise.msfd.compliance.interfaces import (IReportDataView,
                                             IReportDataViewSecondary)
from wise.msfd.compliance.nationaldescriptors.data import get_report_definition
from wise.msfd.compliance.utils import (group_by_mru,
                                        insert_missing_criterions,
                                        ordered_regions_sortkey)
from wise.msfd.compliance.vocabulary import get_regions_for_country
from wise.msfd.data import (get_all_report_filenames,
                            get_envelope_release_date, get_factsheet_url,
                            get_report_file_url, get_report_filename,
                            get_xml_report_data)
from wise.msfd.gescomponents import get_descriptor, get_features
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (current_date, items_to_rows, natural_sort_key,
                             timeit)
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .a7 import Article7, Article7_2018
from .a8 import Article8
from .a8alternate import Article8Alternate
from .a8esa import Article8ESA
from .a9 import Article9, Article9Alternate
from .a10 import Article10, Article10Alternate
from .a34 import Article34, Article34_2018
from .base import BaseView
from .proxy import Proxy2018
from .utils import consolidate_date_by_mru, consolidate_singlevalue_to_list

# from persistent.list import PersistentList
# from six import string_types
# from .utils import row_to_dict

logger = logging.getLogger('wise.msfd')

NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


ReportingInformation = namedtuple('ReportingInformation',
                                  ['report_date', 'reporters'])

ReportingInformation2018 = namedtuple(
    'ReportingInformation', ['ReportedFileLink', 'ContactOrganisation',
                             'ReportingDate'])


def get_reportdata_key(func, self, *args, **kwargs):
    """ Reportdata template rendering cache key generation
    """

    if 'nocache' in self.request.form:
        raise volatile.DontCache

    muids = ",".join([m.id for m in self.muids])
    region = getattr(self, 'country_region_code', ''.join(self.regions))
    focus_muid = getattr(self, 'focus_muid', '')

    cache_key_extra = getattr(self, 'cache_key_extra', '')

    res = '_cache_' + '_'.join([
        func.__name__,
        self.report_year,
        cache_key_extra,
        self.country_code,
        region,
        self.descriptor,
        self.article,
        muids,
        focus_muid,
        current_date(),
    ])
    # TODO why replace '.', makes D1.1 the same as D11
    # res = res.replace('.', '').replace('-', '')
    logger.info("Report data cache key: %s", res)

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


class ReportData2012(BaseView, BaseUtil):
    """ WIP on compliance tables
    """
    implements(IReportDataView)

    year = report_year = '2012'
    section = 'national-descriptors'
    cache_key_extra = 'base'

    @property
    def help_text(self):
        klass = self.article_implementations[self.article]

        return klass.help_text

    @property
    def article_implementations(self):
        res = {
            'Art3': Article34,
            'Art4': Article34,
            'Art7': Article7,
            'Art8esa': Article8ESA,
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

    def get_report_header_data(self, report_by, source_file, factsheet,
                               report_date):
        data = OrderedDict(
            title=self.report_title,
            report_by=report_by,
            source_file=source_file,
            factsheet=factsheet,
            # TODO: do the report_due by a mapping with article: date
            report_due='2012-10-15',
            report_date=report_date,
            help_text=self.help_text,
        )

        return data

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file

        return get_report_filename('2012',
                                   self.country_code,
                                   self.country_region_code,
                                   art or self.article,
                                   self.descriptor)

    @property
    def report_title(self):
        title = "Member State report / {} / 2012/ {} / {} / {}".format(
            self.article,
            self.descriptor_title,
            self.country_name,
            self.country_region_name,
        )

        return title

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

    def _set_response_header(self, xlsio):
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

    def download(self, report_data, report_header):
        xlsio = self.data_to_xls(report_data, report_header)

        return self._set_response_header(xlsio)

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

        report_header_data = self.get_report_header_data(
            rep_info.reporters, source_file, factsheet, rep_info.report_date
        )
        report_header = self.report_header_template(**report_header_data)

        try:
            report_data, report_data_rows = self.get_report_data()
        except:
            report_data, report_data_rows = 'Error in rendering report', []
        trans_edit_html = self.translate_view()()
        self.report_html = report_header + report_data + trans_edit_html

        if 'download' in self.request.form:

            return self.download(report_data_rows, report_header_data)

        return self.index()

    def _get_reporting_info(self, root):
        reporters = root.xpath(
            '//w:ReportingInformation/w:Organisation/text()', namespaces=NSMAP
        )
        date = root.xpath('//w:ReportingInformation/w:ReportingDate/text()',
                          namespaces=NSMAP)

        return reporters, date

    def get_reporting_information(self, filename=None):
        # The MSFD<ArtN>_ReportingInformation tables are not reliable (8b is
        # empty), so we try to get the information from the reported XML files.

        if not filename:
            filename = self.filename

        default = ReportingInformation('2013-04-30', 'Member State')

        if not filename:
            return default

        text = get_xml_report_data(filename)
        root = fromstring(text)

        reporters, date = self._get_reporting_info(root)

        try:
            date_obj = datetime.strptime(date[0], '%d-%m-%Y')
            date_final = date_obj.date().isoformat()
            res = ReportingInformation(date_final, ', '.join(set(reporters)))
        except Exception:
            logger.exception('Could not parse date for %s, %s, %s',
                             self.article, self.descriptor, self.country_code
                             )

            res = ReportingInformation(date[0], ', '.join(set(reporters)))

        return res


class ReportData2012Secondary(ReportData2012):
    """ Class implementation for Article 8 ESA
    """

    implements(IReportDataViewSecondary)

    descriptor = 'Not linked'
    country_region_code = 'No region'

    @property
    def report_title(self):
        title = "Member State report / {} / {} / 2012".format(
            self.article,
            self.country_name,
        )

        return title

    def _get_reporting_info_art_34(self, root):
        reporter = [root.attrib['Organisation']]
        date = [root.attrib['ReportingDate']]

        return reporter, date

    def _get_reporting_info_art_7(self, root):
        default = u'Not available'
        reporter = [root.attrib.get('GeneratedBy', default)]
        date = [root.attrib.get('CreationDate', default)]

        return reporter, date

    def _get_reporting_info(self, root):
        impl = {
            'Art3': self._get_reporting_info_art_34,
            'Art4': self._get_reporting_info_art_34,
            'Art7': self._get_reporting_info_art_7,
            'Art8esa': self._get_reporting_info_art_34,
        }

        return impl[self.article](root)

    def data_to_xls_art7(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        for region, wdata, report_header in data:
            if not wdata:
                continue

            # add worksheet with report header data
            worksheet = workbook.add_worksheet(
                u'Report header for {}'.format(region)
            )

            for i, (rtitle, rdata) in enumerate(report_header.items()):
                rtitle = rtitle.title().replace('_', ' ')

                if isinstance(rdata, tuple):
                    rdata = rdata[1]

                worksheet.write(i, 0, rtitle)
                worksheet.write(i, 1, rdata)

            worksheet = workbook.add_worksheet(
                u'Report data for {}'.format(region)
            )

            for i, row in enumerate(wdata['Report data']):
                row_label = row[0]
                worksheet.write(i, 0, row_label)
                row_values = row[1]

                for j, v in enumerate(row_values):
                    worksheet.write(i, j + 1, v)

        workbook.close()
        out.seek(0)

        return out

    def download_art7(self, report_data):
        xlsio = self.data_to_xls_art7(report_data)

        return self._set_response_header(xlsio)

    def __call__(self):
        """ Article 3 & 4 reports are separated per regions
            This means we can have more than one report xml for a country
            one for each region

            Merge the data from each region, and display it in one table
        """

        # we treat Art 3 & 4 different because of multiple report files

        if self.article not in ('Art3', 'Art4'):
            return super(ReportData2012Secondary, self).__call__()

        template = Template('pt/report-data-view-art34.pt')
        report_header_template = Template('pt/report-data-header-art34.pt')
        regions = get_regions_for_country(self.country_code)

        filenames = [
            (r[0], r[1], get_report_filename('2012', self.country_code, r[0],
                                             self.article, self.descriptor))

            for r in regions
        ]

        filenames = sorted(filenames,
                           key=lambda i: ordered_regions_sortkey(i[0]))

        trans_edit_html = self.translate_view()()

        reports = []
        report_data = []

        for region, region_name, filename in filenames:
            if not filename:
                continue

            url = get_report_file_url(filename)
            source_file = (filename, url + '/manage_document')
            factsheet = get_factsheet_url(url)

            view = Article34(self, self.request, self.country_code,
                             region, self.descriptor, self.article,
                             self.muids, filename)

            rendered_view = view()

            rep_info = self.get_reporting_information(filename=filename)
            report_header_data = self.get_report_header_data(
                rep_info.reporters, source_file, factsheet,
                rep_info.report_date
            )
            report_header = report_header_template(self, self.request,
                                                   region=region_name,
                                                   **report_header_data)
            reports.append(report_header + rendered_view + trans_edit_html)

            report_data.append((region, serialize_rows(view.rows),
                                report_header_data))

        self.reports = reports

        if 'download' in self.request.form:

            return self.download_art7(report_data)

        return template(self, self.request)


class ReportData2012Like2018(ReportData2012):
    """ An alternative implementation, mapping data like the 2018 views
    """

    cache_key_extra = 'like2018'

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


class ReportData2018(BaseView):
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
        'Art3': "To be completed...",
        'Art4': "To be completed...",
        'Art7': "To be completed..."
    }

    @property
    def help_text(self):
        return self.help_texts[self.article]

    Art8 = Template('pt/report-data-multiple-muid.pt')
    Art9 = Template('pt/report-data-multiple-muid.pt')
    Art10 = Template('pt/report-data-multiple-muid.pt')
    # Art9 = Template('pt/report-data-single-muid.pt')

    subform = None      # used for the snapshot selection form

    @property
    def all_descriptor_ids(self):
        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        all_ids = set(all_ids)

        return all_ids

    def _get_order_cols_Art8(self, descr):
        descr = descr.split('.')[0]
        criteria_priority = ('MarineReportingUnit', 'GESComponent', 'Criteria',
                             'Feature', 'Element', 'Element2', 'Element2Code',
                             'IntegrationRuleTypeParameter')

        default = ('MarineReportingUnit', 'GESComponent', 'Feature',
                   'Element', 'Element2', 'Element2Code', 'Criteria',
                   'IntegrationRuleTypeParameter',)

        order_by = {
            'D2': criteria_priority,
            'D4': criteria_priority,
            'D5': ('MarineReportingUnit', 'GESComponent', 'Feature',
                   'Criteria', 'Element', 'Element2', 'Element2Code',
                   'IntegrationRuleTypeParameter',
                   ),
            'D6': default,
            'D7': criteria_priority,
            'D8': criteria_priority,
            'D11': criteria_priority,
            'default': default
        }

        return order_by.get(descr, order_by['default'])

    def _get_order_cols_Art10(self):
        order = ('TargetCode', 'Features', 'Element')

        return order

    def get_data_from_view_Art8(self):
        sess = db.session()
        t = sql2018.t_V_ART8_GES_2018

        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        # muids = [x.id for x in self.muids]
        conditions = [
            t.c.CountryCode == self.country_code,
            # t.c.Region == self.country_region_code,
            # t.c.MarineReportingUnit.in_(muids),     #
            t.c.GESComponent.in_(all_ids)
        ]

        # Handle the case of Romania that submitted duplicate data,
        # where Element is empty, but Criteria has data
        if self.country_code != 'RO':
            conditions.append(
                or_(t.c.Element.isnot(None),
                    t.c.Criteria.isnot(None))
            )
        else:
            conditions.append(
                t.c.Element.isnot(None)
            )

        if self.country_code != 'DK':
            conditions.insert(
                1, t.c.Region == self.country_region_code
            )
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(1,
                              or_(t.c.Region == 'NotReported',
                                  t.c.Region == self.country_region_code
                                  )
                              )

        orderby = [
            getattr(t.c, x) for x in self._get_order_cols_Art8(self.descriptor)
        ]

        # groupby IndicatorCode
        q = sess\
            .query(t)\
            .filter(*conditions)\
            .order_by(*orderby)\
            .distinct()

        # For the following countries filter data by features
        # for other countries return all data
        country_filters = ('BE', )

        if self.country_code not in country_filters:
            return q

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        for row in q:
            if not self.descriptor.startswith('D1.'):
                out.append(row)
                continue

            feats = set((row.Feature, ))

            if feats.intersection(ok_features):
                out.append(row)

        return out

    def get_data_from_view_Art10(self):
        t = sql2018.t_V_ART10_Targets_2018

        conditions = [t.c.CountryCode == self.country_code]

        if self.country_code != 'DK':
            conditions.insert(
                1, t.c.Region == self.country_region_code
            )
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(1,
                              or_(t.c.Region == 'NotReported',
                                  t.c.Region == self.country_region_code
                                  )
                              )

        count, res = db.get_all_records_ordered(
            t,
            self._get_order_cols_Art10(),
            *conditions
        )

        out = []

        # GESComponents contains multiple values separated by comma
        # filter rows by splitting GESComponents
        for row in res:
            ges_comps = getattr(row, 'GESComponents', ())
            ges_comps = set([g.strip() for g in ges_comps.split(',')])

            if ges_comps.intersection(self.all_descriptor_ids):
                out.append(row)

        if not self.descriptor.startswith('D1.'):
            return out

        # conditions = []
        # params = get_parameters(self.descriptor)
        # p_codes = [p.name for p in params]
        # conditions.append(t.c.Parameter.in_(p_codes))

        # Filtering results based on FeaturesSmart and other conditions
        # I don't think this code should be kept. Probably the edge case should
        # be documented. It makes it fragile and dependent on correct
        # definitions in FeaturesSmart. I think it's trying to avoid showing
        # too many results when the GESComponent has been incorectly reported
        # on the <Target> records.
        ok_features = set([f.name for f in get_features(self.descriptor)])
        out_filtered = []

        for row in out:
            # Because some Features are missing from FeaturesSmart
            # we consider 'D1' descriptor valid for all 'D1.x'
            # and we keep the data if 'D1' is present in the GESComponents
            # countries_filter = for these countries DO NOT filter by features
            ges_comps = getattr(row, 'GESComponents', ())
            countries_filter = ()  # ('RO', 'DK')
            if 'D1' in ges_comps and self.country_code in countries_filter:
                out_filtered.append(row)
                continue

            feats = set(row.Features.split(','))

            if feats.intersection(ok_features):
                out_filtered.append(row)

        return out_filtered

    def get_data_from_view_Art9(self):

        t = sql2018.t_V_ART9_GES_2018

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        conditions = [
            t.c.CountryCode == self.country_code,
            t.c.GESComponent.in_(all_ids)
        ]

        if self.country_code != 'DK':
            conditions.insert(
                1, or_(t.c.Region == self.country_region_code,
                       t.c.Region.is_(None))
            )
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(1,
                              or_(t.c.Region == 'NotReported',
                                  t.c.Region == self.country_region_code,
                                  t.c.Region.is_(None)
                                  )
                              )

        count, q = db.get_all_records_ordered(
            t,
            ('GESComponent', ),
            *conditions
        )

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        # There are cases when justification for delay is reported
        # for a ges component. In these cases region, mru, features and
        # other fields are empty. Justification for delay should be showed
        # for all regions, mrus
        for row in q:
            if not row.Features:
                out.append(row)
                continue

            if not self.descriptor.startswith('D1.'):
                out.append(row)
                continue

            feats = set(row.Features.split(','))

            if feats.intersection(ok_features):
                out.append(row)

        return out

    def get_data_from_view(self, article):
        data = getattr(self, 'get_data_from_view_' + article)()

        return data

    @db.use_db_session('2018')
    @timeit
    def get_data_from_db(self):
        data = self.get_data_from_view(self.article)
        data = [Proxy2018(row, self) for row in data]

        if self.request.form.get('split-mru') and (len(data) > 2000):
            if self.muids:
                if getattr(self, 'focus_muid', None) is None:
                    self.focus_muid = self.muids[0].name

                self.focus_muids = self._get_muids_from_data(data)

        if self.article == 'Art8':
            order = self._get_order_cols_Art8(self.descriptor)
            data = consolidate_singlevalue_to_list(data,
                                                   'IndicatorCode',
                                                   order,
                                                   )

            data_by_mru = group_by_mru(data)

        if self.article == 'Art10':
            # data_by_mru = group_by_mru(data)
            order = self._get_order_cols_Art10()
            data_by_mru = consolidate_singlevalue_to_list(
                data, 'MarineReportingUnit', order
            )
            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                data_by_mru = {}

        if self.article == 'Art9':
            # data_by_mru = consolidate_date_by_mru(data_by_mru)
            data_by_mru = consolidate_singlevalue_to_list(
                data, 'MarineReportingUnit'
            )
            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                data_by_mru = {}
            insert_missing_criterions(data_by_mru, self.descriptor_obj)

        res = []

        fields = get_report_definition(self.article).get_fields()

        for mru, rows in data_by_mru.items():
            _rows = items_to_rows(rows, fields)

            res.append((mru, _rows))

        # resort the results by marine reporting unit
        res_sorted = sorted(
            res, key=lambda r: natural_sort_key(r[0].__repr__()))

        return res_sorted

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

        if hasattr(self, 'focus_muid'):
            # filter the data based on selected muid
            # this is used to optmize display of really long data
            data = [t for t in data if t[0].name == self.focus_muid]

        if date_selected:
            filtered = [x for x in snapshots if x[0] == date_selected]

            if filtered:
                date, data = filtered[0]
            else:
                raise ValueError("Snapshot doesn't exist at this date")

        return data

    def _get_muids_from_data(self, data):
        muids = set()
        for row in data:
            o = getattr(row, '__o')
            muid = o.MarineReportingUnit
            muids.add(muid)

        return list(sorted(muids))

    # def get_muids_from_data(self, data):
    #     # TODO: this shouldn't exist anymore
    #     if isinstance(data[0][0], (unicode, str)):
    #         all_muids = sorted(set([x[0] for x in data]))
    #
    #         return ', '.join(all_muids)
    #
    #     all_muids = [x[0] for x in data]
    #     seen = []
    #     muids = []
    #
    #     for muid in all_muids:
    #         name = muid.name
    #
    #         if name in seen:
    #             continue
    #
    #         seen.append(name)
    #         muids.append(muid)
    #
    #     return ItemList(rows=muids)

    @db.use_db_session('2018')
    @timeit
    def get_report_metadata(self):
        """ Returns metadata about the reported information
        """
        t = sql2018.ReportedInformation
        schemas = {
            'Art8': 'ART8_GES',
            'Art9': 'ART9_GES',
            'Art10': 'ART10_Targets',
        }
        count, item = db.get_item_by_conditions(
            t,
            'ReportingDate',
            t.CountryCode == self.country_code,
            t.Schema == schemas[self.article],
            reverse=True,
        )
        return item

    @property
    def report_header_title(self):
        title = "Member State report / {} / 2018 / {} / {} / {}".format(
            self.article,
            self.descriptor_title,
            self.country_name,
            self.country_region_name,
        )

        return title

    def get_report_header(self):
        report = self.get_report_metadata()

        link = report_by = report_date = None
        if report:
            link = report.ReportedFileLink
            link = (link.rsplit('/', 1)[1], link)
            report_by = report.ContactOrganisation
            report_date = report.ReportingDate

        report_header = self.report_header_template(
            title=self.report_header_title,
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by=report_by,
            source_file=link,
            report_due='2018-10-15',
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=False
        )

        return report_header

    @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2018 report data: %s %s %s %s",
                    self.country_code, self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()
        report_header = self.get_report_header()
        template = self.get_template(self.article)

        return template(data=data, report_header=report_header)

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        for index, (wtitle, wdata) in enumerate(data):
            _wtitle = '{}_{}'.format(index + 1, unicode(wtitle)[:28])

            worksheet = workbook.add_worksheet(_wtitle)

            for i, (row_label, row_values) in enumerate(wdata):
                worksheet.write(i, 0, row_label.title)

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

    def auto_translate(self, data=None):
        if not data:
            data = self.get_report_data()

        # report_def = REPORT_DEFS[self.year][self.article]
        # translatables = report_def.get_translatable_fields()
        translatables = self.TRANSLATABLES
        seen = set()

        for table in data:
            muid, table_data = table

            for row in table_data:
                field, cells = row
                if field.name in translatables:
                    for value in cells:
                        if value not in seen:
                            retrieve_translation(self.country_code, value)
                            seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        url = self.context.absolute_url() + '/@@view-report-data-2018'
        return self.request.response.redirect(url)

    def get_template(self, article):
        template = getattr(self, article, None)

        return template

    @timeit
    def __call__(self):

        # allow focusing on a single muid if the data is too big
        if 'focus_muid' in self.request.form:
            self.focus_muid = self.request.form['focus_muid'].strip()
        # self.focus_muid = 'BAL-AS-EE-ICES_SD_29'

        self.content = ''
        template = self.get_template(self.article)

        if not template:
            return self.index()

        self.subform = self.get_form()

        if ('download' in self.request.form):  # and report_data
            return self.download()

        if 'translate' in self.request.form and self.can_view_assessment_data:
            return self.auto_translate()

        trans_edit_html = self.translate_view()()

        print "will render report"
        report_html = self.render_reportdata()
        self.report_html = report_html + trans_edit_html

        @timeit
        def render_html():
            return self.index()

        return render_html()

    def get_form(self):

        if not self.subform:
            form = SnapshotSelectForm(self, self.request)
            self.subform = form

        return self.subform


class ReportData2018Secondary(ReportData2018):
    implements(IReportDataViewSecondary)

    descriptor = 'Not linked'
    country_region_code = 'No region'

    Art3 = Template('pt/report-data-secondary-2018.pt')
    Art4 = Template('pt/report-data-secondary-2018.pt')
    Art7 = Template('pt/report-data-secondary-2018.pt')

    def article_name(self):
        get_art_name = super(ReportData2018Secondary, self).article_name

        if self.article not in ('Art3', 'Art4'):
            return get_art_name()

        art_name = '{} & {}'.format(get_art_name('Art3'),
                                    get_art_name('Art4'))

        return art_name

    def get_previus_url(self, grouped_urls, url):
        for region, group in grouped_urls.items():
            # find the right group for our url
            if url not in group:
                continue

            # if our url is the last from its group, it does not have previous
            # file
            if group[-1] == url:
                return None

            url_index = group.index(url)

            return group[url_index + 1]

    def get_report_metadata_from_view(self, view, filename):
        fileurl = get_report_file_url(filename)
        root = view.get_report_file_root(filename)

        reporters = date = None
        try:
            reporters = root.attrib['GeneratedBy']
            date = root.attrib['CreationDate']
        except:
            pass

        metadata = ReportingInformation2018(
            fileurl,
            reporters,
            date
        )

        return metadata

    @property
    def report_header_title(self):
        article = self.article
        if self.article in ('Art3', 'Art4'):
            article = 'Art3-4'

        title = "Member State report: {} / {}".format(
            self.country_name,
            article,
        )

        return title

    def get_template(self, article):
        article = article.replace('-', '')
        template = getattr(self, article, None)

        return template

    def get_implementation_view(self, filename, prev_filename):
        """ In other articles (8, 9, 10) for 2018 year,
        we get the data from the DB (MSFD2018_production)

        Here instead we will get the data from the report xml from CDR
        by initializing and calling the view's class to setup the data
        """

        klass = {'Art7': Article7_2018,
                 'Art3': Article34_2018,
                 'Art4': Article34_2018}.get(self.article)

        init_args = [self, self.request, self.country_code,
                     self.country_region_code, self.descriptor, self.article,
                     self.muids, filename]

        if self.article in ['Art3', 'Art4'] and prev_filename:
            prev_view = klass(
                self, self.request, self.country_code, self.country_region_code,
                self.descriptor, self.article, self.muids, prev_filename
            )
            prev_view.setup_data()
            previous_mrus = prev_view.available_mrus
            init_args.append(previous_mrus)

        view = klass(*init_args)
        view.setup_data()

        return view

    def auto_translate(self):
        self.render_reportdata()
        seen = set()

        all_translatables = (self.translatable_data +
                             self.translatable_extra_data)

        for value in all_translatables:
            if not value:
                continue

            if not isinstance(value, basestring):
                continue

            if value not in seen:
                retrieve_translation(self.country_code, value)
                seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        url = self.context.absolute_url() + '/@@view-report-data-2018'
        return self.request.response.redirect(url)


    def get_translatable_data(self, view):
        res = []

        for row in view.rows:
            field_name = row.title

            if field_name not in self.TRANSLATABLES:
                continue

            res.extend(row.raw_values)

        return set(res)

    def render_reportdata(self):
        """
        1. Get all reported files under Article 7 or 3/4
        2. Render the data separately for all files
        3. Concat the rendered htmls into a single

        :return: rendered html
        """

        translatable_extra_data = []
        translatable_data = []

        template = self.get_template(self.article)
        urls = get_all_report_filenames(self.country_code, self.article)

        rendered_results = []

        # identify order of files, grouped by region. If multiple regions are
        # reported in a file, then just sort them by envelope release date.
        # once sorted, create view for each file. Each view can potentially get
        # a reference to the previous file data.

        grouped_urls = defaultdict(list)
        for url in urls:
            view = self.get_implementation_view(url, None)
            regions = "-".join(view.available_regions)
            grouped_urls[regions].append(url)

        for (index, url) in enumerate(urls):
            prev_url = self.get_previus_url(grouped_urls, url)

            # For article 3/4 2018, the data from previous "version" of the
            # file should also be sent. Then it will be possible to identify
            # which MRUs have been added/removed
            view = self.get_implementation_view(url, prev_url)
            translatable_extra_data.extend(view.translatable_extra_data)
            translatable_data.extend(self.get_translatable_data(view))

            report = self.get_report_metadata_from_view(view, url)
            # Report Header
            report_by = None
            report_date = get_envelope_release_date(url)

            if report:
                report_by = report.ContactOrganisation
                # report_date = report.ReportingDate

            res = []
            source_file = (url.rsplit('/', 1)[-1], url + '/manage_document')
            factsheet = get_factsheet_url(url)

            view()      # updates the view
            data = [Proxy2018(row, self) for row in view.cols]

            if self.article == 'Art7':
                data_by_mru = group_by_mru(data)
            else:
                data_by_mru = {'no mru': data}

            fields = get_report_definition(self.article).get_fields()

            for mru, rows in data_by_mru.items():
                _rows = items_to_rows(rows, fields)

                res.append((mru, _rows))

            report_header = self.report_header_template(
                title=(index == 0 and self.report_header_title or ''),
                factsheet=factsheet,
                # TODO: find out how to get info about who reported
                report_by=report_by,
                source_file=source_file,
                report_due=None,
                report_date=report_date.date(),
                help_text=self.help_text,
                multiple_source_files=False,
                show_navigation=index == 0,
            )

            rendered_results.append(template(data=res,
                                             report_header=report_header,
                                             show_navigation=False))

        self.translatable_extra_data = translatable_extra_data
        self.translatable_data = translatable_data

        res = "<hr/>".join(rendered_results)
        return res or "No data found"
