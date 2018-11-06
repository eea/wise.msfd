from collections import namedtuple
from ..base import BaseComplianceView


RegionStatus = namedtuple('CountryStatus',
                           ['name', 'status', 'state_id', 'url'])


class RegionalDescriptorsOverview(BaseComplianceView):
    section = 'regional-descriptors'

    def regions(self):
        regions = self.context.contentValues()
        res = []

        for region in regions:
            state_id, state_label = self.process_phase(region)
            info = RegionStatus(region.Title(), state_label, state_id,
                                region.absolute_url())

            res.append(info)

        return res

