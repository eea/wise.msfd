from zope.interface import Interface
from zope.schema import Text, TextLine

from plone.supermodel.model import Schema


class IComplianceModuleFolder(Interface):
    """ A container that implements the compliance module functionality

    Ex: /compliance-module/
    """


class INationalDescriptorsFolder(Interface):
    """ A container for national descriptors assessments

    Ex: /compliance-module/national-descriptors-assessments/
    """


class ICountryDescriptorsFolder(Schema):
    """ A container for a country's descriptor assessments

    Ex: /compliance-module/national-descriptors-assessments/lv/
    """

    title = TextLine(title=u'Title', required=True)


class INationalRegionDescriptorFolder(Interface):
    """ A container for a country's region

    Ex: /compliance-module/national-descriptors-assessments/lv/bal
    """


class IDescriptorFolder(Interface):
    """ Container for individual descriptor article assessments

    Ex: /compliance-module/national-descriptors-assessments/lv/bal/d5
    """


class INationalDescriptorAssessment(Schema):
    """ A Country > Descriptor > Article assessment

    Ex: /compliance-module/national-descriptors-assessments/lv/bal/d5/art8
    """


class ICommentsFolder(Schema):
    """ A container for a track of discussion (comments)

    Ex: /compliance-module/national-descriptors-assessments/lv/bal/d5/art8/tl
    """


class IComment(Schema):
    """ A container for a track of discussion (comments)
    """

    text = Text(title=u'Comment text', required=True)


class IRegionalDescriptorsFolder(Interface):
    """ A container for national descriptors assessments
    """


class IReportDataView(Interface):
    """ Plone pages that display report data
    """
