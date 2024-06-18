#pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.interfaces import ICountryDescriptorsFolder


class BaseView(BaseComplianceView):
    """ Base view specific to national descriptor pages
    """

    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
    )

    @property
    def current_phase(self):
        country_folder = self.get_parent_by_iface(ICountryDescriptorsFolder)
        state, title = self.process_phase(country_folder)

        return state, title

    @property
    def TRANSLATABLES(self):
        # for 2018, returns a list of field names that are translatable
        if self._translatables:
            return self._translatables

        translatables = self.get_report_translatable_fields()

        if translatables:
            return translatables

        self._translatables = []

        return self._translatables

    @TRANSLATABLES.setter
    def set_translatables(self, v):
        self._translatables = v
