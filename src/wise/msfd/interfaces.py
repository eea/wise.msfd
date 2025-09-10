# pylint: skip-file
from __future__ import absolute_import
from zope.interface import Interface, provider
from zope.schema import Choice, Date, List, Set, Text  # Int, TextLine
from plone.supermodel import model
from plone.autoform.interfaces import IFormFieldProvider


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
    """IMarineUnitIDSelect"""
    marine_unit_id = Choice(
        title=u"MarineUnitID",
        # description=u"Select one or more MarineUnitIDs that you're
        # interested",
        required=True,
        vocabulary="wise_search_marine_unit_id"
    )


class IMarineUnitIDsSelect(Interface):
    """IMarineUnitIDsSelect"""
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
    code = Text(title=u"Code", description=u"", required=False)

    origin = List(title=u"Origin of the measure",
                  description=u"", required=False)
    nature = List(title=u"Nature of the measure",
                  description=u"", required=False)
    status = List(title=u"Status", description=u"", required=False)
    impacts = List(title=u"Measure impacts to",
                   description=u"", required=False)
    impacts_further_details = List(
        title=u"Measure impacts to, further details", description=u"",
        required=False)
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
    approaching_areas = List(title=u"Approaching Areas",
                             description=u"", required=False)
    areas_to_be_avoided = List(
        title=u"Areas To Be Avoided", description=u"", required=False)
    descriptors = List(title=u"Descriptors", description=u"", required=False)
    ecological_impacts = List(
        title=u"Ecological Impacts", description=u"", required=False)
    future_scenarios = List(title=u"Future Scenarios",
                            description=u"", required=False)
    effect_on_hydromorphology = List(
        title=u"Effect On Hydromorphology", description=u"", required=False)
    ktms_it_links_to = List(title=u"Ktms It Links To",
                            description=u"", required=False)
    links_to_existing_policies = List(
        title=u"Links To Existing Policies", description=u"", required=False)
    msfd_spatial_scope = List(
        title=u"Msfd Spatial Scope", description=u"", required=False)
    mspd_implementation_status = List(
        title=u"Mspd Implementation Status", description=u"", required=False)
    nature_of_physical_modification = List(
        title=u"Nature Of Physical Modification", description=u"",
        required=False)
    source = List(title=u"Source", description=u"", required=False)
    authority = List(title=u"Authority", description=u"", required=False)
    general_view = List(title=u"General View", description=u"", required=False)
    ports = List(title=u"Ports", description=u"", required=False)
    future_expectations = List(
        title=u"Future Expectations", description=u"", required=False)
    safety_manner = List(title=u"Safety Manner",
                         description=u"", required=False)
    objective = List(title=u"Objective", description=u"", required=False)
    categories = List(title=u"Categories", description=u"", required=False)
    precautionary_areas = List(
        title=u"Precautionary Areas", description=u"", required=False)
    priority_areas = List(title=u"Priority Areas",
                          description=u"", required=False)
    relevant_targets = List(title=u"Relevant Targets",
                            description=u"", required=False)
    relevant_features_from_msfd_annex_iii = List(
        title=u"Relevant Features From Msfd Annex Iii", description=u"",
        required=False)
    region = List(title=u"Region", description=u"", required=False)
    shipping_tackled = List(title=u"Shipping Tackled",
                            description=u"", required=False)
    traffic_separation_scheme = List(
        title=u"Traffic Separation Scheme", description=u"", required=False)
    type_of_pressure = List(title=u"Type Of Pressure",
                            description=u"", required=False)
    approaching_areas = List(title=u"Approaching Areas",
                             description=u"", required=False)
    areas_to_be_avoided = List(
        title=u"Areas To Be Avoided", description=u"", required=False)
    descriptors = List(title=u"Descriptors", description=u"", required=False)
    ecological_impacts = List(
        title=u"Ecological Impacts", description=u"", required=False)
    future_scenarios = List(title=u"Future Scenarios",
                            description=u"", required=False)
    effect_on_hydromorphology = List(
        title=u"Effect On Hydromorphology", description=u"", required=False)
    ktms_it_links_to = List(title=u"Ktms It Links To",
                            description=u"", required=False)
    links_to_existing_policies = List(
        title=u"Links To Existing Policies", description=u"", required=False)
    msfd_spatial_scope = List(
        title=u"Msfd Spatial Scope", description=u"", required=False)
    mspd_implementation_status = List(
        title=u"Mspd Implementation Status", description=u"", required=False)
    nature_of_physical_modification = List(
        title=u"Nature Of Physical Modification", description=u"",
        required=False)
    source = List(title=u"Source", description=u"", required=False)
    authority = List(title=u"Authority", description=u"", required=False)
    general_view = List(title=u"General View", description=u"", required=False)
    ports = List(title=u"Ports", description=u"", required=False)
    future_expectations = List(
        title=u"Future Expectations", description=u"", required=False)
    safety_manner = List(title=u"Safety Manner",
                         description=u"", required=False)
    objective = List(title=u"Objective", description=u"", required=False)
    categories = List(title=u"Categories", description=u"", required=False)
    precautionary_areas = List(
        title=u"Precautionary Areas", description=u"", required=False)
    priority_areas = List(title=u"Priority Areas",
                          description=u"", required=False)
    relevant_targets = List(title=u"Relevant Targets",
                            description=u"", required=False)
    relevant_features_from_msfd_annex_iii = List(
        title=u"Relevant Features From Msfd Annex Iii", description=u"",
        required=False)
    region = List(title=u"Region", description=u"", required=False)
    shipping_tackled = List(title=u"Shipping Tackled",
                            description=u"", required=False)
    traffic_separation_scheme = List(
        title=u"Traffic Separation Scheme", description=u"", required=False)
    type_of_pressure = List(title=u"Type Of Pressure",
                            description=u"", required=False)


@provider(IFormFieldProvider)
class IIndicatorMOFields(model.Schema):
    """Fields for indicator_mo content type """

    objective_ds = Set(
        title=u"Objective/enabler", description=u"", required=False)
    target_ds = Set(title=u"Target", description=u"", required=False)
    modification_date = Date(
        title=u"Modified date (indicator)", description=u"", required=False)


@provider(IFormFieldProvider)
class INISFields(model.Schema):
    """Fields for non_indigenous_species content type """

    nis_region = Text(
        title=u"Region", description=u"MSFD Region", required=False)
    nis_subregion = Text(
        title=u"Subregion", description=u"MSFD sub-region", required=False)
    nis_country = List(
        title=u"Country",
        description=u"Select one or more countries",
        required=False,
    )
