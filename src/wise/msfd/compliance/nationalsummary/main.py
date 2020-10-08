
from ..interfaces import INationalSummaryCountryFolder
from ..nationaldescriptors.main import NationalDescriptorsOverview
from .base import BaseNatSummaryView


class NationalSummaryOverview(BaseNatSummaryView, NationalDescriptorsOverview):
    """ base view at /assessment-module/national-summaries """

    section = 'national-summaries'
    iface_country_folder = INationalSummaryCountryFolder
