# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
import logging
from collections import OrderedDict
from io import BytesIO
from six import text_type

from lxml.etree import fromstring
from zope.interface import implementer

import xlsxwriter
from eea.cache import cache
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db
from wise.msfd.base import BaseUtil
from wise.msfd.compliance.interfaces import (
    IReportDataView,
    IReportDataViewSecondary,
    IReportDataViewOverview,
)
from wise.msfd.compliance.nationaldescriptors.data import get_report_definition
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.data import (
    get_factsheet_url,
    get_report_file_url,
    get_report_fileurl_art131418_2016,
    get_report_filename,
    get_xml_report_data,
)
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.translation import get_translated

from .art2012implementations.a7 import Article7
from .art2012implementations.a8 import Article8
from .art2012implementations.a8alternate import Article8Alternate
from .art2012implementations.a8esa import Article8ESA
from .art2012implementations.a9 import Article9, Article9Alternate
from .art2012implementations.a10 import Article10, Article10Alternate
from .art2012implementations.a11 import (
    Article11, Article11Overview, Article11Compare)
from .art2012implementations.a131418 import Article13, Article14, Article18
from .art2012implementations.a34 import Article34
from ..base import BaseView
from .utils import (serialize_rows, get_reportdata_key, date_format,
                    ReportingInformation, NSMAP, FILENAME_FIX)
from .reportdata2018 import ReportData2020

logger = logging.getLogger("wise.msfd")


@implementer(IReportDataView)
class ReportData2012(BaseView, BaseUtil):
    """WIP on compliance tables"""

    year = report_year = "2012"
    section = "national-descriptors"
    report_due = "2012-10-15"
    cache_key_extra = "base"
    is_side_by_side = False

    @property
    def help_text(self):
        klass = self.article_implementations[self.article]

        return klass.help_text

    @property
    def article_implementations(self):
        res = {
            "Art3": Article34,
            "Art4": Article34,
            "Art7": Article7,
            "Art8esa": Article8ESA,
            "Art8": Article8,
            "Art9": Article9,
            "Art10": Article10,
            "Art11": Article11,
            "Art11Overview": Article11Overview,
            "Art13": Article13,
            "Art14": Article14,
            "Art18": Article18,
        }

        return res

    def get_criterias_list(self, descriptor):
        """Get the list of criterias for the specified descriptor

        :param descriptor: 'D5'
        :return: (('D5', 'Eutrophication'),
                  ('5.1.1', 'D5C1'),
                  ('5.2.1', 'D5C2'), ... )

        # TODO: the results here need to be augumented by L_GESComponents
        """

        result = [(descriptor, self.descriptor_label)]

        criterions = get_descriptor(descriptor).criterions

        for crit in criterions:
            for alt in crit.alternatives:
                title = "{} ({}) {}".format(crit._id or "", alt[0], alt[1])
                indicator = alt[0]

                result.append((indicator, title))

        return result

    def get_report_view(self):
        logger.info(
            "Rendering 2012 report for: %s %s %s %s",
            self.country_code,
            self.descriptor,
            self.article,
            ",".join([x.id for x in self.muids]),
        )
        klass = self.article_implementations[self.article]

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
        )

        return view

    def get_report_definition(self):
        rep_def = get_report_definition(self.year, self.article).get_fields()

        if self.is_side_by_side:
            return rep_def

        filtered_fields = [f for f in rep_def if f.section != "empty"]

        return filtered_fields

    def get_report_translatable_fields(self):
        rep_def = get_report_definition(self.year, self.article)

        if not rep_def:
            return []

        return rep_def.get_translatable_fields()

    @cache(get_reportdata_key, dependencies=["translation"])
    def get_report_data(self):
        view = self.get_report_view()
        rendered_view = view()

        # get cacheable raw values
        rows = serialize_rows(view.rows)

        return rendered_view, rows

    def get_report_header_data(
        self,
        report_by,
        source_file,
        factsheet,
        report_date,
        multiple_source_files=False,
    ):
        data = OrderedDict(
            title=self.report_title,
            report_by=report_by,
            source_file=source_file,
            factsheet=factsheet,
            report_due=self.report_due,
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=multiple_source_files,
            use_translation=True,
        )

        return data

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file
        filename = get_report_filename(
            self.year,
            self.country_code,
            self.country_region_code,
            art or self.article,
            self.descriptor,
        )

        filename_normalized = filename

        if filename:
            if isinstance(filename, (tuple, list)):
                filename_normalized = [
                    FILENAME_FIX.sub("", fname) for fname in filename
                ]
            else:
                filename_normalized = FILENAME_FIX.sub("", filename)

        return filename_normalized

    @property
    def report_title(self):
        title = "Member State report / {} / {} / {} / {} / {}".format(
            self.article,
            self.report_year,
            self.descriptor_title,
            self.country_name,
            self.country_region_name,
        )

        return title

    def data_to_xls(self, data, report_header):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {"in_memory": True})

        # add worksheet with report header data
        worksheet = workbook.add_worksheet(text_type("Report header"))

        for i, (wtitle, wdata) in enumerate(report_header.items()):
            wtitle = wtitle.title().replace("_", " ")

            if isinstance(wdata, (list, tuple)):
                if report_header.get("multiple_source_files", False):
                    wdata = "\n".join([x[1] for x in wdata])
                else:
                    wdata = wdata[1]

            worksheet.write(i, 0, wtitle)
            worksheet.write(i, 1, wdata)

        for wtitle, wdata in data.items():  # add worksheet(s) with report data
            if not wdata:
                continue

            worksheet = workbook.add_worksheet(text_type(wtitle)[:30])

            for i, row in enumerate(wdata):
                row_label = row[0]
                worksheet.write(i, 0, row_label)
                row_values = row[1]

                for j, v in enumerate(row_values):
                    try:
                        transl = get_translated(v, self.country_code) or v
                        worksheet.write(i, j + 1, transl)
                    except:
                        if hasattr(v, "rows") and v.rows:
                            try:
                                v_rows = [text_type(x) for x in v.rows]
                                worksheet.write(i, j + 1, "#".join(v_rows))
                                continue
                            except:
                                import pdb

                                pdb.set_trace()

                        worksheet.write(i, j + 1, "")

        workbook.close()
        out.seek(0)

        return out

    def _set_response_header(self, xlsio):
        sh = self.request.response.setHeader

        sh(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet",
        )
        fname = "-".join(
            [self.country_code, self.country_region_code,
                self.article, self.descriptor]
        )
        sh("Content-Disposition", "attachment; filename=%s.xlsx" % fname)

        return xlsio.read()

    def download(self, report_data, report_header):
        xlsio = self.data_to_xls(report_data, report_header)

        return self._set_response_header(xlsio)

    @db.use_db_session("2012")
    def __call__(self):
        # if self.descriptor.startswith('D1.'):       # map to old descriptor
        #     # self._descriptor = 'D1'               # this hardcodes D1.x
        #                                             # descriptors to D1
        #     assert self.descriptor == 'D1'

        if "translate" in self.request.form:
            report_view = self.get_report_view()
            report_view.auto_translate()

            messages = IStatusMessage(self.request)
            messages.add(
                "Auto-translation initiated, please refresh " "in a couple of minutes",
                type="info",
            )

        print(("Will render report for: %s" % self.article))
        self.filename = filename = self.get_report_filename()
        factsheet = None

        source_file = ("File not found", None)
        multiple_source_files = False

        if filename:
            if isinstance(filename, (tuple, list)):
                multiple_source_files = True
                try:
                    source_file = [
                        (
                            f,
                            get_report_file_url(f, self.country_code)
                            + "/manage_document",
                        )
                        for f in filename
                    ]
                except:
                    logger.exception("Error in getting HTML Factsheet URL)")
            else:
                url = get_report_file_url(filename, self.country_code)
                if url:
                    try:
                        factsheet = get_factsheet_url(url)
                    except Exception:
                        logger.exception(
                            "Error in getting HTML Factsheet URL %s", url)
                else:
                    logger.warning(
                        "No factsheet url, filename is: %r", filename)

                source_file = (filename, url + "/manage_document")

        rep_info = self.get_reporting_information()

        report_header_data = self.get_report_header_data(
            rep_info.reporters,
            source_file,
            factsheet,
            rep_info.report_date,
            multiple_source_files,
        )
        report_header = self.report_header_template(**report_header_data)
        try:
            report_data, report_data_rows = self.get_report_data()
        except:
            report_data, report_data_rows = "Error in rendering report", []
        trans_edit_html = self.translate_view()()
        self.report_html = report_header + report_data + trans_edit_html

        if "download" in self.request.form:

            return self.download(report_data_rows, report_header_data)

        return self.index()

    def _get_reporting_info(self, root):
        reporters = root.xpath(
            "//w:ReportingInformation/w:Organisation/text()", namespaces=NSMAP
        )
        date = root.xpath(
            "//w:ReportingInformation/w:ReportingDate/text()", namespaces=NSMAP
        )

        if not date:
            date.append("-")

        return reporters, date

    def get_reporting_information(self, filename=None):
        # The MSFD<ArtN>_ReportingInformation tables are not reliable (8b is
        # empty), so we try to get the information from the reported XML files.

        if not filename:
            f = self.filename
            filename = isinstance(f, (tuple, list)) and f[0] or f
        else:
            filename = isinstance(filename, (tuple, list)
                                  ) and filename[0] or filename

        default = ReportingInformation('2013-04-30', 'Member State')

        if not filename:
            return default

        text = get_xml_report_data(filename, self.country_code)
        root = fromstring(text)

        reporters, date = self._get_reporting_info(root)

        try:
            date = date_format(date[0])
            res = ReportingInformation(date, ", ".join(set(reporters)))
        except Exception:
            logger.exception(
                "Could not parse date for %s, %s, %s",
                self.article,
                self.descriptor,
                self.country_code,
            )

            res = ReportingInformation(date[0], ", ".join(set(reporters)))

        return res


class ReportData2014(ReportData2012):
    year = "2014"
    report_year = "2014"
    report_due = "2014-10-15"

    def _get_reporting_info(self, root):
        try:
            reporter = [root.attrib["Organisation"]]
        except:
            reporter = ["Reporter not found"]

        try:
            date = [root.attrib["ReportingDate"]]
        except:
            date = ["Date not found"]

        return reporter, date

    def get_report_header_data(
        self,
        report_by,
        source_file,
        factsheet,
        report_date,
        multiple_source_files=False,
    ):
        data = OrderedDict(
            title=self.report_title,
            report_by=report_by,
            source_file=source_file,
            factsheet=factsheet,
            report_due=self.report_due,
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=multiple_source_files,
            use_translation=True,
        )

        return data

    def get_report_view(self):
        klass = self.article_implementations[self.article]

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            self.filename,
        )

        return view

    def filter_filenames_by_region(self, all_filenames):
        # filter by regions if country has multiple regions
        # TODO need better filtering by <Region> text
        filenames = []
        for fileurl in all_filenames:
            if len(self.regions) == 1:
                filenames.append(fileurl)
                continue

            if (
                "/" + self.country_region_code.lower() not in fileurl
                and "/" + self.country_region_code.upper() not in fileurl
            ):

                continue

            filenames.append(fileurl)

        return filenames

    @db.use_db_session("2012")
    def __call__(self):
        # returns all fileurls from sparql, including monitoring programme
        # and monitoring subprogramme files
        all_filenames = self.get_report_filename()
        filename = self.filter_filenames_by_region(all_filenames)
        self.filename = filename

        if "translate" in self.request.form:
            report_view = self.get_report_view()
            report_view.auto_translate()

            messages = IStatusMessage(self.request)
            messages.add(
                "Auto-translation initiated, please refresh " "in a couple of minutes",
                type="info",
            )

        print(("Will render report for: %s" % self.article))

        try:
            report_data, report_data_rows = self.get_report_data()
        except:
            report_data, report_data_rows = "Error in rendering report", []

        factsheet = None
        multiple_source_files = True
        source_file = [(f, f + "/manage_document") for f in filename]

        rep_info = self.get_reporting_information(
            filename=filename and filename[0] or None
        )

        report_header_data = self.get_report_header_data(
            rep_info.reporters,
            source_file,
            factsheet,
            rep_info.report_date,
            multiple_source_files,
        )
        report_header = self.report_header_template(**report_header_data)

        trans_edit_html = self.translate_view()()
        self.report_html = report_header + report_data + trans_edit_html

        if "download" in self.request.form:

            return self.download(report_data_rows, report_header_data)

        return self.index()


class ReportData2016(ReportData2012):
    year = "2016"
    report_year = "2016"
    report_due = "2016-10-15"

    def _get_reporting_info(self, root):
        reporter = [root.attrib["ReporterName"]]
        date = [root.attrib["ReportingDate"]]

        return reporter, date

    def get_report_view(self):
        klass = self.article_implementations[self.article]

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            self.fileurl,
        )

        return view

    @db.use_db_session("2012")
    def __call__(self):
        # if self.descriptor.startswith('D1.'):       # map to old descriptor
        #     # self._descriptor = 'D1'               # this hardcodes D1.x
        #                                             # descriptors to D1
        #     assert self.descriptor == 'D1'

        print(("Will render report for: %s" % self.article))

        self.filename = filename = self.get_report_filename()
        self.fileurl = fileurl = get_report_fileurl_art131418_2016(
            filename, self.country_code, self.country_region_code, self.article
        )

        if "translate" in self.request.form:
            report_view = self.get_report_view()
            report_view.auto_translate()

            messages = IStatusMessage(self.request)
            messages.add(
                "Auto-translation initiated, please refresh " "in a couple of minutes",
                type="info",
            )

        factsheet = None

        source_file = ("File not found", None)
        multiple_source_files = False

        if fileurl:
            try:
                factsheet = get_factsheet_url(fileurl)
            except Exception:
                logger.exception(
                    "Error in getting HTML Factsheet URL %s", fileurl)
        else:
            logger.warning(
                "No factsheet url, filename is: %r", filename)

        source_file = (filename, fileurl + "/manage_document")

        rep_info = self.get_reporting_information()

        report_header_data = self.get_report_header_data(
            rep_info.reporters,
            source_file,
            factsheet,
            rep_info.report_date,
            multiple_source_files,
        )
        report_header = self.report_header_template(**report_header_data)
        try:
            report_data, report_data_rows = self.get_report_data()
        except:
            report_data, report_data_rows = "Error in rendering report", []
        trans_edit_html = self.translate_view()()
        self.report_html = report_header + report_data + trans_edit_html

        if "download" in self.request.form:

            return self.download(report_data_rows, report_header_data)

        return self.index()


class ReportData2018Art18(ReportData2016):
    year = "2018"
    report_year = "2018"
    report_due = "2018-10-15"

    def _get_reporting_info(self, root):
        reporter = [root.attrib["ContactOrganisation"]]
        date = [root.attrib["ReportingDate"]]

        return reporter, date


@implementer(IReportDataViewOverview)
class ReportDataOverview2014Art11(ReportData2014):
    @property
    def descriptor(self):
        return "Not defined"

    @property
    def article(self):
        return "Art11"

    @property
    def report_title(self):
        title = "Member State report / {} / {} / {} / {}".format(
            self.article,
            self.report_year,
            self.country_name,
            self.country_region_name,
        )

        return title

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file

        filename = get_report_filename(
            self.year,
            self.country_code,
            self.country_region_code,
            art or self.article,
            self.descriptor,
        )

        res = []

        for fname in filename:
            text = get_xml_report_data(fname)
            root = fromstring(text)

            if root.tag == "MON":
                res.append(fname)
                break

        return res

    def get_report_definition(self):
        rep_def = get_report_definition(
            self.year, "Art11Overview").get_fields()

        return rep_def

    def get_report_translatable_fields(self):
        rep_def = get_report_definition(self.year, "Art11Overview")

        if not rep_def:
            return []

        return rep_def.get_translatable_fields()

    def get_report_view(self):
        klass = self.article_implementations["Art11Overview"]

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            self.filename,
        )

        return view


class ReportData20142020(ReportData2014):
    is_side_by_side = True
    cache_key_extra = "side-by-side"
    report_year = "2014-2020"
    report_due = "2014-10-15; 2020-10-15"

    def download(self, report_data, report_header):
        klass = Article11Compare

        view_2020 = ReportData2020(
            self.context, self.request, self.is_side_by_side)
        data_2020 = view_2020.get_data_from_db()

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            data_2020,
            self.filename,
        )
        view.setup_data()

        data_2014 = view.rows
        res = {"Report data": []}

        for i, (field, row) in enumerate(data_2020[0][1]):
            xls_title = data_2014[i].title
            xls_row = data_2014[i].raw_values + [field.title] + row
            res["Report data"].append((xls_title, xls_row))

        xlsio = self.data_to_xls(res, report_header)

        return self._set_response_header(xlsio)

    @property
    def TRANSLATABLES(self):
        rep_def_2014 = get_report_definition("2014", self.article)
        rep_def_2020 = get_report_definition("2020", self.article)
        translatables_2014 = rep_def_2014.get_translatable_fields()
        translatables_2020 = rep_def_2020.get_translatable_fields()

        return translatables_2014 + translatables_2020

    def get_report_header_data(
        self,
        report_by,
        source_file,
        factsheet,
        report_date,
        multiple_source_files=False,
    ):

        self.get_report_view()
        metadata_2020 = self.report_metadata_2020

        try:
            source_files_2020 = [
                (x.ReportedFileLink, x.ReportedFileLink + "/manage_document")
                for x in metadata_2020
            ]
        except:
            source_files_2020 = []
            metadata_2020 = []

        report_date_2020 = (
            metadata_2020 and metadata_2020[0].ReportingDate.isoformat() or ""
        )

        data = OrderedDict(
            title=self.report_title,
            report_by=report_by,
            source_file=source_file + source_files_2020,
            factsheet=factsheet,
            report_due=self.report_due,
            report_date=report_date + "; " + report_date_2020,
            help_text=self.help_text,
            multiple_source_files=multiple_source_files,
            use_translation=True,
        )

        return data

    def get_report_view(self):
        klass = Article11Compare

        view_2020 = ReportData2020(
            self.context, self.request, self.is_side_by_side)
        data_2020 = view_2020.get_data_from_db()

        self.report_metadata_2020 = view_2020.get_report_metadata()

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            data_2020,
            self.filename,
        )

        return view


@implementer(IReportDataViewSecondary)
class ReportData2012Secondary(ReportData2012):
    """Class implementation for Article 8 ESA"""

    descriptor = "Not linked"
    country_region_code = "No region"

    @property
    def report_title(self):
        title = "Member State report / {} / {} / 2012".format(
            self.article,
            self.country_name,
        )

        return title

    @cache(get_reportdata_key, dependencies=["translation"])
    def get_report_data(self, filename):
        view = self.get_report_view(filename)
        rendered_view = view()

        # get cacheable raw values
        rows = serialize_rows(view.rows)
        # rows = []

        return rendered_view, rows

    def get_report_view(self, filename):
        logger.info(
            "Rendering 2012 report for: %s %s %s %s",
            self.country_code,
            self.descriptor,
            self.article,
            ",".join([x.id for x in self.muids]),
        )
        klass = self.article_implementations[self.article]

        view = klass(
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            filename,
        )

        return view

    def data_to_xls(self, data, report_headers):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {"in_memory": True})

        for region_code, report_header in report_headers.items():
            # add worksheet with report header data
            worksheet = workbook.add_worksheet(
                text_type("Report header" + region_code)
            )

            for i, (wtitle, wdata) in enumerate(report_header.items()):
                wtitle = wtitle.title().replace("_", " ")

                if isinstance(wdata, (list, tuple)):
                    if report_header.get("multiple_source_files", False):
                        wdata = "\n".join([x[1] for x in wdata])
                    else:
                        wdata = wdata[1]

                worksheet.write(i, 0, wtitle)
                worksheet.write(i, 1, wdata)

        for wtitle, wdata in data.items():  # add worksheet(s) with report data
            if not wdata:
                continue

            worksheet = workbook.add_worksheet(text_type(wtitle)[:30])

            for i, row in enumerate(wdata):
                row_label = row[0]
                worksheet.write(i, 0, row_label)
                row_values = row[1]

                for j, v in enumerate(row_values):
                    try:
                        transl = get_translated(v, self.country_code) or v
                        worksheet.write(i, j + 1, transl)
                    except:
                        if hasattr(v, "rows") and v.rows:
                            try:
                                v_rows = [text_type(x) for x in v.rows]
                                worksheet.write(i, j + 1, "#".join(v_rows))
                                continue
                            except:
                                import pdb

                                pdb.set_trace()

                        worksheet.write(i, j + 1, "")

        workbook.close()
        out.seek(0)

        return out

    def __call__(self):
        rendered_results = []
        multiple_source_files = False
        download_rows = {}
        download_headers = {}

        for region_index, region_code in enumerate(self.regions):
            filename = get_report_filename(
                self.year, self.country_code, region_code, self.article, self.descriptor
            )
            trans_edit_html = self.translate_view()()

            if filename:
                url = get_report_file_url(filename, self.country_code)
                if url:
                    try:
                        factsheet = get_factsheet_url(url)
                    except Exception:
                        logger.exception(
                            "Error in getting HTML Factsheet URL %s", url)
                else:
                    logger.warning(
                        "No factsheet url, filename is: %r", filename)

                source_file = (filename, url + "/manage_document")

            rep_info = self.get_reporting_information(filename)
            report_header_data = self.get_report_header_data(
                rep_info.reporters,
                source_file,
                factsheet,
                rep_info.report_date,
                multiple_source_files,
            )
            report_header_data["region_name"] = REGIONS[region_code]
            report_header_data["show_navigation"] = region_index == 0
            report_header_data["title"] = region_index == 0 and self.report_title or ""
            report_header = self.report_header_template(**report_header_data)

            try:
                # import pdb; pdb.set_trace()
                report_data, report_data_rows = self.get_report_data(filename)
            except:
                report_data, report_data_rows = "Error in rendering report", []

            download_rows[region_code] = report_data_rows["Report data"]
            download_headers[region_code] = report_header_data
            rendered_results.append(report_header + report_data)

        if "download" in self.request.form:

            # report_header_data
            return self.download(download_rows, download_headers)

        res = "<hr/>".join(rendered_results)
        self.report_html = res + "" + trans_edit_html

        return self.index()


class ReportData2012Like2018(ReportData2012):
    """An alternative implementation, mapping data like the 2018 views"""

    cache_key_extra = "like2018"

    @property
    def article_implementations(self):
        res = {
            "Art8": Article8Alternate,
            "Art9": Article9Alternate,
            "Art10": Article10Alternate,
        }

        return res
