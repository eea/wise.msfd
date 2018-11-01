import datetime
import logging
from collections import namedtuple

from zope.schema import Choice, Text
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone.api import user
from plone.z3cform.layout import wrap_form
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from wise.msfd.base import EmbeddedForm, MainFormWrapper  # BaseUtil,
from wise.msfd.compliance.base import get_descriptor_elements, get_questions
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView  # , Container
from ..vocabulary import form_structure

# from Products.Five.browser import BrowserView
# from wise.msfd.gescomponents import get_ges_criterions
# from wise.msfd import db, sql2018  # sql,

logger = logging.getLogger('wise.msfd')


# mapping of title: field_name
additional_fields = {
    'Summary': u'Summary',
    # u'Conclusion': 'Conclusion',
    # 'Score': 'Score'
}

summary_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('recommendations', u'Recommendations for Member State')
)


class EditAssessmentDataForm(Form, BaseComplianceView):
    """ Edit the assessment for a national descriptor, for a specific article
    """

    subforms = None
    session_name = 'session_2018'
    template = ViewPageTemplateFile("./pt/nat-desc-edit-assessment-data.pt")

    @property
    def help(self):
        return render_assessment_help(self.criterias)

    @property
    def title(self):
        return 'Edit Assessment for {}'.format(self.descriptor)

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        data, errors = self.extractData()
        # if not errors:
        # TODO: check for errors
        # TODO: check the following code, maybe we don't need the try/except
        try:
            data['assessor'] = user.get_current().getId()
        except:
            data['assessor'] = 'system'
        data['assess_date'] = datetime.date.today()
        self.context.assessment_data = data

    @property
    def fields(self):
        if not self.subforms:
            self.subforms = self.get_subforms()

        fields = []

        for subform in self.subforms:
            fields.extend(subform.fields._data_values)

        return Fields(*fields)

    def _build_subforms(self, questions, criterias):
        """ Build a form of options from a tree of options
        """

        assessment_data = self.context.assessment_data

        forms = []

        # TODO: filter on question klass and national descriptor assessment
        # phase

        for question in questions:
            form = EmbeddedForm(self, self.request)

            form.title = question.definition

            form._question = question

            form._criterias = criterias

            fields = []

            for criteria in criterias:
                for element in criteria.elements:
                    # u'{}_{}'.format(criteria.id, element.id)
                    field_title = criteria.title
                    field_name = '{}_{}_{}_{}'.format(
                        self.article, question.id, criteria.id, element.id
                    )
                    choices = question.answers
                    terms = [SimpleTerm(c, i, c)
                             for i, c in enumerate(choices)]
                    default = assessment_data.get(field_name, None)
                    field = Choice(
                        title=field_title,
                        __name__=field_name,
                        vocabulary=SimpleVocabulary(terms),
                        required=False,
                        default=default,
                    )
                    field._criteria = criteria
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

    # TODO: use memoize
    @property
    def criterias(self):
        els = get_descriptor_elements(
            'compliance/nationaldescriptors/questions/data'
        )

        return els[self.descriptor]

    def get_subforms(self):
        # article = self.get_flattened_data(self)['article'].capitalize()

        qs = get_questions(
            'compliance/nationaldescriptors/questions/data'
        )
        questions = filtered_questions(qs[self.article], self.process_phase())

        subforms = self._build_subforms(questions, self.criterias)

        return subforms


def filtered_questions(questions, phase):
    """ Get the questions appropriate for the phase
    """

    if phase == 'phase3':
        res = [q for q in questions if q.klass == 'coherence']
    else:
        res = [q for q in questions if q.klass != 'coherence']

    return res


EditAssessmentDataView = wrap_form(EditAssessmentDataForm, MainFormWrapper)

Cell = namedtuple('Cell', ['text', 'rowspan'])


help_template = PageTemplateFile('./pt/assessment-question-help.pt')


def render_assessment_help(criterias):
    elements = []
    methods = []

    for c in criterias:
        elements.extend([e.id for e in c.elements])
        methods.append(c.methodological_standard.id)

    element_count = {}

    for k in elements:
        element_count[k] = elements.count(k)

    method_count = {}

    for k in methods:
        method_count[k] = methods.count(k)

    rows = []
    seen = []

    for c in criterias:
        row = []
        cel = c.elements[0]     # TODO: also support multiple elements

        if cel.id not in seen:
            seen.append(cel.id)
            rowspan = element_count[cel.id]
            cell = Cell(cel.definition, rowspan)
            row.append(cell)

        cell = Cell(c.definition, 1)
        row.append(cell)

        meth = c.methodological_standard

        if meth.id not in seen:
            seen.append(meth.id)
            rowspan = method_count[meth.id]
            cell = Cell(meth.definition, rowspan)
            row.append(cell)

        rows.append(row)

    return help_template(rows=rows)
