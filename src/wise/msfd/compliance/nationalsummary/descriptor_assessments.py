#pylint: skip-file
from __future__ import absolute_import
import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.compliance.vocabulary import ASSESSED_ARTICLES
from wise.msfd.gescomponents import DESCRIPTOR_TYPES

from .base import BaseNatSummaryView

logger = logging.getLogger('wise.msfd')


class DescriptorLevelAssessments(BaseNatSummaryView, AssessmentDataMixin):

    template = ViewPageTemplateFile('pt/descriptor-level-assessments.pt')

    article_titles = {
        'Art9': 'Article 9 - GES Determination',
        'Art8': 'Article 8 - Initial Assessment',
        'Art10': 'Article 10 - Environmental Targets',
        'Art11': 'Article 11 - Monitoring Programmes',
    }

    descriptor_types = DESCRIPTOR_TYPES

    def get_article_title(self, article):
        return self.article_name(article)
        # return self.article_titles[article]

    def __call__(self):
        data = self.setup_descriptor_level_assessment_data()

        self.descr_assess_data = data

        return self.template(data=data)
