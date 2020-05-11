
from ..nationaldescriptors.main import NationalDescriptorsOverview
from .base import BaseNatSummaryView


class NationalSummaryOverview(BaseNatSummaryView, NationalDescriptorsOverview):
    section = 'national-summaries'
