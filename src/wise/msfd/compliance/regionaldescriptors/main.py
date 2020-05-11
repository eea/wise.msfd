from collections import namedtuple

from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF

from wise.msfd.compliance.base import REG_DESC_QUESTIONS
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.nationaldescriptors.main import (
    CONCLUSION_COLOR_TABLE, format_assessment_data)
from wise.msfd.gescomponents import get_descriptor

from .assessment import ASSESSMENTS_2012
from .base import BaseRegComplianceView


RegionStatus = namedtuple('CountryStatus',
                          ['name', 'countries', 'status', 'state_id', 'url'])

ARTICLE_WEIGHTS = {
    'Art9': {
        'adequacy': 0.0,
        'consistency': 0.0,
        'coherence': 1.0
    },
    'Art8': {
        'adequacy': 0.0,
        'consistency': 0.0,
        'coherence': 1.0
    },
    'Art10': {
        'adequacy': 0.0,
        'consistency': 0.0,
        'coherence': 1.0
    }
}


class RegionalDescriptorsOverview(BaseRegComplianceView):
    section = 'regional-descriptors'

    def regions(self):
        regions = self.context.contentValues()
        res = []

        for region in regions:
            countries = [x[1] for x in region._countries_for_region]
            state_id, state_label = self.process_phase(region)
            info = RegionStatus(region.Title(), ", ".join(countries),
                                state_label, state_id,
                                region.absolute_url())

            res.append(info)

        return res


class RegionalDescriptorRegionsOverview(BaseRegComplianceView):
    section = 'regional-descriptors'

    def get_regions(self):
        regions = [
            x for x in self.context.contentValues()
            if x.portal_type == 'Folder'
        ]

        return regions

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

    def ready_phase2(self):
        return False


class RegionalDescriptorArticleView(BaseRegComplianceView):
    section = 'regional-descriptors'

    assessment_data_2012_tpl = VPTF('pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = VPTF('pt/assessment-data-2018.pt')
    _questions = REG_DESC_QUESTIONS

    @property
    def questions(self):
        qs = self._questions[self.article]

        return qs

    @property
    def title(self):
        return u"Regional descriptor / {} / 2018 / {} / {}".format(
            self.article,
            self.descriptor_title,
            self.country_region_name,
        )

    # @property
    # def criterias(self):
    #     return self.descriptor_obj.sorted_criterions()      # criterions

    def get_assessments_data_2012(self):
        res = []

        for x in ASSESSMENTS_2012:
            if x.region.strip() != self.country_region_code:
                continue

            if x.descriptor.strip() != self.descriptor_obj.id.split('.')[0]:
                continue

            article = x.article.replace(" ", "")

            if not article.startswith(self.article):
                continue

            res.append(x)

        sorted_res = sorted(
            res, key=lambda i: int(i.overall_score), reverse=True
        )

        return sorted_res

    def get_assessment_2012_header_data(self, assessments_2012):
        res = {}

        if not assessments_2012:
            return res

        assessments_2012 = assessments_2012[0]

        res['report_by'] = assessments_2012.report_by
        res['assessed_by'] = assessments_2012.assessment_by
        res['assess_date'] = assessments_2012.date_assessed.date()
        res['file_name'] = assessments_2012.commission_report.split('/')[-1]
        res['file_url'] = assessments_2012.commission_report

        return res

    def get_elements_for_question(self):
        # Because Art 10 questions are based on targets
        # It is a hack to return something for article 10, to be able to
        # answer the first question
        if self.article == 'Art10':
            return self.descriptor_obj.criterions

        elements = self.questions[0].get_all_assessed_elements(
            self.descriptor_obj,
            muids=[]
        )

        return elements

    def __call__(self):
        if 'assessor' in self.request.form:
            assessors = self.request.form['assessor']

            if isinstance(assessors, list):
                assessors = ', '.join(assessors)
            self.context.saved_assessment_data.ass_new = assessors

        # BBB:
        context = self.context

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        # Assessment 2012
        assessments_2012 = self.get_assessments_data_2012()
        assessment_2012_header_data = self.get_assessment_2012_header_data(
            assessments_2012
        )
        self.assessment_header_2012 = self.assessment_header_template(
            report_by=assessment_2012_header_data.get('report_by', '-'),
            assessor_list=self.assessor_list,
            assessors=assessment_2012_header_data.get('assessed_by', '-'),
            assess_date=assessment_2012_header_data.get('assess_date', '-'),
            source_file=[
                assessment_2012_header_data.get('file_name', '-'),
                assessment_2012_header_data.get('file_url', ''),
            ],
            show_edit_assessors=False,
        )
        self.assessment_data_2012 = self.assessment_data_2012_tpl(
            data=assessments_2012
        )

        score_2012 = (assessments_2012 and assessments_2012[0].overall_score
                      or 0)
        conclusion_2012 = (assessments_2012 and assessments_2012[0].conclusion
                           or 'Not found')
        conclusion_2012_color = CONCLUSION_COLOR_TABLE.get(score_2012, 0)

        # Assessment 2018
        assessors_2018 = getattr(
            self.context.saved_assessment_data, 'ass_new', 'Not assessed'
        )
        data = self.context.saved_assessment_data.last()
        elements = self.get_elements_for_question()
        assess_date_2018 = data.get('assess_date', u'Not assessed')
        source_file_2018 = ('To be addedd...', '.')
        muids = None
        article_weights = ARTICLE_WEIGHTS
        assessment = format_assessment_data(
            self.article,
            # self.get_available_countries(),
            elements,
            self.questions,
            muids,
            data,
            self.descriptor_obj,
            article_weights,
            self
        )
        change = int(
            assessment.phase_overall_scores
            .get_range_index_for_phase('coherence') - score_2012
        )

        can_edit = self.check_permission('wise.msfd: Edit Assessment')
        show_edit_assessors = self.assessor_list and can_edit

        self.assessment_header_2018_html = self.assessment_header_template(
            report_by="Member state",
            assessor_list=self.assessor_list,
            assessors=assessors_2018,
            assess_date=assess_date_2018,
            source_file=source_file_2018,
            show_edit_assessors=show_edit_assessors,
        )
        self.assessment_data_2018_html = self.assessment_data_2018_tpl(
            assessment=assessment,
            score_2012=score_2012,
            conclusion_2012=conclusion_2012,
            conclusion_2012_color=conclusion_2012_color,
            change_since_2012=change,
            can_comment=self.can_comment
        )

        return self.index()

