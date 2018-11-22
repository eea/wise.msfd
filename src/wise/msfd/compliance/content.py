from zope.interface import implements

from plone.dexterity.content import Container

from .interfaces import (ICountryDescriptorsFolder,
                         INationalDescriptorAssessment)


class CountryDescriptorsFolder(Container):
    """ Assessment implementation for national descriptor assessments
    """
    implements(ICountryDescriptorsFolder)


# class NationalRegionFolder(Container):
#     """
#     """
#     implements(INationalRegionFolder)


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
