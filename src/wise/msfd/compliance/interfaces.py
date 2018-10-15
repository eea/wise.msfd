from zope.interface import Interface

from plone.supermodel.model import Schema


class IComplianceModuleFolder(Interface):
    """ A container that implements the compliance module functionality
    """


class INationalDescriptorsFolder(Interface):
    """ A container for national descriptors assessments
    """


class ICountryDescriptorsFolder(Interface):
    """ A container for a country's descriptor assessments
    """


class IDescriptorFolder(Interface):
    """ Container for individual descriptor article assessments
    """


class INationalDescriptorAssessment(Schema):
    """ A Country > Descriptor > Article assessment
    """
