# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.api import portal
from plone.z3cform.layout import wrap_form

from wise.msfd.base import MainFormWrapper
from wise.msfd.compliance.vocabulary import get_regions_for_country

from .base import BaseComplianceView
from .interfaces import IRecommendationStorage
from .nationaldescriptors.main import CountryStatus


RECOMMENDATION_ANNOTATION_KEY = 'wise.msfd.recommendations'
STORAGE_KEY = 'recommendations'
TOPICS_STORAGE_KEY = '__topics__'


class MSRecommendationsStart(BaseComplianceView):
    section = 'national-descriptors'

    def countries(self):
        countries = self.context.contentValues()
        res = []

        for country in countries:

            state_id, state_label = self.process_phase(country)
            info = CountryStatus(country.id.upper(), country.Title(),
                                 state_label, state_id, country.absolute_url())

            res.append(info)

        return res


class MSRecommendationsEditForm(BaseComplianceView):
    """ Edit the assessment for a national descriptor, for a specific article
    """
    name = 'art-view'
    section = 'national-descriptors'

    subforms = None
    year = session_name = '2018'
    template = ViewPageTemplateFile("./pt/ms-recommendations-edit.pt")
    _questions = []  # recommendations

    @property
    def country_code(self):
        return self.context.id.upper()

    @property
    def region_codes(self):
        country_regions = get_regions_for_country(self.country_code)
        # region_codes = [x[0] for x in country_regions]

        return country_regions

    def recommendation_needed(self, region_code, recom_regions):
        if 'EU' in recom_regions:
            return True

        if region_code in recom_regions:
            return True

        for recom_region in recom_regions:
            if '-' not in recom_region:
                continue

            _region, _ccode = recom_region.split(' - ')

            if _ccode != self.country_code:
                continue

            if _region != region_code:
                continue

            return True

        return False

    def get_recommendations_by_region(self, region):
        # recommendation attributes: code, topic, text, ms_region [], descriptors []

        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, None)
        recommendations = []
        
        for code, recommendation in storage_recom.items():
            is_needed = self.recommendation_needed(
                region, recommendation.ms_region)

            if is_needed:
                # TODO filter by region
                recommendations.append(recommendation)

        return recommendations

    def __call__(self):
        return self.template()


# MSRecommendationsEditFormView = wrap_form(MSRecommendationsEditForm, MainFormWrapper)