# -*- coding: utf-8 -*-

from datetime import datetime
from io import BytesIO

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.api import portal
from plone.z3cform.layout import wrap_form
from zope.schema import Choice, Text
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from wise.msfd.base import EmbeddedForm, MainFormWrapper
from wise.msfd.compliance.vocabulary import get_regions_for_country
from wise.msfd.gescomponents import get_all_descriptors, get_descriptor
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
        return [('EU', 'All subregions')] + country_regions

    def recommendation_needed(self, region_code, recom_regions):
        """ identify all recommendations for a single country """

        if 'EU' in recom_regions:
            return True

        if region_code in recom_regions:
            return True

        # if set(self.region_codes).intersection(set(recom_regions)):
        #     return True

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
    def descriptors(self):
        descriptors = get_all_descriptors()
        descriptors.pop(0)  # remove D1 general descriptor

        res = []

        for desc in descriptors:
            desc_obj = get_descriptor(desc[0])

            res.append((desc_obj.template_vars['title'], desc_obj.title))

        return res
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
        
        
        for code, recommendation in storage_recom.items():
            for region_code, region_title in self.region_codes:
                is_needed = self.recommendation_needed(
                    region_code, recommendation.ms_region)
                
                if not is_needed:
                    continue

                form = EmbeddedForm(self, self.request)
                fields = []  # descriptors

                for descr_code, descr_title in self.descriptors:
                    if descr_code not in recommendation.descriptors:
                        continue

                    field = Choice(
                        title=unicode(descr_code),
                        __name__="{}_{}_{}".format(
                            code, descr_code, region_code),
                        vocabulary=SimpleVocabulary(terms),
                        required=False,
                        default=default,
                    )
                    # field._criteria = criteria
                    fields.append(field)

                text_field = Text(
                        title=u'Comments on recommendation',
                        __name__="{}_{}_{}_comment".format(
                            code, descr_code, region_code), 
                        required=False, 
                        default=None
                    )

                fields.append(text_field)

                form.fields = Fields(*fields)
                form.recommendation = recommendation
                form.region = region_code
                forms.append(form)

        return forms

    def get_subforms_for_region(self, region):
        res = []

        for subform in self.subforms:
            if region == subform.region:
                res.append(subform)

            # ms_regions = subform.recommendation.ms_region
            
            # if region in ms_regions:
            #     res.append(subform)
            #     continue

            # for ms_region in ms_regions:
            #     _region = ms_region.split(' - ')

            #     if region == _region[0]:
            #         res.append(subform)

        return res


    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        data, errors = self.extractData()

        # import pdb; pdb.set_trace()


# MSRecommendationsEditFormView = wrap_form(MSRecommendationsEditForm, MainFormWrapper)