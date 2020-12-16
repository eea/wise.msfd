# -*- coding: utf-8 -*-

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from wise.msfd.compliance.utils import group_by_mru
from wise.msfd.data import (get_all_report_filenames,
                            get_envelope_release_date, get_factsheet_url,
                            get_report_file_url, get_report_filename,
                            get_xml_report_data)
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, items_to_rows, timeit)

from ..nationaldescriptors.data import get_report_definition
from ..nationaldescriptors.reportdata import ReportData2018Secondary
from ..nationaldescriptors.proxy import Proxy2018
from .base import BaseNatSummaryView


logger = logging.getLogger('wise.msfd')


class ReportData2018SecondaryOverview(ReportData2018Secondary,
                                      BaseNatSummaryView):
    is_translatable = False
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header-secondary.pt'
    )

    @property
    def descriptor(self):
        return 'Not linked'

    @property
    def muids(self):
        return []

    @property
    def country_region_code(self):
        return 'No region'

    def render_reportdata(self):
        """
        1. Get all reported files under Article 7 or 3/4
        2. Render the data separately for all files
        3. Concat the rendered htmls into a single

        :return: rendered html
        """

        template = self.get_template(self.article)
        urls = get_all_report_filenames(self.country_code, self.article)

        rendered_results = []

        for (index, url) in enumerate(urls[:1]):
            prev_url = url
            view = self.get_implementation_view(url, prev_url)
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
                title=self.title,
                factsheet=factsheet,
                report_by=report_by,
                source_file=source_file,
                report_due=None,
                report_date=report_date.date(),
                help_text=self.help_text,
                multiple_source_files=False,
                show_navigation=False,
            )

            rendered_results.append(template(data=res,
                                             report_header=report_header,
                                             show_navigation=False))

        res = "<hr/>".join(rendered_results)

        return res or "No data found"

    def __call__(self):
        return self.render_reportdata()


class Article7Table(ReportData2018SecondaryOverview):
    article = 'Art7'
    title = 'Who is responsible for MSFD implementation?'


class Article34Table(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Where is the MSFD implemented? & Areas for MSFD reporting'


class NationalOverviewView(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    def title(self):
        title = u"National overview: {}".format(self.country_name)

        return title

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.overview_header_template(
            title="National summary report: {}".format(
                self.country_name,
            )
        )
        self.tables = [
            report_header,
            Article7Table(self.context, self.request)(),
            Article34Table(self.context, self.request)(),
            # trans_edit_html,
        ]

        return self.template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self.context.absolute_url())

            return self.request.response.redirect(url)

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'translate' in self.request.form:
            for value in self._translatable_values:
                retrieve_translation(self.country_code, value)

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        @timeit
        def render_html():
            return self.index()

        return render_html()
