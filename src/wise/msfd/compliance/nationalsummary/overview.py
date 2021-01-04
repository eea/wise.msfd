# -*- coding: utf-8 -*-

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from wise.msfd.compliance.assessment import AssessmentDataMixin
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
from .assessmentsummary import SummaryAssessment
from .base import BaseNatSummaryView
from .introduction import ReportingHistoryTable


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

            # Report Header
            report_date = get_envelope_release_date(url)

            view()      # updates the view
            data = [Proxy2018(row, self) for row in view.cols]

            if self.article == 'Art7':
                data_by_mru = group_by_mru(data)
            else:
                data_by_mru = {'no mru': data}

            fields = get_report_definition(self.article).get_fields()
            fields_filtered = [
                f for f in fields
                if self.render_sections.get(f.section, True)
            ]

            res = []

            for mru, rows in data_by_mru.items():
                _rows = items_to_rows(rows, fields_filtered)

                res.append((mru, _rows))

            report_header = self.report_header_template(
                title=self.title,
                report_date=report_date.date(),
                show_navigation=False,
                article_name=self.article_name
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
    render_sections = {}


class Article34TableMarineWaters(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Where is the MSFD implemented?'
    article_name = 'Art. 3(1) Marine waters'
    render_sections = {
        'marine_waters': True,
        'marine_areas': False,
        'cooperation': False,
    }


class Article34TableMarineAreas(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Areas for MSFD reporting'
    article_name = 'Art. 4/2017 Decision: Marine regions, subregions, ' \
                   'and subdivisions'
    render_sections = {
        'marine_waters': False,
        'marine_areas': True,
        'cooperation': False,
    }


class Article34TableCooperation(ReportData2018SecondaryOverview):
    article = 'Art4'
    title = 'Regional cooperation'
    article_name = 'Art. 5(2) and Art. 6 Regional cooperation'
    render_sections = {
        'marine_waters': False,
        'marine_areas': False,
        'cooperation': True,
    }


class AssessmentSummary2018(BaseNatSummaryView, AssessmentDataMixin):
    template = ViewPageTemplateFile('pt/summary-assessment-overview-2018.pt')
    year = '2018'
    cycle = 'Second cycle'
    cycle_year = '2018-2023'

    def __call__(self):
        self.setup_descriptor_level_assessment_data()

        table = SummaryAssessment(self, self.request, self.overall_scores,
                                  self.nat_desc_country_folder, self.year)

        self.summary_assess_data = table.setup_data()
        macro_assess_sum = table.template.macros['assessment-summary-table']

        return self.template(macro_assess_sum=macro_assess_sum)


class AssessmentSummary2012(AssessmentSummary2018):
    year = '2012'
    cycle = 'First cycle'
    cycle_year = '2012-2017'


class ReportingHistoryTableOverview(ReportingHistoryTable):
    show_header = True
    obligations_needed = None  # meaning we need all obligations

    @property
    def all_obligations(self):
        data = self.data

        obligations = set([x.get('ReportingObligation') for x in data])

        return [[o] for o in obligations]


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
            Article34TableMarineWaters(self.context, self.request)(),
            Article34TableMarineAreas(self.context, self.request)(),
            Article34TableCooperation(self.context, self.request)(),
            AssessmentSummary2012(self.context, self.request)(),
            AssessmentSummary2018(self.context, self.request)(),
            ReportingHistoryTableOverview(self.context, self.request)(),
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
