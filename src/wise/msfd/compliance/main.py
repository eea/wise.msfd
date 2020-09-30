# -*- coding: utf-8 -*-

from zope.annotation.factory import factory
from zope.component import adapter
from zope.interface import implementer

from BTrees.OOBTree import OOBTree
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from persistent import Persistent
from plone.api import portal

from wise.msfd.gescomponents import GES_DESCRIPTORS

from .base import BaseComplianceView
from .interfaces import IRecommendationStorage
# from itertools import chain

ANNOTATION_KEY = 'wise.msfd.recommendations'

class StartComplianceView(BaseComplianceView):
    name = 'comp-start'


class DescriptorsView(BaseComplianceView):
    name = 'comp-start'

    @property
    def descriptors(self):
        return GES_DESCRIPTORS


@implementer(IRecommendationStorage)
@adapter(IPloneSiteRoot)
class RecommendationStorage(OOBTree):
    pass


annotfactory_rec = factory(RecommendationStorage, key=ANNOTATION_KEY)


class Recommendation(Persistent):
    def __init__(self, code, topic, text, ms_region, descriptors):
        self.code = code
        self.topic = topic
        self.text = text

        if not hasattr(ms_region,  '__iter__'):
            ms_region = [ms_region]

        self.ms_region = ms_region

        if not hasattr(descriptors, '__iter__'):
            descriptors = [descriptors]

        self.descriptors = descriptors

    def data_to_list(self):
        return [
            self.code,
            self.topic,
            self.text,
            ', '.join(self.ms_region),
            ', '.join(self.descriptors)
        ]


class RecommendationsView(BaseComplianceView):
    name = 'recommendation'
    section = 'compliance-admin'
    storage_key = 'recommendations'

    topics = (
        'Allocation of species to species groups'
        'Assess progress with targets',
        'Assessment methodology',
        'Assessment scales/areas',
        'Coherence of extent to which GES is achieved',
        'Coherent assessment methodology',
        'Coherent qualitative GES description',
        'Coherent quantitative GES determination',
        'Coherent set of elements',
        'Coherent use of secondary criteria',
        'Extent to which GES is achieved',
        'Features and elements assessed',
        'Good status based on low risk',
        'Guidance on good status based on low risk',
        'Guidance on quantitative GES determination',
        'Integrated MSFD and Birds Directive assessments',
        'Key pressures in (sub)region',
        'Key pressures preventing GES',
        'Link target to direct measures',
        'Lists of parameters and units for reporting',
        'Measurable joint targets',
        'Measurable targets',
        '(Sub)regional targets',
        'Qualitative GES description',
        'Quantify gap to GES',
        'Quantitative GES determination',
        'Targets for key pressures',
        'Use of primary criteria',
    )

    def __call__(self):
        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(self.storage_key, None)

        if not storage_recom:
            storage_recom = OOBTree()
            storage[self.storage_key] = storage_recom

        if 'add-recommendation' in self.request.form:
            form_data = self.request.form

            code = form_data.get('rec_code', '')
            topic = form_data.get('topic', '')
            text = form_data.get('rec_text', '')
            ms_region = form_data.get('ms_or_region', [])
            descriptors = form_data.get('descriptors', [])

            recom = Recommendation(code, topic, text, ms_region, descriptors)
            storage_recom[code] = recom

        # recommendations = {
        #     'Art09/2018/MS/Rec01': [
        #         'Use of primary criteria',
        #         'Provide a qualitative GES description, or an adequate justification for non-use together with which other Member States were informed of its non-use and when, for all primary criteria.',
        #         'FI, EE, PL, SE',
        #         'D1B, D1M, D1F, D3, D6'
        #     ]
        # }

        recommendations = []

        if len(storage_recom.items()):
            for code, recommendation in storage_recom.items():
                try:
                    recommendations.append(recommendation.data_to_list())
                except:
                    import pdb; pdb.set_trace()

        sorted_rec = sorted(recommendations, key=lambda i: i[0])

        return self.index(recommendations=sorted_rec)


class ViewComplianceModule(BaseComplianceView):
    # name = 'comp-start2'

    @property
    def national_descriptors(self):
        pass

    @property
    def regional_descriptors(self):
        pass

    # def get_folder_by_id(self, id):
    #     folders = [
    #         x.contentValues()
    #
    #         for x in self.context.contentValues()
    #
    #         if x.portal_type == 'Folder'
    #         and x.id == id
    #     ]
    #     folders = [f for f in chain(*folders)]
    #
    #     return folders
    #
    # @property
    # def regional_descriptors_folders(self):
    #     id = 'regional-descriptors-assessments'
    #     folders = self.get_folder_by_id(id)
    #
    #     return folders
    #
    # @property
    # def national_descriptors_folders(self):
    #     id = 'national-descriptors-assessments'
    #     folders = self.get_folder_by_id(id)
    #
    #     return folders
