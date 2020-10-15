import logging
from io import BytesIO

from sqlalchemy import or_

from zope.interface import implements

import xlsxwriter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.compliance.interfaces import IRegionalReportDataView
from wise.msfd.gescomponents import get_features, get_parameters
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import ItemList, timeit

from ..nationaldescriptors.utils import consolidate_singlevalue_to_list
from .a8 import RegDescA82012, RegDescA82018Row
from .a9 import RegDescA92012, RegDescA92018Row
from .a10 import RegDescA102012, RegDescA102018Row
from .base import BaseRegComplianceView
from .data import get_report_definition
from .proxy import Proxy2018

logger = logging.getLogger('wise.msfd')


class RegReportData2012(BaseRegComplianceView):
    implements(IRegionalReportDataView)

    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"
    cache_key_extra = 'reg-desc-2012'

    Art8 = RegDescA82012
    Art9 = RegDescA92012
    Art10 = RegDescA102012

    @db.use_db_session('2012')
    def get_report_data(self):
        impl_class = getattr(self, self.article)
        result = impl_class(self, self.request)

        return result.allrows

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = self.country_region_code
        worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

        row_index = 0

        for compoundrow in data:
            title = compoundrow.field.title
            rows = compoundrow.rows

            for row in rows:
                sub_title, values = row
                worksheet.write(row_index, 0, title)
                worksheet.write(row_index, 1, unicode(sub_title or ''))

                for j, value in enumerate(values):
                    worksheet.write(row_index, j + 2, unicode(value or ''))

                row_index += 1

        workbook.close()
        out.seek(0)

        return out

    def download(self):
        xlsdata = self.get_report_data()

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["RegionalDescriptors",
                          self.country_region_code,
                          self.descriptor,
                          self.article,
                          self.year])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    # @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2012 report data: %s %s %s",
                    self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()

        report_header = self.report_header_template(
            title="Member State report / {} / 2012 / {} / {}".format(
                self.article,
                self.descriptor_title,
                self.country_region_name,
            ),
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by='Member state',
            report_due='2012-10-15',
            help_text=self.help_text,
            use_translation=False
        )

        template = self.template

        return template(data=data, report_header=report_header)

    def __call__(self):
        if 'download' in self.request.form:
            return self.download()

        report_html = self.render_reportdata()
        self.report_html = report_html

        @timeit
        def render_html():
            return self.index()

        return render_html()


class RegReportData2018(BaseRegComplianceView):
    implements(IRegionalReportDataView)

    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2018"
    cache_key_extra = "reg-desc-2018"

    # Art8 = ViewPageTemplateFile('pt/report-data.pt')
    # Art9 = ViewPageTemplateFile('pt/report-data.pt')
    # Art10 = ViewPageTemplateFile('pt/report-data.pt')

    Art8 = RegDescA82018Row
    Art9 = RegDescA92018Row
    Art10 = RegDescA102018Row

    @property
    def all_descriptor_ids(self):
        all_ids = list(self.descriptor_obj.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        all_ids = set(all_ids)

        return all_ids

    @property
    def get_data_from_view_Art9(self):
        t = sql2018.t_V_ART9_GES_2018

        count, q = db.get_all_records_ordered(
            t,
            ('GESComponent',),
            or_(t.c.Region.in_(self._countryregion_folder._subregions),
                t.c.Region.is_(None)),
            t.c.GESComponent.in_(self.all_descriptor_ids),
        )

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

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

    @property
    def get_data_from_view_Art8(self):
        sess = db.session()
        t = sql2018.t_V_ART8_GES_2018

        conditions = [
            t.c.Region.in_(self._countryregion_folder._subregions),
            t.c.GESComponent.in_(self.all_descriptor_ids),
            or_(t.c.Element.isnot(None),
                t.c.Criteria.isnot(None)),
        ]

        # groupby IndicatorCode
        q = sess\
            .query(t)\
            .filter(*conditions)\
            .distinct()

        res = [row for row in q]

        return res

    @property
    def get_data_from_view_Art10(self):
        t = sql2018.t_V_ART10_Targets_2018

        # TODO check conditions for other countries beside NL
        # conditions = [t.c.GESComponents.in_(all_ids)]

        count, res = db.get_all_records_ordered(
            t,
            ('Features', 'TargetCode', 'Element'),
            t.c.Region.in_(self._countryregion_folder._subregions),
            # *conditions
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

        conditions = []
        params = get_parameters(self.descriptor)
        p_codes = [p.name for p in params]
        conditions.append(t.c.Parameter.in_(p_codes))
        ok_features = set([f.name for f in get_features(self.descriptor)])
        out_filtered = []

        for row in out:
            feats = set(row.Features.split(','))

            if feats.intersection(ok_features):
                out_filtered.append(row)

        return out_filtered

    @db.use_db_session('2018')
    def get_report_data(self):
        # TODO check if data is filtered by features for D1
        db_data = getattr(self, 'get_data_from_view_' + self.article, None)
        db_data = [Proxy2018(row, self) for row in db_data]

        if self.article == 'Art8':
            db_data = consolidate_singlevalue_to_list(db_data, 'IndicatorCode')

        countries = self.available_countries
        regions = self._countryregion_folder._subregions
        descriptor_obj = self.descriptor_obj

        fields = get_report_definition('2018', self.article).get_fields()

        impl_class = getattr(self, self.article)
        result = []

        for field in fields:
            row_class = impl_class(self, self.request, db_data, descriptor_obj,
                                   regions, countries, field)
            field_data_method = getattr(row_class, field.getrowdata, None)

            if not field_data_method:
                continue

            result.append(field_data_method())

        # result.extend(self.get_adequacy_assessment_data())

        return result

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = self.country_region_code
        worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

        row_index = 0

        for compoundrow in data:
            title = compoundrow.field.title
            field_name = compoundrow.field.name
            rows = compoundrow.rows

            for row in rows:
                # multirow
                if len(row) == 3:
                    title, sub_title, values = row
                # compoundrow
                else:
                    sub_title, values = row

                worksheet.write(row_index, 0, title)
                worksheet.write(row_index, 1, unicode(sub_title or ''))

                for j, value in enumerate(values):
                    if isinstance(value, ItemList):
                        value = "\n".join(value.rows)

                    # if 'value' is a list/tuple meaning it contains both the
                    # original and the translated value, we need
                    # the translated value
                    if hasattr(value, '__iter__'):
                        value = value[0].replace('<br />', '\n')

                    try:
                        unicode_value = unicode(value)
                    except:
                        unicode_value = unicode(value.decode('utf-8'))

                    worksheet.write(row_index, j + 2, unicode_value or '')

                row_index += 1

                if field_name in self.TRANSLATABLES:
                    worksheet.write(row_index, 0, title + ' [Translation]')
                    worksheet.write(row_index, 1, unicode(sub_title or ''))

                    for j, value in enumerate(values):
                        # if 'value' is a list/tuple meaning it contains both
                        # the # original and the translated value, we need
                        # the translated value
                        if hasattr(value, '__iter__'):
                            value = value[1].replace('<br />', '\n')

                        try:
                            unicode_value = unicode(value)
                        except:
                            unicode_value = unicode(value.decode('utf-8'))

                        worksheet.write(row_index, j + 2, unicode_value or '')

                    row_index += 1

        workbook.close()
        out.seek(0)

        return out

    def download(self):
        xlsdata = self.get_report_data()

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["RegionalDescriptors",
                          self.country_region_code,
                          self.descriptor,
                          self.article,
                          self.year])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def auto_translate(self):
        data = self.get_report_data()
        translatables = self.TRANSLATABLES
        seen = set()

        for compoundrow in data:
            rows = compoundrow.rows

            for row in rows:
                sub_title, values = row

                if compoundrow.field.name in translatables:
                    for indx, value in enumerate(values):
                        if not value:
                            continue

                        if value not in seen:
                            country_code = self.available_countries[indx][0]
                            retrieve_translation(country_code, value)
                            seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        url = self.context.absolute_url() + '/@@view-report-data-2018'

        return self.request.response.redirect(url)

    # @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2018 report data: %s %s %s",
                    self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()

        report_header = self.report_header_template(
            title="Member State report / {} / 2018 / {} / {}".format(
                self.article,
                self.descriptor_title,
                self.country_region_name,
            ),
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by='Member state',
            report_due='2018-10-15',
            help_text=self.help_text,
            use_translation=True
        )

        # template = getattr(self, self.article, None)
        template = self.template

        return template(data=data, report_header=report_header)

    def __call__(self):
        if 'download' in self.request.form:
            return self.download()

        if 'translate' in self.request.form:
            return self.auto_translate()

        report_html = self.render_reportdata()
        trans_edit_html = self.translate_view()()
        self.report_html = report_html + trans_edit_html

        @timeit
        def render_html():
            return self.index()

        return render_html()
