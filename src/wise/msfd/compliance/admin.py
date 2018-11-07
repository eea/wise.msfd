import logging

from zope.interface import alsoProvides

from plone.api.content import transition
from plone.dexterity.utils import createContentInContainer as create
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from wise.msfd import db, sql2018

from . import interfaces

logger = logging.getLogger('wise.msfd')


class ToPDB(BrowserView):
    def __call__(self):
        import pdb
        pdb.set_trace()

        return 'ok'


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
    """

    @db.use_db_session('session_2018')
    def _get_countries(self):
        """ Get a list of (code, name) countries
        """

        is_debug = 'production' not in self.request.form

        count, res = db.get_all_records(
            sql2018.LCountry
        )
        countries = [(x.Code, x.Country) for x in res]

        if is_debug:
            countries = [x for x in countries if x[0] in ('LV', 'NL')]

        return countries

    @db.use_db_session('session_2018')
    def _get_regions(self):

        regions = [
            ('BAL', 'Baltic Sea'),
        ]

        return regions

    @db.use_db_session('session_2018')
    def _get_descriptors(self):
        """ Get a list of (code, description) descriptors
        """

        is_debug = 'production' not in self.request.form

        mc = sql2018.LGESComponent
        count, res = db.get_all_records(
            mc,
            mc.GESComponent == 'Descriptor'
        )
        descriptors = [(x.Code, x.Description) for x in res]

        descs = ('D1.1', 'D1.4', 'D5')

        if is_debug:
            descriptors = [x for x in descriptors if x[0] in descs]

        return descriptors

    @db.use_db_session('session_2018')
    def _get_articles(self):
        articles = db.get_unique_from_mapper(
            sql2018.LMSFDArticle,
            'MSFDArticle'
        )

        return ['Art8', 'Art9', 'Art10']

        return articles

    def set_layout(self, obj, name):
        ISelectableBrowserDefault(obj).setLayout(name)

    def set_policy(self, context, name):
        logger.info("Set placeful workflow policy for %s", context.getId())
        config = WorkflowPolicyConfig(
            workflow_policy_in='compliance_section_policy',
            workflow_policy_below='compliance_section_policy',
        )
        context._setObject(config.id, config)

    def make_country(self, parent, code, name):
        cf = create(parent, 'wise.msfd.countrydescriptorsfolder',
                    title=name, id=code)

        for code, description in self._get_descriptors():
            df = create(cf, 'Folder', title=description, id=code)
            alsoProvides(df, interfaces.IDescriptorFolder)

            for art in self._get_articles():
                nda = create(df, 'wise.msfd.nationaldescriptorassessment',
                             title=art)
                logger.info("Created NationalDescriptorAssessment %s",
                            nda.absolute_url())

                self.set_layout(nda, '@@nat-desc-art-view')

                for id, title, trans in [
                        (u'tl', 'Discussion track with Topic Leads',
                         'open_for_tl'),
                        (u'ec', 'Discussion track with EC', 'open_for_ec'),
                ]:
                    dt = create(nda,
                                'wise.msfd.commentsfolder', id=id, title=title)
                    transition(obj=dt, transition=trans)

        return cf

    def make_region(self, parent, code, name):
        rf = create(parent, 'wise.msfd.countrydescriptorsfolder',
                    title=name, id=code)

        return rf

    def __call__(self):

        if 'compliance-module' in self.context.contentIds():
            self.context.manage_delObjects(['compliance-module'])
        cm = create(self.context, 'Folder', title=u'Compliance Module')
        self.set_layout(cm, '@@comp-start')
        self.set_policy(cm, 'compliance_section_policy')

        # cm.__ac_local_roles__['extranet-someone'] = [u'Contributor',
        # u'Editor']

        alsoProvides(cm, interfaces.IComplianceModuleFolder)

        # National Descriptors Assessments
        nda = create(cm, 'Folder', title=u'National Descriptors Assessments')
        self.set_layout(nda, '@@nat-desc-start')
        alsoProvides(nda, interfaces.INationalDescriptorsFolder)

        for code, country in self._get_countries():
            self.make_country(nda, code, country)

        # Regional Descriptors Assessments
        rda = create(cm, 'Folder', title=u'Regional Descriptors Assessments')
        self.set_layout(rda, '@@reg-desc-start')
        alsoProvides(rda, interfaces.IRegionalDescriptorsFolder)

        for rcode, region in self._get_regions():
            self.make_region(rda, rcode, region)

        return cm.absolute_url()
