import logging

from zope.interface import alsoProvides

from plone.api.content import transition
from plone.dexterity.utils import createContentInContainer as create
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from wise.msfd import db, sql2018
from wise.msfd.compliance.vocabulary import REGIONS

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

    @db.use_db_session('2018')
    def _get_descriptors(self):
        """ Get a list of (code, description) descriptors
        """

        mc = sql2018.LGESComponent
        count, res = db.get_all_records(
            mc,
            mc.GESComponent == 'Descriptor'
        )
        descriptors = [(x.Code.split('/')[0], x.Description) for x in res]

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

        return "extranet-wisemarine-msfd-tl-" + code

    def make_country(self, parent, country_code, name):
        cf = create(parent,
                    'wise.msfd.countrydescriptorsfolder',
                    title=name,
                    id=country_code)

        for regid, region in self.get_country_regions(country_code):
            reg = create(cf,
                         'Folder',
                         title=region,
                         id=regid)
            alsoProvides(reg, interfaces.INationalRegionDescriptorFolder)
            self.set_layout(reg, '@@nat-desc-reg-view')

            for desc_code, description in self._get_descriptors():
                df = create(reg, 'Folder', title=description, id=desc_code)
                alsoProvides(df, interfaces.IDescriptorFolder)

                for art in self._get_articles():
                    nda = create(df, 'wise.msfd.nationaldescriptorassessment',
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

        if 'compliance-module' in self.context.contentIds():
            self.context.manage_delObjects(['compliance-module'])

        cm = create(self.context, 'Folder', title=u'Compliance Module')
        self.set_layout(cm, '@@comp-start')
        self.set_policy(cm, 'compliance_section_policy')

        alsoProvides(cm, interfaces.IComplianceModuleFolder)

        lr = cm.__ac_local_roles__
        lr['extranet-wisemarine-msfd-reviewers'] = [u'Reviewer']
        lr['extranet-wisemarine-msfd-editors'] = [u'Editor']

        # Contributor: TL
        # Reviewer: EC
        # Editor: Milieu

        self.setup_nationaldescriptors(cm)
        self.setup_regionaldescriptors(cm)

        return cm.absolute_url()
