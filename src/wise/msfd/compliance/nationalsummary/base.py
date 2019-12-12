
from plone.api.content import get_state
from plone.api.portal import get_tool
from wise.msfd.compliance.base import BaseComplianceView

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces


class BaseNatSummaryView(BaseComplianceView):
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
    )

    section = 'national-summaries'
    _translatables = None

    @property
    def current_phase(self):
        region_folder = self._country_folder
        state, title = self.process_phase(region_folder)

        return state, title

    @property
    def TRANSLATABLES(self):
        # for 2018, returns a list of field names that are translatable

        if self._translatables:
            return self._translatables

        self._translatables = []

        return self._translatables

    @TRANSLATABLES.setter
    def set_translatables(self, v):
        self._translatables = v

    @property
    def _country_folder(self):
        return self.get_parent_by_iface(
            interfaces.INationalSummaryCountryFolder
        )

    def filter_contentvalues_by_iface(self, folder, interface):
        res = [
            f for f in folder.contentValues()
            if interface.providedBy(f)
        ]

        return res

    @property
    def available_countries(self):
        return self._country_folder._countries_for_region

    def process_phase(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]  # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return state, title
