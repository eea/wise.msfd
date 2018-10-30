""" Classes and views to implement the National Descriptors compliance page
"""

from collections import namedtuple, defaultdict
from sqlalchemy import or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.gescomponents import get_ges_criterions
from wise.msfd import db, sql2018

from ..base import BaseComplianceView  # , Container
from ..vocabulary import form_structure

CountryStatus = namedtuple('CountryStatus', ['name', 'status', 'url'])


@db.use_db_session('session_2018')
def get_assessment_data_2012_db(*args):
    """ Returns the 2012 assessment data, from COM_Assessments_2012 table
    """

    articles = {
        'Art8': 'Initial assessment (Article 8)',
        'Art9': 'GES (Article 9)',
        'Art10': 'Targets (Article 10)',
    }

    country, descriptor, article = args
    art = articles.get(article)
    descriptor = descriptor.split('.')[0]

    # country = 'Germany'

    t = sql2018.t_COM_Assessments_2012
    count, res = db.get_all_records(
        t,
        t.c.Country.like('%{}%'.format(country)),
        t.c.Descriptor == descriptor,
        or_(t.c.MSFDArticle == art,
            t.c.MSFDArticle.is_(None))
    )

    return res


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


def get_assessment_data_2012(descriptor_criterions, data):
    Assessment2012 = namedtuple(
        'Assessment2012', ['gescomponents', 'criteria',
                           'summary', 'score']
    )

    Criteria = namedtuple(
        'Criteria', ['crit_name', 'answer']
    )

    gescomponents = [c.id for c in descriptor_criterions]

    assessments = {}

    for row in data:
        fields = row._fields

        def get_val(col):
            return row[fields.index(col)]

        country = get_val('Country')
        criteria = [
            Criteria(get_val('AssessmentCriteria'),
                     get_val('Assessment')),
        ]
        summary = get_val('Conclusions')
        score = get_val('OverallScore')

        if country not in assessments:
            # import pdb; pdb.set_trace()
            assessment = Assessment2012(
                gescomponents,
                criteria,
                summary,
                score,
            )
            assessments[country] = assessment
        else:
            assessments[country].criteria.extend(criteria)

    return assessments


class NationalDescriptorArticleView(BaseComplianceView):
    name = 'nat-desc-art-view'
    assessment_data_2012_tpl = Template('./pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = Template('./pt/assessment-data-2018.pt')

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        # Assessment header 2012
        self.assessment_header_2012 = self.assessment_header_template(
            report_by='Commission',
            assessors='Some Body',
            assess_date='2012-12-22',
            source_file=('To be addedd...', '.')
        )

        # Assessment data 2012
        descriptor_criterions = get_ges_criterions(self.descriptor)

        country_name = self._country_folder.title

        data = get_assessment_data_2012_db(
            country_name,
            self.descriptor,
            self.article
        )
        assessments = get_assessment_data_2012(descriptor_criterions,
                                               data)

        self.assessment_data_2012 = self.assessment_data_2012_tpl(
            data=assessments
        )

        # Assessment header 2018
        self.assessment_header_2018 = self.assessment_header_template(
            report_by='Commission',
            assessors='Some Body',
            assess_date='2018-12-22',
            source_file=('To be addedd...', '.')
        )

        # Assessment data 2018
        data = self.context.assessment_data

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
