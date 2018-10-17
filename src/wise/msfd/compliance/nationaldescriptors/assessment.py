import logging

from zope.schema import Choice, Text
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone.z3cform.layout import wrap_form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql2018  # sql,
from wise.msfd.base import EmbededForm, MainFormWrapper  # BaseUtil,
from wise.msfd.gescomponents import get_ges_criterions
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from ..base import BaseComplianceView  # , Container
from ..vocabulary import form_structure

logger = logging.getLogger('wise.msfd')


def get_default_additional_field_value(
        data_assess,
        article,
        feature,
        assess_crit,
        assess_info,
        field_name
        ):

    # TODO: check the feature param, we no longer need it

    if not data_assess:
        return None

    for x in data_assess:
        field_data = getattr(x, field_name)

        # x.Feature == feature and \

        if x.MSFDArticle == article and \
                x.AssessmentCriteria == assess_crit and \
                x.AssessedInformation == assess_info and \
                field_data:

            return field_data

    return None


def get_default_assessment_value(
        data_assess,
        article,
        feature,
        assess_crit,
        assess_info,
        ges_comp
        ):

    if not data_assess:
        return None

    for x in data_assess:
        if x.MSFDArticle == article and \
                x.AssessmentCriteria == assess_crit and \
                x.AssessedInformation == assess_info and \
                x.GESComponent_Target == ges_comp:
            # x.Feature == feature and \

            return x.Evidence

    return None


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
        pass

    @property
    def fields(self):
        if not self.subforms:
            self.subforms = self.get_subforms()

        fields = []

        for subform in self.subforms:
            fields.extend(subform.fields._data_values)

        return Fields(*fields)

    def _build_subforms(self, tree):
        """ Build a form of options from a tree of options
        """
        base_name = tree.name
        descriptor_criterions = get_ges_criterions(self.descriptor)

        forms = []

        # check if article was already assessed
        @db.use_db_session('session_2018')
        def func():
            mc = sql2018.COMGeneral
            conditions = []
            conditions.append(mc.CountryCode == self.country_code)
            conditions.append(mc.AssessmentTopic == u'National summary')
            conditions.append(mc.MSFDArticle == self.article)
            count, res = db.get_all_records(
                mc,
                *conditions
            )

            if not count:
                return [], None
            else:
                general_id = res[0].Id
                assess_data = self.get_assessment_data(general_id)

                return assess_data, general_id

        data_assess, self.general_id = func()

        for row in tree.children:
            row_name = row.name

            # TODO: we no longer need EmbededForm here, we should get rid of

            form = EmbededForm(self, self.request)

            form.form_name = 'form' + row_name
            fields = []

            form.title = '{}: {}'.format(base_name, row_name)

            for crit in descriptor_criterions:
                field_title = u'{} {}: {}'.format(base_name, row_name,
                                                  crit.title)
                field_name = '{}_{}_{}'.format(base_name, row_name, crit.id)
                # choices = [''] + [x.name for x in row.children]
                choices = [x.name for x in row.children]
                terms = [SimpleTerm(c, i, c) for i, c in enumerate(choices)]

                default = get_default_assessment_value(
                    data_assess,
                    self.article,  # MSFDArticle
                    # data['feature_reported'][0],  # Feature
                    None,       # TODO: what is here????
                    base_name,  # AssessmentCriteria
                    row_name,  # AssessedInformation
                    crit.id  # GESComponent_Target
                )

                field = Choice(
                    title=field_title,
                    __name__=field_name,
                    vocabulary=SimpleVocabulary(terms),
                    required=False,
                    default=default,
                )
                fields.append(field)

            for f in additional_fields.keys():
                default = get_default_additional_field_value(
                    data_assess,
                    self.article,
                    # data['article'],  # MSFDArticle
                    # data['feature_reported'][0],  # Feature
                    None,
                    base_name,  # AssessmentCriteria
                    row_name,  # AssessedInformation
                    additional_fields[f]
                )

                _title = u'{}: {} {}'.format(base_name, row_name, f)
                _name = '{}_{}_{}'.format(base_name, row_name, f)
                _field = Text(
                    title=_title,
                    __name__=_name,
                    required=False,
                    default=default
                )

                fields.append(_field)

            form.fields = Fields(*fields)

            forms.append(form)

        return forms

    def get_subforms(self):
        # article = self.get_flattened_data(self)['article'].capitalize()
        subforms = []

        criterias = filtered_criterias(self.article, self.process_phase)

        for criteria in criterias:
            subforms = self._build_subforms(criteria)

            for subform in subforms:
                subforms.append(subform)

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
