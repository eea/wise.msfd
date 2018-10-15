import logging

from zope.interface import alsoProvides

from plone.dexterity.utils import createContentInContainer as create
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.Five.browser import BrowserView

from . import interfaces

logger = logging.getLogger('wise.msfd')


class ToPDB(BrowserView):
    def __call__(self):
        import pdb; pdb.set_trace()

        return 'ok'


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
    """

    def _get_countries(self):
        """ Get a list of (code, name) countries
        """

        return [
            ('RO', 'Romania'),
        ]

    def _get_descriptors(self):
        return ['D1', 'D5']

    def _get_articles(self):
        return ['Art8', 'Art9', 'Art10']

    def set_layout(self, obj, name):
        ISelectableBrowserDefault(obj).setLayout(name)

    def make_country(self, parent, code, name):
        cf = create(parent, 'Folder', title=name, id=code)
        self.set_layout(cf, '@@nat-desc-country-start')
        alsoProvides(cf, interfaces.ICountryDescriptorsFolder)

        for code in self._get_descriptors():
            df = create(cf, 'Folder', title=code, id=code)
            alsoProvides(df, interfaces.IDescriptorFolder)

            for art in self._get_articles():
                nda = create(df, 'wise.msfd.nationaldescriptorassessment',
                             title=art)
                logger.info("Created NationalDescriptorAssessment %s",
                            nda.absolute_url())

                self.set_layout(nda, '@@nat-desc-art-view')

        return cf

    def __call__(self):
        cm = create(self.context, 'Folder', title=u'Compliance Module')
        self.set_layout(cm, '@@comp-start')
        alsoProvides(cm, interfaces.IComplianceModuleFolder)

        nda = create(cm, 'Folder', title=u'National Descriptors Assessments')
        self.set_layout(nda, '@@nat-desc-start')
        alsoProvides(nda, interfaces.INationalDescriptorsFolder)

        for code, country in self._get_countries():
            self.make_country(nda, code, country)

        return cm.absolute_url()
