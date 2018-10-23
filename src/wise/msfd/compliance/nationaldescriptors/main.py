""" Classes and views to implement the National Descriptors compliance page
"""

from collections import namedtuple  # defaultdict,

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.gescomponents import get_ges_criterions

from ..base import BaseComplianceView  # , Container
from ..vocabulary import form_structure

CountryStatus = namedtuple('CountryStatus', ['name', 'status', 'url'])


def get_assessment_data_2012(*args):
    """ Returns the 2012 assessment data, from COM_Assessments_2012 table
    """

    return []


def get_assessment_data_2018(*args):
    """ Returns the 2018 assessment data, from COM_Assessments table
    """

    return []


class NationalDescriptorsOverview(BaseComplianceView):
    name = 'nat-desc-start'

    def countries(self):
        countries = self.context.contentValues()

        return [CountryStatus(country.Title(), self.process_phase(country),
                              country.absolute_url()) for country in countries]


class NationalDescriptorCountryOverview(BaseComplianceView):
    name = 'nat-desc-country-start'

    def get_articles(self):
        return ['Art8', 'Art9', 'Art10']

    def get_descriptors(self):
        return self.context.contentValues()


Assessment = namedtuple('Assessment',
                        [
                            'gescomponents',
                            'answers',
                            'summary',
                            'recommendations',
                         ])
AssessmentRow = namedtuple(
    'AssessmentRow',
    ['question', 'summary', 'conclusion', 'score', 'values']
)


def get_assessment_data(descriptor_criterions, question_tree, data):
    """ Builds a data structure suitable for display in a template
    """

    # tree = question_tree
    answers = []
    gescomponents = [c.id for c in descriptor_criterions]

    for tree in question_tree.children:
        base_name = tree.name       # can be Adequacy, Consistency or Coherence

        for row in tree.children:
            row_name = row.name     # such as "status assessment"

            values = []

            for crit in descriptor_criterions:
                field_name = '{}_{}_{}'.format(base_name, row_name, crit.id)
                value = data.get(field_name, '-') or '-'
                # values.append((crit.id, value))
                values.append(value)

            question = "{} of {}".format(base_name, row_name)
            summary = 'summary here'
            conclusion = 'conclusion here'
            score = '1'

            qr = AssessmentRow(question, summary, conclusion, score, values)
            answers.append(qr)

    assessment = Assessment(
        gescomponents,
        answers,
        'descriptor summary',
        'descriptor recommendations',
    )

    return assessment


class NationalDescriptorArticleView(BaseComplianceView):
    name = 'nat-desc-art-view'
    assessment_data_2012_tpl = Template('./pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = Template('./pt/assessment-data-2018.pt')

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        data = get_assessment_data_2012(
            self.country_code,
            self.descriptor,
            self.article
        )
        self.assessment_data_2012 = self.assessment_data_2012_tpl(data=data)

        # data = get_assessment_data_2018(
        #     self.country_code,
        #     self.descriptor,
        #     self.article
        # )

        data = self.context.assessment_data

        descriptor_criterions = get_ges_criterions(self.descriptor)
        question_tree = form_structure[self.article]

        assessment = get_assessment_data(
            descriptor_criterions,
            question_tree,
            data
        )
        # print assessment

        self.assessment_data_2018 = self.assessment_data_2018_tpl(
            assessment=assessment
        )
