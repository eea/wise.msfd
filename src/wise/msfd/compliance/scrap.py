# class IAssessmentTopic(Interface):
#     """
#     """
#     assessment_topic = Choice(
#         title=u"Assessment topic",
#         vocabulary=vocab_from_values(ASSESSMENT_TOPICS),
#         required=False,
#     )


# class AssessmentTopicForm(EmbeddedForm):
#     """ Select the memberstate, region, area form
#     """
#
#     fields = Fields(IAssessmentTopic)
#
#     def get_subform(self):
#         return ArticleForm(self, self.request)
#
#
# class IArticleForm(Interface):
#     """
#     """
#     assessed_article = Choice(
#         title=u"Assessed article",
#         vocabulary=vocab_from_values(ASSESSED_ARTICLES),
#         required=False,
#     )
#
#
# class ArticleForm(EmbeddedForm):
#     """
#     """
#
#     fields = Fields(IArticleForm)
#
#     def get_subform(self):
#         return ReportingDeadlineForm(self, self.request)


# class IReportingDeadline(Interface):
#     """
#     """
#     reporting_deadline = Choice(
#         title=u"Reporting deadline",
#         vocabulary=vocab_from_values(REPORTING_DEADLINES),
#         required=False,
#     )
#
#
# class ReportingDeadlineForm(EmbeddedForm):
#     """
#     """
#
#     fields = Fields(IReportingDeadline)
#
#     def get_subform(self):
#         return AssessmentDisplayForm(self, self.request)


# class AssessmentDisplayForm(EmbeddedForm):
#     """
#     """
#     template = ViewPageTemplateFile('pt/assessment_display.pt')
#
#     def get_assessed_article(self):
#         parent = self
#         article = None
#
#         while True:
#             if not hasattr(parent, 'data'):
#                 return []
#             article = parent.data.get('assessed_article')
#
#             if article:
#                 break
#             else:
#                 parent = parent.context
#
#         return article
#
#     def update(self):
#         res = super(AssessmentDisplayForm, self).update()
#         self.contents = ''
#         article = self.get_assessed_article()
#
#         if article == 'Art. 8 Initial assessment (and Art. 17 updates)':
#             self.contents = getMultiAdapter((self, self.request),
#                                             name='deter')()
#
#         return res

# evidences_criteria = [
#     'Primary criterion used',
#     'Primary criterion replaced with secondary criterion',
#     'Primary criterion not used',
#     'Secondary criterion used',
#     'Secondary criterion used instead of primary criterion',
#     'Secondary criterion not used',
#     '2010 criterion/indicator used',
#     '2010 criterion/indicator not used',
#     'Other criterion (indicator) used',
#     'Not relevant',
# ]

# art9_assessment_criterias = ['Adequacy', 'Coherence']

L = Leaf    # short alias

hierarchy = [
    'MSFD article', 'AssessmentCriteria', 'AssessedInformation', 'Evidence'
]

ASSESSMENT_TOPICS = [
    'National summary',
    'Regional summary',
    'GES Descriptor (see term list)',
    'Horizontal targets',
    'Horizontal measures',
    'Geographic areas',
    'Regional cooperation',
]

REPORTING_DEADLINES = [
    '20110115',
    '20121015',
    '20141015',
    '20160331',
    '20181015',
    '20181231',
    '20201015',
    '20220331',
    '20241015',
]


# assessment_environmental_status_A = [
#     ('Yes',
#      'Yes, based on threshold value and, where appropriate, proportion
#      value'),
#     ('Yes-LowRisk',
#      'Yes, based on low risk'),
#     ('No',
#      'No, based on threshold value and, where appropriate, proportion
#      value'),
#     ('Unknown',	'Unknown'),
#     ('NotAssessed',	'Not assessed'),
# ]


# from pprint import pprint


class MainFormWrapper(FormWrapper):
    """ Override mainform wrapper to be able to return XLS file
    """

    index = ViewPageTemplateFile('pt/layout.pt')

    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        threadlocals.session_name = self.form.session_name

    # def render(self):
    #    if 'text/html' not in self.request.response.getHeader('Content-Type'):
    #         return self.contents
    #
    #     return super(MainFormWrapper, self).render()


class IComplianceForm(Interface):
    country = Choice(
        title=u"Country",
        vocabulary="compliance_countries",
        required=True
    )
    report_type = Choice(
        title=u"Report Type",
        vocabulary="compliance_report_types",
        required=True,
    )


class ComplianceForm(Form):
    """ The main forms need to inherit from this clas
    """

    implements(IComplianceForm)
    template = ViewPageTemplateFile('pt/complianceform.pt')
    ignoreContext = True
    reset_page = False
    subform = None
    fields = Fields(IComplianceForm)
    session_name = 'session_2018'

    # @buttonAndHandler(u'Apply filters', name='continue')
    # def handle_continue(self, action):
    #     self.reset_page = True


ComplianceFormView = wrap_form(ComplianceForm, MainFormWrapper)


@provider(IVocabularyFactory)
def compliance_countries(context):
    return db_vocab(sql2018.ReportingHistory, 'CountryCode')


@provider(IVocabularyFactory)
def compliance_report_types(context):
    return vocab_from_values([])

  # older pages
  <!-- <browser:page -->
  <!--   for="*" -->
  <!--   name="compliance" -->
  <!--   class=".compliance.ComplianceFormView" -->
  <!--   permission="zope2.View" -->
  <!--   /> -->

# def get_feature_terms_old():
#
#     # NOTE: this code is no longer used, there are features that are not in the
#     # tsv file. We will use the L_features table
#
#     terms = []
#     seen = []
#
#     for group_name, features in FEATURES.items():
#         if 'activity' in group_name.lower():
#             continue
#
#         for (key, title) in features:
#             if key in seen:
#                 continue
#             seen.append(key)
#             term = OptgroupTerm(value=key, token=key, title=title,
#                                 optgroup=group_name)
#             terms.append(term)
#
#     return terms
import csv
from collections import defaultdict

from pkg_resources import resource_filename

from plone.app.textfield.widget import RichTextWidget
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.content.search import db, interfaces, sql2018
from wise.msfd import db, sql
from z3c.form.browser.text import TextFieldWidget, TextWidget
from z3c.form.browser.textarea import TextAreaWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields

from ..a8_utils import DB_MAPPER_CLASSES, DESC_DATA_MAPPING, DESCR_TOPIC_UTILS
from ..base import BaseArticle2012
from .base import Leaf as L
from .base import EmbeddedForm, ItemDisplayForm


def register_compliance_module(klass):

    class ComplianceModuleMain(klass):
        # template = ViewPageTemplateFile('pt/compliance.pt')

        def get_subform(self):
            # TODO access restriction
            # only show if the user is allowed to see compliance module

            return ComplianceModule(self, self.request)

        def update(self):
            super(klass, self).update()
            # self.compliance_content = ComplianceModule(self, self.request)
            self.subform = self.get_subform()

    return ComplianceModuleMain


class ComplianceModule(EmbeddedForm):
    css_class = 'only-left-side-form'
    # template = ViewPageTemplateFile('pt/compliance.pt')
    fields = Fields(interfaces.IComplianceModule)
    actions = None
    reset_page = False

    def get_subform(self):
        return ComplianceDisplay(self, self.request)

    # def update(self):
    #     super(ComplianceModule, self).update()
    #     self.subform = self.get_subform()


class ComplianceDisplay(ItemDisplayForm):

    template = ViewPageTemplateFile('pt/compliance-display-form.pt')
    data_template = ViewPageTemplateFile('pt/compliance-item-display.pt')
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    # css_class = 'left-side-form'
    # css_class = 'compliance-display'

    def get_db_results(self):
        return 0, {}

    def get_extra_data(self):
        res = list()
        res.append(
            ('Some data from file ', {
                '': [{'Data': "Text here _%s" % x} for x in range(2)]
            }))

        return res

    def get_subform(self):
        return ComplianceAssessment(self, self.request)

    def update(self):
        super(ComplianceDisplay, self).update()
        self.subform = self.get_subform()
        del self.widgets['page']


class ComplianceAssessment(EmbeddedForm):
    # css_class = 'only-left-side-form'
    fields = Fields(interfaces.IComplianceAssessment)
    # fields['com_assessment'].widgetFactory = TextWidget

    mc_com_assessments = 'COM_assessments'
    mc_assessments_comments = 'Assessments_comments'

    @buttonAndHandler(u'Save assessment', name='save_assessment')
    def save_assessment(self, action):
        data, errors = self.extractData()
        assessment = data.get('com_assessment', '')
        import pdb;pdb.set_trace()

        if assessment:
            # TODO save assessment to DB
            reporting_history_id = self.context.item.get('Id', '')
            assessment_id = db.get_all_records(
                self.mc_com_assessments,
                self.mc_com_assessments.Reporting_historyID == reporting_history_id
            )
            values = dict()
            values['Reporting_historyID'] = reporting_history_id
            values['Article'] = ''
            values['GEScomponent'] = ''
            values['Feature'] = ''
            values['assessment_criteria'] = assessment

            if assessment_id:
                conditions = list()
                conditions.append(
                    self.mc_com_assessments.Reporting_historyID == reporting_history_id
                )
                db.update_record(self.mc_com_assessments, *conditions, **values)
            else:
                db.insert_record(self.mc_com_assessments, **values)

    @buttonAndHandler(u'Save comment', name='save_comment')
    def save_comment(self, action):
        data, errors = self.extractData()
        comment = data.get('assessment_comment', '')
        import pdb;pdb.set_trace()

        if comment:
            # TODO save comment to DB
            com_assessmentsId = self.context.item.get('Id', '')
            comment_id = db.get_all_records(
                self.mc_assessments_comments,
                self.mc_assessments_comments.COM_assessmentsID == com_assessmentsId
            )
            values = dict()
            values['COM_assessmentsID'] = com_assessmentsId
            values['organisation'] = ''
            values['Comment'] = comment

            if comment_id:
                conditions = list()
                conditions.append(
                    self.mc_assessments_comments.COM_assessmentsID == com_assessmentsId
                )
                db.update_record(self.mc_assessments_comments, **values)
            else:
                db.insert_record(self.mc_com_assessments, **values)

    def update(self):
        super(ComplianceAssessment, self).update()
        self.data, errors = self.extractData()

    def extractData(self):
        data, errors = super(ComplianceAssessment, self).extractData()

        return data, errors


# def vocab_from_dict(d):
#     """ Build a zope.schema vocabulary from a dict of value: title shape
#     """
#     terms = []
#
#     for k, v in d.items():
#         term = SimpleTerm(k, k, v)
#         terms.append(term)
#
#     return SimpleVocabulary(terms)
# from ..vocabulary import vocab_from_values  # db_vocab,
# from plone.z3cform.layout import FormWrapper, wrap_form
# from z3c.form.field import Fields
# from zope.schema import Choice  # , List
# from zope.schema.interfaces import IVocabularyFactory
# from z3c.form.form import Form
# from zope.interface import Interface, implements, provider

    # report header 2012        - view
    # report data 2012          - view

    # assessment header 2012    - view
    # assessment data_2012      - view

    # reporting header 2018     - form
    # reporting data 2018       - view

    # assessment header 2018    - form
    # assessment FORM 2018      - form

    # reporting_data_header = Template('../pt/reporting-data-header.pt')
    # assessment_header = Template('../pt/assessment-header.pt')

# overview = data table with info
# views needed:
#   - national descriptor overview, 2012
#   - national descriptor overview, 2018


# - assessment topic
#     - national descriptors
#         - choose country
#             - choose article
#                 - 2012 data
#                 - 2018 data
#             - fill in general data
#             - choose descriptor
#     - regional descriptors
#     - national overviews
#     - regional overviews
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFDFeature_Overview.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD9GES_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD8cESA_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD8bPressures_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD8bPressures_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD8aFeatures_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD8aFeatures_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD4Geo_2p0.xsd
# http://icm.eionet.europa.eu/schemas/dir200856ec/MSFD10TI_2p0.xsd


# class ReportAssessment2012(BrowserView, BaseUtil):
#     """ Report and assessment for 2012 national descriptor overview
#     """
#     def __init__(self, context, request):
#         super(ReportAssessment2012, self).__init__(context, request)
#
#         data = self.get_flattened_data(self)
#         self.article_title = dict(ASSESSED_ARTICLES)[data['article']]
#
#         self.report_form_2018 = ReportForm2018(self, self.request)
#

# class IReportForm(Interface):
#     pass
#
#
# class ReportForm2018(EmbeddedForm):
#     fields = Fields(IReportForm)
  <!-- <browser:page -->
  <!--   for="*" -->
  <!--   name="report_assessment_2012" -->
  <!--   class=".nat_desc.ReportAssessment2012" -->
  <!--   template='../pt/nat&#45;desc&#45;overview&#45;report&#45;assessment&#45;2012.pt' -->
  <!--   permission="zope2.View" -->
  <!--   /> -->
  <!--  -->
  <!-- <browser:page -->
  <!--   for="*" -->
  <!--   name="report_assessment_2018" -->
  <!--   class=".nat_desc.ReportAssessment2018" -->
  <!--   permission="zope2.View" -->
  <!--   /> -->

  <!-- <browser:page -->
  <!--   for="*" -->
  <!--   name="deter" -->
  <!--   class=".nat_desc.DeterminationOfGES2012" -->
  <!--   template='../pt/determination.pt' -->
  <!--   permission="zope2.View" -->
  <!--   /> -->

  <!-- <browser:page -->
  <!--   for="*" -->
  <!--   name="report_data_2012" -->
  <!--   class=".nat_desc.ReportData2012" -->
  <!--   template='../pt/report&#45;header&#45;display.pt' -->
  <!--   permission="zope2.View" -->
  <!--   /> -->

  <!-- <utility -->
  <!--   component=".compliance.compliance_countries" -->
  <!--   name="compliance_countries" -->
  <!--   /> -->
  <!--  -->
  <!-- <utility -->
  <!--   component=".compliance.compliance_report_types" -->
  <!--   name="compliance_report_types" -->
  <!--   /> -->
# form_structure = L(
#     'articles', [
#         L('Art4', [
#             L('Adequacy', [
#                 L('MRUscales2017Decision', [
#                     L('Follow scales in 2017 Decision'),
#                     L('Partially follow scales in 2017 Decision'),
#                     L('Do not follow scales in 2017 Decision'),
#                     L('Not relevant'),
#                 ]),
#             ]),
#             L('Consistency', [
#             ]),
#             L('Coherence', [
#             ]),
#         ]),
#         L('Art8'),
#         L('Art9', [
#             L('Adequacy', [
#                 L('CriteriaUsed', [
#                     L('Primary criterion used'),
#                     L('Primary criterion replaced with secondary criterion'),
#                     L('Primary criterion not used'),
#                     L('Secondary criterion used'),
#                     L('Secondary criterion used instead of primary criterion'),
#                     L('Secondary criterion not used'),
#                     L('2010 criterion/indicator used'),
#                     L('2010 criterion/indicator not used'),
#                     L('Other criterion (indicator) used'),
#                     L('Not relevant'),
#                 ]),
#                 L('GESQualitative', [
#                     L('Adapted from Annex I definition'),
#                     L('Adapted from 2017 Decision'),
#                     L('Adapted from 2010 Decision'),
#                     L('Not relevant'),
#                 ]),
#                 L('GESQuantitative', [
#                     L('Threshold values per MRU'),
#                     L('No threshold values'),
#                     L('Not relevant'),
#                 ]),
#                 L('GESAmbition', [
#                     L('No GES extent threshold defined'),
#                     L('Proportion value per MRU set'),
#                     L('No proportion value set'),
#                 ]),
#             ]),
#             L('Coherence', [
#                 L('CriteriaUsed', [
#                     L('Criterion used by all MS in region'),
#                     L('Criterion used by ≥75% MS in region'),
#                     L('Criterion used by ≥50% MS in region'),
#                     L('Criterion used by ≥25% MS in region'),
#                     L('Criterion used by ≤25% MS in region'),
#                     L('Criterion used by all MS in subregion'),
#                 ]),
#                 L('GESQualitative', [
#                     L('High'),
#                     L('Moderate'),
#                     L('Poor'),
#                     L('Not relevant'),
#                 ]),
#                 L('GESQuantitative', [
#                     L('All MS in region use EU (Directive, Regulation or Decision) values'),
#                     L('All MS in region use regional (RSC) values'),
#                     L('All MS in region use EU (WFD coastal) and regional (RSC offshore) values'),
#                     L('All MS in region use EU (WFD coastal); and national (offshore) values'),
#                     L('All MS in region use national values'),
#                     L('Some MS in region use EU (Directive, Regulation or Decision) values and some MS use national values'),
#                     L('Some MS in region use regional (RSC) values and some MS use national values'),
#                     L('Not relevant'),
#                 ]),
#                 L('GESAmbition', [
#                     L('GES extent value same/similar for all MS in region'),
#                     L('GES extent value varies between MS in region'),
#                     L('GES extent threshold varies markedly between MS'),
#                     L('GES extent threshold not reported'),
#                     L('GES proportion value same/similar for all MS in region'),
#                     L('GES proportion value varies between MS in region'),
#                     L('GES proportion value varies markedly between MS'),
#                     L('GES proportion value not reported'),
#                     L('Not relevant'),
#                 ]),
#             ]),
#         ]),
#         L('Art10'),
#     ])


            if l3:  # did information change?
                if l3.name != information:
                    l3 = L(information)
            else:
                l3 = L(information)

            l3.children.append(l4)

            if l2:

            # l3 = l3 or
            # l2 = l2 or L(criteria)
            # l1 = l1 or L(article)

        # def data(k):
        #     return self.get_form_data_by_key(self, k)
        #
        # self.request.form['country'] = data('member_state')
        # self.request.form['article'] = data('article')

        # self.request.form['report_type'] = descriptor
        # TODO: misssing?
        # descriptor = self.get_form_data_by_key(self, 'descriptor')

        # return getMultiAdapter((self, self.request), name='deter')

# from .vocabulary import LABELS


# def parse_features_file():
#     csv_f = resource_filename('wise.content',
#                               'search/data/features.tsv')
#
#     res = defaultdict(list)
#     with open(csv_f, 'rb') as csvfile:
#         csv_file = csv.reader(csvfile, delimiter='\t')
#
#         for row in csv_file:
#             if not (len(row) == 8 and row[-1].lower() == 'y'):
#                 continue
#             res[row[0]].append((row[1], row[2]))
#
#     return res
#
#
# FEATURES = parse_features_file()


# from zope.component import getMultiAdapter
# from zope.interface import Interface, implements
# from zope.schema import Choice, List
#
# from plone.z3cform.layout import wrap_form
# from Products.Five.browser.pagetemplatefile import \
#     ViewPageTemplateFile as Template
# from z3c.form.browser.checkbox import CheckBoxFieldWidget
# from z3c.form.button import buttonAndHandler
# from z3c.form.field import Fields
# from z3c.form.form import Form
# from z3c.formwidget.optgroup.widget import OptgroupFieldWidget
#
# from .. import db, sql2018
# from ..base import MainFormWrapper as BaseFormWrapper
# from ..base import BaseEnhancedForm, EmbeddedForm
# from ..features import features_vocabulary
# from ..interfaces import IMainForm, IMarineUnitIDsSelect
# , Container

# # from .nat_desc import (AssessmentDataForm2018, AssessmentHeaderForm2018,
# #                       ReportData2012, ReportData2018, ReportHeaderForm2018,
# #                        get_assessment_data_2012, get_assessment_data_2018)
# from .vocabulary import articles_vocabulary, descriptors_vocabulary


class ReportHeaderForm2018(BrowserView):
    """ TODO: get code in this
    """

    def __call__(self):
        return ''

        return 'report header form 2018'


class AssessmentHeaderForm2018(BrowserView):
    """ TODO: get code in this
    """
    def __call__(self):
        return ''

        return 'assessment header form 2018'


class ISummaryAssessmentData2018(Interface):
    assessment_summary = Text(
        title=u'Assessment summary',
        required=False
    )
    recommendations = Text(
        title=u'Recommendations',
        required=False
    )


class SummaryAssessmentDataForm2018(EmbeddedForm):
    """
    """

    def __init__(self, context, request):
        super(SummaryAssessmentDataForm2018, self).__init__(context, request)
        fields = [ISummaryAssessmentData2018]
        self.fields = Fields(*fields)

    def set_default_values(self, data):
        general_id = getattr(self.context, 'general_id', None)
        feature = data.get('feature_reported', None)

        if feature:
            feature = feature[0]

        if not general_id:
            return

        assess_data = self.context.get_assessment_data(
            general_id,
            feature
        )
        value = ''

        for name, field in self.fields.items():
            db_field_name = summary_fields[name]
            # import pdb; pdb.set_trace()

            for row in assess_data:
                value = getattr(row, db_field_name)

                if row.MSFDArticle == data['article'] and \
                   row.Feature in data['feature_reported'] and \
                   row.MarineUnit in data['marine_unit_ids'] and \
                   not row.AssessmentCriteria and \
                   value:
                    break

            field.field.default = unicode(value)



class AssessmentDataForm2018(Container, BaseUtil):
    """ The assessment form for 2018
    """

    def __init__(self, context, request):
        super(AssessmentDataForm2018, self).__init__(context, request)
        main_form = self.get_main_form()
        main_form.add_save_handler(self.handle_save)
        self.subforms = []   # make subforms discoverable for saving

    def handle_save(self):
        # TODO: build records from the subforms
        # TODO: don't do saving unless all forms are clear of errors. This
        # needs handling here
        print "Saving assessment form data"

        data = {}
        child_data = {}
        parent_data = self.get_flattened_data(self)

        for form in self.subforms:
            data.update(form.data)

        for children in self.main_assessment_data_forms:
            child_data.update(children.data)

        self._save(data, parent_data, child_data)

    def _save(self, data, parent_data, child_data):

        # save COM_General data
        self.general_id = self.save_general(parent_data)

        # save COM_Assessment data
        self.save_assessment(data, parent_data)

        # save Summary data
        self.save_summary(parent_data, child_data)

        print data
        print parent_data
        print child_data

    def save_general(self, parent_data):
        d_general = {}

        # TODO get Reporting_historyId
        d_general['Reporting_historyId'] = 48
        d_general['CountryCode'] = parent_data['member_state']

        d_general['AssessmentTopic'] = self.context.assessment_topic
        d_general['MSFDArticle'] = parent_data['article']

        # TODO get DateReportDue, ReportBy etc...
        d_general['DateReportDue'] = u'2011-01-15'
        d_general['ReportBy'] = u'Commission'
        d_general['SourceFile'] = ''
        d_general['DateReported'] = ''
        d_general['DateAssessed'] = ''
        d_general['Assessors'] = ''
        d_general['CommissionReport'] = ''

        mc = sql2018.COMGeneral

        if self.general_id:
            d_general['Id'] = [unicode(self.general_id)]
        general_id = db.save_record(mc, **d_general)

        return general_id

    def save_assessment(self, data, parent_data):
        all_features_reported = parent_data['feature_reported']

        for feature_reported in all_features_reported:

            assessment_data = self.get_assessment_data(
                self.general_id,
                feature_reported
            )

            for k, v in data.items():
                if not v:
                    continue

                d = {}

                d['COM_GeneralId'] = self.general_id
                d['MSFDArticle'] = parent_data['article']
                d['Feature'] = feature_reported

                d['AssessmentCriteria'], d['AssessedInformation'], \
                    d['GESComponent_Target'] = k.split('_')

                if d['GESComponent_Target'] in additional_fields.keys():
                    field_name = d.pop('GESComponent_Target')
                    field_name = additional_fields.get(field_name)
                    d[field_name] = v
                else:
                    field_name = 'GESComponent_Target'
                    d['Evidence'] = v

                # TODO
                # 1 - create separate entry in COM_Assessments table for
                #   every Marine Unit ID ??????
                # 2 - save records one by one, or many at once

                for mru in parent_data['marine_unit_ids']:
                    d['MarineUnit'] = mru

                    id_assess = []

                    # get the Id from assessment_data, if found it will be
                    # an update, otherwise an insert into db

                    for x in assessment_data:
                        if x.MarineUnit != mru:
                            continue

                        if (x.AssessedInformation != d['AssessedInformation']):
                            continue

                        if (x.AssessmentCriteria != d['AssessmentCriteria']):
                            continue

                        if field_name in additional_fields.values():
                            if getattr(x, field_name):
                                id_assess.append(x.Id)

                                break

                        if (getattr(x, field_name) == d.get(field_name)):
                            id_assess.append(x.Id)

                            break

                    if id_assess:
                        d['Id'] = id_assess
                    db.save_record(sql2018.COMAssessment, **d)

    def save_summary(self, parent_data, child_data):
        features_reported = parent_data['feature_reported']

        for feature in features_reported:

            assessment_data = self.get_assessment_data(
                self.general_id,
                feature
            )

            for k, v in child_data.items():
                if not v:
                    continue

                field_name = summary_fields.get(k)
                d = {}

                d[field_name] = unicode(v)
                d['COM_GeneralId'] = self.general_id
                d['MSFDArticle'] = parent_data['article']
                d['Feature'] = feature

                for mru in parent_data['marine_unit_ids']:
                    d['MarineUnit'] = mru

                    id_assess = []

                    for row in assessment_data:
                        if getattr(row, field_name) and \
                           not row.AssessmentCriteria:

                            id_assess.append(row.Id)

                    if id_assess:
                        d['Id'] = id_assess
                    db.save_record(sql2018.COMAssessment, **d)

    @use_db_session('session_2018')
    def get_assessment_data(self, general_id, feature=None):
        conditions = []
        conditions.append(sql2018.COMAssessment.COM_GeneralId == general_id)

        if feature:
            conditions.append(sql2018.COMAssessment.Feature == feature)

        cnt, assess_data = db.get_all_records(
            sql2018.COMAssessment,
            *conditions
        )

        return assess_data

    def _build_subforms(self, tree):
        """ Build a form of options from a tree of options
        """
        base_name = tree.name
        # TODO: get list of descriptors?
        data = self.get_flattened_data(self)

        descriptor = data['descriptor']
        descriptor_criterions = get_ges_criterions(descriptor)

        forms = []

        # check if article was already assessed
        @use_db_session('session_2018')
        def func():
            mc = sql2018.COMGeneral
            conditions = []
            conditions.append(mc.CountryCode == data['member_state'])
            conditions.append(mc.AssessmentTopic == u'National summary')
            conditions.append(mc.MSFDArticle == data['article'])
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

            form = EmbeddedForm(self, self.request)

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
                    data['article'],  # MSFDArticle
                    data['feature_reported'][0],  # Feature
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
                    data['article'],  # MSFDArticle
                    data['feature_reported'][0],  # Feature
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

    def build_forms(self):
        article = self.get_flattened_data(self)['article'].capitalize()
        try:
            article = form_structure[article]
        except KeyError:    # article is not in form structure yet
            return
        assessment_criterias = article.children

        for criteria in assessment_criterias:
            subforms = self._build_subforms(criteria)

            for subform in subforms:
                self.subforms.append(subform)

    def render_subforms(self):
        out = u''

        for form in self.subforms:
            out += form()

        out = u'<div class="collapsed-container">{}</div>'.format(out)

        return out

    def update(self):
        print ("====Doing assessment data form update")
        # TODO: identify the cases when the update happens

        if not self.subforms:  # update may be called multiple times? When?
            self.build_forms()

        sumform = SummaryAssessmentDataForm2018(self, self.request)

        data = self.get_flattened_data(self)
        sumform.set_default_values(data)
        # sumform.fields['recommendations'].field.default = u'DEFAULTED'

        self.main_assessment_data_forms = [
            sumform
        ]
        self.children = [
            # BasicAssessmentDataForm2018(self, self.request),
            self.render_subforms,
        ] + self.main_assessment_data_forms
# TODO: define the tabs selection label for mobile view (see wise-macros.pt)

# class MainAssessmentForm(BaseEnhancedForm, Form):
#     """ Base form for all main compliance view forms
#
#     # mostly similar to .base.MainForm
#     """
#     implements(IMainForm)
#     template = Template('../pt/mainform.pt')        # compliance-main
#     ignoreContext = True
#     reset_page = False
#     subform = None
#     subform_content = None
#     fields = Fields()
#     # css_class = 'compliance-form-main'
#     session_name = 'session'
#
#     main_forms = MAIN_FORMS
#     _is_save = False
#
#     def __init__(self, context, request):
#         Form.__init__(self, context, request)
#         self.save_handlers = []
#
#     def add_save_handler(self, handler):
#         self.save_handlers.append(handler)
#
#     @buttonAndHandler(u'Apply filters', name='continue')
#     def handle_continue(self, action):
#         self._is_save = True
#
#     def get_subform(self):
#         if self.subform:
#             return self.subform(self, self.request)
#
#     def update(self):
#         super(MainAssessmentForm, self).update()
#         print ("===Doing main form update")
#         self.data, self.errors = self.extractData()
#
#         has_values = self.data.values() and all(self.data.values())
#
#         if has_values:
#             self.subform = self.get_subform()
#
#             if self.subform:
#                 # we need to update and "execute" the subforms to be able to
#                 # discover them, because the decision process regarding
#                 # discovery is done in the update() method of subforms
#
#                 # with restore_session():
#                 # when using different sessions, we will need to restore
#                 # the self.session current session name
#                 self.subform_content = self.subform()
#
#         if self._is_save:
#             for handler in self.save_handlers:
#                 handler()
#
#
# class MainFormWrapper(BaseFormWrapper):
#     index = Template('../pt/layout.pt')     # compliance-
#
#
# class IMemberState(Interface):
#     member_state = Choice(
#         title=u"Country",
#         vocabulary="wise_search_member_states",
#         required=False,
#     )
#
#
# class NationalDescriptorForm(MainAssessmentForm):
#     # TODO: redo. Old '@@comp-national-descriptor'
#     assessment_topic = 'GES Descriptor (see term list)'
#     fields = Fields(IMemberState)
#     name = "comp-national-descriptor"
#
#     form_id = 'wise-compliance-form'
#
#     form_id_top = 'wise-compliance-form-top'
#
#     form_container_class = 'wise-compliance-form-container'
#
#     def get_subform(self):
#         return GESDescriptorForm(self, self.request)
#
#
# NationalDescriptorFormView = wrap_form(NationalDescriptorForm,
# MainFormWrapper)
#
#
# class IGESDescriptor(Interface):
#     descriptor = Choice(
#         title=u"Descriptor",
#         vocabulary=descriptors_vocabulary,
#         required=False,
#         default='D5'
#     )
#
#
# class GESDescriptorForm(EmbeddedForm):
#     fields = Fields(IGESDescriptor)
#
#     def get_subform(self):
#         return ArticleForm(self, self.request)
#
#
# class IArticle(Interface):
#     article = Choice(
#         title=u"Article",
#         vocabulary=articles_vocabulary,
#         required=False,
#     )
#
#
# class ArticleForm(EmbeddedForm):
#     fields = Fields(IArticle)
#
#     def get_subform(self):
#         return MarineUnitIDsForm(self, self.request)
#
#     @db.use_db_session('session_2018')
#     def get_muids_2018(self, article, country):
#         m = {
#             'Art8': sql2018.ART8GESMarineUnit
#         }
#
#         ris = db.get_unique_from_mapper(
#             sql2018.ReportedInformation,
#             'Id',
#             sql2018.ReportedInformation.CountryCode == country
#         )
#         ris = [int(c) for c in ris]
#         t = m.get(article)
#
#         if not t:
#             print "TODO: provide support for article ", article
#
#             return []
#
#         muids = db.get_unique_from_mapper(
#             t,
#             'MarineReportingUnit',
#             t.IdReportedInformation.in_(ris),
#         )
#
#         print muids
#
#         return muids
#
#     def get_available_marine_unit_ids(self):
#         # marine_unit_ids = self.data.get('marine_unit_ids')
#
#         # TODO: should also do the request form reading
#         data = self.get_flattened_data(self)
#         article = data['article']
#         country = data['member_state']
#
#         if country:
#             _count, d_2012 = db.get_marine_unit_ids(member_states=[country])
#             d_2018 = self.get_muids_2018(article, country)
#
#             return (_count + len(d_2018), d_2012 + d_2018)
#         else:
#             return []
#
#
# class MarineUnitIDsForm(EmbeddedForm):
#     fields = Fields(IMarineUnitIDsSelect)
#     fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget
#
#     def get_subform(self):
#         return BasicAssessmentDataForm2018(self, self.request)
#
#
# class IBasicAssessmentData2018(Interface):
#     """ The basic fields for the assessment data for 2018
#     """
#     # TODO: this needs a select box?
#     feature_reported = List(
#         title=u'Feature reported',
#         value_type=Choice(vocabulary=features_vocabulary),
#     )
#
#
# class BasicAssessmentDataForm2018(EmbeddedForm):
#     """
#     """
#
#     fields = Fields(IBasicAssessmentData2018)
#     fields['feature_reported'].widgetFactory = OptgroupFieldWidget
#
#     def get_subform(self):
#         return NationalDescriptorAssessmentForm(self, self.request)
#
#
# class NationalDescriptorAssessmentForm(Container):
#     """ Form to create and assess a national descriptor overview
#     """
#     assessment_topic = u'National summary'
#
#     form_name = "national-descriptor-assessment-form"
#     render = Template('pt/container.pt')
#     css_class = "left-side-form"
#
#     def update(self):
#         super(NationalDescriptorAssessmentForm, self).update()
#
#         # a quick hack to allow splitting up the code reusing the concept of
#         # subforms. Some of them are actually views. They're callbables that:
#         # - render themselves
#         # - answer to the save() method?
#         self.subforms = [
#             ReportData2012(self, self.request),
#
#             ReportHeaderForm2018(self, self.request),
#             ReportData2018(self, self.request),
#             AssessmentHeaderForm2018(self, self.request),
#             AssessmentDataForm2018(self, self.request)
#         ]
#
#         for child in self.subforms:
#             if hasattr(child, 'update'):
#                 child.update()

    # TODO NOT used method, delete this?
    # def get_ges_descriptions(self, indicators):
    #     """
    #     :param indicators:
    #     :return:
    #     """
    #     res = {}
    #
    #     for indic in indicators:
    #         res[indic.ReportingFeature] = indic.DescriptionGES
    #
    #     return res

    # TODO NOT used method, delete this?
    # def get_descriptors_for_muid(self, muid):
    #     return sorted(
    #         [x for x in self.indicator_descriptors if x.MarineUnitID == muid],
    #         key=lambda o: o.ReportingFeature
    #     )

    # old method to get data, not used
    # TODO maybe delete this in the future
    def get_data_reported(self, marine_unit_id, descriptor):
        descriptor_class = DESCRIPTORS.get(descriptor, None)

        if not descriptor_class:
            return []

        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mapper_class = mc[1]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name + 'Assesment')
            mc_assesment_ind = getattr(sql, 'MSFD8b' + theme_name +
                                       'AssesmentIndicator')
            id_indicator_col = 'MSFD8b_' + theme_name + \
                '_AssesmentIndicator_ID'

            count, res = db.compliance_art8_join(
                [
                    # getattr(mc_assesment_ind, id_indicator_col),
                    mapper_class.Topic, mapper_class.Description,
                    mapper_class.SumInfo1,
                    mapper_class.SumInfo1Unit,
                    mapper_class.SumInfo1Confidence, mapper_class.TrendsRecent,
                    mapper_class.TrendsFuture,

                    getattr(mc_assesment_ind, id_indicator_col),

                    mc_assesment_ind.GESIndicators,
                    mc_assesment_ind.OtherIndicatorDescription,
                    mc_assesment_ind.ThresholdValue,
                    mc_assesment_ind.ThresholdValueUnit,
                    mc_assesment_ind.ThresholdProportion,

                    mc_assessment.Status,
                    mc_assessment.StatusConfidence,
                    mc_assessment.StatusTrend, mc_assessment.StatusDescription,
                    mc_assessment.Limitations,
                    mapper_class.RecentTimeStart, mapper_class.RecentTimeEnd
                ],
                mc_assessment,
                mc_assesment_ind,
                mapper_class.MarineUnitID == marine_unit_id
            )

            results.append(res)

        return results[0]

    # @property
    # def descriptors(self):
    #     """ Get all descriptor codes
    #     :return: ['D1', 'D2', ..., 'D10', 'D11']
    #     """
    #     m = sql.MSFDFeaturesOverview
    #     res = db.get_unique_from_mapper(
    #         m, 'RFCode',
    #         m.FeatureType == 'GES descriptor'
    #     )
    #
    #     return res

        # is_changed = False
        #
        # if not prev_snap:
        #     return is_changed, res
        #
        # res_changed = deepcopy(res)
        #
        # for mru_row in res_changed:
        #     mru = mru_row[0]
        #     data = mru_row[1]
        #     prev_data = [x[1] for x in prev_snap if x[0] == mru][0]
        #
        #     for val_name_row in data:
        #         val_name = val_name_row[0]
        #         values = val_name_row[1]
        #         prev_values = [x[1] for x in prev_data if \
        #         x[0] == val_name][0]
        #
        #         for indx in range(len(values)):
        #             val = values[indx]
        #             prev_val = prev_values[indx]
        #
        #             if val != prev_val:
        #                 values[indx] = [prev_val, val]
        #                 is_changed = True
        #
        # return is_changed, res_changed

    def compare_data(self, res, prev_snap):

        return res != prev_snap
        # last_snap = snapshots[-1]

        # # self.is_changed = self.compare_data(self.new_data, last_snap[1])
        # self.is_changed = True
        # self.subform.is_changed = lambda: self.is_changed
        # self.subform.buttons['harvest'].condition = \
        #     lambda form: form.is_changed()

        # print "Nr of snapshots: {}".format(len(snapshots))
        # print "selected date: {}".format(date_selected)

# def get_default_additional_field_value(
#         data_assess,
#         article,
#         feature,
#         assess_crit,
#         assess_info,
#         field_name
#         ):
#
#     # TODO: check the feature param, we no longer need it
#
#     if not data_assess:
#         return None
#
#     for x in data_assess:
#         field_data = getattr(x, field_name)
#
#         # x.Feature == feature and \
#
#         if x.MSFDArticle == article and \
#                 x.AssessmentCriteria == assess_crit and \
#                 x.AssessedInformation == assess_info and \
#                 field_data:
#
#             return field_data
#
#     return None


# def get_default_assessment_value(
#         data_assess,
#         article,
#         feature,
#         assess_crit,
#         assess_info,
#         ges_comp
#         ):
#
#     if not data_assess:
#         return None
#
#     for x in data_assess:
#         if x.MSFDArticle == article and \
#                 x.AssessmentCriteria == assess_crit and \
#                 x.AssessedInformation == assess_info and \
#                 x.GESComponent_Target == ges_comp:
#             # x.Feature == feature and \
#
#             return x.Evidence
#
#     return None
#


class Leaf(object):
    """ A generic leaf in a tree. Behaves somehow like a tree
    """

    children = ()

    def __repr__(self):
        return "<Leaf '%s'>" % self.name

    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

    def __getitem__(self, name):
        for c in self.children:
            if c.name == name:
                return c
        raise KeyError

    def __setitem__(self, name, v):
        v.name = name
        self.children.append(v)

    def add(self, item):
        if item not in self.children:
            self.children.append(item)


    # def default_countries(self):
    #     # TODO: this needs to be adjusted for subprogrammes
    #
    #     regions = self.data.get('region_subregions')
    #
    #     if regions:
    #         submonprog_ids = []
    #         mptypes_subprog = self.get_mptypes_subprog()
    #         mp_type_ids = self.get_mp_type_ids()
    #
    #         for mid in mp_type_ids:
    #             submonprog_ids.extend(mptypes_subprog[int(mid)])
    #
    #         res = db.get_unique_from_mapper(
    #             sql.MSFD11MONSub,
    #             'MemberState',
    #             sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids),
    #             sql.MSFD11MONSub.Region.in_(regions),
    #         )
    #
    #         return res
    #
    #     return all_values_from_field(self, self.fields['member_states'])
    #
    # def default_regions(self):
    #     return all_values_from_field(self, self.fields['region_subregions'])
    #
    # def default_marine_unit_ids(self):
    #     return all_values_from_field(self, self.fields['marine_unit_ids'])

    # def default_regions(self):
    #     return all_values_from_field(self, self.fields['region_subregions'])
    #
    # def default_countries(self):
    #     regions = self.data.get('regions')
    #
    #     if regions:
    #         mp_type_ids = self.context.get_mp_type_ids()
    #         mon_ids = db.get_unique_from_mapper(
    #             sql.MSFD11MP,
    #             'MON',
    #             sql.MSFD11MP.MPType.in_(mp_type_ids)
    #         )
    #         res = db.get_unique_from_mapper(
    #             sql.MSFD11MON,
    #             'MemberState',
    #             sql.MSFD11MON.ID.in_(mon_ids),
    #             sql.MSFD11MON.Region.in_(regions)
    #         )
    #
    #         return [x.strip() for x in res]
    #
    #     return all_values_from_field(self, self.fields['member_states'])
    #
    # def default_marine_unit_ids(self):
    #     return all_values_from_field(self, self.fields['marine_unit_ids'])


def parse_forms_file():
    csv_f = resource_filename('wise.msfd',
                              'data/forms.tsv')

    res = L('articles')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter='\t')

        l1, l2, l3, l4 = None, None, None, None     # the 4 columns

        for row in csv_file:
            if not row:
                continue
            article, criteria, information, evidence = row
            evidence = unicode(evidence, 'utf-8')

            l4 = L(evidence)    # always last level, we can safely create it

            if (l3 is None) or (l3.name != information):
                l3 = L(information)
            l3.add(l4)

            if (l2 is None) or (l2.name != criteria):
                l2 = L(criteria)
            l2.add(l3)

            if (l1 is None) or (l1.name != article):
                l1 = L(article)
                res.add(l1)
            l1.add(l2)

    return res


form_structure = parse_forms_file()

    # def get_score(self, descriptor):
    #     # NOTE: this is not used
    #
    #     total = 0
    #
    #     for assessment in descriptor.contentValues():
    #         data = getattr(assessment, 'assessment_data', {})
    #         score = data.get('OverallScore', 0)
    #         total += score
    #
    #     return total
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en"
  xmlns:tal="http://xml.zope.org/namespaces/tal"
  xmlns:metal="http://xml.zope.org/namespaces/metal"
  xmlns:i18n="http://xml.zope.org/namespaces/i18n"
  lang="en"
  metal:use-macro="context/main_template/macros/master"
  i18n:domain="eea">

  <body metal:fill-slot="content">

    <div id="layout-contents" tal:define="text context/text | nothing" >
      <div id="wise-search-form">
        <div id="wise-search-form-top">
          <metal:tabs
             metal:use-macro="context/wise-macros/macros/tabs"></metal:tabs>
        </div>

        <div
          class="start-page-content left-side-form"
          tal:content="structure text/output"
          tal:condition="text">
        </div>
      </div>
    </div>

  </body>
</html>
<div tal:repeat="item view/items">
  <div tal:replace="python: view.display_item(item)">
    item display here
  </div>
</div>
<metal:macro define-macro="tabs-comp">
  <div id="wise-search-form">
    <div id="wise-search-form-top">
      <ul class="nav nav-pills topnav hidden-xs">
        <tal:rep tal:repeat="tab view/main_forms">
          <li tal:define="
            maintitle python: tab.titles[0];
            subtitle python: tab.titles[1];
            active python: view.section == tab.section"
            tal:attributes="class python: active and 'tab-active'"
            >
            <a href=""
              tal:attributes="href string:./${tab.view}"
              >
              <span tal:content="maintitle">Article X</span>
              <span tal:content="subtitle">Subtitle here</span>
            </a>
          </li>
        </tal:rep>
      </ul>

      <!-- <div class="visible-xs" style="clear: both;"> -->
      <div class="visible-xs">
        <div>
          Select article:
        </div>
          <select class="notselect" id="mobile-select-article" >
            <tal:rep tal:repeat="tab view/main_forms" >
              <tal:block tal:define="
                maintitle python: tab.titles[0];
                subtitle python: tab.titles[1];
                active python: view.section == tab.section">
                <option tal:attributes="value string:./${tab.view}; data-maintitle maintitle; data-subtitle subtitle;
                selected python: active and 'selected'"
                        tal:content="python: tab.title + ' ' + tab.subtitle"
                >
                </option>
              </tal:block>
            </tal:rep>
          </select>
      </div>
      <!-- <h2 tal:content="view/title">Title here</h2> -->
      <div tal:condition="not: view/subform_content">
        Please refine your search.
      </div>
    </div>

    <!--<div class="wise-search-form-container">-->
      <!--<metal:block use-macro="context/@@ploneform-macros/titlelessform">-->
        <!--<metal:slot fill-slot="fields">-->
          <!--<div class="form-right-side">-->
            <!--<metal:block use-macro="context/@@ploneform-macros/fields" ></metal:block>-->
          <!--</div>-->
        <!--</metal:slot>-->
        <!--<metal:slot fill-slot="actions">-->
          <!--<div tal:content="structure view/subform_content | nothing">subform here</div>-->
          <!--<div class="form-right-side">-->
            <!--<metal:block use-macro="context/@@ploneform-macros/actions" />-->
          <!--</div>-->
        <!--</metal:slot>-->
        <!--<metal:css fill-slot="formtop">-->
          <!--<style>-->

          <!--</style>-->
        <!--</metal:css>-->
      <!--</metal:block>-->

    </div>
  </div>
</metal:macro>
<!--<div id="compliance-module-container">-->
  <!--<div tal:content="structure view/compliance_content">forms</div>-->
<!--</div>-->
<html>
  <head>
     <!--<link href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" rel="stylesheet" integrity="sha384&#45;MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous" />-->
     <!--<style>-->
       <!--body {-->
       <!--font&#45;size: 70%;-->
       <!--}-->
     <!--</style> -->
  </head>
<body>

  <div style="display:none">
<h5>Descriptors (descriptors)</h5>
<div tal:replace="view/descriptors"></div>

<h5>Descriptor labels (descs)</h5>
<div tal:replace="view/descs"></div>

<h5>MarineUnitIds (muids)</h5>
<div tal:replace="view/muids"></div>

<h5>Criterions (criterions)</h5>
<div tal:replace="view/criterions"></div>

<h5>Criterions/Indicators (crit_lab_indics)</h5>
<div tal:replace="view/crit_lab_indics"></div>

<h5>Indicator/Feature Pressures (indics)</h5>
<div tal:replace="view/indic_w_p"></div>

<h5>Criterion labels (criterion_labels)</h5>
<div tal:replace="view/criterion_labels"></div>

<!--<h5>Indicators (indicators)</h5>-->
<!--<div>-->
  <!--<ul>-->
    <!--<li tal:repeat="indic view/indicator_descriptors">-->
      <!--Indicator Code: <span tal:content="indic/ReportingFeature"/>-->
      <!--, ID: <span tal:content="indic/MSFD9_Descriptor_ID"/>-->
    <!--</li>-->
  <!--</ul>-->
<!--</div>-->
  </div>

<div class="container-fluid">
  <!--<div tal:replace="structure view/art_9_tpl" ></div>-->
  <div tal:replace="structure view/art_8_tpl" ></div>
  <!--<div tal:replace="structure view/art_10_tpl" ></div>-->
</div>

</body>
</html>
<table tal:define="res view/data_rows">
  <thead>
    <tr>
      <th
        tal:repeat="label res/keys"
        tal:content="python: view.labelAsTitle(label)">
        Label here
      </th>
    </tr>
  </thead>
  <tbody>
    <tr tal:repeat="row res">
      <td tal:repeat="cell row" tal:content="cell"></td>
    </tr>
  </tbody>
</table>


# @register_form
# class A81bForm(SubForm):
#     title = 'Article 8.1b (Analysis of pressures and impacts)'
#     fields = Fields(interfaces.IA81bSubformSelect)
#     prefix = 'a81bselect'
#     data = {}
#
#     def get_subform(self):
#         klass = THEME_FORMS.get(self.data['theme'])
#
#         return super(A81bForm, self).get_subform(klass)
#

# @register_theme_subform('Ecosystem(s)', 'Pressures and impacts')
# class XXX(ItemDisplayForm, BaseFormUtil):
#     fields = Fields(interfaces.IRecordSelect)
#     prefix = 'a81a_eco'
#
#     def get_db_results(self):
#         page = int(self.data.get('page')) or 0
#         muid = self.get_marine_unit_id()
#         res = db.get_a10_targets(marine_unit_id=muid, page=page)
#
#         return res
#
#     def get_extra_data(self):
#         if not self.item:
#             return {}
#
#         target_id = self.item['MSFD10_Target_ID']
#
#         res = db.get_a10_feature_targets(target_id)
#         ft = pivot_data(res, 'FeatureType')
#
#         # res = db.get_a10_feature_targets(target_id)
#         # criteria = pivot_data(res, 'FeatureType')
#
#         return [
#             ('Feature Types', ft),
#             # ('Criteria Indicators', criteria),
#         ]



# ARTICLES = [
#     ('a81c', 'Article 8.1c (Economic and social analysis)'),
# ]

# articles_vocabulary = SimpleVocabulary(
#     [SimpleTerm(a[0], a[0], a[1]) for a in ARTICLES]
# )
#
#
# @provider(IVocabularyFactory)
# def articles_vocabulary_factory(context):
#     return articles_vocabulary


# A81A_THEMES = [
#     'Ecosystem(s)',
#     'Functional group(s)',
#     'Habitat(s)',
#     'Species(s)',
#     'Other(s)',
#     'NIS Inventory',
#     'Physical',
# ]
#
# a81a_themes_vocabulary = SimpleVocabulary(
#     [SimpleTerm(a, a, a) for a in A81A_THEMES]
# )


# @provider(IVocabularyFactory)
# def a81a_themes_vocabulary_factory(context):
#     return vocab


# A81B_THEMES = [
#     'Extraction of fish and shellfish',
#     'Extraction of seaweed, maerl and other',
#     'Harzardous substances',
#     'Hydrological processes',
#     'Marine litter',
#     'Microbial pathogens',
#     'Non-indigenous species',
#     'Underwater noise',
#     'Nutrients',
#     'Physical damage',
#     'Pollutant events',
#     'Acidification',
# ]

# a81b_themes_vocabulary = SimpleVocabulary(
#     [SimpleTerm(a, a, a) for a in A81B_THEMES]
# )


# @provider(IVocabularyFactory)
# def a81b_themes_vocabulary_factory(context):
#     return a81b_themes_vocabulary


    # def update(self):
    #     super(MainForm, self).update()
    #
    #     self.data, errors = self.extractData()
    #
    #     if all(self.data.values()):
    #         self.data['MarineUnitID'] = db.get_marine_unit_ids(**self.data)
    #
    #         if not errors and self.data['MarineUnitID']:
    #             self.subform = ArticleSelectForm(
    #                 self.context, self.request, self)
    #
    #     if errors:
    #         self.status = self.formErrorsMessage
    #
    #         return

    # import pdb; pdb.set_trace()

#     conn = connection()
#     res = conn.execute(text("""
# SELECT *
# FROM MSFD9_Descriptors
# WHERE
# MarineUnitID = :marine_unit_id
# ORDER BY MSFD9_Descriptor_ID
# OFFSET :page ROWS
# FETCH NEXT 1 ROWS ONLY
# """), marine_unit_id=marine_unit_id, page=page)

# class SubFormsVocabulary(SimpleVocabulary):
#     """ An hackish vocabulary that retrieves subform names for a form
#     """
#
#     # TODO: I'm not sure if this is needed. Its existance needs to be defended
#
#     def __init__(self, form_klass):
#         self.form_klass = form_klass
#         pass
#
#     def __call__(self, context):
#         self.context = context
#
#     @property
#     def _terms(self):
#         terms = []
#
#         forms = SUBFORMS[self.form_klass]
#
#         for k in forms:
#             terms.append(SimpleTerm(k, k.title, k.title))
#
#         return terms
#
#     @property
#     def by_value(self):
#         d = {}
#
#         for term in self._terms:
#             d[term.value] = term
#
#         return d
#
#     @property
#     def by_token(self):
#         d = {}
#
#         for term in self._terms:
#             d[term.token] = term
#
#         return d

# class CollectionDisplayForm(EmbeddedForm):
#     """ Display a collection of data (multiple rows of results)
#     """
#
#     pages = None        # a list of items to show
#
#     template = ViewPageTemplateFile('pt/collection.pt')
#
#     def __init__(self, *args, **kwargs):
#         super(CollectionDisplayForm, self).__init__(*args, **kwargs)
#
#     def update(self):
#         super(CollectionDisplayForm, self).update()
#         self.count, self.items = self.get_db_results()
#
#     def display_item(self, item):
#         return item


# def get_a9_available_marine_unit_ids(marine_unit_ids):
#     """ Returns a list of which muid is available, of the ones provided
#     """
#     sess = session()
#     q = sess.query(sql.MSFD9Descriptor.MarineUnitID).filter(
#         sql.MSFD9Descriptor.MarineUnitID.in_(marine_unit_ids)
#     ).distinct()
#
#     total = q.count()
#
#     return [total, q]


# def get_a10_available_marine_unit_ids(marine_unit_ids):
#     """ Returns a list of which muid is available, of the ones provided
#     """
#     sess = session()
#     q = sess.query(sql.MSFD10Target.MarineUnitID).filter(
#         sql.MSFD10Target.MarineUnitID.in_(marine_unit_ids)
#     ).distinct()
#
#     total = q.count()
#
#     return [total, q]

# def get_a8_available_marine_unit_ids(marine_unit_ids):
#     """ Returns a list of which muid is available, of the ones provided
#
#     TODO: implement specific to A8
#     """
#     sess = session()
#     q = sess.query(sql.MSFD10Target.MarineUnitID).filter(
#         sql.MSFD10Target.MarineUnitID.in_(marine_unit_ids)
#     ).distinct()
#
#     total = q.count()
#
#     return [total, q]



    # def get_db_results(self):
    #     page = self.get_page()
    #     muid = self.get_marine_unit_id()
    #
    #     return db.get_a81a_ecosystem(marine_unit_id=muid, page=page)



    # def get_db_results(self):
    #     mid = self.context.data.get('marine_unit_id')
    #     page = self.get_page()
    #
    #     return db.get_a10_targets(marine_unit_id=mid, page=page)
    # def get_db_results(self):
    #     mid = self.context.data.get('marine_unit_id')
    #     page = self.get_page()
    #
    #     return db.get_a9_descriptors(marine_unit_id=mid, page=page)



# def get_a81a_ecosystem(marine_unit_id, page=0):
#     klass = sql.MSFD8aEcosystem
#
#     sess = session()
#     q = sess.query(klass).filter(
#         klass.MarineUnitID == marine_unit_id
#     ).order_by(
#         klass.MSFD8a_Ecosystem_ID
#     )
#
#     total = q.count()
#     item = q.offset(page).limit(1).first()
#
#     return [total, item]



# def get_a81a_ecosystem_pressureimpacts(rel_id, page=0):
#     klass = sql.MSFD8aEcosystemPressuresImpact
#
#     sess = session()
#     q = sess.query(klass).filter(
#         klass.MSFD8a_Ecosystem == rel_id
#     ).one()
#     item = q.first()
#
#     return [1, item]
# _pressure_impacts


# def get_a10_targets(marine_unit_id, page=0):
#     sess = session()
#     q = sess.query(sql.MSFD10Target).filter_by(
#         MarineUnitID=marine_unit_id
#     ).order_by(sql.MSFD10Target.MSFD10_Target_ID)
#
#     total = q.count()
#     item = q.offset(page).limit(1).first()
#
#     # TODO: the MSFD10_DESCrit is not ORM mapped yet
#     # this query is not finished!!!!
#
#     return [total, item]

#     conn = connection()
#     res = conn.execute(text("""
# SELECT MSFD10_Targets.*, MSFD10_DESCrit.GESDescriptorsCriteriaIndicators
# FROM MSFD10_Targets
# JOIN MSFD10_DESCrit
#     ON MSFD10_Targets.MSFD10_Target_ID = MSFD10_DESCrit.MSFD10_Target
# WHERE
# MSFD10_Targets.MarineUnitID = :marine_unit_id
# ORDER BY MSFD10_Targets.MSFD10_Target_ID
# OFFSET :page ROWS
# FETCH NEXT 1 ROWS ONLY
# """), marine_unit_id=marine_unit_id, page=page)

    # this is a temporary hack to overcome this
    # row = next(res)
    # keys = res.keys()
    # res = dict(zip(keys, row))
    # gdci = res.pop('GESDescriptorsCriteriaIndicators')
    # obj = sql.MSFD10Target(**res)
    # obj.GESDescriptorsCriteriaIndicators = gdci


def get_a9_descriptors(marine_unit_id, page=0):
    sess = session()
    q = sess.query(sql.MSFD9Descriptor).filter(
        sql.MSFD9Descriptor.MarineUnitID == marine_unit_id
    ).order_by(sql.MSFD9Descriptor.MSFD9_Descriptor_ID)

    total = q.count()
    item = q.offset(page).limit(1).first()

    return [total, item]


    # res = db.get_regions_subregions()
    # terms = [SimpleTerm(x, x, x) for x in res]
    # vocab = SimpleVocabulary(terms)
    #
    # return vocab

    # res = db.get_area_types()
    # terms = [SimpleTerm(x, x, x) for x in res]
    # vocab = SimpleVocabulary(terms)
    #
    # return vocab

# def get_member_states():
#     """ Returns a list of member states. Used in Articles 8, 9 and 10 searches
#     """
#     table = sql.t_MSFD4_GegraphicalAreasID
#     col = table.c.MemberState
#
#     sess = session()
#     res = sess.query(col).distinct().order_by(col)
#
#     return [x[0] for x in res]


# def get_regions_subregions():
#     """ Returns a list of regions and subregions.
#     """
#     table = sql.t_MSFD4_GegraphicalAreasID
#     col = table.c.RegionSubRegions
#
#     sess = session()
#     res = sess.query(col).distinct().order_by(col)
#
#     return [x[0] for x in res]


# def get_area_types():
#     """ Returns a list of area types.
#     """
#
#     table = sql.t_MSFD4_GegraphicalAreasID
#     col = table.c.AreaType
#
#     sess = session()
#     res = sess.query(col).distinct().order_by(col)
#
#     return [x[0] for x in res]


# def get_a10_feature_targets(target_id):
#     """ Used in extra_data for A10
#     """
#     conn = connection()
#     res = conn.execute(text("""
# SELECT DISTINCT FeatureType, PhysicalChemicalHabitatsFunctionalPressures
# FROM MarineDB.dbo.MSFD10_FeaturesPressures
# WHERE MSFD10_Target = :target_id
# """), target_id=target_id)
#
#     items = []
#
#     for item in res:
#         items.append(item)
#
#     return sorted(items)
#
#
# def get_a10_criteria_indicators(target_id):
#     conn = connection()
#     res = conn.execute(text("""
# SELECT DISTINCT GESDescriptorsCriteriaIndicators
# FROM MarineDB.dbo.MSFD10_DESCrit
# WHERE MSFD10_Target = :target_id
# """), target_id=target_id)
#
#     items = []
#
#     for item in res:
#         items.append(item)
#
#     return sorted(items)
<div
  tal:define="css_class view/css_class | string:"
  tal:attributes="class string:item-subform subform ${css_class};
                  id view/form_name">

  <metal:block use-macro="context/@@ploneform-macros/fields" />

  <tal:block tal:condition="python: view.item ">
      <h3 tal:content="view/get_record_title">Article title here</h3>
  </tal:block>

  <div tal:content="structure view/data_template | nothing"></div>
  <div tal:content="structure view/extras | nothing"></div>

  <tal:def define="subform view/subform | nothing">
    <div class="subform-level-x" tal:condition="subform">
      <div tal:content="structure subform">subform here</div>
    </div>
  </tal:def>

  <!--<tal:def define="compliance view/compliance_module | nothing">-->
    <!--<div tal:condition="compliance">-->
      <!--<div tal:content="structure compliance">compliance module here</div>-->
    <!--</div>-->
  <!--</tal:def>-->


</div>
<dl tal:define="item view/item">
  <tal:rep repeat="key python:view.get_obj_fields(item)" tal:condition="item">
    <tal:def tal:define="value item/?key; value python: view.print_value(value)">
      <dt tal:condition="value">
        <span tal:content="python: view.name_as_title(key)"
          tal:attributes="title key">Label</span>
      </dt>
      <dd tal:condition="value">
        <span tal:content="structure value">Some value here</span>
        <em tal:condition="not: value">No value</em>
      </dd>
    </tal:def>
  </tal:rep>
</dl>
# @use_db_session('2018')
# def save_record(mapper_class, **data):
#     print "we don't save, please save"
#
#     return
#     sess = session()
#
#     id_primary_key = data.pop('Id', [])
#     mc = mapper_class(**data)
#
#     len_ids = len(id_primary_key)
#
#     # insert into db if no Id provided
#
#     if len_ids < 1:
#         sess.add(mc)
#     # update the row(s) based on the Id(s)
#     else:
#         condition = []
#
#         # due to a bug??, if only one Id is provided
#         # because of the "in_" operator we get an error
#
#         if len_ids > 1:
#             condition.append(mapper_class.Id.in_(id_primary_key))
#         else:
#             condition.append(mapper_class.Id == id_primary_key[0])
#
#         sess.query(mapper_class).filter(*condition).update(data)
#
#     return
#     # try:
#     #     transaction.commit()
#     # except Exception as e:
#     #     print "------------ we rollback, please check before deploy!!!!!!!!!"
#     #     print e
#     #     sess.rollback()
#     #
#     #     return
#     #     # transaction.commit()
#
#     if not id_primary_key:
#         id_primary_key = mc.Id
#
#     return id_primary_key







#
#
#
#
#
# class Article910(BaseArticle2012):
#     """
#     """
#
#     Art9 = Template('pt/report-data-a9.pt')
#     Art10 = Template('pt/report-data-a10.pt')
#
#     # Art 10 methods
#     @property
#     def get_environment_data(self):
#         """ Get all data from a table
#         :return: table result
#         """
#         mc = sql.MSFD10Target
#         descr_nr = self.descriptor[1:]
#         count, res = db.get_all_records(
#             mc,
#             and_(
#                 mc.Topic == 'EnvironmentalTarget',
#                 mc.ReportingFeature.like('%{}%'.format(descr_nr)),
#                 mc.MarineUnitID.in_(self.muids)
#             )
#         )
#
#         if res:
#             return res[0]
#
#         return []
#
#     # Art 9 methods
#     @property
#     def criterions(self):
#         """ Get all criterions(indicators) and the descriptor
#             for a descriptor
#         :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#         """
#         nr = self.descriptor[1:]
#         m = sql.MSFDFeaturesOverview
#         res = db.get_unique_from_mapper(
#             m, 'RFCode',
#             or_(
#                 and_(m.RFCode.like('{}.%'.format(nr)),
#                      m.FeatureType == 'GES criterion',),
#                 and_(m.RFCode.like('{}'.format(self.descriptor)),
#                      m.FeatureType == 'GES descriptor')
#             ),
#             m.FeatureRelevant == 'Y',
#             m.FeatureReported == 'Y',
#         )
#
#         return res
#
#     def get_indicators_with_feature_pressures(self, muids, criterions):
#         """ Get a dict with all indicators and their corresponding features
#
#         :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
#         :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#         :return: {'5.2.2-indicator 5.2C': ['Transparency', 'InputN_Psubst'],
#         {'5.2.1- indicator 5.2B': ['InputN_Psubst', 'FunctionalGroupOther'],
#             ...}
#         """
#         t = sql.t_MSFD9_Features
#         count, res = db.get_all_records(
#             t,
#             t.c.MarineUnitID.in_(muids),
#         )
#         res = [row_to_dict(t, r) for r in res]
#
#         indicators = defaultdict(set)
#
#         for row in res:
#             rf = row['ReportingFeature']
#             indicators[rf].add(row['FeaturesPressuresImpacts'])
#
#         res = {}
#
#         for k, v in indicators.items():
#             flag = False
#
#             for crit in criterions:
#                 if k.startswith(crit):
#                     flag = True
#
#             if flag:
#                 res[k] = v
#
#         return res
#
#     def get_criterion_labels(self, criterions):
#         """ Get all labels for the criterions
#         :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#         :return: [('5.1', '5.1: Nutrients levels'),
#             ('5.1.2', '5.1.2: Nutrient ratios (silica'), (...)]
#         """
#         count, res = db.get_all_records(
#             sql.MSFD11CommonLabel,
#             sql.MSFD11CommonLabel.value.in_(criterions),
#             sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
#                                              'list-GESCriteria')),
#         )
#
#         criterion_labels = dict([(x.value, x.Text) for x in res])
#         # add D5 criterion to the criterion lists too
#         criterion_labels[self.descriptor] = self.context.desc_label
#
#         return criterion_labels
#
#     def get_indicator_title(self, value):
#
#         return value
#
#     def get_marine_unit_id_title(self, muid):
#         t = sql_extra.MSFD4GeographicalAreaID
#         res = db.get_unique_from_mapper(
#             t,
#             'MarineUnits_ReportingAreas',
#             t.MarineUnitID == muid,
#         )
#
#         assert len(res) == 1
#
#         if res:
#             title = u'{} - {}'.format(muid, res[0])
#         else:
#             title = muid
#
#         return title
#
#     def get_indicator_descriptors(self, muids, available_indicators):
#         """ Get data based on Marine Units and available indicators
#
#         :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
#         :param available_indicators: ['5.2.2-indicator 5.2C',
#                                       '5.2.1- indicator 5.2B']
#         :return: table result
#         """
#         # TODO: sort the results based on ascending muid?
#         count, res = db.get_all_records(
#             sql.MSFD9Descriptor,
#             sql.MSFD9Descriptor.MarineUnitID.in_(muids),
#             sql.MSFD9Descriptor.ReportingFeature.in_(available_indicators)
#         )
#
#         return res
#
#     @property
#     def crit_lab_indics(self):
#         """ Get all criterions with their reported indicators
#         :return: {'5.1': [],
#                   '5.1.1': ['5.1.1-indicator 5.1A', '5.1.1-indicator 5.1B']
#                   , ...}
#         """
#         crit_lab_indics = defaultdict(list)
#
#         for crit_lab in self.criterion_labels.keys():
#             crit_lab_indics[crit_lab] = []
#
#             for ind in self.indic_w_p.keys():
#                 norm_ind = ind.split('-')[0]
#
#                 if crit_lab == norm_ind:
#                     crit_lab_indics[crit_lab].append(ind)
#
#             if not crit_lab_indics[crit_lab]:
#                 crit_lab_indics[crit_lab].append('')
#
#         crit_lab_indics[u'GESOther'] = ['']
#
#         return crit_lab_indics
#
#     @property
#     def colspan(self):
#         colspan = len([item
#                        for sublist in self.crit_lab_indics.values()
#
#                        for item in sublist])
#
#         return colspan
#
#     def setup_data(self):
#         # {u'5.2.2-indicator 5.2C': set([u'Transparency', u'InputN_Psubst']),
#         self.indic_w_p = self.get_indicators_with_feature_pressures(
#             self.muids, self.criterions
#         )
#
#         self.criterion_labels = self.get_criterion_labels(
#             self.criterions
#         )
#
#         self.indicator_descriptors = self.get_indicator_descriptors(
#             self.muids, self.indic_w_p.keys()
#         )
#
#     def __call__(self):
#         self.setup_data()
#
#         t_impl = getattr(self, self.article, None)
#
#         self.content = t_impl and t_impl() or ""
#
#         return self.content
#

# ----------- SCRAP code

# The problem is that there appears to be a missing link that connects
# the indicator assessment to the real <Analysis> tag in the XML file
# We use the database to bypass this problem
# dbitem = self.indicator_assessment.database_assessment()
# rep_type = self.report.report_type
#
# # TODO: may need a mapping
#
# if rep_type.endswith('s'):      # quick hack, should get a mapping
#     rep_type = rep_type[:-1]
#
# return getattr(dbitem, 'MSFD8b_{}'.format(rep_type))

# def __init__(self, report, indicator_assessment, country_code,
#              marine_unit_id, criterion):
#
#     super(A8Item, self).__init__([])
#
#     self.country_code = country_code
#     self.criterion = criterion
#     self.marine_unit_id = marine_unit_id
#
#     # How to handle multiple reports?
#     self.report = report
#     self.indicator_assessment = indicator_assessment
#
#     attrs = [
#         ('SumInfo1 [ValueAchieved]', self.suminfo1),
#         ('[ProportionThresholdValue]', lambda: 'Row not implemented'),
#
#         # TODO: check fields
#
#         ('Status [CriteriaStatus]', self.as_status),
#         ('StatusTrend', self.as_status_trend),
#         ('StatusConfidence', self.as_status_confidence),
#         ('StatusDescription [DescriptionCriteria]',
#          self.as_status_description),
#         ('Limitations (DesciptionElement)', self.limitations),
#         ('RecentTimeStart/RecentTimeEnd/AssessmentDateStart/'
#          'AssessmentDateEnd [AssessmentPeriod]', self.recent_time_start),
#
#         ('LevelPressureOverall: Description', self.lpo_description),
#         ('LevelPressureOverall: SumInfo1 [proportion of area subject '
#          'to nutrient enrichment]', self.lpo_suminfo1),
#         ('LevelPressureOverall: SumInfo1Confidence', self.lpo_confidence),
#
#         # TODO: this needs to be done in a generic mode.
#         # LevelPressure<PressureID>
#         # ImpactPressure<PressureID>
#
#         ('LevelPressureN/P/OLoad: Description', self.pres_description),
#         ('LevelPressureN/P/OLoad: SumInfo1 [input load of '
#          'nitrogen/phosphorus/organic matter]', self.pres_sum1),
#         ('LevelPressureN/P/OLoad: SumInfo1Unit', self.pres_unit),
#         ('LevelPressureN/P/OLoad: SumInfo1Confidence',
#          self.pres_confidence),
#         ('LevelPressureN/P/OLoad: TrendsRecent', self.pres_trend_recent),
#         ('LevelPressureN/P/OLoad: TrendsFuture', self.pres_trend_future),
#
#         ('Activities: Description', self.activity_description),
#         ('ActivityType', self.activity_type),
#         ('InfoGaps', self.info_gaps),
#     ]
#
#     for title, handler in attrs:
#         self[title] = self.handle_missing_assessment(handler)
#
# def info_gaps(self):
#     v = self.report['w:Analysis/w:InfoGaps/text()']
#
#     return v and v[0] or ''
#
# def activity_description(self):
#     x = self.report['w:Analysis/w:Activities/w:Description/text()']
#
#     return x and x[0] or ''
#
# def activity_type(self):
#     nodes = self.report['w:Analysis/w:Activities/'
#                         'w:Activity/w:ActivityType/text()']
#
#     return ', '.join(nodes)
#
# def lpo_confidence(self):
#     x = 'w:Analysis/w:LevelPressureOverall/w:SumInfo1Confidence/text()'
#     v = self.report[x]
#
#     if v:
#         return v[0]
#
# def lpo_description(self):
#     x = 'w:Analysis/w:LevelPressureOverall/w:Description/text()'
#     v = self.report[x]
#
#     if v:
#         return v[0]
#
# def lpo_suminfo1(self):
#     x = 'w:Analysis/w:LevelPressureOverall/w:SumInfo1/text()'
#     v = self.report[x]
#
#     if v:
#         return v[0]
#
# def recent_time_start(self):
#     v = self.report["w:Metadata[contains(./w:Topic/text(),"
#                     "'AnalysisCharactTrend')]"]
#
#     if v:
#         v = Node(v[0], NSMAP)
#
#         return '{} - {}'.format(v['w:AssessmentStartDate/text()'][0],
#                                 v['w:AssessmentEndDate/text()'][0])
#
# def limitations(self):
#     return self.related_assessment.Limitations
#
# def as_status(self):
#     ia = self.indicator_assessment
#     v = ia['ancestor::w:Assessment/c:Status/text()']
#
#     return v and v[0] or ''
#
# def as_status_trend(self):
#     ia = self.indicator_assessment
#     v = ia['ancestor::w:Assessment/c:StatusTrend/text()']
#
#     return v and v[0] or ''
#
# def as_status_confidence(self):
#     ia = self.indicator_assessment
#     v = ia['ancestor::w:Assessment/c:StatusConfidence/text()']
#
#     return v and v[0] or ''
#
# def as_status_description(self):
#     ia = self.indicator_assessment
#     v = ia['ancestor::w:Assessment/c:StatusDescription/text()']
#
#     return v and v[0] or ''
#
# @property
# def analysis_tag(self):
#     # TODO: I don't think this is well implemented. It doesn't fit the
#     # specification Excel file
#
#     # the Analysis -> LevelPressureNLoad tag
#     _type = self.analysis()
#
#     nodes = self.report['.//w:' + _type]
#
#     if nodes:
#         return Node(nodes[0], NSMAP)
#
# def pres_confidence(self):
#     tag = self.analysis_tag
#
#     if tag:
#         v = self.analysis_tag['w:SumInfo1Confidence/text()']
#
#         return v and v[0] or ''
#
# def pres_trend_recent(self):
#     tag = self.analysis_tag
#
#     if tag:
#         v = self.analysis_tag['w:TrendsRecent/text()']
#
#         return v and v[0] or ''
#
# def pres_trend_future(self):
#     tag = self.analysis_tag
#
#     if tag:
#         v = self.analysis_tag['w:TrendsFuture/text()']
#
#         return v and v[0] or ''
#
# def pres_sum1(self):
#     # search for the Analysis > X tag that correspunds to this analysis
#
#     tag = self.analysis_tag
#
#     if tag:
#         return self.analysis_tag['w:SumInfo1/text()'][0]
#
# def pres_description(self):
#     tag = self.analysis_tag
#
#     if tag:
#         return self.analysis_tag['w:Description/text()'][0]
#
# def pres_unit(self):
#     tag = self.analysis_tag
#
#     if tag:
#         v = self.analysis_tag['w:SumInfo1Unit/text()']
#
#         return v and v[0] or ''
#
# def suminfo1_tv(self):
#     # {'Description': u'Latvijas liel\u0101ko upju .',
#     #  'FutureTimeEnd': None,
#     #  'FutureTimeStart': None,
#     #  'Limitations': None,
#     #  'MSFD8b_Nutrients_ID': 990,
#     #  'MSFD8b_Nutrients_Import': 53,
#     #  'MarineUnitID': u'BAL- LV- AA- 001',
#     #  'RecentTimeEnd': None,
#     #  'RecentTimeStart': None,
#     #  'SumInfo1': u'Nov\u0113rt\u0113jums attiecas ',
#     #  'SumInfo1Confidence': u'Moderate',
#     #  'SumInfo1Unit': u'tonnas/gad\u0101',
#     #  'Topic': u'LevelPressureNLoad',
#     #  'TrendsFuture': u'Unknown_NotAssessed',
#     #  'TrendsRecent': u'Unknown_NotAssessed',
#     # return self.related_assessment.SumInfo0Unit
#
#     tv = self.indicator_assessment['c:ThresholdValueUnit/text()']
#
#     return tv and tv[0] or ''
#
# def handle_missing_assessment(self, handler):
#     if handler.__name__ == '<lambda>':      # don't handle lambdas
#         return handler()
#
#     if self.indicator_assessment is None:
#         return ''
#
#     return handler()
#
# def threshold_value(self):
#     return self.indicator_assessment['c:ThresholdValue/text()'][0]
#
# def topic(self):
#     return self.indicator_assessment.topic
#
# def suminfo1(self):
#     return self.related_assessment.SumInfo1
#
# def analysis(self):
#     # import pdb; pdb.set_trace()
#
#     return self.related_assessment.Topic
#
# @property
# def related_assessment(self):
#     """ Locate the imported assessment in the database
#
#     :returns: SQLAlchemy object, like MSFD8bNutrient instance
#     """
#     # The problem is that there appears to be a missing link that connects
#     # the indicator assessment to the real <Analysis> tag in the XML file
#     # We use the database to bypass this problem
#     dbitem = self.indicator_assessment.database_assessment()
#     rep_type = self.report.report_type
#
#     # TODO: may need a mapping
#
#     if rep_type.endswith('s'):      # quick hack, should get a mapping
#         rep_type = rep_type[:-1]
#
#     return getattr(dbitem, 'MSFD8b_{}'.format(rep_type))


# class IndicatorAssessment(Node):
#     """ A wrapper over <Indicators> nodes
#     """
#
#     @property
#     def assessment(self):
#         # the AssessmentPI node
#
#         return Node(self.node.getparent().getparent(), NSMAP)
#
#     @property
#     def topic(self):
#         topic = self.assessment['w:Topic/text()']
#
#         return topic and topic[0] or ''     # empty if descriptor column
#
#     @property
#     def report_type(self):
#         # get the parent tag name as "report type"
#         root = self.node.getroottree()
#         tag_names = get_report_tags(root)
#
#         for name in tag_names:
#             parent = self['ancestor::w:' + name]
#
#             if parent:
#                 return tag_name(parent[0])
#
#     @property
#     def marine_unit_id(self):
#         return self['ancestor::*/w:MarineUnitID/text()'][0]
#
#     @db.use_db_session('2012')
#     def database_assessment(self):
#         mc = ASSESSMENT_MAPPER_CLASSES[self.report_type]
#         count, res = db.get_all_records(
#             mc,
#             mc.Topic == self.topic,
#             mc.MarineUnitID == self.marine_unit_id,
#             raw=True,       # avoid db cache
#         )
#
#         if count > 1:
#             raise ValueError("Multiple assessments")
#
#         if not res:
#             import pdb; pdb.set_trace()
#
#         return res[0]

    # def indicator_assessments(self, criterion):
    #     res = []
    #
    #     indicators = [IndicatorAssessment(n, NSMAP)
    #                   for n in self['.//c:Indicators']]
    #
    #     for crit_id in criterion.all_ids():
    #         for n_i in indicators:
    #             crit = n_i['c:Indicator/text()'][0]
    #
    #             if crit == crit_id:
    #                 res.append(n_i)
    #
    #     return res

# def get_related_item(dbitem):
#     """ Automatically detect which attribute of the given object is
#     a relationship and returns the end object of that relationship
#     """
#
#     for name in dir(dbitem):
#         if name.startswith('_'):
#             continue
#
#         v = getattr(name, dbitem)
#
#         if not v:
#             continue
#
#         if isinstance(v, [basestring, int]):
#             continue
#
#         return v

# def assessment_types(self):
#     for node in self['w:Analysis/*']:
#         pass
#

# TODO: redo this, it needs to be done per indicator
# join the criterions with their corresponding assessments
# gc_as = zip(ges_crits,
#             [report.indicator_assessments(gc) for gc in ges_crits])
#
# report = m_reps[0]
# cols = []
#
# for gc, assessments in gc_as:
#     if not assessments:     # if there are no assessments for the
#                             # criterion, just show it
#         item = A8Item(report,
#                       None, self.country_code, muid, gc)
#         cols.append(item)
#
#         continue
#
#     for assessment in assessments:
#         item = A8Item(report,
#                       assessment, self.country_code, muid, gc)
#         cols.append(item)

# map = {
#     'Nutrients': [
#         'LevelPressureNConcentration',
#         'LevelPressurePConcentration',
#         'LevelPressureOConcentration',
#         'ImpactspressureWater',
#         'ImpactspressureSeabed',
#     ],
# }
#
# bases = map[self.report_type]

# self.db_record = self.get_db_record()
#
# mc_assessment = ASSESSMENT_MAPPER_CLASSES[self.report.report_type]
# self.assessment = get_db_assessment(mc_assessment, self.db_record)
#
# self.assessment_indicators = get_related_indicators(self.assessment)
# TODO: these are tags for article 8b, needs also for 8a
# tags = [
#     'PhysicalLoss',
#     'PhysicalDamage',
#     'Noise',
#     'Litter',
#     'HydrologicalProcesses',
#     'HazardousSubstances',
#     'PollutionEvents',
#     'Nutrients',
#     'MicrobialPathogens',
#     'NIS',
#     'ExtractionofFishShellfish',
#     'Acidification',
# ]
# a criterion is either a Descriptor (2018 concept), a Criteria or an Indicator
# assessment_node=None,   # XML node for the assessment
# if assessment:      # TODO: do we need this?
#     for node in self['parent::*/w:AssessmentPI']:
#         an = Node(node, NSMAP)
#         topic = an['w:Topic/text()']
#
#         if topic and topic[0] == assessment.Topic:
#             kw['assessment_node'] = an
#
#             break

# def setup_mapper_classes():
#     res = {}
#
#     for k, v in a8_utils.DB_MAPPER_CLASSES.items():
#         res[k.split('_', 1)[1]] = v
#
#     return res
#
#
# # TODO: this needs check for all classes
# MAPPER_CLASSES = setup_mapper_classes()


# def parse_ges_terms():
#     csv_f = resource_filename('wise.msfd',
#                               'data/ges_terms.tsv')
#
#     with open(csv_f, 'rb') as csvfile:
#         csv_file = csv.reader(csvfile, delimiter='\t')
#         rows = list(csv_file)
#
#     rows = rows[1:]     # skip header
#     res = []
#
#     for row in rows:
#         if len(row) != 4:
#             continue
#         bits = [b.strip() for b in row]
#
#         b1, b2, b3, b4 = bits
#
#         id_2012 = None
#         title_2012 = None
#         id_2018 = None
#         title_2018 = None
#
#         if b1.startswith('D'):
#             # new style criterions. Ex:
#             # D6C5	D6C5 Benthic habitat condition	38	6.2.3 Proportion of ...
#             id_2018 = b1
#             title_2018 = b2.split(' ', 1)[1]
#
#             if b4[0].isdigit():
#                 # we also have the old criterion
#                 id_2012 = b4.split(' ', 1)[0]
#                 title_2012 = b4.split(' ', 1)[1]
#             else:
#                 # add it as GESOther if b4 is '-'
#                 id_2012 = 'GESOther'
#                 title_2012 = b4
#
#             # if the criterion has already been defined, annotate that one
#
#             seen = False
#
#             for crit in res:
#                 if id_2018 and (crit.id == id_2018):
#                     # already seen this criterion, let's append the title
#                     seen = True
#                     crit.alternatives.append((id_2012, title_2012))
#
#             if not seen:
#                 crit = Criterion(id_2018, title_2018)
#
#                 if id_2012:
#                     crit.alternatives.append((id_2012, title_2012))
#
#                 res.append(crit)
#
#             continue
#
#         if b1[0].isdigit():
#             # old style criterions. Ex:
#             # 5.3	5.3 Indirect effects of nutrient enrichment	52	Y
#             id_2012 = b1
#             title_2012 = b2.split(' ', 1)[1]
#
#             crit = Criterion(None, None)
#             crit.alternatives.append((id_2012, title_2012))
#             res.append(crit)
#
#     return res

# from compliance/nationaldescriptors/utils.py
# @db.use_db_session('2018')
# def get_descriptors():
#     """ Get a list of (code, description) descriptors
#     """

    # mc = sql2018.LGESComponent
    # count, res = db.get_all_records(
    #     mc,
    #     mc.GESComponent == 'Descriptor'
    # )
    # descriptors = [(x.Code.split('/')[0], x.Description) for x in res]

    # d = get_all_descriptors()
    # res = {}

    # for k, v in d.items():
    #     res[v.id] = v.title

    # import pdb; pdb.set_trace()

    # return res

# from compliance/nationaldescriptors/a8_new/Article8
    # @db.use_db_session('2018')
    # def descriptor_criterion(self):
        # mc = sql2018.LGESComponent
        # count, res = db.get_all_records(
        #     mc,
        #     mc.GESComponent == 'Descriptor',
        #     raw=True,
        # )
        # descriptors = [(x.Code.split('/')[0], x.Description) for x in res]
        # descriptors = dict(descriptors)
        # descriptor = get_descriptor(self.descriptor)
        # import pdb; pdb.set_trace()

        # return Descriptor(self.descriptor, descriptor.value())
        # return Descriptor(self.descriptor, descriptors[self.descriptor])

        # def make_distinct(col_name, col_data):
        #     """ Features come as a list of comma separated values, with
        #     duplicated values among them. We make those values distinct
        #     """
        #
        #     if col_name not in ('Features', ):
        #         return col_data
        #
        #     if not col_data:
        #         return ''
        #
        #     splitted = col_data.split(',')
        #     distinct = ', '.join(sorted(set(splitted)))
        #
        #     return distinct
# @db.use_db_session('2012')
# def get_criterion_labels(criterions, descriptor, descriptor_label):
#     """ Get all labels for the criterions
#
#     :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#     :return: [('5.1', '5.1: Nutrients levels'),
#               ('5.1.2', '5.1.2: Nutrient ratios (silica'),
#               (...)]
#     """
#
#     count, res = db.get_all_records(
#         sql.MSFD11CommonLabel,
#         sql.MSFD11CommonLabel.value.in_(criterions),
#         sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
#                                          'list-GESCriteria')),
#     )
#
#     criterion_labels = dict([(x.value, x.Text) for x in res])
#     # add D5 criterion to the criterion lists too
#     criterion_labels[descriptor] = descriptor_label
#
#     return criterion_labels
#
#
# @db.use_db_session('2012')
# def get_all_criterions(descriptor):
#     """ Get all criterions(indicators) + descriptor, for a descriptor
#
#     :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#     """
#     nr = descriptor[1:]
#     m = sql.MSFDFeaturesOverview
#     res = db.get_unique_from_mapper(
#         m,
#         'RFCode',
#         or_(
#             and_(m.RFCode.like('{}.%'.format(nr)),
#                  m.FeatureType == 'GES criterion',),
#             and_(m.RFCode.like('{}'.format(descriptor)),
#                  m.FeatureType == 'GES descriptor')
#         ),
#         m.FeatureRelevant == 'Y',
#         m.FeatureReported == 'Y',
#     )
#
#     return res
#
#
#
#
# @db.use_db_session('2012')
# def get_indicators_with_feature_pressures(muids, criterions):
#     """ Get a dict with all indicators and their corresponding features
#
#     :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
#     :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
#     :return: {'5.2.2-indicator 5.2C': ['Transparency', 'InputN_Psubst'],
#              {'5.2.1- indicator 5.2B': ['InputN_Psubst',
#                                         'FunctionalGroupOther'],
#               ...}
#     """
#
#     t = sql.t_MSFD9_Features
#     count, res = db.get_all_records(
#         t,
#         t.c.MarineUnitID.in_(muids),
#     )
#     res = [row_to_dict(t, r) for r in res]
#
#     indicators = defaultdict(set)
#
#     for row in res:
#         rf = row['ReportingFeature']
#         indicators[rf].add(row['FeaturesPressuresImpacts'])
#
#     res = {}
#
#     for k, v in indicators.items():
#         flag = False
#
#         for crit in criterions:
#             if k.startswith(crit):
#                 flag = True
#
#         if flag:
#             res[k] = v
#
#     return res
#
#
# @db.use_db_session('2012')
# def get_indicator_descriptors(muids, available_indicators):
#     """ Get data based on Marine Units and available indicators
#
#     :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
#     :param available_indicators: ['5.2.2-indicator 5.2C',
#                                   '5.2.1- indicator 5.2B']
#     :return: table result
#     """
#     # TODO: sort the results based on ascending muid?
#     count, res = db.get_all_records(
#         sql.MSFD9Descriptor,
#         sql.MSFD9Descriptor.MarineUnitID.in_(muids),
#         sql.MSFD9Descriptor.ReportingFeature.in_(available_indicators)
#     )
#
#     return res
<div tal:repeat="muid view/muids" class="report-section">
  <h4 tal:content="muid">DE_ANS</h4>
  <div class="overflow-table">
    <table class="table table-bordered table-striped table-report"
      tal:define="topic_assessment python: view.get_topic_assessment(muid)">
      <span tal:condition="python: not topic_assessment">Data not reported</span>
      <tal:block tal:define="criterias python: view.context.get_criterias_list(view.descriptor);
        colspan_base python:1;"
        tal:condition="topic_assessment">
        <!-- art8assesment_data python: view.get_assesment_data(muid, view.descriptor); -->

        <!-- <div style="display:block"> -->
        <!--   <h6>Article 8 topics/indicators (topic_assessment)</h6> -->
        <!--   <div tal:replace="topic_assessment"></div> -->
        <!-- </div> -->

        <!-- <tr> -->
        <!--   <th>MarineUnitID</th> -->
        <!--   <td tal:attributes="colspan python: 42" -->
        <!--     tal:content="muid">DE_ANS</td> -->
        <!-- </tr> -->

        <tr>
          <th>CriteriaType
            [GESComponent]</th>
          <tal:block tal:repeat="crit criterias">
            <td tal:attributes="colspan python: view.get_col_span_indicator(crit[0])"
              tal:content="python: crit[1]"/>
          </tal:block>
        </tr>

        <tr tal:define="col_name string:Topic;">
          <th>Analysis</th>
          <tal:block tal:repeat="crit criterias">
            <tal:block tal:repeat="print_val python:
              view.print_feature(crit[0], col_name, 0)">
              <td tal:content="print_val"/>
            </tal:block>
          </tal:block>
        </tr>

        <tr>
          <th>[Element]</th>
          <td colspan="42">Row not implemented</td>
        </tr>


        <tr>
          <th>[Parameter]</th>
          <td colspan="42">Row not implemented</td>
        </tr>

        <tal:block tal:define="topic_group_index python:0;">
          <tr tal:define="col_name string:ThresholdValue;">
            <th>Threshold Value</th>
            <metal:row define-macro="print_asses_ind">
              <tal:block tal:repeat="crit criterias">
                <tal:block tal:repeat="print_val python:
                  view.print_asses_ind(crit[0], col_name, topic_group_index)">
                  <td tal:content="print_val"/>
                </tal:block>
              </tal:block>
            </metal:row>
          </tr>

          <tr tal:define="col_name string:SumInfo1">
            <th>SumInfo1
              [ValueAchieved]</th>
            <td colspan="42">Row not implemented</td>
          </tr>

          <tr tal:define="col_name string:ThresholdValueUnit;">
            <th>SumInfo1Unit/
              ThresholdValueUnit [ValueUnit]</th>
            <metal:macro use-macro="template/macros/print_asses_ind"/>
          </tr>

          <tr>
            <th>[ProportionThresholdValue]</th>
            <td colspan="42">Row not implemented</td>
          </tr>

          <tr tal:define="col_name string:SumInfo1">
            <th>PressureLevelN/P/
              Oconcentration/
              ImpactsPressureWater/
              Seabed: SumInfo1
              [ProportionValueAchieved]</th>
            <metal:row define-macro="print_base">
              <tal:block tal:repeat="crit criterias">
                <tal:block tal:repeat="print_val python:
                  view.print_base(crit[0], col_name, topic_group_index)">
                  <td tal:attributes="colspan python: colspan_base if print_val else 1"
                    tal:content="print_val"/>
                </tal:block>
              </tal:block>
            </metal:row>
          </tr>

          <!-- TODO not sure which column to show here-->
          <!-- SumInfo1Confidence, StatusConfidence -->
          <tr tal:define="col_name string:SumInfo1Confidence;">
            <th>PressureLevelN/P/
              OConcentration/
              ImpactsPressureWater/
              Seabed: SumInfo1Confidence</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:TrendsRecent;">
            <th>PressureLevelN/P/
              OConcentration/
              ImpactsPressureWater/
              Seabed: TrendRecent</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:TrendsFuture;">
            <th>PressureLevelN/P/
              OConcentration/
              ImpactsPressureWater/
              Seabed: TrendFuture</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:Description;">
            <th>PressureLevelN/P/
              Oconcentration/
              ImpactsPressureWater/
              Seabed: Description
              [Parameter]</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo2">
            <th>ImpactsPressureWater/
              Seabed: SumInfo2</th>
            <!--<td colspan="42">Row not implemented</td>-->
            <tal:block tal:repeat="crit criterias">
              <tal:block tal:repeat="print_val python:
                view.print_suminfo2(crit[0], topic_group_index)">
                <td tal:content="print_val"/>
              </tal:block>
            </tal:block>
          </tr>

          <tr tal:define="col_name string:GESIndicators;">
            <th>Indicator
              [RelatedIndicator]</th>
            <metal:macro use-macro="template/macros/print_asses_ind"/>
          </tr>

          <tr tal:define="col_name string:Status;">
            <th>Status
              [CriteriaStatus]</th>
            <metal:row define-macro="print_asses">
              <tal:block tal:repeat="crit criterias">
                <tal:block tal:repeat="print_val python:
                  view.print_asses(crit[0], col_name, topic_group_index)">
                  <td tal:content="print_val"/>
                </tal:block>
              </tal:block>
            </metal:row>
          </tr>

          <tr tal:define="col_name string:StatusTrend;">
            <th>StatusTrend</th>
            <metal:macro use-macro="template/macros/print_asses"/>
          </tr>

          <!-- TODO not sure which column to show here-->
          <!-- SumInfo1Confidence, StatusConfidence -->
          <tr tal:define="col_name string:StatusConfidence;">
            <th>StatusConfidence</th>
            <metal:macro use-macro="template/macros/print_asses"/>
          </tr>

          <tr tal:define="col_name string:StatusDescription;">
            <th>StatusDescription
              [DescriptionCriteria]</th>
            <metal:macro use-macro="template/macros/print_asses"/>
          </tr>

          <tr tal:define="col_name string:Limitations;">
            <th>Limitations
              (DescriptionElement)</th>
            <metal:macro use-macro="template/macros/print_asses"/>
          </tr>

          <tr tal:define="col_name_start string:RecentTimeStart;
            col_name_end string:RecentTimeEnd">
            <th>RecentTimeStart/
              RecentTimeEnd/
              AssessmentDateStart/
              AssessmentDateEnd
              [AssessmentPeriod</th>
            <td colspan="42"
              tal:define="print_val python: view.metadata_data"
              tal:content="python: print_val[0] if print_val else ''">Row not implemented</td>
          </tr>
        </tal:block>


        <tal:block tal:define="topic_group_index python:1;
          colspan_base python: sum((len(topic_assessment['LevelPressureNConcentration']),
          len(topic_assessment['LevelPressurePConcentration']),
          len(topic_assessment['LevelPressureOConcentration'])));">
          <tr tal:define="col_name string:Description;">
            <th>LevelPressureOverall:
              Description</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo1;">
            <th>LevelPressureOverall:
              SumInfo1
              [proportion of area subject
              to nutrient enrichment]</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo1Confidence;">
            <th>LevelPressureOverall:
              SumInfo1Confidence</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>
        </tal:block>


        <tal:block tal:define="topic_group_index python:2;">
          <tr tal:define="col_name string:Description;">
            <th>LevelPressureN/P/OLoad:
              Desciption</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo1;">
            <th>LevelPressureN/P/
              OLoad: SumInfo1
              [input load of nitrogen/
              phosphorus/organic matter]</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo1Unit;">
            <th>LevelPressureN/P/
              OLoad: SumInfo1Unit</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:SumInfo1Confidence;">
            <th>LevelPressureN/P/
              OLoad: SumInfo1Confidence</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:TrendsRecent;">
            <th>LevelPressureN/P/
              OLoad: TrendsRecent</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>

          <tr tal:define="col_name string:TrendsFuture;">
            <th>LevelPressureN/P/
              OLoad: TrendFuture</th>
            <metal:macro use-macro="template/macros/print_base"/>
          </tr>
        </tal:block>

        <tr tal:define="col_name string:Description;">
          <th>Activities:
            Description</th>
          <td tal:attributes="colspan python:42"
            tal:define="print_val python: view.activ_descr_data"
            tal:content="python: print_val[0].Description if print_val else ''">Row not implemented</td>
        </tr>

        <tr tal:define="col_name string:ActivityType;">
          <th>ActivityType</th>
          <td tal:attributes="colspan python:42"
            tal:content="python: view.activ_data">Row not implemented</td>
        </tr>

        <tr tal:define="col_name string:InfoGaps;">
          <th>InfoGaps</th>
          <td tal:attributes="colspan python:42"
            tal:define="print_val python:[
            row.Description

            for row in view.base_data

            if row.Topic == 'InfoGaps'];"
            tal:content="python: print_val[0] if print_val else ''">Row not implemented</td>
        </tr>

      </tal:block>
    </table>
  </div>
</div>




class Article8(BaseArticle2012):
    template = Template('pt/report-data-a8.pt')

    def get_suminfo2_data(self, marine_unit_id, descriptor):
        """ Get all data from table _SumInfo2ImpactedElement
        for specific Marine Units and descriptor

        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: {u'ImpactPressureSeabedHabitats':
                     [u'ShallRock', u'ShallSand'],
                  u'ImpactPressureWaterColumn':
                     [u'NutrientLevels', u'Transparency']}
        """

        results = defaultdict(list)
        tables = DESC_DATA_MAPPING[descriptor]

        for table in tables:
            tbl_name = '{}SumInfo2ImpactedElement'.format(table.replace('_',
                                                                        ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )

            for row in res:
                topic = row.ImpactType
                sum_info2 = row.SumInfo2
                results[topic].append(sum_info2)

        return results

    def get_metadata_data(self, marine_unit_id, descriptor):
        """ Get all data from table _Metadata
        for specific Marine Units and descriptor

        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: list [u'1973 - 2008', ...]
        """

        results = []

        tables = DESC_DATA_MAPPING[descriptor]

        for table in tables:
            tbl_name = 't_{}Metadata'.format(table)
            mc_assessment = getattr(sql, tbl_name, None)

            if mc_assessment is None:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.c.MarineUnitID == marine_unit_id
            )

            for row in res:
                start = row[2]
                end = row[3]

                if row[1].startswith('Assessment') and start and end:
                    val = ' - '.join((start, end))
                    results.extend([val])

                    break

        return results

    def get_activity_descr_data(self, marine_unit_id, descriptor):
        """ Get all data from table _ActivityDescription
        for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}ActivityDescription'.format(table.replace("_", ""))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_activity_data(self, descriptor):
        """ Get all data from table _Activity for specific descriptor
        :param descriptor: 'D5'
        :return: list [u'AgricultForestry; Urban']
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}Activity'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            d = self.activ_descr_data
            col = '{}_ActivityDescription_ID'.format(table)
            # _id_act_descr = getattr(d[0], col, 0) if d else 0
            _id_act_descr = [getattr(x, col, 0) for x in d]

            col_ad = '{}_ActivityDescription'.format(table)
            count, res = db.get_all_records(
                mc_assessment,
                getattr(mc_assessment, col_ad).in_(_id_act_descr)
            )
            res = [x.Activity for x in res if x.Activity != 'NotReported']
            results.extend(res)

        results = '; '.join(sorted(set(results)))

        return results

    def get_assesment_ind_data(self, marine_unit_id, descriptor):
        """ Get all data from table _AssesmentIndicator
        for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}AssesmentIndicator'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_assesment_data(self, marine_unit_id, descriptor):
        """ Get all data from table _Assesment
        for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}Assesment'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_base_data(self, marine_unit_id, descriptor):
        """ Get all data from base table
        for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            mapper_class = DB_MAPPER_CLASSES.get(table, None)

            if not mapper_class:
                continue

            count, res = db.get_all_records(
                mapper_class,
                mapper_class.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_topic_assessment(self, marine_unit_id):
        """ Get dict with topics(analisys/features) and the GESComponents

        :param marine_unit_id: 'LV-001'
        :return: {'LevelPressureOLoad': ['5.1.1'],
            u'ImpactPressureWaterColumn': [u'5.2.1', u'5.2.1', u'5.2.2'],
            ...}
        """
        self.descriptor = self.descriptor.split('.')[0]

        self.base_data = self.get_base_data(marine_unit_id,
                                            self.descriptor)

        self.asses_data = self.get_assesment_data(marine_unit_id,
                                                  self.descriptor)

        self.asses_ind_data = self.get_assesment_ind_data(
            marine_unit_id, self.descriptor)

        self.activ_descr_data = self.get_activity_descr_data(
            marine_unit_id, self.descriptor)

        self.activ_data = self.get_activity_data(self.descriptor)

        self.metadata_data = self.get_metadata_data(marine_unit_id,
                                                    self.descriptor)

        self.suminfo2_data = self.get_suminfo2_data(marine_unit_id,
                                                    self.descriptor)

        topic_assesment = defaultdict(list)

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )
        topic_ind = DESCR_TOPIC_UTILS['topic_indicators'].get(self.descriptor,
                                                              {})

        for row in self.base_data:
            base_topic = getattr(row, 'Topic', None)
            asses_topic = topic_atn.get(base_topic, 'NOT FOUND')

            # if not asses_topic:
            #     continue
            topic_assesment[base_topic] = []

            indicators = [
                x.GESIndicators

                for x in self.asses_ind_data

                if x.Topic == asses_topic
            ]

            if not indicators:
                indic = topic_ind.get(base_topic, 'INDICATOR EMPTY')
                indicators = (indic, )

            topic_assesment[base_topic].extend(indicators)

        self.topic_assesment = topic_assesment

        return topic_assesment

    def get_col_span_indicator(self, indicator):
        """ Get colspan based on the count of indicators
        :param indicator: '5.2.1'
        :return: integer
        """

        colspan = 0
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])
        topics_needed = self.topic_assesment.keys()

        if topic_groups:
            topics_needed = topic_groups[0]

        for topic, indics in self.topic_assesment.items():
            count = indics.count(indicator)

            if topic in topics_needed:
                colspan += count

        if not colspan:
            colspan = 1

        return colspan

    def print_feature(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        results = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])
        topics_needed = self.topic_assesment.keys()

        if topic_groups:
            topics_needed = topic_groups[topic_group_index]

        for row in self.base_data:
            topic = row.Topic

            if topic in topics_needed:
                nr = self.topic_assesment[topic].count(indicator)

                for i in range(nr):
                    results.append(getattr(row, col_name))

        if not results:
            return ['']

        return results

    def print_asses_ind(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )

        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = topic_atn.get(topic)

            res = []

            for row_asess in self.asses_ind_data:
                if row_asess.Topic == asses_topic and \
                        row_asess.GESIndicators == indicator:
                    res.append(getattr(row_asess, col_name))

            if not res:
                results.append('')
            else:
                results.extend(res)

        if not results:
            return ['']

        return results

    def print_base(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            print_val = getattr(row, col_name)
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def print_asses(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )

        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = topic_atn.get(topic)

            print_val = [
                getattr(row, col_name)

                for row in self.asses_data

                if row.Topic == asses_topic
            ]
            print_val = print_val[0] if print_val else ''
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def print_suminfo2(self, indicator, topic_group_index):
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            print_val = ', '.join(self.suminfo2_data[topic])
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def __call__(self):
        template = self.template
        self.content = template and template() or ""

        return self.content


    COMMON_LABELS.update(csv_labels)
    COMMON_LABELS.update(xsd_labels)

    common_labels = len(list(csv_labels.keys()) +
                        list(xsd_labels.keys())) - len(COMMON_LABELS)

    csv_nr = len(list(csv_labels.keys()))
    xsd_nr = len(list(xsd_labels.keys()))

    print("""Labels count:
    Total labels: %s
    Common_labels: %s
    .csv_nr: %s
    .xsd_nr: %s""" % (len(COMMON_LABELS), common_labels, csv_nr, xsd_nr))

    return





  var autoTranslation = function(e) {
    e.preventDefault();

    var text = $(this).parents('td.translatable').find('.tr.text').text();
    var target_languages = ['EN'];
    // var source_lang = 'EN';

    $.ajax({
      type: "POST",
      url: "./@@translate-text",
      dataType: 'json',
      data: {
        "text-to-translate": text,
        "targetLanguages": target_languages,
        // "sourceLanguage": source_lang,
        "externalReference": text, // set by us, used as identifier
        "sourceObject": window.location.href,
      },
      success: function(result) {
        $.ajax({
          type: "POST",
          url: "./@@translate-text",
          tryCount : 0,
          retryLimit : 20,
          data: {
            "from_annot": result.externalRefId,
          },
          success: function(translation) {
            if (translation) {
              location.reload();
            }
            else {
              this.tryCount++;

              if (this.tryCount <= this.retryLimit) {
                //try again
                $.ajax(this);
                return;
              }
              return;
            }
          },
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout') {
              this.tryCount++;

              if (this.tryCount <= this.retryLimit) {
                //try again
                $.ajax(this);
                return;
              }
              return;
            }

            if (xhr.status == 500) {
              //handle error
            } else {
              //handle error
            }
          }});
      },
      error: function(result) {
        alert('error');
      }
    });
  };


  var editTranslation = function(e) {
    //e.preventDefault();
    var $cell = $(this).parents('td.translatable');

    var $text_div = $('.tr-text', $cell);
    var old_translation = $('.transl', $text_div).text();
    var orig_text = $('.text', $text_div).text();

    $original.text(orig_text);
    $old.text(old_translation);

    $('#form-edit-translation #new_transl').html(old_translation);

  };

  var submitTranslation = function(e) {
    e.preventDefault();

    var orig_text = $original.text();
    var $form = $('#form-edit-translation');
    var translation = $("#new_transl", form).html();

    $.ajax({
      form: $form,
      type: 'POST',
      url: './translate-callback',
      dataType: 'json',
      data: {
        'external-reference': orig_text,
        'translation': translation
      },
      success: function(result) {
        location.reload();
      },
      error: function(result) {
        alert('ERROR saving translation!');
      }
    });
  };
    // $(".autoTransl").on("click", autoTranslation);
    // $('.editTransl').on("click", editTranslation);
    // $('.submitTransl').on("click", submitTranslation);

//
// var queue = [];
// $('.subform .right .comments').each(function(){
//   queue.push(this);
// });
//
// function processQueue() {
// }
// setTimeout(processQueue, 1000);
def parse_ges_components():
    # Node: this method is not used, it doesn't offer a way to map old
    # criterias to new criterias
    # {
    #   "code": "1.1.3",
    #   "label": "(Indicator(old)) Area covered by the species (for
    #   sessile/benthic species)",
    #   "descriptor": "D1"
    # },
    gcomps = TERMSLIST['GESComponents']

    # {
    #   "code": "5.2",
    #   "label": "(Criteria(old)) Direct effects of nutrient enrichment",
    #   "descriptor": "D5"
    # },
    gcrits = TERMSLIST['GESCriterias']

    # {
    #   "code": "D1.1",
    #   "label": "(Descriptor) D1 - Biodiversity - birds"
    # },
    gdescs = TERMSLIST['GESDescriptors']

    descriptors = {d['label']: Descriptor(d['code'], d['label'])
                   for d in gdescs}
    descriptors['D1'] = Descriptor('D1', 'D1 - Biodiversity')
    criterions = {}

    for c in (gcomps + gcrits):
        if c['code'] not in criterions:
            c = Criterion(c['code'], c['label'], [])
            descriptors[c['descriptor']].criterions.add(c)
            criterions[c['code']] = c
        else:
            c = criterions[c['code']]
            descriptors[c['descriptor']].criterions.add(c)

    return descriptors, criterions


    # @property
    # def criterias(self):
    #     return self.descriptor_obj.criterions

    # TODO: use memoize
        # els = get_descriptor_elements(
        #     'compliance/nationaldescriptors/data'
        # )
        #
        # desc = self.descriptor.split('.')[0]
        #
        # return els[desc]


# def parse_features():
#     res = {}
#
#     FEATURES = TERMSLIST['ReferenceFeature']        # FeaturesSmart
#
#     for fr in FEATURES:
#         feature = fr['Feature']
#
#         if feature in res:
#             continue
#
#         descs = set([f['GEScomponent']
#                      .replace('D6/D1', 'D6').replace('D4/D1', 'D4')
#
#                      for f in FEATURES
#
#                      if f['Feature'] == feature])
#
#         res[feature] = Feature(feature, descs)
#
#     return res
            # Klass = self.implementations[descriptor][0]

            # count, res = db.get_all_records(
            #     Impl.mapper,
            #     Impl.mapper.MarineUnitID.in_(self.muids)
            # )

                # if fieldname not in group_by_fields:
                #     continue

                # # TODO: this needs to be refactored into a function, to allow
                # # easier understanding of code
                #
                # # rewrite some rows with list of all possible values
                # all_values = [
                #     getattr(x, fieldname)
                #
                #     for x in data
                #
                #     if (x.MarineReportingUnit == mru) and
                #     (getattr(x, fieldname) is not None)
                # ]
                # seen = []
                # uniques = []
                #
                # # if the values are unicode
                #
                # if isinstance(all_values[0], (unicode, str)):
                #     row[1] = [', '.join(set(all_values))] * len(row_data)
                #
                #     continue
                #
                # # if the values are ItemList types, make the values unique
                #
                # for item in all_values:
                #     item_label_class = item.rows[0]
                #     name = item_label_class.name
                #
                #     if name in seen:
                #         continue
                #
                #     seen.append(name)
                #     uniques.append(item_label_class)
                #
                # row[1] = [ItemList(rows=uniques)] * len(row_data)

            # TODO: this needs to be redone to take advantage of smart
            # self.muids
            # mru_label = GES_LABELS.get('mrus', mru)
            #
            # if mru_label != mru:
            #     mru_label = u"{} ({})".format(mru_label, unicode(mru))
            #
def consolidate_data(data, group_by_fields):
    """ Reduce number of rows in data, by omitting rows with identical values

    The problem is that the view query is a union, where the rows are repeated
    multiple times, ones for each combination of TargetCode or PressureCode.
    We filter them by only including those rows that haven't been seen
    """

    if not data:
        return {}

    res = defaultdict(list)

    # Ignore the following fields when hashing the rows

    fieldnames = data[0]._fields
    ignored_idx = [fieldnames.index(f) for f in group_by_fields]
    # ignored_idx = []

    seen = []

    for row in data:
        # omitting the ignored fields, make a hash to identify duplicate rows

        hash = tuple([v
                      for (i, v) in enumerate(row)

                      if i not in ignored_idx])

        if hash in seen:
            continue

        seen.append(hash)

        if not row.MarineReportingUnit:     # skip rows without muid
            continue

        res[row.MarineReportingUnit].append(row)

    return res


    # def get_group_by_fields(self):
    #     res = [
    #         x.get('name')
    #
    #         for x in self.nodes
    #
    #         if x.attrib.get('exclude', 'false') == 'true'
    #     ]
    #
    #     return res


# def get_sorted_fields(year, article, fields):
#     """ Sorts a list of fields according to report definition for given year
#     """
#
#     repdef = REPORT_DEFS[year][article]
#
#     return _resort_fields(repdef, fields)
#
#
# def get_field_definitions_from_data(data, article):
#     _fields, fields_defs = None, None
#
#     for dataset in data.values():
#         if _fields:
#             break
#
#         for row in dataset:
#             if row._fields is not None:
#                 _fields = row._fields
#                 fields_defs = get_sorted_fields('2018', article, _fields)
#
#     return fields_defs

        # sess = db.session()
        # T = sql.MSFD10Target
        # dt = sql.t_MSFD10_DESCrit
        #
        # D_q = sess.query(dt).join(T)
        # D_a = aliased(dt, alias=D_q.subquery())
        #
        # targets = sess\
        #     .query(T)\
        #     .order_by(T.ReportingFeature)\
        #     .filter(T.MarineUnitID.in_(muids))\
        #     .filter(T.Topic == 'EnvironmentalTarget')\
        #     .join(D_a)\
        #     .filter(D_a.c.GESDescriptorsCriteriaIndicators.in_(ok_ges_ids))\
        #     .distinct()\
        #     .all()
        # print 'Resulting targets: ', len(targets)
        #
        # # TODO: also get 2012 targets here
        #
        # return [Target(r.ReportingFeature.replace(' ', '_').lower(),
        #                r.ReportingFeature,
        #                r.Description) for r in targets]


# def target_code_to_description(node, value):
#     """
#     """
#
#     # TODO: this doesn't work properly, to fix
#     title = GES_LABELS.get('targets', value)
#
#     return ItemLabel(title, value)
    // // stretch all cells to the maximum table columns;
    // var max = 0;
    // var $tr = $('tr.merge', this);
    // $tr.each(function(){
    //   $tds = $('td', this);
    //   if ($tds.length > max) {
    //     max = $tds.length;
    //   }
    // });
    //
    // $tr.each(function(){
    //   $tds = $('td', this);
    //   if ($tds.length) {
    //     var td = $tds[$tds.length - 1];
    //     $(td).attr('colspan', max - $tds.length + 1);
    //   }
    // });
    //
