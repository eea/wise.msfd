# class IAssessmentTopic(Interface):
#     """
#     """
#     assessment_topic = Choice(
#         title=u"Assessment topic",
#         vocabulary=vocab_from_values(ASSESSMENT_TOPICS),
#         required=False,
#     )


# class AssessmentTopicForm(EmbededForm):
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
# class ArticleForm(EmbededForm):
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
# class ReportingDeadlineForm(EmbededForm):
#     """
#     """
#
#     fields = Fields(IReportingDeadline)
#
#     def get_subform(self):
#         return AssessmentDisplayForm(self, self.request)



# class AssessmentDisplayForm(EmbededForm):
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
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.content.search import db, interfaces, sql2018
from z3c.form.browser.text import TextFieldWidget, TextWidget
from z3c.form.browser.textarea import TextAreaWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields

from .base import EmbededForm, ItemDisplayForm


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


class ComplianceModule(EmbededForm):
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


class ComplianceAssessment(EmbededForm):
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
# class ReportForm2018(EmbededForm):
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
