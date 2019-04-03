import logging
from collections import namedtuple

from zope.interface import alsoProvides

from plone import api
from plone.api.content import transition
from plone.dexterity.utils import createContentInContainer as create
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from wise.msfd import db, sql2018
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.gescomponents import get_all_descriptors

from . import interfaces
from .base import BaseComplianceView

logger = logging.getLogger('wise.msfd')

CONTRIBUTOR_GROUP_ID = 'extranet-wisemarine-msfd-tl'
REVIEWER_GROUP_ID = 'extranet-wisemarine-msfd-reviewers'
EDITOR_GROUP_ID = 'extranet-wisemarine-msfd-editors'


class ToPDB(BrowserView):
    def __call__(self):
        import pdb
        pdb.set_trace()

        return 'ok'


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
    """

    @property
    def debug(self):
        return 'production' not in self.request.form

    @db.use_db_session('2018')
    def _get_countries(self):
        """ Get a list of (code, name) countries
        """

        count, res = db.get_all_records(
            sql2018.LCountry
        )
        countries = [(x.Code, x.Country) for x in res]

        if self.debug:
            countries = [x for x in countries if x[0] in ('LV', 'NL', 'DE')]

        return countries

    def _get_descriptors(self):
        """ Get a list of (code, description) descriptors
        """

        descriptors = get_all_descriptors()

        debug_descriptors = ('D1', 'D1.1', 'D4', 'D5', 'D6')

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
        t = sql2018.MarineReportingUnit
        regions = db.get_unique_from_mapper(
            t,
            'Region',
            t.CountryCode == country_code
        )

        blacklist = ['NotReported']

        return [(code, REGIONS.get(code, code))
                for code in regions

                if code not in blacklist]

    def get_group(self, code):
        if '.' in code:
            code = 'd1'
        code = code.lower()

        return "{}-{}".format(CONTRIBUTOR_GROUP_ID, code)

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

                for art in self._get_articles():
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

                    for id, title, trans in [
                            (u'tl', 'Discussion track with Topic Leads',
                             'open_for_tl'),
                            (u'ec', 'Discussion track with EC', 'open_for_ec'),
                    ]:
                        if id not in nda.contentIds():
                            dt = create(nda,
                                        'wise.msfd.commentsfolder',
                                        id=id,
                                        title=title)
                            transition(obj=dt, transition=trans)

        return cf

    def make_region(self, parent, code, name):
        rf = create(parent, 'wise.msfd.countrydescriptorsfolder',
                    title=name, id=code)

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
        rda = create(parent,
                     'Folder', title=u'Regional Descriptors Assessments')
        self.set_layout(rda, '@@reg-desc-start')
        alsoProvides(rda, interfaces.IRegionalDescriptorsFolder)

        for rcode, region in REGIONS.items():
            self.make_region(rda, rcode, region)

    def __call__(self):

        # if 'compliance-module' in self.context.contentIds():
        #     self.context.manage_delObjects(['compliance-module'])

        if 'compliance-module' in self.context.contentIds():
            cm = self.context['compliance-module']
        else:
            cm = create(self.context, 'Folder', title=u'Compliance Module')

            self.set_layout(cm, '@@comp-start')
            self.set_policy(cm, 'compliance_section_policy')

            alsoProvides(cm, interfaces.IComplianceModuleFolder)

            lr = cm.__ac_local_roles__
            lr[REVIEWER_GROUP_ID] = [u'Reviewer']
            lr[EDITOR_GROUP_ID] = [u'Editor']

        # Contributor: TL
        # Reviewer: EC
        # Editor: Milieu

        self.setup_nationaldescriptors(cm)
        # self.setup_regionaldescriptors(cm)

        return cm.absolute_url()


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
    section = 'national-descriptors'

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
