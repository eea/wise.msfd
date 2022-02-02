
from __future__ import absolute_import
from collections import OrderedDict
import logging
import re
from io import BytesIO

from sqlalchemy import or_

from zope.interface import implementer, implementer_only, implements, implementsOnly

import xlsxwriter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.compliance.base import is_row_relevant_for_descriptor
from wise.msfd.compliance.interfaces import (IRegionalReportDataView,
                                             IRegReportDataViewOverview)
from wise.msfd.compliance.utils import DummyReportField
from wise.msfd.data import get_report_filename
from wise.msfd.gescomponents import (FEATURES_ORDER, get_features,
                                     get_parameters)
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (ItemLabel, ItemList, fixedorder_sortkey,
                             items_to_rows, timeit)

from ..nationaldescriptors.reportdata import (ORDER_COLS_ART11, ReportData2014,
                                              ReportData2020)
from ..nationaldescriptors.utils import (consolidate_singlevalue_to_list,
                                         group_multiple_fields)
from .a8 import RegDescA82012, RegDescA82018Row
from .a9 import RegDescA92012, RegDescA92018Row
from .a10 import RegDescA102012, RegDescA102018Row
from .a11 import RegArticle11
from .base import BaseRegComplianceView
from .data import get_report_definition
from .proxy import Proxy2018
import six

logger = logging.getLogger('wise.msfd')


href_regex = re.compile(r'(?<=href=\")[^\"]+(?=\")')


@implementer(IRegionalReportDataView)
class RegReportData2012(BaseRegComplianceView):
    # implements(IRegionalReportDataView)

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
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])

        row_index = 0

        for compoundrow in data:
            title = compoundrow.field.title
            rows = compoundrow.rows

            for row in rows:
                sub_title, values = row
                worksheet.write(row_index, 0, title)
                worksheet.write(row_index, 1, six.text_type(sub_title or ''))

                for j, value in enumerate(values):
                    worksheet.write(row_index, j + 2, six.text_type(value or ''))

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


@implementer(IRegionalReportDataView)
class RegReportData2014(ReportData2014, BaseRegComplianceView):
    # implements(IRegionalReportDataView)

    @property
    def article_implementations(self):
        res = {
            'Art11': RegArticle11,
        }

        return res

    @property
    def muids(self):
        return []

    @property
    def regions(self):
        return self._countryregion_folder._subregions

    @property
    def country_code(self):
        return self.country_region_code

    @property
    def report_title(self):
        title = "Member State report / {} / {} / {} / {}".format(
            self.article,
            self.report_year,
            self.descriptor_title,
            self.country_region_name,
        )

        return title

    def translate_value(self, fieldname, value, source_lang):
        t = ReportData2014.translate_value(self, fieldname, value, source_lang)

        return t

    def get_report_definition(self):
        rep_def = get_report_definition(self.year, self.article).get_fields()

        filtered_rep_def = [f for f in rep_def if f.section != 'empty']

        return filtered_rep_def

    def get_report_header_data(self, report_by, source_file, factsheet,
                               report_date, multiple_source_files=False):
        data = OrderedDict(
            title=self.report_title,
            report_by=report_by,
            source_file=[],
            factsheet=factsheet,
            report_due=self.report_due,
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=multiple_source_files,
            use_translation=False
        )

        return data

    def get_report_filename(self):
        res = []

        for ccode, cname in self.available_countries:
            filenames = get_report_filename(
                '2014',
                ccode,
                self.country_region_code,
                self.article,
                self.descriptor,
            )

            res.extend(filenames)

        return res

    def filter_filenames_by_region(self, all_filenames):
        """ impossible to filter files by region by only looking
            at the filename """

        return all_filenames

        filenames = []
        subregions = self._countryregion_folder._subregions

        for fileurl in all_filenames:
            for subregion in subregions:
                if 'msfd_mp/env' in 'fileurl':
                    filenames.append(fileurl)
                    continue

                if 'msfd_mp/' + subregion.lower() not in fileurl:
                    import pdb; pdb.set_trace()
                    continue

        return filenames


@implementer(IRegionalReportDataView)
class RegReportData2018(BaseRegComplianceView):
    # implements(IRegionalReportDataView)

    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2018"
    report_due = "2018-10-15"
    report_by = "Member state"
    cache_key_extra = "reg-desc-2018"

    # Art8 = ViewPageTemplateFile('pt/report-data.pt')
    # Art9 = ViewPageTemplateFile('pt/report-data.pt')
    # Art10 = ViewPageTemplateFile('pt/report-data.pt')

    Art8 = RegDescA82018Row
    Art9 = RegDescA92018Row
    Art10 = RegDescA102018Row

    @property
    def report_header_title(self):
        title = "Member State report / {} / 2018 / {} / {}".format(
                self.article,
                self.descriptor_title,
                self.country_region_name,
            )

        return title

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

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out_filtered = []

        blacklist_descriptors = ['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5',
                                 'D1.6', 'D4', 'D6']
        blacklist_descriptors.remove(self.descriptor)
        blacklist_features = []

        for _desc in blacklist_descriptors:
            blacklist_features.extend([
                f.name for f in get_features(_desc)
            ])

        blacklist_features = set(blacklist_features)

        for row in out:
            # Because some Features are missing from FeaturesSmart
            # we consider 'D1' descriptor valid for all 'D1.x'
            # and we keep the data if 'D1' is present in the GESComponents
            # countries_filter = for these countries DO NOT filter by features
            ges_comps = getattr(row, 'GESComponents', ())
            ges_comps = set([g.strip() for g in ges_comps.split(',')])
            countries_nofilter = []  # ('RO', 'DK', 'CY', 'MT')

            if 'D1' in ges_comps and row.CountryCode in countries_nofilter:
                out_filtered.append(row)
                continue

            row_needed = is_row_relevant_for_descriptor(
                row, self.descriptor, ok_features, blacklist_features,
                ges_comps
            )

            if row_needed:
                out_filtered.append(row)

        return out_filtered

    def get_report_definition(self):
        rep_def = get_report_definition(self.year, self.article).get_fields()

        return rep_def

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

        fields = self.get_report_definition()

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
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])

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
                worksheet.write(row_index, 1, six.text_type(sub_title or ''))

                for j, value in enumerate(values):
                    if isinstance(value, ItemList):
                        rows = value.rows

                        # it is 'Member state report' field
                        if rows and isinstance(rows[0], ItemLabel):
                            rows = [
                                "{}: {}".format(
                                    r.name, href_regex.search(r.title).group())
                                for r in rows
                            ]

                        value = "\n".join(rows)

                    # if 'value' is a list/tuple meaning it contains both the
                    # original and the translated value, we need
                    # the translated value
                    if hasattr(value, '__iter__'):
                        value = value[0].replace('<br />', '\n')

                    try:
                        unicode_value = six.text_type(value)
                    except:
                        unicode_value = six.text_type(value.decode('utf-8'))

                    worksheet.write(row_index, j + 2, unicode_value or '')

                row_index += 1

                if field_name in self.TRANSLATABLES:
                    worksheet.write(row_index, 0, title + ' [Translation]')
                    worksheet.write(row_index, 1, six.text_type(sub_title or ''))

                    for j, value in enumerate(values):
                        # if 'value' is a list/tuple meaning it contains both
                        # the # original and the translated value, we need
                        # the translated value
                        if hasattr(value, '__iter__'):
                            value = value[1].replace('<br />', '\n')

                        try:
                            unicode_value = six.text_type(value)
                        except:
                            unicode_value = six.text_type(value.decode('utf-8'))

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

    def get_report_header(self):
        report_header = self.report_header_template(
            title=self.report_header_title,
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by=self.report_by,
            report_due=self.report_due,
            help_text=self.help_text,
            use_translation=True
        )

        return report_header

    # @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2018 report data: %s %s %s",
                    self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()

        report_header = self.get_report_header()

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


@implementer_only(IRegionalReportDataView)
class RegReportData2020(ReportData2020, RegReportData2018):
    # implementsOnly(IRegionalReportDataView)

    report_due = "2020-10-15"
    report_by = None
    section = 'regional-descriptors'
    Art11 = ViewPageTemplateFile('pt/report-data-multiple-muid.pt')

    @property
    def region(self):
        return self._countryregion_folder.id

    @property
    def country_region_code(self):
        """" Needed for caching """
        return self.region

    @property
    def country_code(self):
        """" Needed for caching """

        countries = [c[0] for c in self.available_countries]

        return ','.join(countries)

    @property
    def regions(self):
        """" Needed for caching """
        return [self.region]

    @property
    def report_header_title(self):
        title = "Member State report / {} / {} / {} / {}".format(
            self.article,
            self.report_year,
            self.descriptor_title,
            self.country_region_name,
        )

        return title

    def translate_value(self, fieldname, value, source_lang):
        t = ReportData2020.translate_value(self, fieldname, value, source_lang)

        return t

    def get_report_definition(self):
        rep_def = get_report_definition(self.year, self.article).get_fields()

        return rep_def

    def get_report_header(self):
        return RegReportData2018.get_report_header(self)

    @db.use_db_session('2018')
    @timeit
    def get_data_from_db(self):
        data = self.get_data_from_view(self.article)
        data = [Proxy2018(row, self) for row in data]
        order = ORDER_COLS_ART11

        data_ = consolidate_singlevalue_to_list(
            data, 'Element', order
        )

        grouped_fields = ('Element', 'GESCriteria', 'P_Parameters',
                          'ParameterOther')

        data_by_mru, features = group_multiple_fields(
            data_,
            'Feature',
            grouped_fields,
            order
        )

        if data_by_mru:
            data_by_mru = {"": data_by_mru}
        else:
            data_by_mru = {}

        res = []

        fields = self.get_report_definition()
        feature_field_orig = [a for a in fields if a.title == 'Features'][0]
        f_field_index = fields.index(feature_field_orig)

        feature_fields = [
            DummyReportField(f)
            for f in sorted(features,
                            key=lambda i: fixedorder_sortkey(i.name,
                                                             FEATURES_ORDER))
        ]

        fields_all = (fields[:f_field_index] + feature_fields +
                      fields[f_field_index + len(grouped_fields) + 1:])

        for mru, rows in data_by_mru.items():
            _rows = items_to_rows(rows, fields_all)

            res.append((mru, _rows))

        return res


@implementer_only(IRegReportDataViewOverview)
class RegReportDataOverview2020Art11(RegReportData2020):
    # implementsOnly(IRegReportDataViewOverview)

    is_primary_article = False

    @property
    def descriptor(self):
        return 'Not defined'

    @property
    def article(self):
        return 'Art11'

    def get_report_definition(self):
        article = '{}Overview'.format(self.article)
        rep_def = get_report_definition(self.year, article).get_fields()

        return rep_def

    def get_data_from_view_Art11(self):
        t = sql2018.t_V_ART11_Strategies_Programmes_2020

        conditions = [
            t.c.CountryCode.in_(self.country_code.split(','))
        ]

        count, q = db.get_all_specific_columns(
            [t.c.CountryCode, t.c.ResponsibleCompetentAuthority,
             t.c.ResponsibleOrganisations,
             t.c.RelationshipToCA, t.c.PublicConsultationDates,
             t.c.PublicConsultationSite, t.c.RegionalCooperation],
            *conditions
        )

        return q

    @property
    def report_header_title(self):
        title = "Member State report / Art11 / {} / {} - Overview" \
            .format(self.report_year, self.country_region_name)

        return title
