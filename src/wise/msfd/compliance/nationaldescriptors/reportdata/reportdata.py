# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
from types import SimpleNamespace
import logging
from collections import OrderedDict, defaultdict

from lxml.etree import fromstring
from zope.interface import implementer

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as Template
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018, sql2024  # sql,
from wise.msfd.compliance.interfaces import (
    IReportDataViewSecondary,
    IReportDataViewOverview,
)
from wise.msfd.compliance.nationaldescriptors.data import get_report_definition
from wise.msfd.compliance.utils import group_by_mru
from wise.msfd.data import (
    get_all_report_filenames,
    get_envelope_release_date,
    get_factsheet_url,
    get_report_file_url,
    get_report_filename,
    get_report_fileurl_art131418_2016,
    get_xml_report_data,
)
from wise.msfd.gescomponents import get_descriptor, get_features
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import items_to_rows, timeit

from ..a7 import Article7_2018
from ..a11 import Article11Compare
from ..a34 import Article34_2018
from ..proxy import Proxy2018
from .reportdata2012 import ReportData2012
from .reportdata2018 import ReportData2018
from .utils import date_format, ReportingInformation2018
from six import string_types

logger = logging.getLogger("wise.msfd")


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
class ReportData2018Art8ESA(ReportData2018):
    descriptor = "Not linked"
    country_region_code = "No region"
    country_region_name = "No region"

    Art8esa = Template("../pt/report-data-multiple-muid.pt")

    @property
    def report_header_title(self):
        title = "Member State report / {} / {} / {} ".format(
            self.article,
            self.report_year,
            self.country_name,
        )

        return title

    def get_data_from_view_Art8esa(self):
        t = sql2018.t_V_ART8_ESA_2018

        conditions = [t.c.CountryCode.in_(self.country_code.split(","))]

        count, q = db.get_all_records_ordered(t, ("CountryCode",), *conditions)

        res = []

        for row in q:
            res.append(row)

        return res


@implementer(IReportDataViewSecondary)
class ReportData2018Secondary(ReportData2018):
    descriptor = "Not linked"
    country_region_code = "No region"

    Art3 = Template("../pt/report-data-secondary-2018.pt")
    Art4 = Template("../pt/report-data-secondary-2018.pt")
    Art7 = Template("../pt/report-data-secondary-2018.pt")

    def get_marine_waters(self):
        return ""

    def article_name(self):
        get_art_name = super(ReportData2018Secondary, self).article_name

        if self.article not in ("Art3", "Art4"):
            return get_art_name()

        art_name = " & ".join(
            (
                get_art_name("Art3"),
                get_art_name("Art4"),
                get_art_name("Art5"),
                get_art_name("Art6"),
            )
        )

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
        fileurl = get_report_file_url(filename, self.country_code)
        root = view.get_report_file_root(filename)

        reporters = date = None
        try:
            reporters = root.get("GeneratedBy")

            if not reporters:
                reporters = root.get("Organisation")

            date = root.get("CreationDate")

            if not date:
                date = root.get("ReportingDate")

            date = date_format(date)

        except:
            pass

        metadata = ReportingInformation2018(fileurl, reporters, date)

        return metadata

    @property
    def report_header_title(self):
        article = self.article
        if self.article in ("Art3", "Art4"):
            article = "Art3-4"

        title = "Member State report: {} / {}".format(
            self.country_name,
            article,
        )

        return title

    def get_template(self, article):
        article = article.replace("-", "")
        template = getattr(self, article, None)

        return template

    def get_implementation_view(self, filename, prev_filename, show_mru_usage=False):
        """In other articles (8, 9, 10) for 2018 year,
        we get the data from the DB (MSFD2018_production)

        Here instead we will get the data from the report xml from CDR
        by initializing and calling the view's class to setup the data
        """

        klass = {
            "Art7": Article7_2018,
            "Art3": Article34_2018,
            "Art4": Article34_2018,
        }.get(self.article)

        init_args = [
            self,
            self.request,
            self.country_code,
            self.country_region_code,
            self.descriptor,
            self.article,
            self.muids,
            filename,
        ]

        if self.article in ["Art3", "Art4"] and prev_filename:
            prev_view = klass(
                self,
                self.request,
                self.country_code,
                self.country_region_code,
                self.descriptor,
                self.article,
                self.muids,
                prev_filename,
                show_mru_usage=show_mru_usage,
            )
            prev_view.setup_data()
            previous_mrus = prev_view.available_mrus
            init_args.append(previous_mrus)

        view = klass(*init_args, show_mru_usage=show_mru_usage)
        view.setup_data()

        return view

    def auto_translate(self):
        self.render_reportdata()
        seen = set()

        all_translatables = self.translatable_data + self.translatable_extra_data

        for value in all_translatables:
            if not value:
                continue

            if not isinstance(value, string_types):
                continue

            if value not in seen:
                retrieve_translation(self.country_code, value)
                seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(
            "Auto-translation initiated, please refresh " "in a couple of minutes",
            type="info",
        )

        url = self.context.absolute_url() + "/@@view-report-data-2018"
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

        for index, url in enumerate(urls):
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
                if not report_date:
                    report_date = report.ReportingDate

            res = []
            source_file = (url.rsplit("/", 1)[-1], url + "/manage_document")

            factsheet = get_factsheet_url(url)

            view()  # updates the view
            data = [Proxy2018(row, self) for row in view.cols]

            if self.article == "Art7":
                data_by_mru = group_by_mru(data)
            else:
                data_by_mru = {"no mru": data}

            fields = get_report_definition(
                self.year, self.article).get_fields()

            for mru, rows in data_by_mru.items():
                _rows = items_to_rows(rows, fields)

                res.append((mru, _rows))

            report_header = self.report_header_template(
                title=(index == 0 and self.report_header_title or ""),
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

            rendered_results.append(
                template(data=res, report_header=report_header,
                         show_navigation=False)
            )

        self.translatable_extra_data = translatable_extra_data
        self.translatable_data = translatable_data

        res = "<hr/>".join(rendered_results)

        return res or "No data found"


class ReportData2020(ReportData2018):
    """Implementation for Article 11 report data view for year 2020"""

    report_year = "2020"  # used by cache key
    year = "2020"  # used in report definition and translation
    report_due = "2020-10-15"
    is_overview = False

    def __init__(self, context, request, is_side_by_side=False):
        super(ReportData2020, self).__init__(context, request)

        self.is_side_by_side = is_side_by_side

    @property
    def muids(self):
        return []

    @db.use_db_session("2018")
    @timeit
    def get_report_metadata(self):
        """Returns metadata about the reported information"""

        article = self.article

        if self.is_overview:
            article = article + "Overview"

        t = sql2018.ReportedInformation
        schemas = {
            "Art11": ["ART11_Programmes", "ART11_Strategies"],
            "Art11Overview": ["ART11_Strategies"],
        }
        items = []

        for schema in schemas[article]:
            try:
                count, item = db.get_item_by_conditions(
                    t,
                    "ReportingDate",
                    t.CountryCode == self.country_code,
                    t.Schema == schema,
                    reverse=True,
                )
            except:
                # no data reported
                continue

            items.append(item)

        return items

    def get_report_header(self):
        report_items = self.get_report_metadata()

        report_by = report_date = None
        links = []

        for report in report_items:
            link = report.ReportedFileLink
            link = (link.rsplit("/", 1)[1], link)
            links.append(link)
            report_by = report.ContactOrganisation
            report_date = report.ReportingDate

        report_header = self.report_header_template(
            title=self.report_header_title,
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by=report_by,
            source_file=links,
            report_due=self.report_due,
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=True,
        )

        return report_header


class ReportData2022(ReportData2018):
    """Implementation for Article 13 and 14 report data view for year 2022"""

    report_year = "2022"  # used by cache key
    year = "2022"  # used in report definition and translation
    report_due = "2022-10-15"

    @property
    def muids(self):
        return []


class ReportData2024(ReportData2018):
    """Implementation for Article 8, 9 and 10 report data view for year 2024"""

    report_year = "2024"  # used by cache key
    year = "2024"  # used in report definition and translation
    report_due = "2024-10-15"

    report_header_template = Template('../pt/report-data-header-2024.pt')

    def _get_order_cols_Art8(self, descr):
        descr = descr.split(".")[0]
        criteria_priority = (
            "MarineReportingUnit",
            "GEScomponent",
            "Criteria",
            "Feature",
            "Element",
            "Element2",
            # "Element2Code",
            "IntegrationRuleTypeParameter",
        )

        default = (
            "MarineReportingUnit",
            "GEScomponent",
            "Feature",
            "Element",
            "Element2",
            # "Element2Code",
            "Criteria",
            "IntegrationRuleTypeParameter",
        )

        order_by = {
            "D2": criteria_priority,
            "D4": criteria_priority,
            "D5": (
                "MarineReportingUnit",
                "GEScomponent",
                "Feature",
                "Criteria",
                "Element",
                "Element2",
                # "Element2Code",
                "IntegrationRuleTypeParameter",
            ),
            "D6": default,
            "D7": criteria_priority,
            "D8": criteria_priority,
            "D11": criteria_priority,
            "default": default,
        }

        return order_by.get(descr, order_by["default"])

    # @db.use_db_session("2018")
    def get_report_metadata(self):
        """Returns metadata about the reported information"""
        item = SimpleNamespace()
        item.ReportedFileLink = '/'
        item.ContactOrganisation = ''
        item.ReportingDate = self._reporting_date

        return item

    @db.use_db_session('2024')
    def get_data_from_view_Art8_2024(self):
        sess = db.session()
        t = sql2024.t_V_ART8_GES_2024

        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        # muids = [x.id for x in self.muids]
        conditions = [
            t.c.CountryCode == self.country_code,
            # t.c.Region == self.country_region_code,
            # t.c.MarineReportingUnit.in_(muids),     #
            t.c.GEScomponent.in_(all_ids),
        ]

        orderby = [getattr(t.c, x)
                   for x in self._get_order_cols_Art8(self.descriptor)]

        # groupby IndicatorCode
        q = sess.query(t).filter(*conditions).order_by(*orderby).distinct()

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        for row in q:
            if not self.descriptor.startswith("D1."):
                out.append(row)
                continue

            feats = set((row.Feature,))

            if feats.intersection(ok_features):
                out.append(row)

        self._reporting_date = out and out[0].ReportingDate or None

        return out

    def get_data_from_view_Art10_2024(self):
        return self.get_data_from_view_Art10()

    def get_data_from_view_Art9_2024(self):
        return self.get_data_from_view_Art9()


@implementer(IReportDataViewOverview)
class ReportDataOverview2020Art11(ReportData2020):
    is_primary_article = False
    is_overview = True

    @property
    def descriptor(self):
        return "Not defined"

    @property
    def article(self):
        return "Art11"

    @property
    def TRANSLATABLES(self):
        article = "{}Overview".format(self.article)
        rep_def = get_report_definition(self.year, article)
        translatables = rep_def.get_translatable_fields()

        return translatables

    def get_report_definition(self):
        article = "{}Overview".format(self.article)
        rep_def = get_report_definition(self.year, article).get_fields()

        return rep_def

    def get_data_from_view_Art11(self):
        t = sql2018.t_V_ART11_Strategies_Programmes_2020

        conditions = [t.c.CountryCode.in_(self.country_code.split(","))]

        columns = [
            t.c.ResponsibleCompetentAuthority,
            t.c.ResponsibleOrganisations,
            t.c.RelationshipToCA,
            t.c.PublicConsultationDates,
            t.c.PublicConsultationSite,
            t.c.RegionalCooperation,
        ]

        # count, q = db.get_all_specific_columns(
        #     *columns,
        #     *conditions
        # )

        sess = db.session()
        q = sess.query(*columns).filter(*conditions).first()

        return [q]

    @property
    def report_header_title(self):
        title = "Member State report / Art11 / 2020 / {} / {} - Overview".format(
            self.country_name, self.country_region_name
        )

        return title

    @property
    def translate_redirect_url(self):
        url = self.context.absolute_url() + "/@@art11-view-report-data-2020"

        return url
