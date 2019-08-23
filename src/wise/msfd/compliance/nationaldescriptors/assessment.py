import datetime
import logging

from zope.schema import Choice, Text
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from AccessControl import Unauthorized
from persistent.list import PersistentList
from plone.api import user
# from plone.api.user import get_roles
from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd.base import EditAssessmentFormWrapper as MainFormWrapper
from wise.msfd.base import EmbeddedForm
from wise.msfd.compliance.assessment import (PHASES, additional_fields,
                                             render_assessment_help,
                                             summary_fields)
from wise.msfd.compliance.base import get_questions
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.gescomponents import get_descriptor  # get_descriptor_elements
from wise.msfd.translation import get_translated, retrieve_translation
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .base import BaseView

# from zope.security import checkPermission
# PageTemplateFile,

logger = logging.getLogger('wise.msfd')


class EditAssessmentHistory(BaseView, BrowserView):
    def report_assessment(self):
        saved_assessment_data = self.context.saved_assessment_data
        sorted_tables = []

        for table_pair in saved_assessment_data:
            sorted_tables.append(
                sorted(table_pair.items(), key=lambda x: x[0]))

        return sorted_tables[::-1]

    @property
    def title(self):
        return "Edit Assessment History for: {}/ {}/ {}".format(
            self.country_region_name,
            self.descriptor,
            self.article,
        )


class EditAssessmentDataForm(Form, BaseView):
    """ Edit the assessment for a national descriptor, for a specific article
    """
    name = 'art-view'
    section = 'national-descriptors'

    subforms = None
    year = session_name = '2018'
    template = ViewPageTemplateFile("./pt/edit-assessment-data.pt")
    _questions = get_questions()

    @property
    def criterias(self):
        return self.descriptor_obj.sorted_criterions()      # criterions

    @property
    def help(self):
        return render_assessment_help(self.criterias, self.descriptor)

    @property
    def title(self):
        return "Edit Comission assessment: {}/ {}/ {}/ {}/ 2018".format(
            self.country_title,
            self.country_region_name,
            self.descriptor,
            self.article,
        )

    @buttonAndHandler(u'Translate targets', name='translate')
    def handle_translate(self, action):
        seen = set()

        for question in self.questions:
            elements = question.get_assessed_elements(
                self.descriptor_obj, muids=self.muids
            )

            for element in elements:
                value = element.definition

                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        url = self.context.absolute_url() + '/@@edit-assessment-data-2018'
        self.request.response.setHeader('Content-Type', 'text/html')

        return self.request.response.redirect(url)

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        # BBB code, useful for development
        context = self.context

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()
        last = self.context.saved_assessment_data.last()

        # roles = get_roles(obj=self.context)
        # if 'Contributor' not in roles and ('Manager' not in roles)\
        #         and 'Editor' not in roles:

        if self.read_only_access:
            raise Unauthorized

        data, errors = self.extractData()
        # if not errors:
        # TODO: check for errors

        datetime_now = datetime.datetime.now().replace(microsecond=0)

        for question in self.questions:
            elements = question.get_assessed_elements(self.descriptor_obj,
                                                      muids=self.muids)

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
        """ Returns True if question is not editable
        """

        if self.read_only_access:
            return True

        state, _ = self.current_phase
        is_disabled = question.klass not in PHASES.get(state, ())

        return is_disabled

    @property
    def fields(self):
        if not self.subforms:
            self.subforms = self.get_subforms()

        fields = []

        for subform in self.subforms:
            fields.extend(subform.fields._data_values)

        return Fields(*fields)

    @property       # TODO: memoize
    def descriptor_obj(self):
        return get_descriptor(self.descriptor)

    # TODO: use memoize
    @property
    def questions(self):
        qs = self._questions[self.article]

        return qs

    def get_subforms(self):
        """ Build a form of options from a tree of options

        TODO: this method does too much, should be refactored
        """
        assessment_data = {}

        if hasattr(self.context, 'saved_assessment_data'):
            assessment_data = self.context.saved_assessment_data.last()
        # assess_date = assessment_data.get('assess_date')
        # assess_date = hasattr(assess_date, 'strftime') \
        #     and assess_date.strftime('%d %b %Y') or '-'
        assess_date = '-'

        forms = []

        # is_ec_user = not self.can_comment_tl
        # is_other_tl = not (self.can_comment_tl or self.can_comment_tl)

        for question in self.questions:
            phase = [
                k

                for k, v in PHASES.items()

                if question.klass in v
            ][0]

            elements = question.get_assessed_elements(
                self.descriptor_obj, muids=self.muids
            )

            form = EmbeddedForm(self, self.request)
            form.title = question.definition
            last_upd = '{}_{}_Last_update'.format(self.article, question.id)
            form._last_update = assessment_data.get(last_upd, assess_date)
            form._question_type = question.klass
            form._question_phase = phase
            form._question = question
            form._elements = elements
            form._disabled = self.is_disabled(question)
            # or is_other_tl or is_ec_user

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
                    self.article, question.id, element.id       # , element
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

        # TODO assessment summary form moved to assesment overview page
        assessment_summary_form = EmbeddedForm(self, self.request)
        assessment_summary_form.title = u"Assessment summary"
        last_upd = '{}_assess_summary_last_upd'.format(self.article)
        assessment_summary_form._last_update = assessment_data.get(
            last_upd, assess_date
        )
        assessment_summary_form.subtitle = u''
        assessment_summary_form._disabled = (
            self.read_only_access  # or not self.can_comment_tl
        )
        asf_fields = []

        for name, title in summary_fields:
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

    def get_translated(self, value):
        translated = get_translated(value, self.country_code)

        if translated:
            return translated

        return value


EditAssessmentDataView = wrap_form(EditAssessmentDataForm, MainFormWrapper)
