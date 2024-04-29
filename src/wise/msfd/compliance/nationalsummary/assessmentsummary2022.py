# -*- coding: utf-8 -*-

from __future__ import absolute_import
from collections import defaultdict
from datetime import datetime
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.api import portal
from wise.msfd.compliance.interfaces import (INationalSummary2022Folder,
                                             INationalSummaryEdit,
                                             IRecommendationStorage)
from wise.msfd.compliance.main import (
    RecommendationsTable, STORAGE_KEY
    )
from wise.msfd.compliance.vocabulary import get_regions_for_country
from wise.msfd.gescomponents import DESCRIPTOR_TYPES
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import timeit

from zope.interface import implementer

import pdfkit

from .base import BaseNatSummaryView
from .descriptor_assessments import DescriptorLevelAssessments
from .introduction import Introduction

logger = logging.getLogger('wise.msfd')


@implementer(INationalSummary2022Folder)
class AssessmentSummary2022View(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    report_header_template = ViewPageTemplateFile(
        'pt/assessment-export-header.pt'
    )
    year = "2012"

    render_header = True

    # def _get_css(self):
    #     return [
    #         resource_filename('wise.msfd',
    #                           'static/wise/dist/css/compliance.css'),
    #         resource_filename('wise.msfd',
    #                           'static/wise/dist/css/pdf_export.css'),
    #     ]

    # def _get_cover(self):
    #     absolute_url = self.context.absolute_url()
    #     cover_url = absolute_url + '/export-cover'

    #     if 'localhost' in absolute_url:
    #         cover_url = 'https://water.europa.eu/marine/assessment-module/' \
    #                     'national-summaries/lv/export-cover'

    #     return cover_url

    # def _get_toc(self):
    #     xsl_file = resource_filename('wise.msfd', 'data/pdf_toc.xsl'),

    #     toc = {"xsl-style-sheet": xsl_file}

    #     return toc

    # def download_pdf(self):
    #     options = {
    #         'margin-top': '0.5in',
    #         'margin-right': '0.5in',
    #         'margin-bottom': '0.5in',
    #         'margin-left': '0.5in',
    #         'footer-font-size': '7',
    #         'footer-right': '[page]',
    #         'encoding': "UTF-8",
    #         'load-error-handling': 'ignore',
    #         # 'load-media-error-handling': 'ignore'
    #     }
    #     css = self._get_css()
    #     cover = self._get_cover()
    #     toc = self._get_toc()
    #     path_wkhtmltopdf = '/plone/instance/parts/wkhtmltopdf/wkhtmltopdf'
    #     config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    #     doc = pdfkit.from_string(
    #         self.report_html, False, options=options,
    #         cover=cover,
    #         toc=toc,
    #         css=css,
    #         cover_first=True,
    #         configuration=config
    #     )
    #     sh = self.request.response.setHeader

    #     sh('Content-Type', 'application/pdf')
    #     fname = "{}-{}-{}".format(
    #         self.country_name, self.get_status().title().replace(' ', ''),
    #         str(datetime.now().date())
    #     )
    #     sh('Content-Disposition',
    #        'attachment; filename=%s.pdf' % fname)

    #     return doc

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Commission assessment / Art16 / 2022 / {}-summary".format(
                self.country_name,
            )
        )
        # trans_edit_html = self.translate_view()()

        # 4. Descriptor-level assessments
        # descriptor_lvl_assess = DescriptorLevelAssessments(self, self.request)
        # descriptor_lvl_assess_view = descriptor_lvl_assess()
        # overall_scores = descriptor_lvl_assess.overall_scores
        # nat_desc_country_folder = descriptor_lvl_assess.nat_desc_country_folder

        # 1. Introduction
        # introduction = Introduction(self.context, self.request)

        # 2. Summary Assessment
        # sum_assess = SummaryAssessment(self, self.request, overall_scores,
        #                                nat_desc_country_folder)

        # 3. Progress Assessment
        # prog_assess = ProgressAssessment(self, self.request)

        self.tables = [
            report_header,
            # introduction,
            # sum_assess,
            # prog_assess,
            # descriptor_lvl_assess,
            # trans_edit_html,
        ]

        # if self.render_header:
        #     # 5. Recommendations table
        #     recomm_table = Recommendations(self, self.request)

        #     self.tables.append(recomm_table)

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
