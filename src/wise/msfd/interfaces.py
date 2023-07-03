from __future__ import absolute_import
from zope.interface import Attribute, Interface
from zope.schema import Choice, List  # Int, Text, TextLine
from plone.supermodel import model
from plone.autoform.interfaces import IFormFieldProvider
from zope.schema import Text

# from plone.app.textfield import RichText


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

    measure_name = Text(title=u"Measure name", description=u"", required=False)
    sector = Text(title=u"Sector", description=u"", required=False)
    use = Text(title=u"Use or activity", description=u"", required=False)
    origin = Text(title=u"Origin of the measure",
                  description=u"", required=False)
    nature = Text(title=u"Nature of the measure",
                  description=u"", required=False)
    status = Text(title=u"Status", description=u"", required=False)
    impacts = Text(title=u"Measure impacts to",
                   description=u"", required=False)
    impacts_further_details = Text(
        title=u"Measure impacts to, further details", description=u"", required=False)
    water_body_cat = Text(title=u"Water body category",
                          description=u"", required=False)
    spatial_scope = Text(title=u"Spatial scope",
                         description=u"", required=False)
    country_coverage = Text(title=u"Country coverage",
                            description=u"", required=False)

    # Further info
    measure_purpose = Text(title=u"Measure purpose",
                           description=u"", required=False)
    measure_type = Text(title=u"Measure type", description=u"", required=False)
    measure_location = Text(title=u"Measure location",
                            description=u"", required=False)
    measure_response = Text(title=u"Measure response",
                            description=u"", required=False)
    measure_additional_info = Text(
        title=u"Measure additional info", description=u"", required=False)
    pressure_type = Text(title=u"Type of pressure",
                         description=u"", required=False)
    pressure_name = Text(title=u"Pressure name",
                         description=u"", required=False)
    ranking = Text(title=u"Ranking", description=u"", required=False)
    season = Text(title=u"Season", description=u"", required=False)
