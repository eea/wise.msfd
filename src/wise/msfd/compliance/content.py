from zope.interface import implements

from plone.dexterity.content import Container

from .interfaces import (ICountryDescriptorsFolder,
                         INationalDescriptorAssessment)


class CountryDescriptorsFolder(Container):
    """ Assessment implementation for national descriptor assessments
    """
    implements(ICountryDescriptorsFolder)


class NationalDescriptorAssessment(Container):
    """ Assessment implementation for national descriptor assessments
    """
    implements(INationalDescriptorAssessment)
