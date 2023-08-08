from plone.app.dexterity.behaviors.metadata import (
    DCFieldProperty, MetadataBase)
from .interfaces import (ISPMeasureFields)


class SPMeasureFields(MetadataBase):
    """SPMeasure fields"""

    sector = DCFieldProperty(ISPMeasureFields["sector"])
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
