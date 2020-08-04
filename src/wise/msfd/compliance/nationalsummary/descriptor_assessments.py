import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.assessment import (get_assessment_data_2012_db,
                                             filter_assessment_data_2012,
                                             AssessmentDataMixin)
from wise.msfd.compliance.interfaces import (IDescriptorFolder,
                                             INationalDescriptorAssessment,
                                             INationalRegionDescriptorFolder)
from wise.msfd.compliance.utils import ordered_regions_sortkey
from wise.msfd.gescomponents import DESCRIPTOR_TYPES
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from .base import BaseNatSummaryView
from .odt_utils import create_heading, create_table_descr

logger = logging.getLogger('wise.msfd')


class DescriptorLevelAssessments(BaseNatSummaryView, AssessmentDataMixin):

    template = ViewPageTemplateFile('pt/descriptor-level-assessments.pt')

    article_titles = {
        'Art9': 'Article 9 - GES Determination',
        'Art8': 'Article 8 - Initial Assessment',
        'Art10': 'Article 10 - Environmental Targets'
    }

    descriptor_types = DESCRIPTOR_TYPES

    def get_article_title(self, article):

        return self.article_titles[article]

    @timeit
    def setup_descriptor_level_assessment_data(self):
        """
        :return: res =  [("Baltic Sea", [
                    ("D7 - Hydrographical changes", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                    ("D1.4 - Birds", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                ]
            )]
        """

        res = []

        country_folder = [
            country
            for country in self._nat_desc_folder.contentValues()
            if country.id == self.country_code.lower()
        ][0]

        self.nat_desc_country_folder = country_folder
        region_folders = self.filter_contentvalues_by_iface(
            country_folder, INationalRegionDescriptorFolder
        )

        region_folders_sorted = sorted(
            region_folders, key=lambda i: ordered_regions_sortkey(i.id.upper())
        )

        for region_folder in region_folders_sorted:
            region_code = region_folder.id
            region_name = region_folder.title
            descriptor_data = []
            descriptor_folders = self.filter_contentvalues_by_iface(
                region_folder, IDescriptorFolder
            )

            for descriptor_folder in descriptor_folders:
                desc_id = descriptor_folder.id.upper()
                desc_name = descriptor_folder.title
                articles = []
                article_folders = self.filter_contentvalues_by_iface(
                    descriptor_folder, INationalDescriptorAssessment
                )

                for article_folder in article_folders:
                    article = article_folder.title

                    assess_data = self._get_assessment_data(article_folder)
                    article_data = self._get_article_data(
                        region_code.upper(), country_folder.title,
                        desc_id, assess_data, article
                    )
                    articles.append((article, article_data))

                articles = sorted(
                    articles,
                    key=lambda i: fixedorder_sortkey(i[0], self.ARTICLE_ORDER)
                )

                descriptor_data.append(
                    ((desc_id, desc_name), articles)
                )

            res.append((region_name, descriptor_data))

        return res

    def get_odt_data(self, document):
        res = []

        h = create_heading(1, u"Descriptor-level assessments")
        res.append(h)

        all_data = self.descr_assess_data

        for region in all_data:
            h = create_heading(2, region[0])
            res.append(h)
            all_descriptors_data = region[1]

            for descriptor_type in self.descriptor_types:
                h = create_heading(3, descriptor_type[0])
                res.append(h)

                for descriptor in descriptor_type[1]:
                    descriptor_data = [
                        d
                        for d in all_descriptors_data
                        if d[0][0] == descriptor
                    ][0]
                    h = create_heading(4, descriptor_data[0][1])
                    res.append(h)

                    articles = descriptor_data[1]
                    for article in articles:
                        h = create_heading(5, article[0])
                        res.append(h)
                        article_data = article[1]

                        t = create_table_descr(document, article_data)

                        res.append(t)

        return res

    def __call__(self):
        data = self.setup_descriptor_level_assessment_data()

        self.descr_assess_data = data

        return self.template(data=data)
