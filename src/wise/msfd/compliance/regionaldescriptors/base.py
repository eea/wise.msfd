from collections import namedtuple

from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONS

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces
from .utils import compoundrow

COUNTRY = namedtuple("Country", ["id", "title", "definition", "is_primary"])


class BaseRegComplianceView(BaseComplianceView):
    # TODO is this used? delete if not
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
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

    def get_available_countries(self):
        res = [
            COUNTRY(x[0], x[1], "", lambda _: True)
            for x in self.available_countries
        ]

        return res


class BaseRegDescRow(object):
    not_rep = u""
    rep = u"Reported"

    def __init__(self, context, request, db_data, descriptor_obj,
                 region, countries, field):
        self.context = context
        self.request = request
        self.db_data = db_data
        self.descriptor_obj = descriptor_obj
        self.region = region
        self.countries = countries
        self.field = field

    def get_unique_values(self, field):
        values = set([
            getattr(row, field)
            for row in self.db_data
            if getattr(row, field)
        ])

        return sorted(values)

    @compoundrow
    def get_countries_row(self):
        rows = []
        country_names = [x[1] for x in self.context.available_countries]
        rows.append(('', country_names))

        return rows

    @compoundrow
    def get_mru_row(self):
        rows = []
        values = []
        for country_code, country_name in self.countries:
            value = set([
                row.MarineReportingUnit
                for row in self.db_data
                if row.CountryCode == country_code
            ])
            values.append(len(value))

        rows.append((u'Number used', values))

        return rows

    @compoundrow
    def get_feature_row(self):
        rows = []
        features = self.get_unique_values("Features")
        all_features = []
        for feat in features:
            all_features.extend(feat.split(','))

        for feature in set(all_features):
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                        and row.Features
                        and feature in row.Features.split(',')
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            rows.append((feature, values))

        return rows
