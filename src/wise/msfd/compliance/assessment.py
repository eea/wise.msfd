import logging
from collections import namedtuple

from zope.schema import Text

from plone.api.portal import get_tool

from AccessControl import Unauthorized
from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.interfaces import (IEditAssessorsForm,
                                             INationalDescriptorsFolder,
                                             IRegionalDescriptorAssessment,
                                             IRegionalDescriptorRegionsFolder,
                                             IRegionalDescriptorsFolder)
from wise.msfd.compliance.regionaldescriptors.base import BaseRegComplianceView
from wise.msfd.compliance.scoring import (CONCLUSIONS, get_overall_conclusion,
                                          get_range_index, OverallScores)
from wise.msfd.compliance.utils import get_assessors, set_assessors
from wise.msfd.compliance.vocabulary import (REGIONAL_DESCRIPTORS_REGIONS,
                                             SUBREGIONS_TO_REGIONS)
from wise.msfd.gescomponents import get_descriptor  # get_descriptor_elements
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .base import BaseComplianceView

logger = logging.getLogger('wise.msfd')


# This somehow translates the real value in a color, to be able to compress the
# displayed information in the assessment table
# New color table with answer score as keys, color as value
ANSWERS_COLOR_TABLE = {
    '1': 1,      # very good
    '0.75': 2,   # good
    '0.5': 4,    # poor
    '0.25': 5,   # very poor
    '0': 3,      # not reported
    '0.250': 6,  # not clear
    '/': 7       # not relevant
}

# score_value as key, color as value
CONCLUSION_COLOR_TABLE = {
    5: 0,       # not relevant
    4: 1,       # very good
    3: 2,       # good
    2: 4,       # poor
    1: 5,       # very poor
    0: 3        # not reported
}

CHANGE_COLOR_TABLE = {
    -2: 5,
    -1: 4,
    0: 6,
    1: 3,
    2: 2,
    3: 1,
}


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
    ('progress', u'Progress since 2012'),
    ('recommendations', u'Recommendations for Member State'),
)

reg_summary_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress since 2012'),
    ('recommendations', u'Recommendations'),
)

# TODO not used
progress_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress since 2012'),
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
    def summary_fields(self):
        return summary_fields

    @property
    def summary_data(self):
        saved_data = self.context.saved_assessment_data.last()

        _fields = []

        for name, title in self.summary_fields:
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

    @property
    def summary_fields(self):
        return reg_summary_fields


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


class EditAssessmentDataFormMain(Form):

    @property
    def criterias(self):
        return self.descriptor_obj.sorted_criterions()      # criterions

    @property
    def help(self):
        return render_assessment_help(self.criterias, self.descriptor)

    def is_disabled(self, question):
        """ Returns True if question is not editable
        """

        if self.read_only_access:
            return True

        # Is this still needed?
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


class AssessmentDataMixin(object):
    """ Helper class for easier access to the assesment_data for
        national and regional descriptor assessments

        Currently used to get the coherence score from regional descriptors

        TODO: implement a method to get the adequacy and consistency scores
        from national descriptors assessment
    """

    @property
    def _nat_desc_folder(self):
        portal_catalog = get_tool('portal_catalog')
        brains = portal_catalog.searchResults(
            object_provides=INationalDescriptorsFolder.__identifier__
        )
        nat_desc_folder = brains[0].getObject()

        return nat_desc_folder

    @property
    def _reg_desc_folder(self):
        portal_catalog = get_tool('portal_catalog')
        brains = portal_catalog.searchResults(
            object_provides=IRegionalDescriptorsFolder.__identifier__
        )
        nat_desc_folder = brains[0].getObject()

        return nat_desc_folder

    @property
    def _reg_desc_region_folders(self):
        return self.filter_contentvalues_by_iface(
            self._reg_desc_folder, IRegionalDescriptorRegionsFolder
        )

    @property
    def rdas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.regionaldescriptorassessment',
        )

        for brain in brains:
            obj = brain.getObject()

            if not IRegionalDescriptorAssessment.providedBy(obj):
                continue

            yield obj

    def get_color_for_score(self, score_value):
        return CONCLUSION_COLOR_TABLE[score_value]

    def get_conclusion(self, score_value):
        concl = list(reversed(CONCLUSIONS))[score_value]

        return concl

    def _get_assessment_data(self, article_folder):
        if not hasattr(article_folder, 'saved_assessment_data'):
            return {}

        return article_folder.saved_assessment_data.last()

    def get_main_region(self, region_code):
        """ Returns the main region (used in regional descriptors)
            for a sub region (used in national descriptors)
        """

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            if region_code in region.subregions:
                return region.code

        return region_code

    def get_coherence_data(self, region_code, descriptor, article):
        """ For year 2018
        :return: {'color': 5, 'score': 0, 'max_score': 0,
                'conclusion': (1, 'Very poor')
            }
        """

        article_folder = None

        for obj in self.rdas:
            descr = obj.aq_parent.id.upper()

            if descr != descriptor:
                continue

            region = obj.aq_parent.aq_parent.id.upper()

            if region != self.get_main_region(region_code):
                continue

            art = obj.title

            if art != article:
                continue

            article_folder = obj

            break

        assess_data = self._get_assessment_data(article_folder)

        res = {
            'score': 0,
            'max_score': 0,
            'color': 0,
            'conclusion': (0, 'Not reported')
        }

        for k, score in assess_data.items():
            if '_Score' not in k:
                continue

            if not score:
                continue

            is_not_relevant = getattr(score, 'is_not_relevant', False)
            weighted_score = getattr(score, 'weighted_score', 0)
            max_weighted_score = getattr(score, 'max_weighted_score', 0)

            if not is_not_relevant:
                res['score'] += weighted_score
                res['max_score'] += max_weighted_score

        score_percent = int(round(res['max_score'] and (res['score'] * 100)
                                  / res['max_score'] or 0))
        score_val = get_range_index(score_percent)

        res['color'] = self.get_color_for_score(score_val)
        res['conclusion'] = (score_val, self.get_conclusion(score_val))

        return res

    def get_reg_assessments_data_2012(self, article=None, region_code=None,
                                      descriptor_code=None):
        """ Get the regional descriptor assessment 2012 data """
        from .regionaldescriptors.assessment import ASSESSMENTS_2012

        if not article:
            article = self.article

        if not region_code:
            region_code = self.country_region_code

        if not descriptor_code:
            descriptor_code = self.descriptor_obj.id

        res = []

        for x in ASSESSMENTS_2012:
            if x.region.strip() != region_code:
                continue

            if x.descriptor.strip() != descriptor_code.split('.')[0]:
                continue

            art = x.article.replace(" ", "")

            if not art.startswith(article):
                continue

            res.append(x)

        sorted_res = sorted(
            res, key=lambda i: int(i.overall_score), reverse=True
        )

        return sorted_res