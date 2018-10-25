import logging

from zope.interface import alsoProvides

from plone.api.portal import get_tool
from plone.dexterity.utils import createContentInContainer as create
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.Five.browser import BrowserView
from wise.msfd import db, sql2018

from . import interfaces

logger = logging.getLogger('wise.msfd')


class ToPDB(BrowserView):
    def __call__(self):
        import pdb; pdb.set_trace()

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
    def _get_descriptors(self):
        mc = sql2018.LGESComponent
        descriptors = db.get_unique_from_mapper(
            mc,
            'Code',
            mc.GESComponent == 'Descriptor'
        )

        return ['D1', 'D5']

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

        tool = get_tool('portal_placeful_workflow')
        config = tool.getWorkflowPolicyConfig(context)

        # NOTE: updates workflow mappings
        config.setPolicyBelow(name, True)

    def make_country(self, parent, code, name):
        cf = create(parent, 'wise.msfd.countrydescriptorsfolder',
                    title=name, id=code)
        # self.set_layout(cf, '@@nat-desc-country-start')
        # alsoProvides(cf, interfaces.ICountryDescriptorsFolder)

        for code in self._get_descriptors():
            df = create(cf, 'Folder', title=code, id=code)
            alsoProvides(df, interfaces.IDescriptorFolder)

            for art in self._get_articles():
                nda = create(df, 'wise.msfd.nationaldescriptorassessment',
                             title=art)
                logger.info("Created NationalDescriptorAssessment %s",
                            nda.absolute_url())

                self.set_layout(nda, '@@nat-desc-art-view')

                for id, title in [
                        (u'tl', 'Discussion track with Topic Leads'),
                        (u'ec', 'Discussion track with EC'),
                ]:
                    create(nda, 'wise.msfd.commentsfolder', id=id, title=title)

        return cf

    def __call__(self):
        cm = create(self.context, 'Folder', title=u'Compliance Module')
        self.set_layout(cm, '@@comp-start')
        # self.set_policy(cm, 'compliance_section_policy')

        # cm.__ac_local_roles__['extranet-someone'] = [u'Contributor',
        # u'Editor']

        alsoProvides(cm, interfaces.IComplianceModuleFolder)

        nda = create(cm, 'Folder', title=u'National Descriptors Assessments')
        self.set_layout(nda, '@@nat-desc-start')
        alsoProvides(nda, interfaces.INationalDescriptorsFolder)

        for code, country in self._get_countries():
            self.make_country(nda, code, country)

        return cm.absolute_url()
