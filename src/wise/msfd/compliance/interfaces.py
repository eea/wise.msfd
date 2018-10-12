from zope.interface import Interface


class IComplianceModule(Interface):
    """ A container that implements the compliance module functionality
    """


class INationalDescriptors(Interface):
    """ A container for national descriptors
    """


class ICountryDescriptors(Interface):
    """ A container for a country's descriptor assessments
    """

