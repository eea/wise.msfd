#pylint: skip-file
from __future__ import absolute_import
import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.interfaces import (IDescriptorFolder,
                                             IRegionalDescriptorAssessment)
from wise.msfd.compliance.assessment import DESCRIPTOR_SUMMARY
from wise.msfd.compliance.scoring import OverallScores
from wise.msfd.utils import fixedorder_sortkey, t2rt

from ..nationalsummary.descriptor_assessments import DescriptorLevelAssessments
from ..regionaldescriptors.main import ARTICLE_WEIGHTS
from .base import BaseRegSummaryView

logger = logging.getLogger('wise.msfd')


class RegDescriptorLevelAssessments(BaseRegSummaryView,
                                    DescriptorLevelAssessments):
    """ Make National summary code compatible for Regional summary """

    template = ViewPageTemplateFile('pt/descriptor-level-assessments.pt')

    def _get_article_data(self, region_code, descriptor,
                          assess_data, article):
        phase_overall_scores = OverallScores(ARTICLE_WEIGHTS, article)

        # Get the coherence scores from regional descriptors
        phase_overall_scores.coherence = self.get_coherence_data(
            region_code, descriptor, article
        )

        cscore_val, conclusion = phase_overall_scores.coherence['conclusion']
        # score = phase_overall_scores.get_score_for_phase('coherence')
        coherence = ("{} ({})".format(conclusion, cscore_val),
                     phase_overall_scores.coherence['color'])

        overallscore_val, score = phase_overall_scores.get_overall_score(
            article, is_national=False
        )

        conclusion = self.get_conclusion(overallscore_val)
        overall_score_2018 = (
            "{} ({})".format(conclusion, overallscore_val),
            self.get_color_for_score(overallscore_val)
        )

        assessment_summary = t2rt(
            assess_data.get('{}_assessment_summary'.format(article)) or '-'
        )
        progress_assessment = t2rt(
            assess_data.get('{}_progress'.format(article)) or '-'
        )
        recommendations = t2rt(
            assess_data.get('{}_recommendations'.format(article)) or '-'
        )
        __key_2018 = (region_code, descriptor, article, '2018')
        self.overall_scores[__key_2018] = overall_score_2018

        reg_assess_2012 = self.get_reg_assessments_data_2012(
            article, region_code, descriptor
        )
        coherence_2012 = ('-', '0')
        coherence_change_since_2012 = '-'

        if reg_assess_2012:
            __score = int(reg_assess_2012[0].overall_score)
            coherence_2012 = ("{} ({})".format(reg_assess_2012[0].conclusion,
                                               __score),
                              self.get_color_for_score(__score))
            if cscore_val == '-':
                cscore_val = 0

            coherence_change_since_2012 = int(cscore_val - __score)

            __key_2012 = (region_code, descriptor, article, '2012')
            self.overall_scores[__key_2012] = coherence_2012

        res = DESCRIPTOR_SUMMARY(
            assessment_summary, progress_assessment, recommendations,
            "", "", coherence, overall_score_2018,
            "", "",
            coherence_2012, coherence_change_since_2012
        )

        return res

    def setup_descriptor_level_assessment_data(self):
        """ Setup the regional assessments data for a region

        :return: res =  [("Baltic Sea", [
                    ("D7 - Hydrographical changes", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                    ("D1.4 - Birds", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                ]
            )]
        """
        self.overall_scores = {}
        res = []

        region_folder = [
            region
            for region in self._reg_desc_region_folders
            if region.id == self.region_code.lower()
        ][0]

        self.reg_desc_region_folder = region_folder
        region_code = region_folder.id
        region_name = region_folder.title

        descriptor_data = []
        descriptor_folders = self.filter_contentvalues_by_iface(
            region_folder, IDescriptorFolder
        )

        for descriptor_folder in descriptor_folders:
            desc_id = descriptor_folder.id.upper()
            if desc_id == 'D1':
                continue

            desc_name = descriptor_folder.title
            articles = []
            article_folders = self.filter_contentvalues_by_iface(
                descriptor_folder, IRegionalDescriptorAssessment
            )

            for article_folder in article_folders:
                article = article_folder.title

                if article in ('Art11', ):
                    continue

                assess_data = self._get_assessment_data(article_folder)
                article_data = self._get_article_data(
                    region_code.upper(), desc_id, assess_data, article
                )
                articles.append((article, article_data))

            articles = sorted(
                articles,
                key=lambda i: fixedorder_sortkey(i[0], self.ARTICLE_ORDER)
            )

            descriptor_data.append(
                ((desc_id, desc_name), articles)
            )

        res.append((region_name, descriptor_data))

        return res