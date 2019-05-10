from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.utils import CompoundRow, Row

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


class BaseRegDescRow(object):
    not_rep = u""
    rep = u"Reported"

    def __init__(self, db_data, descriptor_obj, region, countries, field):
        self.db_data = db_data
        self.descriptor_obj = descriptor_obj
        self.region = region
        self.countries = countries
        self.field = field

    def get_mru_row(self):
        values = []
        for country_code, country_name in self.countries:
            value = set([
                row.MarineReportingUnit
                for row in self.db_data
                if row.CountryCode == country_code
            ])
            values.append(len(value))

        row = Row('Number used', values)

        return CompoundRow(self.field.title, [row])

    def get_feature_row(self):
        rows = []
        features = ("Get feature!", )

        for feature in features:
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            row = Row(feature, values)
            rows.append(row)

        return CompoundRow(self.field.title, rows)
