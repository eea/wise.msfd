from __future__ import absolute_import
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .base import BaseComplianceView


class TabsViewlet(ViewletBase, BaseComplianceView):
    template = ViewPageTemplateFile('pt/tabs.pt')

    def index(self):
        # print "Rendering tabs viewlet"
        return self.template()

    @property
    def name(self):
        return getattr(self.view, 'name', 'help')
