""" Classes and views to implement the National Descriptors compliance page
"""

import re
from collections import namedtuple
from logging import getLogger

from sqlalchemy import or_

from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql2018
from wise.msfd.compliance.base import get_questions
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.scoring import get_overall_conclusion
from wise.msfd.compliance.vocabulary import SUBREGIONS_TO_REGIONS
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.utils import t2rt

from ..base import BaseComplianceView

CountryStatus = namedtuple('CountryStatus',
                           ['name', 'status', 'state_id', 'url'])

logger = getLogger('wise.msfd')


@db.use_db_session('2018')
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
    section = 'national-descriptors'

    def countries(self):
        countries = self.context.contentValues()
        res = []

        for country in countries:
            state_id, state_label = self.process_phase(country)
            info = CountryStatus(country.Title(), state_label, state_id,
                                 country.absolute_url())

            res.append(info)

        return res


class NationalDescriptorCountryOverview(BaseComplianceView):
    section = 'national-descriptors'

    def get_regions(self):
        return self.context.contentValues()

    def get_descriptors(self, region):
        order = [
            'd1.1', 'd1.2', 'd1.3', 'd1.4', 'd1.5', 'd1.6', 'd2', 'd3', 'd4',
            'd5', 'd6', 'd7', 'd8', 'd9', 'd10', 'd11',
        ]

        return [region[d] for d in order]

    def get_articles(self, desc):
        order = ['art9', 'art8', 'art10']

        return [desc[a] for a in order]


Assessment = namedtuple('Assessment',
                        [
                            'gescomponents',
                            'answers',
                            'assessment_summary',
                            'recommendations',
                            'overall_score',
                            'overall_conclusion'
                        ])
AssessmentRow = namedtuple(
    'AssessmentRow',
    [
        'question',
        'summary',
        'conclusion',
        'conclusion_color',
        'score',
        'values'
    ]


)


# This somehow translates the real value in a color, to be able to compress the
# displayed information in the assessment table

# TODO: this needs to be redone, according to new scoring rules
COLOR_TABLE = {
    2: [1, 4],
    3: [1, 3, 4],
    4: [1, 2, 3, 4],
    5: [1, 2, 3, 4, 5],
    6: [1, 2, 3, 4, 5, 0]      # TODO: this needs to be removed
}


# get the criteria value to be shown in the assessment data 2018 table
def get_crit_val(question, element):
    use_crit = question.use_criteria

    if use_crit == 'targets':
        return element.title

    is_prim = element.is_primary
    crit = element.id

    if use_crit == 'all':
        return crit

    if is_prim and use_crit == 'primary':
        return crit

    if not is_prim and use_crit == 'secondary':
        return crit

    return ''


def format_assessment_data(article, elements, questions, muids, data):
    """ Builds a data structure suitable for display in a template

    This is used to generate the assessment data overview table for 2018

    TODO: this is doing too much. Need to be simplified and refactored.
    """

    answers = []
    overall_score = 0

    for question in questions:
        values = []
        choices = dict(enumerate(question.answers))

        if question.use_criteria == 'none':
            field_name = '{}_{}'.format(article, question.id)
            v = data.get(field_name, None)

            if v is not None:
                label = choices[v]
                color_index = COLOR_TABLE[len(choices)][v]
            else:
                color_index = 0
                label = 'Not filled in'

            value = (label, color_index, u'All criterias')
            values.append(value)
        else:
            for element in elements:
                field_name = '{}_{}_{}'.format(
                    article, question.id, element.id
                )
                v = data.get(field_name, None)

                if v is not None:
                    label = choices[v]
                    try:
                        color_index = COLOR_TABLE[len(choices)][v]
                    except Exception:
                        logger.exception('Invalid color table')
                        color_index = len(COLOR_TABLE)
                        # label = 'Invalid color table'

                else:
                    color_index = 0
                    label = 'Not filled in'

                value = (
                    label,
                    color_index,
                    get_crit_val(question, element)
                )

                values.append(value)

        summary_title = '{}_{}_Summary'.format(article, question.id)
        summary = data.get(summary_title) or ''

        sn = '{}_{}_Score'.format(article, question.id)
        score = data.get(sn, 0)

        cn = '{}_{}_Conclusion'.format(article, question.id)
        conclusion = data.get(cn, '')
        conclusion_color = 5 - data.get(        # TODO: explain this,
                                                # I believe it's wrong
            '{}_{}_RawScore'.format(article, question.id), 5
        )
        overall_score += score     # use raw score or score?

        qr = AssessmentRow(question.definition, summary, conclusion,
                           conclusion_color, score, values)
        answers.append(qr)

    # assessment summary and recommendations
    assess_sum = data.get('%s_assessment_summary' % article)
    recommend = data.get('%s_recommendations' % article)

    # overall_score = overall_score * 100 / len(questions)
    try:
        overall_conclusion = get_overall_conclusion(overall_score)
    except:
        logger.exception("Error in getting overall conclusion")
        overall_conclusion = (1, 'error')

    assessment = Assessment(
        elements,
        answers,
        assess_sum or '-',
        recommend or '-',
        overall_score,
        overall_conclusion
    )

    return assessment


@db.use_db_session('2018')
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


# TODO: use memoization for old data, needs to be called again to get the
# score, to allow delta compute for 2018
#
# @memoize

Assessment2012 = namedtuple(
    'Assessment2012', [
        'gescomponents',
        'criteria',
        'summary',
        'overall_ass',
        'score'
    ]
)

Criteria = namedtuple(
    'Criteria', ['crit_name', 'answer']
)

REGION_RE = re.compile('.+\s\((?P<region>.+)\)$')


def filter_assessment_data_2012(data, region_code, descriptor_criterions):
    """ Filters and formats the raw db data for 2012 assessment data
    """
    gescomponents = [c.id for c in descriptor_criterions]

    assessments = {}

    for row in data:
        fields = row._fields

        def col(col):
            return row[fields.index(col)]

        country = col('Country')

        # The 2012 assessment data have the region in the country name
        # For example: United Kingdom (North East Atlantic)
        # When we display the assessment data (which we do, right now, based on
        # subregion), we want to match the data according to the "big" region

        if '(' in country:
            region = REGION_RE.match(country).groupdict()['region']

            if SUBREGIONS_TO_REGIONS[region_code] != region:
                continue

        summary = col('Conclusions')
        score = col('OverallScore')
        overall_ass = col('OverallAssessment')
        criteria = Criteria(
            col('AssessmentCriteria'),
            t2rt(col('Assessment'))
        )

        if country not in assessments:
            assessment = Assessment2012(
                gescomponents,
                [criteria],
                summary,
                overall_ass,
                score,
            )
            assessments[country] = assessment
        else:
            assessments[country].criteria.append(criteria)

    return assessments


class NationalDescriptorRegionView(BaseComplianceView):
    section = 'national-descriptors'


class NationalDescriptorArticleView(BaseComplianceView):
    section = 'national-descriptors'

    assessment_data_2012_tpl = Template('./pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = Template('./pt/assessment-data-2018.pt')

    @property
    def title(self):
        return "Commision assessment: {} / {} / {} / {} / 2018".format(
            self.country_title,
            self.country_region_name,
            self.descriptor,
            self.article,
        )

    @property
    def criterias(self):
        return self.descriptor_obj.sorted_criterions()      # criterions

    @property
    def questions(self):
        qs = get_questions(
            'compliance/nationaldescriptors/data'
        )

        return qs[self.article]

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        # Assessment data 2012
        descriptor_criterions = get_descriptor(self.descriptor).criterions

        country_name = self._country_folder.title

        try:
            db_data_2012 = get_assessment_data_2012_db(
                country_name,
                self.descriptor,
                self.article
            )
            assessments_2012 = filter_assessment_data_2012(
                db_data_2012,
                self.country_region_code,       # TODO: this will need refactor
                descriptor_criterions,
            )

            self.assessment_data_2012 = self.assessment_data_2012_tpl(
                data=assessments_2012
            )

            if assessments_2012.get(country_name):
                score_2012 = assessments_2012[country_name].score
            else:       # fallback
                ctry = assessments_2012.keys()[0]
                score_2012 = assessments_2012[ctry].score

            report_by, assessors, assess_date, source_file = \
                get_assessment_head_data_2012(db_data_2012)
        except:
            logger.exception("Could not get assessment data for 2012")
            self.assessment_data_2012 = ''
            score_2012 = 100
            report_by, assessors, assess_date, source_file = [
                'Not found'] * 3 + [('Not found', '')]

        # Assessment header 2012

        self.assessment_header_2012 = self.assessment_header_template(
            report_by=report_by,
            assessors=assessors,
            assess_date=assess_date,
            source_file=source_file
        )

        # Assessment data 2018
        data = self.context.saved_assessment_data.last()
        elements = self.questions[0].get_all_assessed_elements(
            self.descriptor_obj, muids=self.muids
        )

        assessment = format_assessment_data(
            self.article,
            elements,
            self.questions,
            self.muids,
            data
        )

        self.assessment_data_2018_html = self.assessment_data_2018_tpl(
            assessment=assessment,
            score_2012=score_2012
        )

        # Assessment header 2018
        report_by_2018 = u'Commission'
        assessors_2018 = self.context.saved_assessment_data.assessors
        assess_date_2018 = data.get('assess_date', u'Not assessed')
        source_file_2018 = ('To be addedd...', '.')

        self.assessment_header_2018_html = self.assessment_header_template(
            report_by=report_by_2018,
            assessors=assessors_2018,
            assess_date=assess_date_2018,
            source_file=source_file_2018,
        )
