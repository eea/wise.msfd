from zope.interface import implements

from persistent.list import PersistentList
from plone.dexterity.content import Container

from .interfaces import (ICountryDescriptorsFolder,
                         IMSFDReportingHistoryFolder,
                         INationalDescriptorAssessment,
                         INationalSummaryCountryFolder,
                         INationalSummaryEdit,
                         INationalSummaryOverviewFolder,
                         IRegionalDescriptorAssessment,
                         IRegionalDescriptorRegionsFolder,
                         IRegionalSummaryRegionFolder)


class MSFDReportingHistoryFolder(Container):
    """ MSFD Reporting history folder
    """
    implements(IMSFDReportingHistoryFolder)


class CountryDescriptorsFolder(Container):
    """ Assessment implementation for national descriptor assessments
    """
    implements(ICountryDescriptorsFolder)


class RegionDescriptorsFolder(Container):
    """ Assessment implementation for regional descriptor assessments
    """
    implements(IRegionalDescriptorRegionsFolder)


class NationalSummaryCountryFolder(Container):
    """ Assessment implementation for national summary assessments
    """
    implements(INationalSummaryCountryFolder)


class NationalSummaryEditFolder(Container):
    """ Implementation for national summary assessments edit page
    """
    implements(INationalSummaryEdit)


class NationalSummaryOverviewFolder(Container):
    """ Assessment implementation for national summary assessments
    """
    implements(INationalSummaryOverviewFolder)


class RegionalSummaryRegionFolder(Container):
    """ Assessment implementation for regional summary assessments
    """
    implements(IRegionalSummaryRegionFolder)


class NationalDescriptorAssessment(Container):
    """ Assessment implementation for national descriptor assessments
    """

    implements(INationalDescriptorAssessment)
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


class RegionalDescriptorAssessment(Container):
    """ Assessment implementation for regional descriptor assessments
    """

    implements(IRegionalDescriptorAssessment)
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
