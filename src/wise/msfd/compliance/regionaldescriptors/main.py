from collections import namedtuple

from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF

from wise.msfd.compliance.base import get_questions
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.nationaldescriptors.main import format_assessment_data
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

    # assessment_data_2012_tpl = VPTF('pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = VPTF(
        '../nationaldescriptors/pt/assessment-data-2018.pt'
    )
    _questions = get_questions("compliance/regionaldescriptors/data")

    @property
    def questions(self):
        qs = self._questions[self.article]

        return qs

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
        # BBB:

        context = self.context

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        self.assessment_header_2018_html = self.assessment_header_template(
            report_by="Report by 2018",
            assessor_list=self.assessor_list,
            assessors="Assessors 2018",
            assess_date="Date 2018",
            source_file=["File 2018", ""],
            show_edit_assessors=True,
        )
        data = self.context.saved_assessment_data.last()
        muids = None
        assessment = format_assessment_data(
            self.article,
            self.get_available_countries(),
            self.questions,
            muids,
            data,
            self.descriptor_obj
        )
        self.assessment_data_2018_html = self.assessment_data_2018_tpl(
            assessment=assessment,
            score_2012="-99",
            conclusion_2012="Get conclusion 2012"
        )

        self.assessment_header_2012 = self.assessment_header_template(
            report_by="Report by 2012",
            assessor_list=self.assessor_list,
            assessors="Assessors 2012",
            assess_date="Date 2012",
            source_file=["File 2012", ""],
            show_edit_assessors=False,
        )
        self.assessment_data_2012 = None

        return self.index()