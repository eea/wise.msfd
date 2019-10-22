import logging
from collections import namedtuple

from zope.schema import Text

from AccessControl import Unauthorized
from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.interfaces import IEditAssessorsForm
from wise.msfd.compliance.regionaldescriptors.base import BaseRegComplianceView
from wise.msfd.compliance.utils import get_assessors, set_assessors
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .base import BaseComplianceView

logger = logging.getLogger('wise.msfd')

# TODO which question type belongs to which phase?
PHASES = {
    'phase1': ('adequacy', 'consistency'),
    'phase2': ('coherence', ),
    'phase3': (),
}

# mapping of title: field_name
additional_fields = {
    'Summary': u'Summary',
}

summary_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress assessment'),
    ('recommendations', u'Recommendations for Member State'),
)

# TODO not used
progress_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress assessment'),
    ('recommendations', u'Recommendations for Member State'),
)


class EditAssessorsForm(Form, BaseComplianceView):
    """ Assessment settings form, used to edit the assessors list

    /compliance-module/national-descriptors-assessments/edit-assessors
    """

    ignoreContext = True
    name = 'edit-assessors'
    section = 'compliance-admin'
    title = u'Edit assessed by'
    fields = Fields(IEditAssessorsForm)
    template = ViewPageTemplateFile('pt/edit-assessors.pt')

    @buttonAndHandler(u'Save', name='Save')
    def hande_save(self, action):
        data, errors = self.extractData()

        if not errors:
            value = data.get('assessed_by', '')
            value = ', '.join(value.split('\r\n'))
            set_assessors(value)

    def updateWidgets(self):
        super(EditAssessorsForm, self).updateWidgets()
        assessed_by_field = self.fields['assessed_by'].field
        default = assessed_by_field.default
        annot_assessors = get_assessors()
        annot_assessors = '\r\n'.join(annot_assessors.split(', '))

        if annot_assessors and default != annot_assessors:
            assessed_by_field.default = annot_assessors
            self.update()


class ViewAssessmentSummaryForm(BaseComplianceView):
    """ Render the assessment summary, progress assessment
    and recommendations for member state for view

    """

    template = ViewPageTemplateFile("pt/assessment-summary-form-view.pt")

    @property
    def summary_data(self):
        saved_data = self.context.saved_assessment_data.last()

        _fields = []

        for name, title in summary_fields:
            _name = '{}_{}'.format(
                self.article, name
            )

            text = saved_data.get(_name, None)

            _fields.append((title, text))

        return _fields

    def __call__(self):
        fields = self.summary_data

        return self.template(fields=fields)


class ViewAssessmentSummaryFormRegional(BaseRegComplianceView,
                                        ViewAssessmentSummaryForm):
    """ Render the assessment summary, progress assessment
    and recommendations for member state for view

        Wrapper class for regional descriptors
    """


class EditAssessmentSummaryForm(Form, BaseComplianceView):
    """ Edit the assessment summary

    Fields are: summary, recommendations, progress assessment
    """
    # TODO unused

    title = u"Edit progress assessment"
    template = ViewPageTemplateFile("pt/inline-form.pt")
    _saved = False

    @property
    def fields(self):
        saved_data = self.context.saved_assessment_data.last()

        _fields = []

        for name, title in progress_fields:
            _name = '{}_{}'.format(
                self.article, name
            )

            default = saved_data.get(_name, None)
            _field = Text(title=title,
                          __name__=_name, required=False, default=default)
            _fields.append(_field)

        return Fields(*_fields)

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        if self.read_only_access:
            raise Unauthorized

        data, errors = self.extractData()

        if errors:
            return

        context = self.context

        # BBB code, useful in development

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        saved_data = self.context.saved_assessment_data.last()

        if not saved_data:
            self.context.saved_assessment_data.append(data)
        else:
            saved_data.update(data)
        self.context.saved_assessment_data._p_changed = True

    def nextURL(self):
        return self.context.absolute_url()

    @property
    def action(self):
        return self.context.absolute_url() + '/@@edit-assessment-summary'

    def render(self):
        if self.request.method == 'POST':
            Form.render(self)

            return self.request.response.redirect(self.nextURL())

        return Form.render(self)


Cell = namedtuple('Cell', ['text', 'rowspan'])


help_template = PageTemplateFile('pt/assessment-question-help.pt')


def render_assessment_help(criterias, descriptor):
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

        if not c.elements:
            logger.info("Skipping %r from help rendering", c)

            continue
        cel = c.elements[0]     # TODO: also support multiple elements

        if cel.id not in seen:
            seen.append(cel.id)
            rowspan = element_count[cel.id]
            cell = Cell(cel.definition, rowspan)
            row.append(cell)

        prim_label = c.is_primary(descriptor) and 'primary' or 'secondary'
        cdef = u"<strong>{} ({})</strong><br/>{}".format(
            c.id, prim_label, c.definition
        )

        cell = Cell(cdef, 1)
        row.append(cell)

        meth = c.methodological_standard

        if meth.id not in seen:
            seen.append(meth.id)
            rowspan = method_count[meth.id]
            cell = Cell(meth.definition, rowspan)
            row.append(cell)

        rows.append(row)

    return help_template(rows=rows)
