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
# from ..base import BaseEnhancedForm, EmbededForm
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


class SummaryAssessmentDataForm2018(EmbededForm):
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
# class GESDescriptorForm(EmbededForm):
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
# class ArticleForm(EmbededForm):
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
# class MarineUnitIDsForm(EmbededForm):
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
# class BasicAssessmentDataForm2018(EmbededForm):
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
