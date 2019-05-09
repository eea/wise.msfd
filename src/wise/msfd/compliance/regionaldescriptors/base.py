from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONS

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces


class BaseRegComplianceView(BaseComplianceView):
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        'pt/assessment-header.pt'
    )

    section = 'regional-descriptors'

    @property
    def _countryregion_folder(self):
        return self.get_parent_by_iface(
            interfaces.IRegionalDescriptorRegionsFolder
        )

    @property
    def _article_assessment(self):
        return self.get_parent_by_iface(
            interfaces.IRegionalDescriptorAssessment
        )

    @property
    def region_name(self):
        return REGIONS[self.country_region_code]

    @property
    def available_countries(self):
        return self._countryregion_folder._countries_for_region