from zope.interface import implements

from plone.dexterity.content import Container

from .interfaces import INationalDescriptorAssessment


class NationalDescriptorAssessment(Container):
    """ Assessment implementation for national descriptor assessments
    """
    implements(INationalDescriptorAssessment)
