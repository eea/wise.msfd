
from __future__ import absolute_import
from plone.api.content import get_state
from plone.api.portal import get_tool
from plone.app.textfield.interfaces import ITransformer
from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces


class BaseRegSummaryView(BaseComplianceView):
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
    )

    section = 'regional-summaries'
    _translatables = None
    _translatable_values = []

    ARTICLE_ORDER = ('Art9', 'Art8', 'Art10')

    def region_name_url(self):
        region_code = self.region_code

        region_title = [
            r.title
            for r in REGIONAL_DESCRIPTORS_REGIONS
            if r.code == region_code.upper()
        ][0]

        region_title = region_title.lower().replace(' ', '-')

        return region_title

    def _format_date(self, date):
        if not date:
            return '-'

        date = date.strftime("%d %B %Y")

        return date

    def date(self, context=None):
        if not context:
            context = self.context

        date = context.modified()
        date = self._format_date(date)

        return date

    def get_transformer(self, context=None):
        if not context:
            context = self

        transformer = ITransformer(context)

        return transformer

    def get_transformed_richfield_text(self, fieldname):
        raw_text = getattr(self._region_folder, fieldname, None)
        text = u"-"

        context = self._region_folder

        if raw_text:
            transformer = self.get_transformer(context=context)
            text = transformer(raw_text, 'text/plain')

        return text

    def get_field_value(self, attribute):
        country_folder = self._region_folder
        default = "-"

        if not hasattr(country_folder, attribute):
            return default

        progress = getattr(country_folder, attribute)
        output = getattr(progress, 'output', default)

        return output

    @property
    def current_phase(self):
        region_folder = self._region_folder
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
        """ Needs to be defined for our National summaries code
            to be compatible with Regional summaries
        """

        return self._region_folder

    @property
    def _region_folder(self):
        return self.get_parent_by_iface(
            interfaces.IRegionalSummaryRegionFolder
        )

    @property
    def country_code(self):
        """ Needs to be defined for our National summaries code
            to be compatible with Regional summaries
        """

        return self.region_code

    @property
    def country_name(self):
        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if region.code == self.region_code:
                return region.title

        return self.region_name

    @property
    def region_name(self):
        return self._region_folder.title

    @property
    def region_code(self):
        return self._region_folder.id.upper()

    @property
    def available_countries(self):
        return self._region_folder._countries_for_region

    @property
    def available_subregions(self):
        return self._region_folder._subregions

    @property
    def subregions(self):
        subregions = self.available_subregions

        # if it is a main region, it has only himself as subregion
        if len(subregions) == 1:
            return "None"

        return ", ".join(subregions)

    def process_phase(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]  # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return state, title
