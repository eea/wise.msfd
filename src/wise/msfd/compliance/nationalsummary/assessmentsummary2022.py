# -*- coding: utf-8 -*-

from __future__ import absolute_import
from collections import defaultdict
from datetime import datetime
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.api import portal
from wise.msfd.compliance.assessment import (ANSWERS_COLOR_TABLE,
                                             ARTICLE_WEIGHTS,
                                             CONCLUSION_COLOR_TABLE,
                                             AssessmentDataMixin,
                                             get_assessment_data_2012_db,
                                             get_assessment_data_2016_art1314,
                                             get_recommendation_data_2016_art1314,
                                             get_assessment_data_2016_art1314_overall,
                                             filter_assessment_data_2012,
                                             summary_fields_2016_cross)
from wise.msfd.compliance.base import (
    NAT_DESC_QUESTIONS, is_row_relevant_for_descriptor)

from wise.msfd.compliance.interfaces import (INationalSummary2022Folder,
                                             INationalSummaryCountryFolder,
                                             INationalSummaryEdit,
                                             IRecommendationStorage)
from wise.msfd.compliance.main import (RecommendationsTable, STORAGE_KEY)
from wise.msfd.compliance.nationaldescriptors.main import (
    format_assessment_data_2022
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


class CrossCuttingTable(BaseNatSummaryView):
    """"""

    template = ViewPageTemplateFile('pt/summary-assessment.pt')
    sections = (
        ("E Socio-economic assessment", ["Ad11E", "Ad12E"]),
        ("Impact of climate change", ["Ad13F",]),
        ("Funding of the measures", ["Ad14G", "Ad15G"]),
        ("Links to other policies", ["Ad16H", "Ad17H", "Ad18H"]),
        ("Regional cooperation and transboundary impacts", ["Ad19I", "Ad20I"]),
        ("Public consultation", ["Ad21J", "Ad22J"]),
        ("Administrative processes", ["Ad23K", "Ad24K"]),
    )

    def __init__(self, context, request, assessment_data):
        super(CrossCuttingTable, self).__init__(context, request)

        self.assessment_data = assessment_data


@implementer(INationalSummary2022Folder)
class AssessmentSummary2022View(BaseNatSummaryView):
    questions = NAT_DESC_QUESTIONS
    article_weights = ARTICLE_WEIGHTS
    articles_needed = ('Art13', 'Art14', 'Art13-completeness-2022',
                       'Art14-completeness-2022', 'Cross-cutting-2022')
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    report_header_template = ViewPageTemplateFile(
        'pt/assessment-export-header.pt'
    )
    year = "2012"

    render_header = True

    def setup_data_cross_cutting(self, assessment_data):
        elements = self.questions['Art1314CrossCutting'][0].get_all_assessed_elements(
            'DCrossCutting',
            muids=[]  # self.muids
        )

        self.assessment_data_cross_cutting = format_assessment_data_2022(
            'Art1314CrossCutting',
            elements,
            self.questions['Art1314CrossCutting'],
            [],
            assessment_data,
            'DCrossCutting',
            self.article_weights,
            self
        )

    def setup_data(self):
        catalog = portal.get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        res = []

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            obj_title = obj.title.capitalize()

            if obj_title not in self.articles_needed:
                continue

            # x = self.get_parent_by_iface(INationalSummary2022Folder)
            # xx = self.get_parent_by_iface(INationalSummaryCountryFolder)

            if self.country_code.lower() in obj.getPhysicalPath():
                assessment_data = obj.saved_assessment_data.last() if hasattr(
                    obj, 'saved_assessment_data') else {}

                if (assessment_data):
                    if 'Cross-cutting-2022' in obj_title:
                        self.setup_data_cross_cutting(assessment_data)

                    res.append(obj)

        import pdb
        pdb.set_trace()

        return res

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

        data = self.setup_data()

        # 4. Descriptor-level assessments
        # descriptor_lvl_assess = DescriptorLevelAssessments(self, self.request)
        # descriptor_lvl_assess_view = descriptor_lvl_assess()
        # overall_scores = descriptor_lvl_assess.overall_scores
        # nat_desc_country_folder = descriptor_lvl_assess.nat_desc_country_folder

        # 1. Introduction
        # introduction = Introduction(self.context, self.request)

        # 2. Summary Assessment
        # cross_cutting = CrossCuttingTable(
        #     self, self.request, self.assessment_data_cross_cutting)

        # 3. Progress Assessment
        # prog_assess = ProgressAssessment(self, self.request)

        self.tables = [
            report_header,
            # introduction,
            # cross_cutting,
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
