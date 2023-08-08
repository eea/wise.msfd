from __future__ import absolute_import
from zope.interface import Attribute, Interface
from zope.schema import Choice, List  # Int, Text, TextLine
from plone.supermodel import model
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider
from zope.schema import Text

class IMainForm(Interface):
    """ A marker interface to easily identify main forms
    """


class IEmbeddedForm(Interface):
    """ A form that is "embeded" in another form
    """

    def extras():
        """ Return extra-html to show after the main data
        """


class IMarineUnitIDSelect(Interface):
    marine_unit_id = Choice(
        title=u"MarineUnitID",
        # description=u"Select one or more MarineUnitIDs that you're
        # interested",
        required=True,
        vocabulary="wise_search_marine_unit_id"
    )


class IMarineUnitIDsSelect(Interface):
    marine_unit_ids = List(
        title=u"MarineUnitID",
        # description=u"Select one or more MarineUnitIDs that you're
        # interested",
        value_type=Choice(vocabulary="wise_search_marine_unit_ids"),
        required=False
    )


@provider(IFormFieldProvider)
class ISPMeasureFields(model.Schema):
    """Fields for SPMeasure """

    sector = List(title=u"Sector", description=u"", required=False)
    use = List(title=u"Use or activity", description=u"", required=False)
    origin = List(title=u"Origin of the measure",
                  description=u"", required=False)
    nature = List(title=u"Nature of the measure",
                  description=u"", required=False)
    status = List(title=u"Status", description=u"", required=False)
    impacts = List(title=u"Measure impacts to",
                   description=u"", required=False)
    impacts_further_details = List(
        title=u"Measure impacts to, further details", description=u"", required=False)
    water_body_cat = List(title=u"Water body category",
                          description=u"", required=False)
    spatial_scope = List(title=u"Spatial scope",
                         description=u"", required=False)
    country_coverage = List(title=u"Country coverage",
                            description=u"", required=False)

    # Further info
    measure_purpose = List(title=u"Measure purpose",
                           description=u"", required=False)
    measure_type = List(title=u"Measure type", description=u"", required=False)
    measure_location = List(title=u"Measure location",
                            description=u"", required=False)
    measure_response = List(title=u"Measure response",
                            description=u"", required=False)
    measure_additional_info = List(
        title=u"Measure additional info", description=u"", required=False)
    pressure_type = List(title=u"Type of pressure",
                         description=u"", required=False)
    pressure_name = List(title=u"Pressure name",
                         description=u"", required=False)
    ranking = List(title=u"Ranking", description=u"", required=False)
    season = List(title=u"Season", description=u"", required=False)
