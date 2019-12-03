
from wise.msfd.compliance.nationaldescriptors.main import CountryStatus

from .base import BaseNatSummaryView


class NationalSummaryOverview(BaseNatSummaryView):
    section = 'national-summaries'

    def countries(self):
        countries = self.context.contentValues()
        res = []

        for country in countries:
            state_id, state_label = self.process_phase(country)
            info = CountryStatus(country.Title(), state_label, state_id,
                                 country.absolute_url())

            res.append(info)

        return res

