from __future__ import absolute_import
from zope.interface import Interface
from zope.schema import Text, TextLine

from plone.supermodel.model import Schema


class IMSRecommendationsFeedback(Interface):
    """ Implements MS response for art 12 recommendations 
    
    /assessment-module/ms-recommendations/be
    """


class IRecommendationStorage(Interface):
    """ Provide storage (as a mapping) for recommendations

    Keys will be the recommendation code
    """


class IComplianceModuleMarker(Interface):
    """ A marker interface for request that happens inside compliance folder
    """


class IComplianceModuleFolder(Interface):
    """ A container that implements the compliance module functionality

    Ex: /assessment-module/
    """


class IMSFDReportingHistoryFolder(Interface):
    """ A container for MSFD reporting history

    /assessment-module/msfd-reporting-history/
    """


class INationalDescriptorsFolder(Interface):
    """ A container for national descriptors assessments

    Ex: /assessment-module/national-descriptors-assessments/
    """


class ICountryDescriptorsFolder(Schema):
    """ A container for a country's descriptor assessments

    Ex: /assessment-module/national-descriptors-assessments/lv/
    """

    title = TextLine(title=u'Title', required=True)


class ICountryStartReports(Interface):
    """ Interface used to override the HTML head title

    Ex: /assessment-module/national-descriptors-assessments/lv/reports
    """


class ICountryStartAssessments(Interface):
    """ Interface used to override the HTML head title

    Ex: /assessment-module/national-descriptors-assessments/lv/assessments
    """


class INationalRegionDescriptorFolder(Interface):
    """ A container for a country's region

    Ex: /assessment-module/national-descriptors-assessments/lv/bal
    """


class IDescriptorFolder(Interface):
    """ Container for individual descriptor article assessments

    Ex: /assessment-module/national-descriptors-assessments/lv/bal/d5
    """


class INationalDescriptorAssessment(Schema):
    """ A Country > Region > Descriptor > Article assessment

    Ex: /assessment-module/national-descriptors-assessments/lv/bal/d5/art8
    """


class INationalDescriptorAssessmentSecondary(Schema):
    """ A Country > Region > Article assessment, used for "secondary"
        articles like Article 3-4, Article 7, Article8ESA

    Ex: /assessment-module/national-descriptors-assessments/lv/bal/art3-4
    """


class ICommentsFolder(Schema):
    """ A container for a track of discussion (comments)

    Ex: /assessment-module/national-descriptors-assessments/lv/bal/d5/art8/tl
    """


class IComment(Schema):
    """ A container for a track of discussion (comments)
    """

    text = Text(title=u'Comment text', required=True)


class IEditAssessmentForm(Interface):
    """ Interface for assessment edit form

    """


class IEditAssessmentFormSecondary(Interface):
    """ Interface for assessment edit form

    """


class IEditAssessmentFormCrossCutting(Interface):
    """ Interface for assessment edit form

    """


class IReportDataView(Interface):
    """ Plone pages that display report data
    """


class IReportDataViewSecondary(Interface):
    """ Plone pages that display report data
    """


class IReportDataViewOverview(Interface):
    """ Plone pages that display report data (overview)
    """


class IRegReportDataViewOverview(Interface):
    """ Plone pages that display regional report data (overview)
    """


class IEditAssessorsForm(Interface):
    """ Interface for assessment settings form

    Ex: /assessment-module/national-descriptors-assessments/edit-assessors
    """

    assessed_by = Text(
        title=u'Edit assessors list',
        required=False,
        default=u'Assessor1\r\nAssessor2'
    )


# Interfaces for Regional descriptors section

class IRegionalReportDataView(Interface):
    """ Interface for regional descriptors report data views
    """


class IRegionalDescriptorsFolder(Interface):
    """ A container for regional descriptors

    Ex: /assessment-module/regional-descriptors-assessments
    """


class IRegionalDescriptorRegionsFolder(Interface):
    """ A container for a regions descriptors

    Ex: /assessment-module/regional-descriptors-assessments/bal
    """


class IRegionStartReports(Interface):
    """ /assessment-module/regional-descriptors-assessments/bal/reports
    """


class IRegionStartAssessments(Interface):
    """ /assessment-module/regional-descriptors-assessments/bal/assessments
    """


class IRegionalDescriptorAssessment(Schema):
    """ A Region > Descriptor > Article assessment

    Ex: /assessment-module/regional-descriptors-assessments/bal/d5/art8
    """


class IRegionalEditAssessmentForm(Interface):
    """ /assessment-module/regional-descriptors-assessments/bal/d6/art8/
        /@@edit-assessment-data-2018
    """


# Interfaces for National summaries section

class INationalSummaryFolder(Interface):
    """ A container for national summaries

    Ex: /assessment-module/national-summaries
    """


class INationalSummaryEdit(Interface):
    """ A container for national summaries edit

    Ex: /assessment-module/national-summaries
    """


class INationalSummaryCountryFolder(Interface):
    """ A container for national summaries countries

    Ex: /assessment-module/national-summaries/lv
    """


class INationalSummaryOverviewFolder(Interface):
    """ A container for national summaries overview

        Ex: /assessment-module/national-summaries/lv/overview
        """


# Interfaces for Regional summaries

class IRegionalSummaryFolder(Interface):
    """ A container for regional summaries

    Ex: /assessment-module/regional-summaries
    """


class IRegionalSummaryRegionFolder(Interface):
    """ A container for regional summaries regions

    Ex: /assessment-module/regional-summaries/bal
    """


class IRegionalSummaryOverviewFolder(Interface):
    """ A container for regional overview pages

    /assessment-module/regional-summaries/bal/overview
    """