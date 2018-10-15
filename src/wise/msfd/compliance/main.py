# -*- coding: utf-8 -*-
# from zope.component import getMultiAdapter
from collections import namedtuple

from zope.interface import Interface, implements
from zope.schema import Choice, List

from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.formwidget.optgroup.widget import OptgroupFieldWidget

from . import interfaces
from .. import db, sql2018
from ..base import MainFormWrapper as BaseFormWrapper
from ..base import BaseEnhancedForm, EmbededForm
from ..features import features_vocabulary
from ..interfaces import IMainForm, IMarineUnitIDsSelect
from .base import Container
from .nat_desc import (AssessmentDataForm2018, AssessmentHeaderForm2018,
                       Report2012, ReportData2018, ReportHeaderForm2018)
from .vocabulary import articles_vocabulary, descriptors_vocabulary

CountryStatus = namedtuple('CountryStatus', ['name', 'status', 'url'])


MAIN_FORMS = [
    # view name, (title, explanation)
    ('@@comp-start',
     ('Compliance Module',
      'Start Page'),
     ),
    ('national-descriptors-assessments/@@nat-desc-start',
     ('National descriptors',
      'Member states reports and Commission assessments'),
     ),
    ('@@comp-regional-descriptor',
     ('Regional descriptors',
      'Member states reports and Commission assessments'),
     ),
    ('@@comp-national-overviews',
     ('National overviews',
      'Overview for a Member state'),
     ),
    ('@@comp-regional-overviews',
     ('Regional overviews',
      'Overview for all Member states in a region',),
     ),
]

# TODO: define the tabs selection label for mobile view (see wise-macros.pt)


class BaseComplianceView(BrowserView):
    """ Base class for compliance views
    """

    main_forms = MAIN_FORMS

    def get_parent_by_iface(self, iface):
        for parent in self.request.other['PARENTS']:
            if iface.providedBy(parent):
                return parent

        raise ValueError('Parent not found: {}'.format(iface))

    def root_url(self):
        root = self.get_parent_by_iface(interfaces.IComplianceModuleFolder)

        return root and root.absolute_url() or ''

    @property
    def _article_assessment(self):
        return self.get_parent_by_iface(
            interfaces.INationalDescriptorAssessment
        )

    @property
    def _descriptor_folder(self):
        return self.get_parent_by_iface(
            interfaces.IDescriptorFolder
        )

    @property
    def _country_folder(self):
        return self.get_parent_by_iface(
            interfaces.ICountryDescriptorsFolder
        )

    @property
    def _national_descriptors_folder(self):
        return self.get_parent_by_iface(
            interfaces.INationalDescriptorsFolder
        )

    @property
    def _compliance_folder(self):
        return self.get_parent_by_iface(
            interfaces.IComplianceModuleFolder
        )


class StartComplianceView(BaseComplianceView):
    name = 'comp-start'


class NationalDescriptorsOverview(BaseComplianceView):
    name = 'nat-desc-start'

    def countries(self):
        countries = self.context.contentValues()

        return [CountryStatus(country.Title(), 'phase0',
                              country.absolute_url()) for country in countries]


class NationalDescriptorCountryOverview(BaseComplianceView):
    name = 'nat-desc-country-start'

    def get_status(self):
        return "Phase 1"

    def get_articles(self):
        return ['Art8', 'Art9', 'Art10']

    def get_descriptors(self):
        return self.context.contentValues()


class NationalDescriptorArticleView(BaseComplianceView):
    name = 'nat-desc-art-view'

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        self.article = self._article_assessment.getId()
        self.descriptor = self._descriptor_folder.getId()
        self.country = self._country_folder.getId()


class MainAssessmentForm(BaseEnhancedForm, Form):
    """ Base form for all main compliance view forms

    # mostly similar to .base.MainForm
    """
    implements(IMainForm)
    template = Template('../pt/mainform.pt')        # compliance-main
    ignoreContext = True
    reset_page = False
    subform = None
    subform_content = None
    fields = Fields()
    # css_class = 'compliance-form-main'
    session_name = 'session'

    main_forms = MAIN_FORMS
    _is_save = False

    def __init__(self, context, request):
        Form.__init__(self, context, request)
        self.save_handlers = []

    def add_save_handler(self, handler):
        self.save_handlers.append(handler)

    @buttonAndHandler(u'Apply filters', name='continue')
    def handle_continue(self, action):
        self._is_save = True

    def get_subform(self):
        if self.subform:
            return self.subform(self, self.request)

    def update(self):
        super(MainAssessmentForm, self).update()
        print ("===Doing main form update")
        self.data, self.errors = self.extractData()

        has_values = self.data.values() and all(self.data.values())

        if has_values:
            self.subform = self.get_subform()

            if self.subform:
                # we need to update and "execute" the subforms to be able to
                # discover them, because the decision process regarding
                # discovery is done in the update() method of subforms

                # with restore_session():
                # when using different sessions, we will need to restore
                # the self.session current session name
                self.subform_content = self.subform()

        if self._is_save:
            for handler in self.save_handlers:
                handler()


class MainFormWrapper(BaseFormWrapper):
    index = Template('../pt/layout.pt')     # compliance-


class IMemberState(Interface):
    member_state = Choice(
        title=u"Country",
        vocabulary="wise_search_member_states",
        required=False,
    )


class NationalDescriptorForm(MainAssessmentForm):
    # TODO: redo. Old '@@comp-national-descriptor'
    assessment_topic = 'GES Descriptor (see term list)'
    fields = Fields(IMemberState)
    name = "comp-national-descriptor"

    form_id = 'wise-compliance-form'

    form_id_top = 'wise-compliance-form-top'

    form_container_class = 'wise-compliance-form-container'

    def get_subform(self):
        return GESDescriptorForm(self, self.request)


NationalDescriptorFormView = wrap_form(NationalDescriptorForm, MainFormWrapper)


class IGESDescriptor(Interface):
    descriptor = Choice(
        title=u"Descriptor",
        vocabulary=descriptors_vocabulary,
        required=False,
        default='D5'
    )


class GESDescriptorForm(EmbededForm):
    fields = Fields(IGESDescriptor)

    def get_subform(self):
        return ArticleForm(self, self.request)


class IArticle(Interface):
    article = Choice(
        title=u"Article",
        vocabulary=articles_vocabulary,
        required=False,
    )


class ArticleForm(EmbededForm):
    fields = Fields(IArticle)

    def get_subform(self):
        return MarineUnitIDsForm(self, self.request)

    @db.use_db_session('session_2018')
    def get_muids_2018(self, article, country):
        m = {
            'Art8': sql2018.ART8GESMarineUnit
        }

        ris = db.get_unique_from_mapper(
            sql2018.ReportedInformation,
            'Id',
            sql2018.ReportedInformation.CountryCode == country
        )
        ris = [int(c) for c in ris]
        t = m.get(article)

        if not t:
            print "TODO: provide support for article ", article

            return []

        muids = db.get_unique_from_mapper(
            t,
            'MarineReportingUnit',
            t.IdReportedInformation.in_(ris),
        )

        print muids

        return muids

    def get_available_marine_unit_ids(self):
        # marine_unit_ids = self.data.get('marine_unit_ids')

        # TODO: should also do the request form reading
        data = self.get_flattened_data(self)
        article = data['article']
        country = data['member_state']

        if country:
            _count, d_2012 = db.get_marine_unit_ids(member_states=[country])
            d_2018 = self.get_muids_2018(article, country)

            return (_count + len(d_2018), d_2012 + d_2018)
        else:
            return []


class MarineUnitIDsForm(EmbededForm):
    fields = Fields(IMarineUnitIDsSelect)
    fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return BasicAssessmentDataForm2018(self, self.request)


class IBasicAssessmentData2018(Interface):
    """ The basic fields for the assessment data for 2018
    """
    # TODO: this needs a select box?
    feature_reported = List(
        title=u'Feature reported',
        value_type=Choice(vocabulary=features_vocabulary),
    )


class BasicAssessmentDataForm2018(EmbededForm):
    """
    """

    fields = Fields(IBasicAssessmentData2018)
    fields['feature_reported'].widgetFactory = OptgroupFieldWidget

    def get_subform(self):
        return NationalDescriptorAssessmentForm(self, self.request)


class NationalDescriptorAssessmentForm(Container):
    """ Form to create and assess a national descriptor overview
    """
    assessment_topic = u'National summary'

    form_name = "national-descriptor-assessment-form"
    render = Template('pt/container.pt')
    css_class = "left-side-form"

    def update(self):
        super(NationalDescriptorAssessmentForm, self).update()

        # a quick hack to allow splitting up the code reusing the concept of
        # subforms. Some of them are actually views. They're callbables that:
        # - render themselves
        # - answer to the save() method?
        self.subforms = [
            Report2012(self, self.request),

            ReportHeaderForm2018(self, self.request),
            ReportData2018(self, self.request),
            AssessmentHeaderForm2018(self, self.request),
            AssessmentDataForm2018(self, self.request)
        ]

        for child in self.subforms:
            if hasattr(child, 'update'):
                child.update()
