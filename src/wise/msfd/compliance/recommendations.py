# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.api import portal
from plone.z3cform.layout import wrap_form
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from wise.msfd.base import EmbeddedForm, MainFormWrapper
from wise.msfd.compliance.vocabulary import get_regions_for_country

from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .base import BaseComplianceView
from .interfaces import IRecommendationStorage
from .nationaldescriptors.base import BaseView
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


class MSRecommendationsEditForm(BaseView, Form):
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

    @property
    def fields(self):
        if not self.subforms:
            self.subforms = self.get_subforms()

        fields = []

        for subform in self.subforms:
            fields.extend(subform.fields._data_values)

        return Fields(*fields)

    def get_subforms(self):
        # recommendation attributes: code, topic, text, ms_region [], descriptors []
        choices = (u'By 2024', u'After 2024', u'No action')
        terms = [
            SimpleTerm(token=i, value=c, title=c) 
            for i, c in enumerate(choices)
        ]
        default = u'By 2024'
        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, None)
        forms = []
        
        descriptors = [u'D2', u'D5', u'D6']

        for code, recommendation in storage_recom.items():
            # is_needed = self.recommendation_needed(
            #     region, recommendation.ms_region)

            is_needed = True

            if is_needed:
                form = EmbeddedForm(self, self.request)
                fields = []  # descriptors

                for descr in descriptors:
                    field = Choice(
                        title=descr,
                        __name__="{}_{}".format(code, descr),
                        vocabulary=SimpleVocabulary(terms),
                        required=False,
                        default=default,
                    )
                    # field._criteria = criteria
                    fields.append(field)

                form.fields = Fields(*fields)
                form.recommendation = recommendation
                forms.append(form)

        return forms

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        return "todo"


# MSRecommendationsEditFormView = wrap_form(MSRecommendationsEditForm, MainFormWrapper)