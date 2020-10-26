import datetime
import logging
from collections import namedtuple

from persistent.list import PersistentList
from pkg_resources import resource_filename
from zope.schema import Choice, Text
from zope.interface import implements
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from AccessControl import Unauthorized
from plone.api import user
from plone.z3cform.layout import wrap_form
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from pyexcel_xlsx import get_data
from wise.msfd.base import EmbeddedForm, MainFormWrapper
from wise.msfd.compliance.assessment import (PHASES,
                                             EditAssessmentDataFormMain,
                                             EditAssessmentSummaryForm,
                                             additional_fields,
                                             reg_summary_fields,
                                             render_assessment_help)
from wise.msfd.compliance.base import REG_DESC_QUESTIONS
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.interfaces import IRegionalEditAssessmentForm
from wise.msfd.utils import t2rt
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields

from .base import BaseRegComplianceView

logger = logging.getLogger('wise.msfd')


Assessment_2012 = namedtuple(
    'Assessment_2012',
    ['region', 'descriptor', 'article', 'coherence', 'summary',
     'overall_score', 'conclusion',
     'report_by', 'assessment_by', 'date_assessed', 'commission_report'
     ]
)


def parse_assessments_2012_file():
    f = resource_filename(
        'wise.msfd', 'data/Regional_Descriptors_2012_assessment.xlsx'
    )

    res = []

    with open(f, 'rb') as file:
        sheets = get_data(file)
        rows = sheets['Assessment']

        for row in rows[1:]:
            if not row:
                break

            report_by = 'Commission'
            assessment_by = 'Milieu'
            date_assessed = datetime.datetime.strptime('2019-09-20',
                                                       '%Y-%m-%d')
            commission_report = 'http://ec.europa.eu/environment/marine/' \
                                'eu-coast-and-marine-policy/implementation/' \
                                'pdf/national_reports.zip'

            row.extend(
                [report_by, assessment_by, date_assessed, commission_report]
            )

            res.append(Assessment_2012(*row))

    return res


ASSESSMENTS_2012 = parse_assessments_2012_file()


class RegDescEditAssessmentSummaryForm(BaseRegComplianceView,
                                       EditAssessmentSummaryForm):
    """ Needed to override EditAssessmentSummaryForm's methods """


class RegEditAssessmentFormWrapper(MainFormWrapper):
    implements(IRegionalEditAssessmentForm)


class RegDescEditAssessmentDataForm(BaseRegComplianceView,
                                    EditAssessmentDataFormMain):
    """ Edit the assessment for a regional descriptor, for a specific article
    """

    subforms = None
    year = session_name = '2018'
    template = ViewPageTemplateFile("pt/edit-assessment-data.pt")
    _questions = REG_DESC_QUESTIONS

    @property
    def title(self):
        return "Edit Commission assessment / {} / 2018 / {} / {}".format(
            self.article,
            self.descriptor,
            self.country_region_code,
        )

    def format_last_change(self, last_update):
        default = '-'
        toLocalizedTime = self.context.toLocalizedTime
        # convert the last_update datetime to local timezone
        local_time = toLocalizedTime(last_update, long_format=True) or default

        if local_time == default:
            return default

        # parse the datestring to reformat into a clearer format
        local_time = datetime.datetime.strptime(
            local_time, '%b %d, %Y %I:%M %p'
        )
        local_time = datetime.datetime.strftime(
            local_time, "%Y-%m-%d %H:%M"
        )

        return local_time

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):

        # roles = get_roles(obj=self.context)

        if self.read_only_access:
            raise Unauthorized

        context = self.context

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        last = self.context.saved_assessment_data.last().copy()
        datetime_now = datetime.datetime.now().replace(microsecond=0)

        data, errors = self.extractData()
        # if not errors:
        # TODO: check for errors

        for question in self.questions:
            # countries = self.get_available_countries()
            elements = question.get_assessed_elements(self.descriptor_obj,
                                                      muids=[])

            values = []
            score = None

            if question.use_criteria == 'none':
                field_name = '{}_{}'.format(self.article, question.id)
                values.append(data.get(field_name, None))

            for element in elements:
                field_name = '{}_{}_{}'.format(
                    self.article, question.id, element.id
                )
                values.append(data.get(field_name, None))

            # score is updated if ALL of the fields have been answered

            if values and None not in values:
                score = question.calculate_score(self.descriptor, values)

            name = '{}_{}_Score'.format(self.article, question.id)
            last_upd = '{}_{}_Last_update'.format(self.article, question.id)
            logger.info("Set score: %s - %s", name, score)
            data[name] = score

            last_values = last.get(name, [])
            last_values = getattr(last_values, 'values', '')
            score_values = getattr(score, 'values', '')

            if last_values != score_values:
                data[last_upd] = datetime_now

            # check if _Summary text is changed, and update _Last_update field
            summary = '{}_{}_Summary'.format(self.article, question.id)

            if last.get(summary, '') != data.get(summary, ''):
                data[last_upd] = datetime_now

        last_upd = "{}_assess_summary_last_upd".format(
            self.article
        )
        name = "{}_assessment_summary".format(self.article)

        if last.get(name, '') != data.get(name, ''):
            data[last_upd] = datetime_now

        overall_score = 0

        for k, v in data.items():
            if not k.endswith('_Score'):
                continue
            else:
                overall_score += getattr(v, 'weighted_score', 0)

        data['OverallScore'] = overall_score

        try:
            data['assessor'] = user.get_current().getId()
        except:
            data['assessor'] = 'system'

        data['assess_date'] = datetime.date.today()

        if last != data:
            last.update(data)
            self.context.saved_assessment_data.append(last)

        url = self.context.absolute_url() + '/@@edit-assessment-data-2018'
        self.request.response.setHeader('Content-Type', 'text/html')

        return self.request.response.redirect(url)

    def is_disabled(self, question):
        return False
        state, _ = self.current_phase
        disabled = question.klass not in PHASES.get(state, ())

        return disabled

    def get_subforms(self):
        """ Build a form of options from a tree of options

        TODO: this method does too much, should be refactored
        """
        assessment_data = {}

        if hasattr(self.context, 'saved_assessment_data'):
            assessment_data = self.context.saved_assessment_data.last()

        assess_date = '-'
        forms = []

        for question in self.questions:
            phase = [
                k

                for k, v in PHASES.items()

                if question.klass in v
            ][0]

            elements = question.get_assessed_elements(
                self.descriptor_obj, muids=[]
            )

            form = EmbeddedForm(self, self.request)
            form.title = question.definition
            last_upd = '{}_{}_Last_update'.format(self.article, question.id)
            form._last_update = assessment_data.get(last_upd, assess_date)
            form._assessor = assessment_data.get('assessor', '-')
            form._question_type = question.klass
            form._question_phase = phase
            form._question = question
            form._elements = elements
            form._disabled = self.is_disabled(question)

            fields = []

            if not elements:  # and question.use_criteria == 'none'
                field_title = u'All criteria'
                field_name = '{}_{}'.format(self.article, question.id)
                choices = question.answers

                terms = [SimpleTerm(token=i, value=i, title=c)
                         for i, c in enumerate(choices)]

                # Add 'Not relevant' to choices list
                # terms.extend([
                #     SimpleTerm(token=len(terms) + 1,
                #                value=None,
                #                title=u'Not relevant')
                # ])

                default = assessment_data.get(field_name, None)
                field = Choice(
                    title=field_title,
                    __name__=field_name,
                    vocabulary=SimpleVocabulary(terms),
                    required=False,
                    default=default,
                )
                # field._criteria = criteria
                fields.append(field)

            for element in elements:
                field_title = element.title
                field_name = '{}_{}_{}'.format(
                    self.article, question.id, element.id
                )
                choices = question.answers
                terms = [SimpleTerm(token=i, value=i, title=c)
                         for i, c in enumerate(choices)]

                default = assessment_data.get(field_name, None)
                field = Choice(
                    title=unicode(field_title),
                    __name__=field_name,
                    vocabulary=SimpleVocabulary(terms),
                    required=False,
                    default=default,
                )
                field._element = element
                fields.append(field)

            for name, title in additional_fields.items():
                _name = '{}_{}_{}'.format(self.article, question.id, name)

                default = assessment_data.get(_name, None)
                _field = Text(title=title,
                              __name__=_name, required=False, default=default)

                fields.append(_field)

            form.fields = Fields(*fields)
            forms.append(form)

        assessment_summary_form = EmbeddedForm(self, self.request)
        assessment_summary_form.title = u"Assessment summary"
        last_upd = '{}_assess_summary_last_upd'.format(self.article)
        assessment_summary_form._last_update = assessment_data.get(
            last_upd, assess_date
        )
        assessment_summary_form._assessor = assessment_data.get(
            'assessor', '-'
        )
        assessment_summary_form.subtitle = u''
        assessment_summary_form._disabled = self.read_only_access
        asf_fields = []

        for name, title in reg_summary_fields:
            _name = '{}_{}'.format(
                self.article, name
            )

            default = assessment_data.get(_name, None)
            _field = Text(title=title,
                          __name__=_name, required=False, default=default)
            asf_fields.append(_field)

        assessment_summary_form.fields = Fields(*asf_fields)

        forms.append(assessment_summary_form)

        return forms


RegDescEditAssessmentDataView = wrap_form(
    RegDescEditAssessmentDataForm, RegEditAssessmentFormWrapper)
