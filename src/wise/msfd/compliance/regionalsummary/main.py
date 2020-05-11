
from ..nationaldescriptors.main import CountryStatus
from .base import BaseRegSummaryView


class RegionalSummaryOverview(BaseRegSummaryView):
    section = 'regional-summaries'

    def regions(self):
        regions = self.context.contentValues()
        res = []

        for region in regions:
            state_id, state_label = self.process_phase(region)
            info = CountryStatus(region.id, region.Title(), state_label,
                                 state_id, region.absolute_url())

            res.append(info)

        return res

