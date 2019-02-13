from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.base import BaseComplianceView

from .data import REPORT_DEFS


class BaseView(BaseComplianceView):
    """ Base view specific to national descriptor pages
    """

    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        'pt/assessment-header.pt'
    )

    @property
    def TRANSLATABLES(self):
        # for 2018, returns a list of field names that are translatable

        if self._translatables:
            return self._translatables

        year = REPORT_DEFS[self.year]

        if self.article in year:
            return year[self.article].get_translatable_fields()

        self._translatables = []

        return self._translatables

    @TRANSLATABLES.setter
    def set_translatables(self, v):
        self._translatables = v
