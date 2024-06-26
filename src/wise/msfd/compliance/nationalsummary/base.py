#pylint: skip-file
from __future__ import absolute_import
from plone.api.content import get_state
from plone.api.portal import get_tool
from plone.app.textfield.interfaces import ITransformer
from wise.msfd.compliance.base import BaseComplianceView

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces


class BaseNatSummaryView(BaseComplianceView):
    overview_header_template = ViewPageTemplateFile(
        'pt/overview-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
    )

    section = 'national-summaries'
    _translatables = None
    _translatable_values = []

    def country_name_url(self):
        return self.country_name.lower().replace(' ', '-')

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

    def get_odt_data(self, document):
        return []

    def get_transformer(self, context=None):
        if not context:
            context = self

        transformer = ITransformer(context)

        return transformer

    def get_transformed_richfield_text(self, fieldname):
        raw_text = getattr(self._country_folder, fieldname, None)
        text = u"-"

        context = self._country_folder

        if raw_text:
            transformer = self.get_transformer(context=context)
            text = transformer(raw_text, 'text/plain')

        return text

    def get_field_value(self, attribute, context=None):
        country_folder = context

        if not context:
            country_folder = self._country_folder

        default = "-"

        if not hasattr(country_folder, attribute):
            return default

        progress = getattr(country_folder, attribute)
        output = getattr(progress, 'output', default)

        return output

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
