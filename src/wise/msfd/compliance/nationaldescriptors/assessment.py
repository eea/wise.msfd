import datetime
import logging

from zope.schema import Choice, Text
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone.api import user
from plone.z3cform.layout import wrap_form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.base import EmbededForm, MainFormWrapper  # BaseUtil,
from wise.msfd.compliance.base import get_descriptor_elements, get_questions
from wise.msfd.gescomponents import get_ges_criterions
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView  # , Container
from ..vocabulary import form_structure

# from wise.msfd import db, sql2018  # sql,

logger = logging.getLogger('wise.msfd')


# mapping of title: field_name
additional_fields = {
    u'Summary': 'Description_Summary',
    u'Conclusion': 'Conclusion',
    # 'Score': 'Score'
}

summary_fields = {
    'assessment_summary': u'Description_Summary',
    'recommendations': u'RecommendationsArt9'
}


class EditAssessmentDataForm(Form, BaseComplianceView):
    """ Edit the assessment for a national descriptor, for a specific article
    """

    subforms = None
    session_name = 'session_2018'
    template = ViewPageTemplateFile("./pt/nat-desc-edit-assessment-data.pt")

    @property
    def title(self):
        return 'Edit Assessment for {}'.format(self.descriptor)

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        data, errors = self.extractData()
        # if not errors:
        # TODO: check for errors
        data['assessor'] = user.get_current()
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

    def _build_subforms(self, questions, criteria):
        """ Build a form of options from a tree of options
        """
        import pdb; pdb.set_trace()

        # base_name = tree.name
        # descriptor_criterions = get_ges_criterions(self.descriptor)
        #
        # forms = []
        #
        # assessment_data = self.context.assessment_data
        #
        # for row in tree.children:
        #     row_name = row.name
        #
        #     # TODO: we no longer need EmbededForm here, we should get rid of
        #
        #     form = EmbededForm(self, self.request)
        #
        #     form.form_name = 'form' + row_name
        #     fields = []
        #
        #     form.title = '{}: {}'.format(base_name, row_name)
        #
        #     for crit in descriptor_criterions:
        #         field_title = u'{} {}: {}'.format(base_name, row_name,
        #                                           crit.title)
        #         field_name = '{}_{}_{}'.format(base_name, row_name, crit.id)
        #         # choices = [''] + [x.name for x in row.children]
        #         choices = [x.name for x in row.children]
        #         terms = [SimpleTerm(c, i, c) for i, c in enumerate(choices)]
        #
        #         default = assessment_data.get(field_name, None)
        #         field = Choice(
        #             title=field_title,
        #             __name__=field_name,
        #             vocabulary=SimpleVocabulary(terms),
        #             required=False,
        #             default=default,
        #         )
        #         fields.append(field)
        #
        #     for f in additional_fields.keys():
        #
        #         _title = u'{}: {} {}'.format(base_name, row_name, f)
        #         _name = '{}_{}_{}'.format(base_name, row_name, f)
        #         default = assessment_data.get(_name, None)
        #         _field = Text(
        #             title=_title,
        #             __name__=_name,
        #             required=False,
        #             default=default
        #         )
        #
        #         fields.append(_field)
        #
        #     form.fields = Fields(*fields)
        #
        #     forms.append(form)
        #
        # return forms

    def get_subforms(self):
        # article = self.get_flattened_data(self)['article'].capitalize()
        subforms = []

        els = get_descriptor_elements(
            'compliance/nationaldescriptors/questions/data'
        )
        qs = get_questions(
            'compliance/nationaldescriptors/questions/data'
        )
        import pdb; pdb.set_trace()
        questions = qs[self.article]

        for criteria in els[self.descriptor]:
            forms = self._build_subforms(questions, criteria)
            subforms.extend(forms)

        # criterias = filtered_criterias(self.article, self.process_phase())
        #
        # for criteria in criterias:
        #     forms = self._build_subforms(criteria)
        #     subforms.extend(forms)

        return subforms


def filtered_criterias(article, phase):
    """ Get the assessment criterias
    """

    try:
        struct = form_structure[article]
    except KeyError:    # article is not in form structure yet
        logger.warning("Article form not implemented %s", article)

        return []

    if phase != 'phase3':
        children = [c.name for c in struct.children if c.name != 'Coherence']
    else:
        children = ['Coherence']

    criterias = [c for c in struct.children if c.name in children]

    return criterias


EditAssessmentDataView = wrap_form(EditAssessmentDataForm, MainFormWrapper)
