#pylint: skip-file
from __future__ import absolute_import
from zope.interface import implements, implementer

from persistent.list import PersistentList
from plone.dexterity.content import Container

from .interfaces import (ICountryDescriptorsFolder,
                         IMSFDReportingHistoryFolder,
                         IMSRecommendationsFeedback,
                         INationalDescriptorAssessment,
                         INationalSummaryCountryFolder,
                         INationalSummaryEdit,
                         INationalSummaryOverviewFolder,
                         INationalSummary2022Folder,
                         IRegionalDescriptorAssessment,
                         IRegionalDescriptorRegionsFolder,
                         IRegionalSummaryRegionFolder,
                         IRegionalSummaryOverviewFolder)


@implementer(IMSRecommendationsFeedback)
class MSRecommendationsFeedback(Container):
    """ Implementation for MS response for art 12 recommendation """

    # implements(IMSRecommendationsFeedback)


@implementer(IMSFDReportingHistoryFolder)
class MSFDReportingHistoryFolder(Container):
    """ MSFD Reporting history folder
    """
    # implements(IMSFDReportingHistoryFolder)


@implementer(ICountryDescriptorsFolder)
class CountryDescriptorsFolder(Container):
    """ Assessment implementation for national descriptor assessments
    """
    # implements(ICountryDescriptorsFolder)


@implementer(IRegionalDescriptorRegionsFolder)
class RegionDescriptorsFolder(Container):
    """ Assessment implementation for regional descriptor assessments
    """
    # implements(IRegionalDescriptorRegionsFolder)


@implementer(INationalSummaryCountryFolder)
class NationalSummaryCountryFolder(Container):
    """ Assessment implementation for national summary assessments
    """
    # implements(INationalSummaryCountryFolder)


@implementer(INationalSummary2022Folder)
class NationalSummary2022Folder(Container):
    """ Assessment implementation for national summary assessments
    """
    # implements(INationalSummaryCountryFolder)


@implementer(INationalSummaryEdit)
class NationalSummaryEditFolder(Container):
    """ Implementation for national summary assessments edit page
    """
    # implements(INationalSummaryEdit)


@implementer(INationalSummaryOverviewFolder)
class NationalSummaryOverviewFolder(Container):
    """ Assessment implementation for national summary assessments
    """
    # implements(INationalSummaryOverviewFolder)


@implementer(IRegionalSummaryRegionFolder)
class RegionalSummaryRegionFolder(Container):
    """ Assessment implementation for regional summary assessments
    """
    # implements(IRegionalSummaryRegionFolder)


@implementer(IRegionalSummaryOverviewFolder)
class RegionalSummaryOverviewFolder(Container):
    """ implementation for regional overview page
    """
    # implements(IRegionalSummaryOverviewFolder)


@implementer(INationalDescriptorAssessment)
class NationalDescriptorAssessment(Container):
    """ Assessment implementation for national descriptor assessments
    """

    # implements(INationalDescriptorAssessment)
    _data = None

    def _get_assessment_data(self):
        return self._data or {}

    def _set_assessment_data(self, value):
        self._data = value
        self._p_changed = True

    assessment_data = property(_get_assessment_data, _set_assessment_data)

    @property
    def assessment_summary(self):
        art = self.getId().capitalize()
        data = self.assessment_data

        return data.get('{}_assessment_summary'.format(art), '')


@implementer(IRegionalDescriptorAssessment)
class RegionalDescriptorAssessment(Container):
    """ Assessment implementation for regional descriptor assessments
    """

    # implements(IRegionalDescriptorAssessment)
    _data = None

    def _get_assessment_data(self):
        return self._data or {}

    def _set_assessment_data(self, value):
        self._data = value
        self._p_changed = True

    assessment_data = property(_get_assessment_data, _set_assessment_data)

    @property
    def assessment_summary(self):
        art = self.getId().capitalize()
        data = self.assessment_data

        return data.get('{}_assessment_summary'.format(art), '')


class AssessmentData(PersistentList):

    # data = []       # TODO: why is this? This needs to be migrated

    @property
    def assessors(self):
        if not self:
            return 'Not assessed'

        assessors = set()

        for data in self:
            assessor = data.get('assessor')

            if assessor is None:
                continue
                # raise ValueError('No assessor in data')

            assessors.add(assessor)

        if not assessors:
            return 'Not assessed'

        return ', '.join(assessors)

    def _append(self, data):
        # self.data.append(data)
        self.append(data)

        self._p_changed = True

    # def last(self):
    #     if not self.data:
    #         return {}
    #
    #     return self.data[-1]

    def last(self):
        if not self:
            return {}

        return self[-1]
