# pylint: skip-file
""" admin.py """
# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
import logging
import requests

from zope.interface import alsoProvides

from plone.api.content import transition
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer as create
from plone.namedfile.file import NamedBlobImage
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from wise.msfd import db

from wise.msfd.compliance.vocabulary import (get_all_countries,
                                             get_regions_for_country,
                                             REGIONAL_DESCRIPTORS_REGIONS,
                                             REPORTING_HISTORY_ENV)
from wise.msfd.gescomponents import get_all_descriptors

from .admin import CONTRIBUTOR_GROUP_ID, REVIEWER_GROUP_ID, EDITOR_GROUP_ID
from .. import interfaces
from ..base import _get_secondary_articles


logger = logging.getLogger('wise.msfd')


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
        /bootstrap-compliance?setup=nationaldesc&production=1
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

    def _get_articles(self):
        """_get_articles"""
        return ['Art8', 'Art9', 'Art10', 'Art8-2024', 'Art9-2024', 'Art10-2024']

    def set_layout(self, obj, name):
        """set_layout"""
        ISelectableBrowserDefault(obj).setLayout(name)

    def set_policy(self, context, name):
        """set_policy"""
        logger.info("Set placeful workflow policy for %s", context.getId())
        config = WorkflowPolicyConfig(
            workflow_policy_in='compliance_section_policy',
            workflow_policy_below='compliance_section_policy',
        )
        context._setObject(config.id, config)

    @db.use_db_session('2018')
    def get_country_regions(self, country_code):
        """get_country_regions"""
        regions = get_regions_for_country(country_code)

        return regions

    def get_group(self, code):
        """get_group"""
        if '.' in code:
            code = 'd1'
        code = code.lower()

        return "{}-{}".format(CONTRIBUTOR_GROUP_ID, code)

    def create_comments_folder(self, content):
        """create_comments_folder"""
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

    def create_nda_folder(self, df, desc_code, art,
                          layout='@@nat-desc-art-view'):
        """create_nda_folder"""
        if '2024' in art:
            layout = '@@nat-desc-art-view-2024'

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

        self.set_layout(nda, layout)

        self.create_comments_folder(nda)

    def create_rda_folder(self, df, desc_code, art):
        """create_rda_folder"""
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
        """make_country"""
        if country_code.lower() in parent.contentIds():
            cf = parent[country_code.lower()]
        else:
            cf = create(parent,
                        'wise.msfd.countrydescriptorsfolder',
                        title=name,
                        id=country_code)

        # create 2022 Cross cutting assessment folder
        art = 'cross-cutting-2022'
        if art.lower() in cf.contentIds():
            nda = cf[art.lower()]
        else:
            nda = create(cf,
                         'wise.msfd.nationaldescriptorassessment',
                         title=art)

            logger.info("Created NationalDescriptorAssessment %s",
                        nda.absolute_url())

            self.set_layout(nda, '@@nat-desc-art-view-cross-cutting')

        # Art 13 create 2022 completeness assessment folder
        art = 'art13-completeness-2022'
        if art.lower() in cf.contentIds():
            nda = cf[art.lower()]
        else:
            nda = create(cf,
                         'wise.msfd.nationaldescriptorassessment',
                         title=art)

            logger.info("Created NationalDescriptorAssessment %s",
                        nda.absolute_url())

            self.set_layout(nda, '@@nat-desc-art-view-completeness')
            nda._article = 'Art13Completeness'

        # Art 14 create 2022 completeness assessment folder
        art = 'art14-completeness-2022'
        if art.lower() in cf.contentIds():
            nda = cf[art.lower()]
        else:
            nda = create(cf,
                         'wise.msfd.nationaldescriptorassessment',
                         title=art)

            logger.info("Created NationalDescriptorAssessment %s",
                        nda.absolute_url())

            self.set_layout(nda, '@@nat-desc-art-view-completeness')
            nda._article = 'Art14Completeness'

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

                # article 13, 14, 18
                self.create_nda_folder(df, desc_code, 'Art13',
                                       '@@nat-desc-art-view-2022')
                self.create_nda_folder(df, desc_code, 'Art14',
                                       '@@nat-desc-art-view-2022')
                self.create_nda_folder(df, desc_code, 'Art18')

        return cf

    def make_region(self, parent, region):
        """make_region"""
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
        """setup_nationaldescriptors"""
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
        """setup_regionaldescriptors"""
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
        """setup_nationalsummaries"""
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
                # national_summary Art. 12 (8-9-10) National report - 2018
                cf = create(ns,
                            'national_summary',
                            title=country,
                            id=code)

            self.set_layout(cf, 'assessment-summary')
            alsoProvides(cf, interfaces.INationalSummaryCountryFolder)
            # self.create_comments_folder(cf)

            # create the country overview folder
            if 'overview' in cf.contentIds():
                of = cf['overview']
            else:
                of = create(cf,
                            'wise.msfd.nationalsummaryoverview',
                            title='National summary overview',
                            id='overview')

            self.set_layout(of, 'national-overview')
            alsoProvides(of, interfaces.INationalSummaryOverviewFolder)

            # create the Art. 16 (13-14) National report - 2022
            if 'assessment-summary-2022' in cf.contentIds():
                art16f = cf['assessment-summary-2022']
            else:
                art16f = create(cf,
                                'wise.msfd.nationalsummary2022',
                                title='National summary 2022',
                                id='assessment-summary-2022')

            self.set_layout(art16f, 'assessment-summary-2022')
            alsoProvides(art16f, interfaces.INationalSummary2022Folder)

    def setup_regionalsummaries(self, parent):
        """setup_regionalsummaries"""
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
        """setup_secondary_articles"""
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
        """setup_compliancefolder"""
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
        """setup_msfd_reporting_history_folder"""
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
    """BootstrapAssessmentLandingpages"""

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
            title=u'EU overview - Reports per Descriptor',
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
            cpage.text = RichTextValue(
                '', 'text/plain', 'text/html')
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

            alsoProvides(rpage, interfaces.IRegionalDescriptorRegionsFolder)
            rpage.image = image
            rpage.image_caption = image_caption
            rpage._rcode = code
            rpage.text = RichTextValue(
                '', 'text/plain', 'text/html')
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
