
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from .assessment import AssessmentDataMixin
from .base import BaseComplianceView


class StartLandingPage(BrowserView):
    """ Landing/Home page for assessment module """

    template = ViewPageTemplateFile("pt/landingpage.pt")

    def __call__(self):

        return self.template()


class BaseLandingPageRow(BaseComplianceView, AssessmentDataMixin):
    """ Base class with all the needed base methods to build the landing page
        structure
    """

    template = PageTemplateFile('pt/landingpage-row.pt')

    def __call__(self):

        return self.template(data=self.data)


class BaseRegionRow(BaseLandingPageRow):
    data = {
        'BAL': "test link",
        'ATL': "test link",
        'MED': "test link",
        'BLK': 'test link'
    }
