from collections import Counter, defaultdict, namedtuple
from itertools import chain

from plone.api.content import get_state
from plone.api.portal import get_tool
from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from wise.msfd.gescomponents import FEATURES_DB_2018, THEMES_2018_ORDER
from wise.msfd.labels import get_label
from wise.msfd.translation import get_detected_lang
from wise.msfd.utils import fixedorder_sortkey, ItemLabel

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

    not_rep = u""
    rep = u"Reported"

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

    # def translate_value(self, fieldname, value, source_lang):
    #     is_translatable = fieldname in self.TRANSLATABLES
    #
    #     v = self.translate_view()
    #
    #     if not is_translatable:
    #         return v.cell_tpl(value=value)
    #
    #     if not value:
    #         return v.cell_tpl(value=value)
    #
    #     text = value[0]
    #     translation = value[1] or ''
    #
    #     if get_detected_lang(text) == 'en' or not translation:
    #         return v.cell_tpl(value=text)
    #
    #     return v.translate_tpl(text=text,
    #                            translation=translation,
    #                            can_translate=False,
    #                            source_lang=source_lang)
