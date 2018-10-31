""" Classes and views to implement the National Descriptors compliance page
"""

from collections import namedtuple  # , defaultdict

from sqlalchemy import or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql2018
from wise.msfd.compliance.base import get_descriptor_elements, get_questions
from wise.msfd.gescomponents import get_ges_criterions

from ..base import BaseComplianceView  # , Container

# from ..vocabulary import form_structure

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


def get_assessment_data(article, criterias, questions, data):
    """ Builds a data structure suitable for display in a template
    """

    # tree = question_tree
    answers = []
    gescomponents = [c.id for c in criterias]

    for question in questions:
        # base_name = tree.name
        # # can be Adequacy, Consistency or Coherence
        # base_name = question.klass
        # row_name = question.id
        values = []

        for criteria in criterias:
            for element in criteria.elements:
                field_name = '{}_{}_{}_{}'.format(
                        article, question.id, criteria.id, element.id
                    )
                value = data.get(field_name, '-') or '-'
                values.append(value)

        summary = 'summary here'
        conclusion = 'conclusion here'
        score = '1'

        qr = AssessmentRow(question.definition,
                           summary, conclusion, score, values)
        answers.append(qr)

        # for row in tree.children:
        #     row_name = row.name     # such as "status assessment"
        #
        #     values = []
        #
        #     for crit in descriptor_criterions:
        #         field_name = '{}_{}_{}'.format(base_name, row_name, crit.id)
        #         value = data.get(field_name, '-') or '-'
        #         # values.append((crit.id, value))
        #         values.append(value)
        #
        #     question = "{} of {}".format(base_name, row_name)
        #     summary = 'summary here'
        #     conclusion = 'conclusion here'
        #     score = '1'
        #
        #     qr = AssessmentRow(question, summary, conclusion, score, values)
        #     answers.append(qr)

    assessment = Assessment(
        gescomponents,
        answers,
        'descriptor summary',
        'descriptor recommendations',
    )

    return assessment


@db.use_db_session('session_2018')
def get_assessment_head_data_2012(data):
    if not data:
        return ['Not found'] * 3 + [('Not found', '')]

    ids = [x.COM_General_Id for x in data]
    ids = tuple(set(ids))

    t = sql2018.COMGeneral
    count, res = db.get_all_records(
        t,
        t.Id.in_(ids)
    )

    if count:
        report_by = res[0].ReportBy
        assessors = res[0].Assessors
        assess_date = res[0].DateAssessed
        com_report = res[0].CommissionReport

        return (report_by,
                assessors,
                assess_date,
                (com_report.split('/')[-1], com_report))

    return ['Not found'] * 3 + [('Not found', '')]


def get_assessment_data_2012(descriptor_criterions, data):
    Assessment2012 = namedtuple(
        'Assessment2012', ['gescomponents', 'criteria',
                           'summary', 'overall_ass', 'score']
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
        overall_ass = get_val('OverallAssessment')

        if country not in assessments:
            # import pdb; pdb.set_trace()
            assessment = Assessment2012(
                gescomponents,
                criteria,
                summary,
                overall_ass,
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

    @property
    def criterias(self):
        els = get_descriptor_elements(
            'compliance/nationaldescriptors/questions/data'
        )

        return els[self.descriptor]

    @property
    def questions(self):
        qs = get_questions(
            'compliance/nationaldescriptors/questions/data'
        )

        return qs[self.article]

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        # Assessment data 2012
        descriptor_criterions = get_ges_criterions(self.descriptor)

        country_name = self._country_folder.title

        data = get_assessment_data_2012_db(
            country_name,
            self.descriptor,
            self.article
        )
        assessments = get_assessment_data_2012(
            descriptor_criterions,
            data
        )

        self.assessment_data_2012 = self.assessment_data_2012_tpl(
            data=assessments
        )

        # Assessment header 2012
        report_by, assessors, assess_date, source_file = \
            get_assessment_head_data_2012(data)

        self.assessment_header_2012 = self.assessment_header_template(
            report_by=report_by,
            assessors=assessors,
            assess_date=assess_date,
            source_file=source_file
        )

        # Assessment data 2018
        data = self.context.assessment_data

        assessment = get_assessment_data(
            self.article,
            self.criterias,
            self.questions,
            data
        )
        # print assessment

        self.assessment_data_2018 = self.assessment_data_2018_tpl(
            assessment=assessment
        )

        # Assessment header 2018
        report_by_2018 = u'Commission'
        assessors_2018 = data.get('assessor', u'Not assessed')
        assess_date_2018 = data.get('assess_date', u'Not assessed')
        source_file_2018 = ('To be addedd...', '.')

        self.assessment_header_2018 = self.assessment_header_template(
            report_by=report_by_2018,
            assessors=assessors_2018,
            assess_date=assess_date_2018,
            source_file=source_file_2018,
        )
