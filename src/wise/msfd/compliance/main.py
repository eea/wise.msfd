# -*- coding: utf-8 -*-

from wise.msfd.gescomponents import GES_DESCRIPTORS

from .base import BaseComplianceView

# from itertools import chain


class StartComplianceView(BaseComplianceView):
    name = 'comp-start'


class DescriptorsView(BaseComplianceView):
    name = 'comp-start'

    @property
    def descriptors(self):
        return GES_DESCRIPTORS


class RecommendationsView(BaseComplianceView):
    name = 'recommendation'
    section = 'compliance-admin'

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
        if 'add-recommendation' in self.request.form:
            form_data = self.request.form

            import pdb; pdb.set_trace()

        recommendations = {
            'Art09/2018/MS/Rec01': [
                'Use of primary criteria',
                'Provide a qualitative GES description, or an adequate justification for non-use together with which other Member States were informed of its non-use and when, for all primary criteria.',
                'FI, EE, PL, SE',
                'D1B, D1M, D1F, D3, D6'
            ]
        }

        return self.index(recommendations=recommendations)


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
