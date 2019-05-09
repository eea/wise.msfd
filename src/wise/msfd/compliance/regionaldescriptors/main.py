from collections import namedtuple

from wise.msfd.gescomponents import get_descriptor

from .base import BaseRegComplianceView


RegionStatus = namedtuple('CountryStatus',
                          ['name', 'countries', 'status', 'state_id', 'url'])


class RegionalDescriptorsOverview(BaseRegComplianceView):
    section = 'regional-descriptors'

    def regions(self):
        regions = self.context.contentValues()
        res = []

        for region in regions:
            countries = sorted([x[1] for x in region._countries_for_region])
            state_id, state_label = self.process_phase(region)
            info = RegionStatus(region.Title(), ", ".join(countries),
                                state_label, state_id,
                                region.absolute_url())

            res.append(info)

        return res


class RegionalDescriptorRegionsOverview(BaseRegComplianceView):
    section = 'regional-descriptors'

    def get_regions(self):
        return self.context.contentValues()

    def get_descriptors(self, region):
        order = [
            'd1.1', 'd1.2', 'd1.3', 'd1.4', 'd1.5', 'd1.6', 'd2', 'd3', 'd4',
            'd5', 'd6', 'd7', 'd8', 'd9', 'd10', 'd11',
        ]

        return [region[d] for d in order]

    def descriptor_for_code(self, code):
        desc = get_descriptor(code.upper())

        return desc

    def get_articles(self, desc):
        order = ['art9', 'art8', 'art10']

        return [desc[a] for a in order]


class RegionalDescriptorArticleView(BaseRegComplianceView):
    section = 'regional-descriptors'

    @property
    def title(self):
        return u"Regional descriptor: {} / {} / {} / 2018".format(
            self.country_region_name,
            self.descriptor_title,
            self.article,
        )

    # @property
    # def criterias(self):
    #     return self.descriptor_obj.sorted_criterions()      # criterions

    def __call__(self):

        return self.index()