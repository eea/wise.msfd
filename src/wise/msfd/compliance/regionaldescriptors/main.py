from __future__ import absolute_import
from collections import namedtuple
from io import BytesIO

from zope.interface import alsoProvides, implements
import xlsxwriter

from persistent.list import PersistentList
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF

from wise.msfd.compliance.assessment import (AssessmentDataMixin,
                                             CONCLUSION_COLOR_TABLE)
from wise.msfd.compliance.base import REG_DESC_QUESTIONS
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.interfaces import (IRegionalDescriptorAssessment,
                                             IRegionStartAssessments,
                                             IRegionStartReports)
from wise.msfd.compliance.nationaldescriptors.main import (
    MSFDReportingHistoryMixin, format_assessment_data)
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.utils import ItemList

from ..vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from .base import BaseRegComplianceView
import six


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

    def region_name_url(self):
        region_code = self.country_region_code

        region_title = [
            r.title
            for r in REGIONAL_DESCRIPTORS_REGIONS
            if r.code == region_code.upper()
        ][0]

        region_title = region_title.lower().replace(' ', '-')

        return region_title

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

    def ready_phase2(self):
        return False


class RegDescRegionOverviewReports(RegionalDescriptorRegionsOverview):
    """ Class declaration needed to be able to override HTML head title """

    implements(IRegionStartReports)


class RegDescRegionOverviewAssessments(RegionalDescriptorRegionsOverview,
                                       MSFDReportingHistoryMixin):
    """ Class declaration needed to be able to override HTML head title """

    implements(IRegionStartAssessments)

    def get_url_art12_2012(self):
        article = 'Article 12 (Art.8-9-10)'
        country_code = self.country_region_code
        report_type = 'Commission technical assessment - regional'
        task_product = 'Assessment of 2012 Art. 8-9-10 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)

    def get_url_art12_2014(self):
        article = 'Article 12 (Art.11)'
        country_code = self.country_region_code
        report_type = 'Commission technical assessment - regional'
        task_product = 'Assessment of 2014 Art. 11 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)

    def get_url_art12_2016(self):
        article = 'Article 16 (Art.13-14)'
        country_code = self.country_region_code
        report_type = 'Commission technical assessment - regional'
        task_product = 'Assessment of 2016 Art. 13-14 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)


class RegionalDescriptorArticleView(BaseRegComplianceView,
                                    AssessmentDataMixin):
    implements(IRegionalDescriptorAssessment)

    section = 'regional-descriptors'

    assessment_data_2012_tpl = VPTF('pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = VPTF('pt/assessment-data-2018.pt')
    national_assessment_tpl= VPTF('pt/report-data.pt')
    _questions = REG_DESC_QUESTIONS

    @property
    def questions(self):
        qs = self._questions[self.article]

        return qs

    @property
    def title(self):
        return u"Commission assessment / {} / 2018 / {} / {}".format(
            self.article,
            self.descriptor_title,
            self.country_region_name,
        )

    # @property
    # def criterias(self):
    #     return self.descriptor_obj.sorted_criterions()      # criterions

    # def get_assessments_data_2012(self, article=None, region_code=None,
    #                               descriptor_code=None):
    #
    #     if not article:
    #         article = self.article
    #
    #     if not region_code:
    #         region_code = self.country_region_code
    #
    #     if not descriptor_code:
    #         descriptor_code = self.descriptor_obj.id
    #
    #     res = []
    #
    #     for x in ASSESSMENTS_2012:
    #         if x.region.strip() != region_code:
    #             continue
    #
    #         if x.descriptor.strip() != descriptor_code.split('.')[0]:
    #             continue
    #
    #         art = x.article.replace(" ", "")
    #
    #         if not art.startswith(article):
    #             continue
    #
    #         res.append(x)
    #
    #     sorted_res = sorted(
    #         res, key=lambda i: int(i.overall_score), reverse=True
    #     )
    #
    #     return sorted_res

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

    def data_to_xls(self, data):
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = self.country_region_code
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])

        row_index = 0

        for row in data:
            for i, value in enumerate(row):
                if isinstance(value, ItemList):
                    value = "\n".join(value.rows)

                try:
                    unicode_value = six.text_type(value)
                except:
                    unicode_value = six.text_type(value.decode('utf-8'))

                worksheet.write(row_index, i, unicode_value or '')

            row_index += 1

        workbook.close()
        out.seek(0)

        return out

    def download_summary_national(self):
        xlsdata = self.raw_adeq_assess_data

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["SummaryOfNationalAssessments",
                          self.article,
                          self.year,
                          self.descriptor,
                          self.country_region_code,
                          ])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        if 'assessor' in self.request.form:
            assessors = self.request.form['assessor']

            if isinstance(assessors, list):
                assessors = ', '.join(assessors)
            self.context.saved_assessment_data.ass_new = assessors

        national_assessments_data = self.get_adequacy_assessment_data()
        self.national_assessments_2018 = self.national_assessment_tpl(
            data=national_assessments_data, report_header=""
        )

        if 'download-summary-national' in self.request.form:
            return self.download_summary_national()

        # BBB:
        context = self.context

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        # Assessment 2012
        assessments_2012 = self.get_reg_assessments_data_2012()
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
            show_file_version=False
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
            show_file_version=False
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

