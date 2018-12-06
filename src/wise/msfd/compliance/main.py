# -*- coding: utf-8 -*-

from wise.msfd.gescomponents import GES_DESCRIPTORS

from .base import BaseComplianceView


class StartComplianceView(BaseComplianceView):
    name = 'comp-start'


class DescriptorsView(BaseComplianceView):
    name = 'comp-start'

    @property
    def descriptors(self):
        return GES_DESCRIPTORS
