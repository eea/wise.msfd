# pylint: skip-file
"""behavior.py"""
import traceback
from plone.app.dexterity.behaviors.metadata import (
    DCFieldProperty, MetadataBase)
from .interfaces import (ISPMeasureFields)
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.component import adapter


@adapter(ISPMeasureFields, IObjectModifiedEvent)
def handle_origin_change(obj, event):
    """handle_origin_change"""
    # List of fields to reset when `origin` changes
    fields_to_reset = [
        'nature_of_physical_modification',
        'effect_on_hydromorphology',
        'ecological_impacts',
        'links_to_existing_policies',
        'ktms_it_links_to',
        'relevant_targets',
        'relevant_features_from_msfd_annex_iii',
        'msfd_spatial_scope',
        'measure_purpose',
        'measure_location',
        'measure_response',
        'measure_additional_info',
        'pressure_type',
        'pressure_name',
        'ranking',
        'region',
        'mspd_implementation_status',
        'shipping_tackled',
        'traffic_separation_scheme',
        'priority_areas',
        'approaching_areas',
        'precautionary_areas',
        'areas_to_be_avoided',
        'future_scenarios',
        'source',
        'authority',
        'general_view',
        'ports',
        'future_expectations',
        'safety_manner',
        'objective',
        'categories'
    ]

    stack = traceback.format_stack()
    if any("collective.exportimport" in s for s in stack):
        return

    # Check if the `origin` field has been changed
    for descriptor in event.descriptions:
        if (descriptor.attributes and
                'ISPMeasureFields.origin' in descriptor.attributes):

            # Reset the fields to empty lists
            for field in fields_to_reset:
                setattr(obj, field, [])

            # Optional: Reindex the object if required
            obj.reindexObject()


class SPMeasureFields(MetadataBase):
    """SPMeasure fields"""

    sector = DCFieldProperty(ISPMeasureFields["sector"])
    code = DCFieldProperty(ISPMeasureFields["code"])
    use = DCFieldProperty(ISPMeasureFields["use"])
    origin = DCFieldProperty(ISPMeasureFields["origin"])
    nature = DCFieldProperty(ISPMeasureFields["nature"])
    status = DCFieldProperty(ISPMeasureFields["status"])
    impacts = DCFieldProperty(ISPMeasureFields["impacts"])
    impacts_further_details = DCFieldProperty(
        ISPMeasureFields["impacts_further_details"])
    water_body_cat = DCFieldProperty(ISPMeasureFields["water_body_cat"])
    spatial_scope = DCFieldProperty(ISPMeasureFields["spatial_scope"])
    country_coverage = DCFieldProperty(ISPMeasureFields["country_coverage"])
    measure_purpose = DCFieldProperty(ISPMeasureFields["measure_purpose"])
    measure_type = DCFieldProperty(ISPMeasureFields["measure_type"])
    measure_location = DCFieldProperty(ISPMeasureFields["measure_location"])
    measure_response = DCFieldProperty(ISPMeasureFields["measure_response"])
    measure_additional_info = DCFieldProperty(
        ISPMeasureFields["measure_additional_info"])
    pressure_type = DCFieldProperty(ISPMeasureFields["pressure_type"])
    pressure_name = DCFieldProperty(ISPMeasureFields["pressure_name"])
    ranking = DCFieldProperty(ISPMeasureFields["ranking"])
    season = DCFieldProperty(ISPMeasureFields["season"])
    approaching_areas = DCFieldProperty(ISPMeasureFields["approaching_areas"])
    areas_to_be_avoided = DCFieldProperty(
        ISPMeasureFields["areas_to_be_avoided"])
    descriptors = DCFieldProperty(ISPMeasureFields["descriptors"])
    ecological_impacts = DCFieldProperty(
        ISPMeasureFields["ecological_impacts"])
    future_scenarios = DCFieldProperty(ISPMeasureFields["future_scenarios"])
    effect_on_hydromorphology = DCFieldProperty(
        ISPMeasureFields["effect_on_hydromorphology"])
    ktms_it_links_to = DCFieldProperty(ISPMeasureFields["ktms_it_links_to"])
    links_to_existing_policies = DCFieldProperty(
        ISPMeasureFields["links_to_existing_policies"])
    msfd_spatial_scope = DCFieldProperty(
        ISPMeasureFields["msfd_spatial_scope"])
    mspd_implementation_status = DCFieldProperty(
        ISPMeasureFields["mspd_implementation_status"])
    nature_of_physical_modification = DCFieldProperty(
        ISPMeasureFields["nature_of_physical_modification"])
    source = DCFieldProperty(ISPMeasureFields["source"])
    authority = DCFieldProperty(ISPMeasureFields["authority"])
    general_view = DCFieldProperty(ISPMeasureFields["general_view"])
    ports = DCFieldProperty(ISPMeasureFields["ports"])
    future_expectations = DCFieldProperty(
        ISPMeasureFields["future_expectations"])
    safety_manner = DCFieldProperty(ISPMeasureFields["safety_manner"])
    objective = DCFieldProperty(ISPMeasureFields["objective"])
    categories = DCFieldProperty(ISPMeasureFields["categories"])
    precautionary_areas = DCFieldProperty(
        ISPMeasureFields["precautionary_areas"])
    priority_areas = DCFieldProperty(ISPMeasureFields["priority_areas"])
    relevant_targets = DCFieldProperty(ISPMeasureFields["relevant_targets"])
    relevant_features_from_msfd_annex_iii = DCFieldProperty(
        ISPMeasureFields["relevant_features_from_msfd_annex_iii"])
    region = DCFieldProperty(ISPMeasureFields["region"])
    shipping_tackled = DCFieldProperty(ISPMeasureFields["shipping_tackled"])
    traffic_separation_scheme = DCFieldProperty(
        ISPMeasureFields["traffic_separation_scheme"])
    type_of_pressure = DCFieldProperty(ISPMeasureFields["type_of_pressure"])
