# coding=utf-8
import logging
import os
import requests

from collections import namedtuple
from datetime import datetime
from io import BytesIO
from lxml import etree
from persistent.list import PersistentList

from AccessControl import Unauthorized
from zope.interface import alsoProvides

import xlsxwriter
from eea.cache import cache
from plone import api
from plone.api import portal
from plone.api.content import get_state, transition
from plone.api.portal import get_tool
from plone.dexterity.utils import createContentInContainer as create
from plone.namedfile.file import NamedBlobImage
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.compliance.assessment import (ARTICLE_WEIGHTS,
                                             AssessmentDataMixin,
                                             OverallScores)
from wise.msfd.compliance.interfaces import (INationalDescriptorAssessment,
                                             INationalDescriptorAssessmentSecondary)
from wise.msfd.compliance.vocabulary import (get_all_countries,
                                             get_regions_for_country,
                                             REGIONAL_DESCRIPTORS_REGIONS,
                                             REPORTING_HISTORY_ENV)
from wise.msfd.compliance.regionaldescriptors.base import COUNTRY
from wise.msfd.gescomponents import (get_all_descriptors, get_descriptor,
                                     get_marine_units)
from wise.msfd.labels import get_indicator_labels
from wise.msfd.translation import Translation, get_detected_lang
from wise.msfd.translation.interfaces import ITranslationsStorage
from wise.msfd.utils import get_annot, timeit

from . import interfaces
from .base import (_get_secondary_articles, BaseComplianceView,
                   NAT_DESC_QUESTIONS, REG_DESC_QUESTIONS,
                   report_data_cache_key)

logger = logging.getLogger('wise.msfd')

ANNOT_XLSDATA = 'wise.msfd.xlsdata'
EXPORTPASS = os.environ.get('XMLEXPORTPASS', None)

CONTRIBUTOR_GROUP_ID = 'extranet-wisemarine-msfd-tl'
REVIEWER_GROUP_ID = 'extranet-wisemarine-msfd-reviewers'
EDITOR_GROUP_ID = 'extranet-wisemarine-msfd-editors'

CONCLUSIONS = {
    '/': 'Not relevant',
    '1': 'Very good',
    '0.75': 'Good',
    '0.5': 'Poor',
    '0.25': 'Very poor',
    '0.250': 'Not clear',
    '0': 'Not reported',
}


def get_wf_state_id(context):
    state = get_state(context)
    wftool = get_tool('portal_workflow')
    wf = wftool.getWorkflowsFor(context)[0]  # assumes one wf
    wf_state = wf.states[state]
    wf_state_id = wf_state.id or state

    return wf_state_id


class ToPDB(BrowserView):
    def __call__(self):
        import pdb
        pdb.set_trace()

        return 'ok'


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
    """

    compliance_folder_id = 'assessment-module'

    @property
    def debug(self):
        return 'production' not in self.request.form

    def _get_countries(self):
        """ Get a list of (code, name) countries
        """

        countries = get_all_countries()

        if self.debug:
            countries = [x for x in countries if x[0] in ('LV', 'NL', 'DE')]

        return countries

    @db.use_db_session('2018')
    def _get_countries_names(self, country_codes):
        result = []
        all_countries = self._get_countries()

        for code in country_codes:
            result.extend([x for x in all_countries if x[0] == code])

        return result

    def _get_descriptors(self):
        """ Get a list of (code, description) descriptors
        """

        descriptors = get_all_descriptors()
        descriptors = [d for d in descriptors if d[0] != 'D1']

        debug_descriptors = ('D1.1', 'D4', 'D5', 'D6')

        if self.debug:
            descriptors = [x for x in descriptors if x[0] in debug_descriptors]

        return descriptors

    @db.use_db_session('2018')
    def _get_articles(self):
        # articles = db.get_unique_from_mapper(
        #     sql2018.LMSFDArticle,
        #     'MSFDArticle'
        # )
        # return articles

        return ['Art8', 'Art9', 'Art10']

    def set_layout(self, obj, name):
        ISelectableBrowserDefault(obj).setLayout(name)

    def set_policy(self, context, name):
        logger.info("Set placeful workflow policy for %s", context.getId())
        config = WorkflowPolicyConfig(
            workflow_policy_in='compliance_section_policy',
            workflow_policy_below='compliance_section_policy',
        )
        context._setObject(config.id, config)

    @db.use_db_session('2018')
    def get_country_regions(self, country_code):
        regions = get_regions_for_country(country_code)

        return regions

    def get_group(self, code):
        if '.' in code:
            code = 'd1'
        code = code.lower()

        return "{}-{}".format(CONTRIBUTOR_GROUP_ID, code)

    def create_comments_folder(self, content):
        for id, title, trans in [
            (u'tl', 'Discussion track with Topic Leads', 'open_for_tl'),
            (u'ec', 'Discussion track with EC', 'open_for_ec'),
        ]:
            if id not in content.contentIds():
                dt = create(content,
                            'wise.msfd.commentsfolder',
                            id=id,
                            title=title)
                transition(obj=dt, transition=trans)

    def create_nda_folder(self, df, desc_code, art):
        if art.lower() in df.contentIds():
            nda = df[art.lower()]
        else:
            nda = create(df,
                         'wise.msfd.nationaldescriptorassessment',
                         title=art)
            lr = nda.__ac_local_roles__

            group = self.get_group(desc_code)

            lr[group] = ['Contributor']

            logger.info("Created NationalDescriptorAssessment %s",
                        nda.absolute_url())

            self.set_layout(nda, '@@nat-desc-art-view')

        self.create_comments_folder(nda)

    def create_rda_folder(self, df, desc_code, art):
        if art.lower() in df.contentIds():
            rda = df[art.lower()]
        else:
            rda = create(df,
                         'wise.msfd.regionaldescriptorassessment',
                         title=art)

            lr = rda.__ac_local_roles__
            group = self.get_group(desc_code)
            lr[group] = ['Contributor']

            logger.info("Created RegionalDescriptorArticle %s",
                        rda.absolute_url())

            self.set_layout(rda, '@@reg-desc-art-view')
            alsoProvides(rda, interfaces.IRegionalDescriptorAssessment)

        self.create_comments_folder(rda)

    def make_country(self, parent, country_code, name):

        if country_code.lower() in parent.contentIds():
            cf = parent[country_code.lower()]
        else:
            cf = create(parent,
                        'wise.msfd.countrydescriptorsfolder',
                        title=name,
                        id=country_code)

        for regid, region in self.get_country_regions(country_code):
            if regid.lower() in cf.contentIds():
                reg = cf[regid.lower()]
            else:
                reg = create(cf,
                             'Folder',
                             title=region,
                             id=regid.lower())
                alsoProvides(reg, interfaces.INationalRegionDescriptorFolder)
                self.set_layout(reg, '@@nat-desc-reg-view')

            for desc_code, description in self._get_descriptors():
                if desc_code.lower() in reg.contentIds():
                    df = reg[desc_code.lower()]
                else:
                    df = create(reg, 'Folder', title=description, id=desc_code)
                    alsoProvides(df, interfaces.IDescriptorFolder)

                # articles 8, 9, 10
                for art in self._get_articles():
                    self.create_nda_folder(df, desc_code, art)

                # article 11
                self.create_nda_folder(df, desc_code, 'Art11')

        return cf

    def make_region(self, parent, region):
        code, name = region.code.lower(), region.title

        if code.lower() in parent.contentIds():
            rf = parent[code.lower()]
        else:
            rf = create(parent,
                        'wise.msfd.regiondescriptorsfolder',
                        title=name,
                        id=code)

            rf._subregions = region.subregions
            rf._countries_for_region = self._get_countries_names(
                region.countries
            )
            self.set_layout(rf, '@@reg-region-start')
            alsoProvides(rf, interfaces.IRegionalDescriptorRegionsFolder)

        for desc_code, description in self._get_descriptors():
            if desc_code.lower() in rf.contentIds():
                df = rf[desc_code.lower()]
            else:
                df = create(rf, 'Folder', title=description, id=desc_code)
                alsoProvides(df, interfaces.IDescriptorFolder)

            # articles 8, 9, 10
            for art in self._get_articles():
                self.create_rda_folder(df, desc_code, art)

            # article 11
            self.create_rda_folder(df, desc_code, 'Art11')

        return rf

    def setup_nationaldescriptors(self, parent):
        # National Descriptors Assessments

        if 'national-descriptors-assessments' in parent.contentIds():
            nda = parent['national-descriptors-assessments']
        else:
            nda = create(parent,
                         'Folder', title=u'National Descriptors Assessments')
            self.set_layout(nda, '@@nat-desc-start')
            alsoProvides(nda, interfaces.INationalDescriptorsFolder)

        for code, country in self._get_countries():
            self.make_country(nda, code, country)

    def setup_regionaldescriptors(self, parent):
        # Regional Descriptors Assessments

        if 'regional-descriptors-assessments' in parent.contentIds():
            rda = parent['regional-descriptors-assessments']
        else:
            rda = create(parent,
                         'Folder', title=u'Regional Descriptors Assessments')
            self.set_layout(rda, '@@reg-desc-start')
            alsoProvides(rda, interfaces.IRegionalDescriptorsFolder)

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            self.make_region(rda, region)

    def setup_nationalsummaries(self, parent):
        if 'national-summaries' in parent.contentIds():
            ns = parent['national-summaries']
        else:
            ns = create(parent,
                        'Folder', title=u'National summaries')
            self.set_layout(ns, '@@nat-summary-start')
            alsoProvides(ns, interfaces.INationalSummaryFolder)

        # Changing the content type for national-summaries is not possible
        # need this folder to be able to edit some fields
        if 'edit-summary' not in ns.contentIds():
            es = create(ns, 'wise.msfd.nationalsummaryedit',
                        title='National summary edit', id='edit-summary')
            alsoProvides(es, interfaces.INationalSummaryEdit)

        for code, country in self._get_countries():
            if code.lower() in ns.contentIds():
                cf = ns[code.lower()]
            else:
                # national_summary type used for Assessment summary/pdf export
                cf = create(ns,
                            'national_summary',
                            title=country,
                            id=code)

            self.set_layout(cf, 'assessment-summary')
            alsoProvides(cf, interfaces.INationalSummaryCountryFolder)
            # self.create_comments_folder(cf)

            # create the overview folder
            if 'overview' in cf.contentIds():
                of = cf['overview']
            else:
                of = create(cf,
                            'wise.msfd.nationalsummaryoverview',
                            title='National summary overview',
                            id='overview')

            self.set_layout(of, 'national-overview')
            alsoProvides(of, interfaces.INationalSummaryOverviewFolder)

    def setup_regionalsummaries(self, parent):
        if 'regional-summaries' in parent.contentIds():
            ns = parent['regional-summaries']
        else:
            ns = create(parent,
                        'Folder',
                        title=u'Regional summaries')
            self.set_layout(ns, 'reg-summary-start')
            alsoProvides(ns, interfaces.IRegionalSummaryFolder)

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            code, name = region.code.lower(), region.title
            if code in ns.contentIds():
                rf = ns[code]
            else:
                rf = create(ns,
                            'wise.msfd.regionalsummaryfolder',
                            title=name,
                            id=code)

                rf._subregions = region.subregions
                rf._countries_for_region = self._get_countries_names(
                    region.countries
                )

            self.set_layout(rf, 'assessment-summary')
            alsoProvides(rf, interfaces.IRegionalSummaryRegionFolder)

            # TODO setup the folder for the regional overview page
            # similar to national summaries page
            # create the overview folder
            if 'overview' in rf.contentIds():
                of = rf['overview']
            else:
                of = create(rf,
                            'wise.msfd.regionalsummaryoverview',
                            title='Regional summary overview',
                            id='overview')

            self.set_layout(of, 'regional-overview')
            alsoProvides(of, interfaces.IRegionalSummaryOverviewFolder)

    def setup_secondary_articles(self, parent):
        if 'national-descriptors-assessments' not in parent.contentIds():
            return

        nda_parent = parent['national-descriptors-assessments']
        country_ids = nda_parent.contentIds()

        for country in country_ids:
            country_folder = nda_parent[country]

            for article in _get_secondary_articles():
                if article.lower() in country_folder.contentIds():
                    nda = country_folder[article.lower()]
                else:
                    nda = create(country_folder,
                                 'wise.msfd.nationaldescriptorassessment',
                                 title=article)

                    logger.info("Created NationalDescriptorAssessment %s",
                                nda.absolute_url())

                alsoProvides(
                    nda,
                    interfaces.INationalDescriptorAssessmentSecondary
                )
                self.set_layout(nda, '@@nat-desc-art-view-secondary')

                self.create_comments_folder(nda)

    def setup_compliancefolder(self):
        if self.context.id == self.compliance_folder_id:
            return self.context

        if self.compliance_folder_id in self.context.contentIds():
            cm = self.context[self.compliance_folder_id]
        else:
            cm = create(self.context, 'Folder', title=u'Assessment Module')

            self.set_layout(cm, '@@landingpage')
            self.set_policy(cm, 'compliance_section_policy')

            alsoProvides(cm, interfaces.IComplianceModuleFolder)

            lr = cm.__ac_local_roles__
            lr[REVIEWER_GROUP_ID] = [u'Reviewer']
            lr[EDITOR_GROUP_ID] = [u'Editor']

            # Contributor: TL
            # Reviewer: EC
            # Editor: Milieu

        return cm

    def setup_msfd_reporting_history_folder(self, cm):
        msfd_id = 'msfd-reporting-history'

        if msfd_id in cm.contentIds():
            msfd = cm[msfd_id]
        else:
            msfd = create(cm, 'wise.msfd.reportinghistoryfolder',
                          title='MSFD reporting history',
                          id=msfd_id)

            logger.info("Created MSFD Reporting history folder %s",
                        msfd.absolute_url())

            msfd._msfd_reporting_history_data = REPORTING_HISTORY_ENV

        alsoProvides(msfd, interfaces.IMSFDReportingHistoryFolder)
        self.set_layout(msfd, '@@msfd-reporting-history')

        return msfd

    def __call__(self):

        # if self.compliance_folder_id in self.context.contentIds():
        #     self.context.manage_delObjects([self.compliance_folder_id])

        cm = self.setup_compliancefolder()

        self.setup_msfd_reporting_history_folder(cm)

        DEFAULT = 'regionaldesc,nationalsummary,regionalsummary,secondary'
        targets = self.request.form.get('setup', DEFAULT)

        if targets:
            targets = targets.split(',')
        else:
            targets = DEFAULT

        if "nationaldesc" in targets:
            self.setup_nationaldescriptors(cm)

        if "regionaldesc" in targets:
            self.setup_regionaldescriptors(cm)

        if "nationalsummary" in targets:
            self.setup_nationalsummaries(cm)

        if "secondary" in targets:
            self.setup_secondary_articles(cm)

        if 'regionalsummary' in targets:
            self.setup_regionalsummaries(cm)

        alsoProvides(self.request, IDisableCSRFProtection)

        return cm.absolute_url()


class BootstrapAssessmentLandingpages(BootstrapCompliance):

    def __call__(self):
        image_url = "https://wise-test.eionet.europa.eu/policy-and-reporting/implementation-and-reports/implementation-and-reports/@@download/image/30657450808_59e1973b0b_o.jpg"
        image_caption = "© Paweł Gładyś, WaterPIX /EEA"
        response = requests.get(image_url)
        filename = u'lead_image.png'
        image = NamedBlobImage(data=response.content, filename=filename)

        reports_folder = create(
            self.context,
            'Folder',
            title='Reports and assessments',
            id='reports-and-assessments'
        )

        landingpage = create(
            reports_folder,
            'Folder',
            title='EU overview - Commission reports and assessments, '
                  'Member State reports',
            id='assessment-module-overview'
        )
        self.set_layout(landingpage, 'landingpage')

        report_per_descr = create(
            reports_folder,
            'Folder',
            title=u'EU overview - Member State reports per Descriptor',
            id='assessment-per-descriptor'
        )
        report_per_descr.image = image
        report_per_descr.image_caption = image_caption
        self.set_layout(report_per_descr, 'reports-per-descriptor')

        countries = create(self.context,
                           'Folder',
                           title='Assessment by Country',
                           id='assessment-by-country')
        # self.set_layout(countries, 'landingpage')

        for code, country in self._get_countries():
            cpage = create(countries,
                           'Document',
                           title=country,
                           # id=code.lower()
                           )
            alsoProvides(cpage, interfaces.ICountryDescriptorsFolder)

            cpage.image = image
            cpage.image_caption = image_caption
            cpage._ccode = code.lower()
            self.set_layout(cpage, 'country-landingpage')

        regions = create(self.context,
                         'Folder',
                         title='Assessment by Region',
                         id='assessment-by-region')
        # self.set_layout(regions, 'landingpage')

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            code, name = region.code.lower(), region.title

            rpage = create(regions,
                           'Document',
                           title=name,
                           # id=code
                           )

            rpage.image = image
            rpage.image_caption = image_caption
            rpage._rcode = code
            self.set_layout(rpage, 'region-landingpage')

        alsoProvides(self.request, IDisableCSRFProtection)

        return "Boostrap finished!"


class BoostrapMembestateRecommendations(BootstrapCompliance):
    """ Bootstrap the member state recommendation pages """

    def __call__(self):
        ms_recommendation_page = create(
            self.context,
            'Folder',
            title='Member State responses to Article 12 recommendations \
                (2018 reports on Articles 8, 9, 10)',
            id='ms-recommendations'
        )
        self.set_layout(ms_recommendation_page, 'ms-recommendations-start')

        for code, country in self._get_countries():
            cpage = create(ms_recommendation_page,
                           'wise.msfd.msrecommendationfeedback',
                           title=country,
                           id=code.lower()
                           )
            alsoProvides(cpage, interfaces.IMSRecommendationsFeedback)

            self.set_layout(cpage, 'country-ms-recommendation')

        alsoProvides(self.request, IDisableCSRFProtection)

        return "Success!"


class CleanupCache(BrowserView):
    """ Remove the persistent cache that we have saved in objects
    """

    def __call__(self):
        brains = api.content.find(context=self.context, depth=10000)

        for brain in brains:
            obj = brain.getObject()
            print "For obj", obj

            for name in obj.__dict__.keys():

                if name.startswith('_cache_'):
                    logger.info("Cleaning up %r: %s", obj, name)
                    delattr(obj, name)

        return "done"


User = namedtuple('User', ['username', 'fullname', 'email'])


class ComplianceAdmin(BaseComplianceView):
    """"""

    name = 'admin'
    section = 'compliance-admin'

    @property
    def get_descriptors(self):
        descriptors = get_all_descriptors()

        return descriptors

    def get_users_by_group_id(self, group_id):
        groups_tool = getToolByName(self.context, 'portal_groups')

        g = groups_tool.getGroupById(group_id)
        members = g.getGroupMembers()

        if not members:
            return []

        res = []

        for x in members:
            user = User(x.getProperty('id'),
                        x.getProperty('fullname'),
                        x.getProperty('email'), )
            res.append(user)

        return res

    # @cache      #TODO
    def get_groups_for_desc(self, descriptor):
        descriptor = descriptor.split('.')[0]
        group_id = '{}-{}'.format(CONTRIBUTOR_GROUP_ID, descriptor.lower())

        return self.get_users_by_group_id(group_id)

    @property
    def get_reviewers(self):
        group_id = REVIEWER_GROUP_ID

        return self.get_users_by_group_id(group_id)

    @property
    def get_editors(self):
        group_id = EDITOR_GROUP_ID

        return self.get_users_by_group_id(group_id)


class AdminScoring(BaseComplianceView, AssessmentDataMixin):
    name = 'admin-scoring'
    section = 'compliance-admin'

    questions = NAT_DESC_QUESTIONS
    questions_reg = REG_DESC_QUESTIONS

    def _get_values_for_question(self, data, descriptor_obj, question, muids):
        targets = question.get_assessed_elements(descriptor_obj, muids=muids)

        values = []

        for target in targets:
            target_id = target.id

            field_name = "{}_{}_{}".format(question.article, question.id,
                                           target_id)

            value = data.get(field_name, None)

            if value is not None:
                values.append(value)

        return values

    def descriptor_obj(self, descriptor):
        return get_descriptor(descriptor)

    def get_available_countries(self, region_folder):
        res = [
            # id, title, definition, is_primary
            COUNTRY(x[0], x[1], "", lambda _: True)
            for x in region_folder._countries_for_region
        ]

        return res

    @cache(report_data_cache_key)
    def muids(self, country_code, country_region_code, year):
        """ Get all Marine Units for a country

        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """

        return get_marine_units(country_code,
                                country_region_code,
                                year)

    @property
    def get_descriptors(self):
        """Exclude first item, D1 """
        descriptors = get_all_descriptors()

        return descriptors[1:]

    @property
    @timeit
    def ndas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        for brain in brains:
            obj = brain._unrestrictedGetObject()

            # safety check to exclude secondary articles
            if not INationalDescriptorAssessment.providedBy(obj):
                continue

            # safety check to exclude secondary articles
            obj_title = obj.title.capitalize()
            if obj_title in _get_secondary_articles():
                continue

            if obj_title in ('Art3-4'):
                continue

            yield obj

    @property
    @timeit
    def ndas_sec(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            # safety check to exclude primary articles
            if not INationalDescriptorAssessmentSecondary.providedBy(obj):
                continue

            obj_title = obj.title.capitalize()
            if obj_title not in _get_secondary_articles():
                continue

            yield obj

    def reset_assessment_data(self):
        """ Completely erase the assessment data from the system

        TODO: when implementing the regional descriptors, make sure to adjust
        """

        for obj in self.ndas:
            logger.info('Reset assessment data for %s', obj.absolute_url())

            if hasattr(obj, 'saved_assessment_data'):
                del obj.saved_assessment_data
                obj._p_changed = True

    def recalculate_score_for_objects(self, objects, questions, section):
        for obj in objects:
            if hasattr(obj, 'saved_assessment_data') \
                    and obj.saved_assessment_data:

                logger.info('recalculating scores for %r', obj)

                data = obj.saved_assessment_data.last()
                new_overall_score = 0
                scores = {k: v for k, v in data.items()
                          if '_Score' in k and v is not None}

                article = obj.title
                is_art10_nat_desc = (section == 'national'
                                     and article in ('Art10', ))

                if is_art10_nat_desc:
                    descriptor_id = obj.aq_parent.id.upper()
                    descriptor_obj = self.descriptor_obj(descriptor_id)
                    country_code = obj.aq_parent.aq_parent.aq_parent.id.upper()
                    country_region_code = obj.aq_parent.aq_parent.id.upper()
                    year = '2018'
                    muids = self.muids(country_code, country_region_code, year)

                for q_id, score in scores.items():
                    id_ = score.question.id
                    article = score.question.article
                    _question = [
                        x

                        for x in questions.get(article, ())

                        if x.id == id_
                    ]
                    if not _question:
                        continue

                    _question = _question[0]

                    # new_score_weight = _question.score_weights
                    # _question.score_weights = new_score_weight

                    values = score.values

                    if is_art10_nat_desc:
                        values = self._get_values_for_question(
                            data, descriptor_obj, _question, muids
                        )

                    descriptor = score.descriptor

                    # this is a fix for a special case, when the score object
                    # was initialized with empty values
                    if not values and section == 'regional':
                        field_name = '{}_{}'.format(article, id_)
                        values = [
                            v
                            for k, v in data.items()
                            if field_name in k and isinstance(v, int)
                        ]

                    new_score = _question.calculate_score(descriptor, values)

                    data[q_id] = new_score
                    new_overall_score += getattr(new_score,
                                                 'weighted_score', 0)

                data['OverallScore'] = new_overall_score
                obj.saved_assessment_data._p_changed = True

    def recalculate_scores(self):
        # self.recalculate_score_for_objects(self.ndas, self.questions,
        #                                    'national')
        self.recalculate_score_for_objects(self.rdas, self.questions_reg,
                                           'regional')

    # @cache(lambda func, *args: func.__name__ + args[1].absolute_url(),
    #        lifetime=1800)
    def get_data(self, obj):
        """ Get assessment data for a country assessment object
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article_folder = obj
        article_title = article_folder.title
        descr = obj.aq_parent
        descr_id = descr.id.upper()
        region_code = obj.aq_parent.aq_parent.id.upper()
        region_name = obj.aq_parent.aq_parent.title
        country_code = obj.aq_parent.aq_parent.aq_parent.id.upper()
        country_name = obj.aq_parent.aq_parent.aq_parent.title
        d_obj = self.descriptor_obj(descr_id)
        muids = self.muids(country_code, region_code, '2018')
        data = obj.saved_assessment_data.last()

        phase_overall_scores = OverallScores(ARTICLE_WEIGHTS)
        phase_overall_scores = self._setup_phase_overall_scores(
            phase_overall_scores, data, article_title)
        phase_overall_scores.coherence = self.get_coherence_data(
            region_code, descr_id, article_title
        )

        score_last_change = []

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                last_change_name = "{}_{}_Last_update".format(article_title,
                                                              val.question.id)
                last_change = data.get(last_change_name, '')
                score_last_change.append(last_change)
                last_change = last_change and last_change.isoformat() or ''

                for i, v in enumerate(val.values):
                    options = ([o.title
                                for o in val.question.get_assessed_elements(
                                    d_obj, muids=muids)] or ['All criteria'])

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue
                        option = 'ERROR with options: {} / index: {}'.format(
                            ', '.join(options), i
                        )

                    answer = val.question.answers[v]
                    score = val.question.scores[v]
                    score_title = CONCLUSIONS[score]

                    yield (
                        country_code, country_name, region_code, region_name,
                        d_obj.id, d_obj.title,
                        article_title, val.question.id, option, answer,
                        score, score_title, state, last_change)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                last_change_name = "{}_{}_Last_update".format(article_id,
                                                              question_id)
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_name, region_code, region_name,
                       d_obj.id, d_obj.title,
                       article_id, question_id, 'Summary', val,
                       '', '', state, last_change)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_name, region_code, region_name,
                       d_obj.id, d_obj.title,
                       article_id, ' ', 'Assessment Summary', val,
                       '', '', state, last_change)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_name, region_code, region_name,
                       d_obj.id, d_obj.title,
                       article_id, '', 'Recommendations', val,
                       '', '', state, last_change)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_name, region_code, region_name,
                       d_obj.id, d_obj.title,
                       article_id, '', 'Progress', val,
                       '', '', state, last_change)

        score_last_change = filter(None, score_last_change)
        last_change = score_last_change and max(score_last_change) or ''
        last_change = last_change and last_change.isoformat() or ''

        phases = phase_overall_scores.article_weights.values()[0].keys()

        for phase in phases:
            _phase_score = getattr(phase_overall_scores, phase, {})
            score = phase_overall_scores.get_score_for_phase(phase)
            score_title = _phase_score.get('conclusion', '')[1]

            yield (country_code, country_name, region_code, region_name,
                   d_obj.id, d_obj.title,
                   article_title, '', '2018 {}'.format(phase.capitalize()), '',
                   score, score_title, state, last_change)

        overall_concl, score = phase_overall_scores.get_overall_score(
            article_title)
        score_title = self.get_conclusion(overall_concl)

        yield (country_code, country_name, region_code, region_name,
               d_obj.id, d_obj.title,
               article_title, '', '2018 Overall', '',
               score, score_title, state, last_change)

        # 2012 Adequacy and change
        score_2012, concl_2012 = self.get_assessment_data_2012(
            region_code, country_name, descr_id, article_title
        )

        adeq_2018_score_val = phase_overall_scores.get_range_index_for_phase(
            'adequacy'
        )
        adequacy_2012_change = adeq_2018_score_val - score_2012

        yield (country_code, country_name, region_code, region_name,
               d_obj.id, d_obj.title,
               article_title, '', '2018 Adequacy score value', '',
               adeq_2018_score_val, '', state, last_change)

        yield (country_code, country_name, region_code, region_name,
               d_obj.id, d_obj.title,
               article_title, '', '2012 Adequacy score value', '',
               score_2012, concl_2012, state, last_change)

        yield (country_code, country_name, region_code, region_name,
               d_obj.id, d_obj.title,
               article_title, '', '2012 Adequacy change', '',
               adequacy_2012_change, '', state, last_change)

    def get_data_sec(self, obj):
        """ Get assessment data for a country assessment object
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article_title = obj.title
        country_code = obj.aq_parent.id.upper()
        country_title = obj.aq_parent.title
        data = obj.saved_assessment_data.last()
        d_obj = 'Not linked'
        muids = []

        phase_overall_scores = OverallScores(ARTICLE_WEIGHTS)
        phase_overall_scores = self._setup_phase_overall_scores(
            phase_overall_scores, data, article_title)

        score_last_change = []

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                last_change_name = "{}_{}_Last_update".format(article_title,
                                                              val.question.id)
                last_change = data.get(last_change_name, '')
                score_last_change.append(last_change)
                last_change = last_change and last_change.isoformat() or ''

                for i, v in enumerate(val.values):
                    options = ([o.title
                                for o in val.question.get_assessed_elements(
                                    d_obj, muids=muids)] or ['All criteria'])

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue

                    answer = val.question.answers[v]
                    score = val.question.scores[v]
                    score_title = CONCLUSIONS[score]

                    yield (country_code, country_title, article_title,
                           val.question.id, option, answer, score, score_title,
                           state, last_change)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                last_change_name = "{}_{}_Last_update".format(article_id,
                                                              question_id)
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_title, article_id, question_id,
                       'Summary', val, '', '', state, last_change)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_title, article_id, '',
                       'Assessment Summary', val, '', '', state, last_change)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_title, article_id, '',
                       'Recommendations', val, '', '', state, last_change)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country_code, country_title, article_id, '',
                       'Progress', val, '', '', state, last_change)

        score_last_change = filter(None, score_last_change)
        last_change = score_last_change and max(score_last_change) or ''
        last_change = last_change and last_change.isoformat() or ''

        overall_concl, score = phase_overall_scores.get_overall_score(
            article_title)
        score_title = self.get_conclusion(overall_concl)

        yield (country_code, country_title, article_title, '',
               '2018 Overall', '', score, score_title,
               state, last_change)

    def get_data_rda(self, obj):
        """ Get assessment data for a regional descriptor assessment
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article_title = obj.title
        descr = obj.aq_parent
        region_code = obj.aq_parent.aq_parent.id.upper()
        region_title = obj.aq_parent.aq_parent.title
        d_obj = self.descriptor_obj(descr.id.upper())
        data = obj.saved_assessment_data.last()
        score_last_change = []

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                last_change_name = "{}_{}_Last_update".format(article_title,
                                                              val.question.id)
                last_change = data.get(last_change_name, '')
                score_last_change.append(last_change)
                last_change = last_change and last_change.isoformat() or ''

                for i, v in enumerate(val.values):
                    options = ([o.title
                                for o in val.question.get_assessed_elements(
                                    d_obj, muids=[])] or ['All criteria'])

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue

                    answer = val.question.answers[v]
                    score = val.question.scores[v]
                    score_title = CONCLUSIONS[score]

                    yield (region_code, region_title, d_obj.id, d_obj.title,
                           article_title, val.question.id, option, answer,
                           score, score_title, state, last_change)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                last_change_name = "{}_{}_Last_update".format(article_id,
                                                              question_id)
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (region_code, region_title, d_obj.id, d_obj.title,
                       article_id, question_id, 'Summary', val,
                       '', '', state, last_change)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (region_code, region_title, d_obj.id, d_obj.title,
                       article_id, '', 'Assessment Summary', val,
                       '', '', state, last_change)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (region_code, region_title, d_obj.id, d_obj.title,
                       article_id, '', 'Recommendations', val,
                       '', '', state, last_change)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (region_code, region_title, d_obj.id, d_obj.title,
                       article_id, '', 'Progress', val,
                       '', '', state, last_change)

        score_last_change = filter(None, score_last_change)
        last_change = score_last_change and max(score_last_change) or ''
        last_change = last_change and last_change.isoformat() or ''

        coherence_data = self.get_coherence_data(
            region_code, d_obj.id,article_title)
        score_title = coherence_data['conclusion'][1]
        _max_score = float(coherence_data['max_score'])
        score = int(_max_score and (float(coherence_data['score']) * 100)
                    / _max_score or 0)

        yield (region_code, region_title, d_obj.id, d_obj.title,
               article_title, '', '2018 Coherence', '',
               score, score_title, state, last_change)

    @timeit
    def data_to_xls(self, all_data):
        logger.info('Preparing data to xls!')

        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'constant_memory': True})

        for sheetname, labels, data in all_data:
            worksheet = workbook.add_worksheet(sheetname)

            for i, label in enumerate(labels):
                worksheet.write(0, i, label)

            x = 0

            for objdata in data:
                for row in objdata:
                    x += 1

                    for iv, value in enumerate(row):
                        worksheet.write(x, iv, value)

        workbook.close()
        out.seek(0)

        return out

    @timeit
    def data_to_xml(self, all_data):
        root = etree.Element('data')
        out = BytesIO()

        excludes = ('Progress', 'Summary', 'Recommendations',
                    'Assessment Summary')

        for name, labels, data in all_data:
            index_option = labels.index('Option')
            name = name.title().replace(' ', '_').replace(',', '')
            descr_element = etree.SubElement(root, name)

            for row in data:
                for objdata in row:
                    option = objdata[index_option]

                    if option in excludes:
                        continue

                    element = etree.SubElement(descr_element, 'element')

                    for i, value in enumerate(objdata):
                        label_title = labels[i].title().replace(' ', '')

                        v_element = etree.SubElement(element, label_title)
                        v_element.text = unicode(value)

        tree = etree.ElementTree(root)
        tree.write(out, pretty_print=True, xml_declaration=True,
                   encoding='utf-8')

        out.seek(0)

        return out

    def save_xsldata_to_annot(self, data):
        annot = get_annot()
        annot[ANNOT_XLSDATA] = (datetime.now(), data)

    def get_xlsdata_from_annot(self):
        annot = get_annot()
        xlsdata = annot.get(ANNOT_XLSDATA, (datetime.now(), None))

        return xlsdata

    @timeit
    @cache(lambda func, *args: func.__name__, lifetime=1800)
    def get_export_scores_data(self, context):
        last_savedate, annot_xlsdata = self.get_xlsdata_from_annot()
        diff = datetime.now() - last_savedate
        total_mins = (diff.days * 1440 + diff.seconds / 60)

        if total_mins < 60 and annot_xlsdata:
            logger.info('Got xlsdata from annotations: '
                        'data saved %s minutes ago', total_mins)
            return annot_xlsdata

        # National descriptors data
        nda_labels = ('Country', 'Country title', 'Region', 'Region title',
                      'Descriptor', 'Descriptor title',
                      'Article', 'Question', 'Option', 'Answer',
                      'Score', 'Score title', 'State', 'Last change')

        # transform data to lists to make it cacheable
        nda_xlsdata = [
            [row for row in self.get_data(nda)]
            for nda in self.ndas
            # if (hasattr(nda, 'saved_assessment_data')
            #     and nda.saved_assessment_data)
        ]

        # Regional descriptors data
        rda_labels = ('Region', 'Region title', 'Descriptor',
                      'Descriptor title',
                      'Article', 'Question', 'Option', 'Answer',
                      'Score', 'Score title', 'State', 'Last change')

        # transform data to lists to make it cacheable
        rda_xlsdata = [
            [row for row in self.get_data_rda(rda)]
            for rda in self.rdas
        ]

        # Secondary Articles 3 & 4, 7
        sec_labels = ('Country', 'Country title', 'Article', 'Question',
                      'Option', 'Answer', 'Score', 'Score title',
                      'State', 'Last change')

        # transform data to lists to make it cacheable
        sec_xlsdata = [
            [row for row in self.get_data_sec(sec)]
            for sec in self.ndas_sec
        ]

        all_data = PersistentList()
        all_data.extend([
            ('National descriptors', nda_labels, nda_xlsdata),
            ('Regional descriptors', rda_labels, rda_xlsdata),
            ('Articles 3, 4, 7', sec_labels, sec_xlsdata)
        ])
        self.save_xsldata_to_annot(all_data)

        return all_data

    @timeit
    def export_scores(self, context):
        all_data = self.get_export_scores_data(context)
        xlsio = self.data_to_xls(all_data)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
                           'spreadsheetml.sheet')
        fname = "-".join(['Assessment_Scores',
                          str(datetime.now().replace(microsecond=0))])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def can_export_xml(self, use_password=True):
        if not use_password:
            return True

        password = self.request.form.get('token', None)

        if not password:
            return False

        if not EXPORTPASS:
            return False

        if password != EXPORTPASS:
            return False

        return True

    def export_scores_xml(self, context, use_password):
        can_export_xml = self.can_export_xml(use_password)

        if not can_export_xml:
            raise Unauthorized

        all_data = self.get_export_scores_data(context)

        xlsio = self.data_to_xml(all_data)
        sh = self.request.response.setHeader

        sh('Content-Type', 'text/xml')
        fname = "_".join(['Assessment_Scores',
                          str(datetime.now().replace(microsecond=0))])
        sh('Content-Disposition',
           'attachment; filename=%s.xml' % fname)

        return xlsio.read()

    def __call__(self):

        msgs = IStatusMessage(self.request)

        if 'export-scores' in self.request.form:
            return self.export_scores(self.context)

        if 'export-xml' in self.request.form:
            return self.export_scores_xml(self.context, use_password=False)

        # if 'reset-assessments' in self.request.form:
        #     self.reset_assessment_data()
        #     msgs.add('Assessments reseted successfully!', type='warning')
        #     logger.info('Reset score finished!')

        if 'recalculate-scores' in self.request.form:
            self.recalculate_scores()
            msgs.add('Scores recalculated successfully!', type='info')
            logger.info('Recalculating score finished!')

        return self.index()


class AdminScoringExportXML(AdminScoring):
    def __call__(self):
        file = self.export_scores_xml(self.context, use_password=True)

        return file


class SetupAssessmentWorkflowStates(BaseComplianceView):

    def get_objects(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.regionaldescriptorassessment',
            path='/Plone/assessment-module/regional-descriptors-assessments'
        )

        for brain in brains:
            obj = brain.getObject()

            state = get_wf_state_id(obj)

            if state in ('not_started', 'approved'):
                continue

            if '/d1/' in obj.absolute_url():
                continue

            yield obj, state

    def view_objects(self):
        template = "<tr><td><a href={0}>{0}</a></td><td>{1}<td><tr>"
        res = [template.format(x[0].absolute_url(), x[1]) for x in self.get_objects()]

        return "<table>{}</table".format("".join(res))

    def fix_objects(self):
        changed = 0
        not_changed = 0

        logger.info("Changing workflow states to not_started...")

        for nda, state in self.get_objects():
            # if hasattr(nda, 'saved_assessment_data'):
                # data = nda.saved_assessment_data.last()
                #
                # if data:
                #     not_changed += 1
                #
                #     continue

            changed += 1
            logger.info("State changing for {}".format(nda.__repr__()))
            transition(obj=nda, to_state='approved')

        logger.info("States changed: {}, Not changed: {}".format(
            changed, not_changed)
        )

        alsoProvides(self.request, IDisableCSRFProtection)

        return "Done"


class TranslateIndicators(BrowserView):

    def __call__(self):
        labels = get_indicator_labels().values()
        site = portal.get()
        storage = ITranslationsStorage(site)

        count = 0

        for label in labels:
            lang = get_detected_lang(label)

            if (not lang) or (lang == 'en'):
                continue

            lang = lang.upper()

            langstore = storage.get(lang, None)

            if langstore is None:
                continue

            if label not in langstore:
                langstore[label] = u''
                logger.info('Added %r to translation store for lang %s',
                            label, lang)
                count = +1

        return "Added %s labels" % count


class MigrateTranslationStorage(BrowserView):

    def __call__(self):
        site = portal.get()
        storage = ITranslationsStorage(site)
        count = 0

        for langstore in storage.values():
            for original, translated in langstore.items():
                count = +1

                if hasattr(translated, 'text'):
                    translated = translated.text
                translated = Translation(translated, 'original')

                if not translated.text.startswith('?'):
                    translated.approved = True

                langstore[original] = translated

        return "Migrated {} strings".format(count)
