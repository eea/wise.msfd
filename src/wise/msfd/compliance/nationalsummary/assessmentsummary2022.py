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
                                             CONCLUSION_COLOR_TABLE_2022,
                                             DESCRIPTOR_SUMMARY_2022,
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
from wise.msfd.compliance.scoring import get_overall_conclusion_2022
from wise.msfd.gescomponents import DESCRIPTOR_TYPES, get_descriptor
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import timeit

from zope.interface import implementer

import pdfkit

from .base import BaseNatSummaryView
from .introduction import Introduction

logger = logging.getLogger('wise.msfd')


class DescriptorLevelAssessments2022(BaseNatSummaryView):
    template = ViewPageTemplateFile('pt/descriptor-level-assessments-2022.pt')
    descriptor_types = DESCRIPTOR_TYPES

    def get_article_title(self, article):
        return self.article_name(article)

    def __init__(self, context, request, data_art13, data_art14):
        super(DescriptorLevelAssessments2022, self).__init__(context, request)

        self.assessment_data_art13 = data_art13
        self.assessment_data_art14 = data_art14

    def __call__(self):
        """ 
        :return: res =  [
            ("D7 - Hydrographical changes", [
                    ("Art13", DESCRIPTOR_SUMMARY),
                    ("Art14", DESCRIPTOR_SUMMARY),
                ]
            ),
            ("D1.4 - Birds", [
                    ("Art13", DESCRIPTOR_SUMMARY),
                    ("Art14", DESCRIPTOR_SUMMARY),
                ]
            ),
        ]
        """
        descriptors = DESCRIPTOR_TYPES[0][1] + DESCRIPTOR_TYPES[1][1]
        data = []

        for descriptor in descriptors:
            descr_obj = get_descriptor(descriptor)
            articles_data = []
            # Art13
            if descriptor in ['D1.2', 'D1.3', 'D1.4', 'D1.5', 'D1.6']:
                _article_data = self.assessment_data_art13['D1.1']
            else:
                _article_data = self.assessment_data_art13[descriptor]

            assessment_summary = _article_data.assessment_summary.output
            progress_assessment = _article_data.progress.output
            recommendations = _article_data.recommendations.output

            _adequacy = _article_data.phase_overall_scores.adequacy
            adequacy = ("{} ({})".format(_adequacy['conclusion'][1],
                                         _adequacy['conclusion'][0]),
                        _adequacy['color'])

            _completeness = _article_data.phase_overall_scores.completeness
            completeness = ("{} ({})".format(_completeness['conclusion'][1],
                                         _completeness['conclusion'][0]),
                        _completeness['color'])

            _coherence = _article_data.phase_overall_scores.coherence
            coherence = ("{} ({})".format(_coherence['conclusion'][1],
                                         _coherence['conclusion'][0]),
                        _coherence['color'])

            overall_score_2022 = (
                "{} ({})".format(_article_data.overall_conclusion[1], 
                                 _article_data.overall_conclusion[0]),
                _article_data.overall_conclusion_color)

            art_data = DESCRIPTOR_SUMMARY_2022(
                assessment_summary, progress_assessment, recommendations,
                adequacy, completeness, coherence, overall_score_2022
            )
            articles_data.append(('Art13', art_data))
            # Art14
            # TODO
            data.append(((descr_obj.id, descr_obj.title), articles_data))

        return self.template(data=data)


class CrossCuttingTable2022(BaseNatSummaryView):
    """ CrossCuttingTable2022 """

    template = ViewPageTemplateFile('pt/cross-cutting-2022.pt')
    sections = (
        ("Socio-economic assessment", ["Ad11E", "Ad12E"]),
        ("Impact of climate change", ["Ad13F",]),
        ("Funding of the measures", ["Ad14G", "Ad15G"]),
        ("Links to other policies", ["Ad16G", "Ad17G", "Ad18G"]),
        ("Regional cooperation and transboundary impacts", ["Ad19H", "Ad20H"]),
        ("Public consultation", ["Ad21I", "Ad22I"]),
        ("Administrative processes", ["Ad23J", "Ad24J"]),
    )

    def __init__(self, context, request, assessment_data):
        super(CrossCuttingTable2022, self).__init__(context, request)

        self.assessment_data = assessment_data

    def get_score_for_section(self, section_questions):
        total_score = 0
        total_weight = 0

        for answer in self.assessment_data.answers:
            qcode = answer.question.split(':')[0]

            if qcode not in section_questions:
                continue

            score_achieved = answer.score.score_achieved
            weight = answer.score.weight

            total_score = total_score + (score_achieved * weight)
            total_weight = total_weight + weight

        # import pdb
        # pdb.set_trace()

        final_score = total_score / total_weight if total_weight else 0
        score_value, conclusion = get_overall_conclusion_2022(
            final_score * 100)
        conclusion_color = CONCLUSION_COLOR_TABLE_2022.get(score_value, 0)

        return conclusion_color, conclusion

    def __call__(self):
        data = []

        for section_name, section_questions in self.sections:
            data.append(
                (section_name, self.get_score_for_section(section_questions)))

        return self.template(data=data)


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

    def setup_article_data(self, assessment_data, article_title, descriptor):
        elements = self.questions[article_title][0].get_all_assessed_elements(
            descriptor,
            muids=[]  # self.muids
        )

        res = format_assessment_data_2022(
            article_title,
            elements,
            self.questions[article_title],
            [],
            assessment_data,
            descriptor,
            self.article_weights,
            self
        )

        return res

    def setup_data_cross_cutting(self, assessment_data):
        return self.setup_article_data(
            assessment_data, 'Art1314CrossCutting', 'DCrossCutting')

    def setup_data_completeness_art13(self, assessment_data):
        return self.setup_article_data(
            assessment_data, 'Art13Completeness', 'Completeness')

    def setup_data_completeness_art14(self, assessment_data):
        return self.setup_article_data(
            assessment_data, 'Art13Completeness', 'Completeness')

    def setup_data_art13(self, assessment_data, descriptor_id=''):
        return self.setup_article_data(
            assessment_data, 'Art13', get_descriptor(descriptor_id.upper()))

    def setup_data_art14(self, assessment_data, descriptor_id=''):
        return self.setup_article_data(
            assessment_data, 'Art14', get_descriptor(descriptor_id.upper()))

    def setup_data(self):
        catalog = portal.get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        self.data_cross_cutting = {}
        self.data_completeness_art13 = {}
        self.data_completeness_art14 = {}
        self.data_art13 = {}
        self.data_art14 = {}

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
                    if obj_title == 'Cross-cutting-2022':
                        _data = self.setup_data_cross_cutting(assessment_data)
                        self.data_cross_cutting['All'] = _data

                    elif obj_title == 'Art13-completeness-2022':
                        _data = self.setup_data_completeness_art13(
                            assessment_data)
                        self.data_completeness_art13['All'] = _data

                    elif obj_title == 'Art14-completeness-2022':
                        _data = self.setup_data_completeness_art14(
                            assessment_data)
                        self.data_completeness_art14['All'] = _data

                    elif obj_title == 'Art13':
                        descr_id = obj.aq_parent.id.upper()
                        _data = self.setup_data_art13(
                            assessment_data, descr_id)
                        self.data_art13[descr_id] = _data

                    elif obj_title == 'Art14':
                        descr_id = obj.aq_parent.id.upper()
                        _data = self.setup_data_art14(
                            assessment_data, descr_id)
                        self.data_art14[descr_id] = _data

                    # res.append(obj)

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

        self.setup_data()

        # 1. Introduction
        # introduction = Introduction(self.context, self.request)

        # 4. Descriptor-level assessments
        descriptor_lvl_assess = DescriptorLevelAssessments2022(
            self,
            self.request,
            self.data_art13,
            self.data_art14)
        # descriptor_lvl_assess_view = descriptor_lvl_assess()
        # overall_scores = descriptor_lvl_assess.overall_scores
        # nat_desc_country_folder = descriptor_lvl_assess.nat_desc_country_folder

        # 1. Cross cutting
        cross_cutting = CrossCuttingTable2022(
            self, self.request, self.data_cross_cutting['All'])

        self.tables = [
            report_header,
            # introduction,
            cross_cutting,
            # prog_assess,
            descriptor_lvl_assess,
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
