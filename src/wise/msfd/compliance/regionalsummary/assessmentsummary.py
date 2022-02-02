# -*- coding: utf-8 -*-

from __future__ import absolute_import
from io import BytesIO

from datetime import datetime

import logging

from pkg_resources import resource_filename
from plone.api import portal

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd.compliance.interfaces import (
    IRecommendationStorage, IRegionalSummaryRegionFolder
)
from wise.msfd.compliance.main import (
    RecommendationsTable, STORAGE_KEY
)
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import timeit

from zope.interface import implementer, implements

import pdfkit

from ..nationalsummary.assessmentsummary import (
    AssessmentExportCover, ProgressAssessment, SummaryAssessment
)

from .base import BaseRegSummaryView
from .descriptor_assessments import RegDescriptorLevelAssessments
from .introduction import RegionalIntroduction

logger = logging.getLogger('wise.msfd')


class RegionalAssessmentExportCover(BaseRegSummaryView, AssessmentExportCover):
    """ PDF Assessment cover for regional summaries """


class Recommendations(BaseRegSummaryView):
    template = ViewPageTemplateFile('pt/recommendations.pt')

    def __call__(self):
        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, {})
        default = self.template(data='-')

        if not len(list(storage_recom.items())):
            return default

        subregions = set(self.available_subregions)
        recommendations = []

        for rec_code, recommendation in storage_recom.items():
            ms_region = set(recommendation.ms_region)

            if subregions.intersection(ms_region):
                recommendations.append(recommendation.data_to_list())

        if not recommendations:
            return default

        sorted_rec = sorted(recommendations, key=lambda i: i[0])

        recomm_table = RecommendationsTable(
            recommendations=sorted_rec, show_edit_buttons=False
        )
        res = recomm_table()

        return self.template(data=res)


class RegionalSummaryAssessment(BaseRegSummaryView, SummaryAssessment):
    """ Make National summary code compatible for Regional summary """

    def __init__(self, context, request, overall_scores,
                 reg_desc_region_folder, year='2018'):
        super(SummaryAssessment, self).__init__(context, request)

        self.overall_scores = overall_scores
        self.reg_desc_region_folder = reg_desc_region_folder
        self.year = year

    @property
    def intro_text(self):
        text = "The table shows the overall conclusions on the coherence of " \
               "the information reported by the Member States in the Baltic " \
               "Sea region for each descriptor and article."

        return text

    def setup_data(self):
        res = []
        region_folder = self.reg_desc_region_folder

        table_rows = []
        descr_folders = self.get_descr_folders(region_folder)

        for descr_type, descriptors in self.descriptor_types:
            descr_rows = []

            for descr in descriptors:
                descr_folder = [
                    d
                    for d in descr_folders
                    if d.id.upper() == descr
                ][0]
                # Remove brackets with text from descriptor title
                # D4 - Food webs/D1 Biodiversity - ecosystems (D4/D1)
                descriptor_title = descr_folder.title.split('(')[0]
                row = [descriptor_title]

                for article_folder in descr_folder.contentValues():
                    if article_folder.title in ('Art11', ):
                        continue

                    score = self.get_overall_score(
                        region_folder.id.upper(), descr_folder.id.upper(),
                        article_folder.title
                    )

                    row.append(score)

                descr_rows.append(row)

            table_rows.append((descr_type, descr_rows))

        res.append((region_folder.title, table_rows))

        self.summary_assess_data = res

        return res


class RegProgressAssessment(BaseRegSummaryView, ProgressAssessment):
    """ Make National summary code compatible for Regional summary """

    template = ViewPageTemplateFile('pt/progress-assessment.pt')


@implementer(IRegionalSummaryRegionFolder)
class AssessmentSummaryView(BaseRegSummaryView):
    # implements(IRegionalSummaryRegionFolder)

    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    report_header_template = ViewPageTemplateFile(
        'pt/assessment-export-header.pt'
    )
    year = "2012"

    render_header = True
    render_recommendations = True

    def _get_css(self):
        return [
            resource_filename('wise.msfd',
                              'static/wise/dist/css/compliance.css'),
            resource_filename('wise.msfd',
                              'static/wise/dist/css/pdf_export.css'),
        ]

    def _get_cover(self):
        absolute_url = self.context.absolute_url()
        cover_url = absolute_url + '/export-cover'

        if 'localhost' in absolute_url:
            return ""
            cover_url = cover_url.replace('localhost:5080',
                                          'office.pixelblaster.ro:4880')

        return cover_url

    def _get_toc(self):
        xsl_file = resource_filename('wise.msfd', 'data/pdf_toc.xsl'),

        toc = {"xsl-style-sheet": xsl_file}

        return toc

    def download_pdf(self):
        options = {
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            # 'footer-left': "Page",
            'footer-font-size': '7',
            'footer-right': '[page]',
            'encoding': "UTF-8",
        }
        css = self._get_css()
        cover = self._get_cover()
        toc = self._get_toc()
        path_wkhtmltopdf = '/plone/instance/parts/wkhtmltopdf/wkhtmltopdf'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        doc = pdfkit.from_string(
            self.report_html, False, options=options,
            cover=cover,
            toc=toc,
            css=css,
            cover_first=True,
            configuration=config
        )
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/pdf')
        fname = "{}-{}-{}".format(
            self.country_name, self.get_status().title().replace(' ', ''),
            str(datetime.now().date())
        )
        sh('Content-Disposition',
           'attachment; filename=%s.pdf' % fname)

        return doc

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Commission assessment / Art12 / 2018 / {}-summary".format(
                self.country_name,
            )
        )
        # trans_edit_html = self.translate_view()()

        # 4. Descriptor-level assessments
        descriptor_lvl_assess = RegDescriptorLevelAssessments(self, self.request)
        descriptor_lvl_assess_view = descriptor_lvl_assess()
        overall_scores = descriptor_lvl_assess.overall_scores
        reg_desc_region_folder = descriptor_lvl_assess.reg_desc_region_folder

        # 1. Introduction
        introduction = RegionalIntroduction(self.context, self.request)

        # 2. Summary Assessment
        sum_assess = RegionalSummaryAssessment(
            self, self.request, overall_scores, reg_desc_region_folder
        )

        # 3. Progress Assessment
        prog_assess = RegProgressAssessment(self, self.request)

        self.tables = [
            report_header,
            introduction,
            sum_assess,
            prog_assess,
            descriptor_lvl_assess,
            # ArticleTable(self, self.request, 'Art7'),
            # ArticleTable(self, self.request, 'Art3-4'),
            # trans_edit_html,
        ]

        if self.render_header:
            # 5. Recommendations table
            recomm_table = Recommendations(self, self.request)

            self.tables.append(recomm_table)

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self._country_folder.absolute_url())
            return self.request.response.redirect(url)

        if 'download_pdf' in self.request.form:
            self.render_header = False

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'download_pdf' in self.request.form:
            return self.download_pdf()

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
