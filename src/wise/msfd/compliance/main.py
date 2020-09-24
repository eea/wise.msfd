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
    """"""

    def __call__(self):

        return self.index()

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
