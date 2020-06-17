# -*- coding: utf-8 -*-

from io import BytesIO
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

import pdfkit

from ..nationalsummary.pdfexport import (AssessmentExportCover,
                                         ProgressAssessment, SummaryAssessment)

from .base import BaseRegSummaryView
from .descriptor_assessments import RegDescriptorLevelAssessments
from .introduction import RegionalIntroduction

logger = logging.getLogger('wise.msfd')


class RegionalAssessmentExportCover(BaseRegSummaryView, AssessmentExportCover):
    """ PDF Assessment cover for regional summaries """


class RegionalSummaryAssessment(BaseRegSummaryView, SummaryAssessment):
    """ Make National summary code compatible for Regional summary """

    def __init__(self, context, request, overall_scores,
                 reg_desc_region_folder):
        super(SummaryAssessment, self).__init__(context, request)

        self.overall_scores = overall_scores
        self.reg_desc_region_folder = reg_desc_region_folder

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


class AssessmentExportView(BaseRegSummaryView):
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
            resource_filename('wise.theme',
                              'static/wise/css/main.css'),
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
            'footer-right': 'Page [page] of [topage]',
            'encoding': "UTF-8",
        }
        css = self._get_css()
        cover = self._get_cover()
        toc = self._get_toc()

        doc = pdfkit.from_string(
            self.report_html, False, options=options,
            cover=cover,
            toc=toc,
            css=css,
            cover_first=True
        )
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/pdf')
        fname = "{}-Draft".format(self.country_name)
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

        # 3. Descriptor-level assessments
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

        # 4. Progress Assessment
        prog_assess = ""
        if self.render_recommendations:
            prog_assess = RegProgressAssessment(self, self.request)
        
        self.tables = [
            report_header,
            introduction,
            sum_assess,
            descriptor_lvl_assess,
            prog_assess,
            # ArticleTable(self, self.request, 'Art7'),
            # ArticleTable(self, self.request, 'Art3-4'),
            # trans_edit_html,
        ]

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self._country_folder.absolute_url())
            return self.request.response.redirect(url)

        if 'download_pdf' in self.request.form:
            self.render_header = False
            self.render_recommendations = False

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
