import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.gescomponents import DESCRIPTOR_TYPES

from .base import BaseNatSummaryView
from .odt_utils import create_heading, create_table_descr

logger = logging.getLogger('wise.msfd')


class DescriptorLevelAssessments(BaseNatSummaryView, AssessmentDataMixin):

    template = ViewPageTemplateFile('pt/descriptor-level-assessments.pt')

    article_titles = {
        'Art9': 'Article 9 - GES Determination',
        'Art8': 'Article 8 - Initial Assessment',
        'Art10': 'Article 10 - Environmental Targets'
    }

    descriptor_types = DESCRIPTOR_TYPES

    def get_article_title(self, article):

        return self.article_titles[article]

    def get_odt_data(self, document):
        res = []

        h = create_heading(1, u"Descriptor-level assessments")
        res.append(h)

        all_data = self.descr_assess_data

        for region in all_data:
            h = create_heading(2, region[0])
            res.append(h)
            all_descriptors_data = region[1]

            for descriptor_type in self.descriptor_types:
                h = create_heading(3, descriptor_type[0])
                res.append(h)

                for descriptor in descriptor_type[1]:
                    descriptor_data = [
                        d
                        for d in all_descriptors_data
                        if d[0][0] == descriptor
                    ][0]
                    h = create_heading(4, descriptor_data[0][1])
                    res.append(h)

                    articles = descriptor_data[1]
                    for article in articles:
                        h = create_heading(5, article[0])
                        res.append(h)
                        article_data = article[1]

                        t = create_table_descr(document, article_data)

                        res.append(t)

        return res

    def __call__(self):
        data = self.setup_descriptor_level_assessment_data()

        self.descr_assess_data = data

        return self.template(data=data)
