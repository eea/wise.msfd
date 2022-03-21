""" Classes and views to implement the National Descriptors compliance page
"""

from collections import namedtuple
from logging import getLogger

from zope.interface import implements, alsoProvides

from persistent.list import PersistentList
from plone.api.content import transition
from plone.api.portal import get_tool
from plone.protect import CheckAuthenticator  # , protect
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.compliance.assessment import (ANSWERS_COLOR_TABLE,
                                             ARTICLE_WEIGHTS,
                                             CONCLUSION_COLOR_TABLE,
                                             AssessmentDataMixin,
                                             get_assessment_data_2012_db,
                                             filter_assessment_data_2012)
from wise.msfd.compliance.base import (
    NAT_DESC_QUESTIONS, is_row_relevant_for_descriptor)
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.scoring import (get_overall_conclusion,
                                          get_range_index, OverallScores)
from wise.msfd.compliance.utils import ordered_regions_sortkey
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.data import _extract_pdf_assessments, get_text_reports_2018
from wise.msfd.gescomponents import get_descriptor, get_features
from wise.msfd.utils import t2rt

from .base import BaseView
from ..interfaces import (ICountryDescriptorsFolder, ICountryStartAssessments,
                          ICountryStartReports, IMSFDReportingHistoryFolder)
from .interfaces import (INationaldescriptorArticleView,
                         INationaldescriptorSecondaryArticleView)

logger = getLogger('wise.msfd')


Assessment = namedtuple('Assessment',
                        [
                            'gescomponents',
                            'answers',
                            'assessment_summary',
                            'recommendations',
                            'phase_overall_scores',
                            'overall_score',
                            'overall_conclusion',
                            'overall_conclusion_color'
                        ])
AssessmentRow = namedtuple('AssessmentRow',
                           [
                               'question',
                               'summary',
                               'conclusion',
                               'conclusion_color',
                               'score',
                               'values'
                           ])

CountryStatus = namedtuple('CountryStatus',
                           ['code', 'name', 'status', 'state_id', 'url'])


@db.use_db_session('2018')
def get_assessment_head_data_2012(article, region, country_code):

    t = sql2018.COMGeneral
    count, res = db.get_all_records(
        t,
        t.CountryCode == country_code,
        t.MSFDArticle == article,
        t.RegionSubregion.startswith(region),
        # t.RegionSubregion == region + country_code,
        t.AssessmentTopic == 'GES Descriptor'
    )

    # assert count == 1
    # Removed condition because of spain RegionSubregion
    # ABIES - NOR and ABIES - SUD

    if count:
        # report_by = res[0].ReportBy
        report_by = 'Commission'
        assessors = res[0].Assessors
        assess_date = res[0].DateAssessed
        com_report = res[0].CommissionReport

        return (report_by,
                assessors,
                assess_date,
                (com_report.split('/')[-1], com_report))

    return ['Not found'] * 3 + [('Not found', '')]


class NationalDescriptorsOverview(BaseView):
    section = 'national-descriptors'
    iface_country_folder = ICountryDescriptorsFolder

    def countries(self):
        countries = self.context.contentValues()
        res = []

        for country in countries:
            if not self.iface_country_folder.providedBy(country):
                continue

            state_id, state_label = self.process_phase(country)
            info = CountryStatus(country.id.upper(), country.Title(),
                                 state_label, state_id, country.absolute_url())

            res.append(info)

        return res


class NationalDescriptorCountryOverview(BaseView):
    section = 'national-descriptors'

    def country_name_url(self):
        return self.country_name.lower().replace(' ', '-')

    def get_regions(self, context=None):
        if not context:
            context = self.context

        regions = [
            x for x in context.contentValues()
            if x.portal_type == 'Folder'
        ]

        sorted_regions = sorted(
            regions, key=lambda i: ordered_regions_sortkey(i.id.upper())
        )

        return sorted_regions

    # @protect(CheckAuthenticator)
    def send_to_tl(self):
        regions = self.get_regions()

        for region in regions:
            descriptors = self.get_descriptors(region)

            for desc in descriptors:
                assessments = self.get_articles(desc)

                for assessment in assessments:
                    state_id = self.get_wf_state_id(assessment)

                    if state_id == 'approved':
                        transition(obj=assessment, to_state='in_work')

        IStatusMessage(self.request).add(u'Sent to TL', type='info')

        url = self.context.absolute_url()

        return self.request.response.redirect(url)

    def ready_phase2(self, regions=None):
        # roles = self.get_current_user_roles(self.context)

        if not self.can_view_edit_assessment_data(self.context):
            return False

        if not regions:
            regions = self.get_regions()

        for region in regions:
            descriptors = self.get_descriptors(region)

            for desc in descriptors:
                assessments = self.get_articles(desc)

                for assessment in assessments:
                    state_id = self.get_wf_state_id(assessment)

                    if state_id != 'approved':
                        return False

        return True

    def get_descriptors(self, region):
        order = [
            'd1.1', 'd1.2', 'd1.3', 'd1.4', 'd1.5', 'd1.6', 'd2', 'd3', 'd4',
            'd5', 'd6', 'd7', 'd8', 'd9', 'd10', 'd11',
        ]

        return [region[d] for d in order]

    def descriptor_for_code(self, code):
        desc = get_descriptor(code.upper())

        return desc

    def get_secondary_articles(self, country):
        order = ['art7', 'art3', 'art4']

        return [country[a] for a in order]

    def __call__(self):

        return self.index()


class MSFDReportingHistoryMixin(object):
    def get_msfd_reporting_history(self):
        reporting_data = []
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            object_provides=IMSFDReportingHistoryFolder.__identifier__,
        )

        for brain in brains:
            obj = brain._unrestrictedGetObject()
            reporting_data = obj._msfd_reporting_history_data

            break

        return reporting_data

    def get_msfd_url(self, article, country_code, report_type, task_product):
        data = self.get_msfd_reporting_history()

        res = ['']

        if country_code == 'ATL':
            country_code = 'NEA'

        for row in data:
            if article != row.MSFDArticle:
                continue

            if country_code != row.CountryCode:
                continue

            if report_type != row.ReportType:
                continue

            if task_product != row.TaskProduct:
                continue

            # res.append((row.LocationURL, row.FileName))
            res.append(row.LocationURL)

        return res[-1]


class NatDescCountryOverviewReports(NationalDescriptorCountryOverview):
    """ Class declaration needed to be able to override HTML head title """

    def _is_report_2018_art8(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art8_data:
            # TODO check get_data_from_view_art8 for more edge cases
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region or row.Region == 'NotReported'):
                continue

            if row.GESComponent not in all_ids:
                continue

            if not desc_id.startswith('D1.'):
                return True

            feats = set((row.Feature, ))

            if feats.intersection(ok_features):
                return True

        return False

    def _is_report_2018_art9(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art9_data:
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region or row.Region == 'NotReported'  or row.Region is None):
                continue

            if row.GESComponent not in all_ids:
                continue
            
            if not row.Features:
                return True

            if not desc_id.startswith('D1.'):
                return True

            feats = set(row.Features.split(','))

            if feats.intersection(ok_features):
                return True

        return False    
        
    def _is_report_2018_art10(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])
    
        blacklist_descriptors = ['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5',
                                 'D1.6', 'D4', 'D6']
        
        if descriptor.id in blacklist_descriptors:
            blacklist_descriptors.remove(descriptor.id)
        
        blacklist_features = []
        for _desc in blacklist_descriptors:
            blacklist_features.extend([
                f.name for f in get_features(_desc)
            ])
        blacklist_features = set(blacklist_features)

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art10_data:
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region 
                    or row.Region == 'NotReported'
                    or row.Region is None):
                continue

            ges_comps = getattr(row, 'GESComponents', ())
            ges_comps = set([g.strip() for g in ges_comps.split(',')])

            if not ges_comps.intersection(all_ids):
                continue
            
            if not desc_id.startswith('D1.'):
                return True

            row_needed = is_row_relevant_for_descriptor(
                row, desc_id, ok_features, blacklist_features,
                ges_comps
            )

            if row_needed:
                return True

        return False    
        
    def _is_report_2018_art11(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        region_names = [
            REGIONS[region].replace('&', 'and')
        ]
        region_names = [
            ':' in rname and rname.split(':')[1].strip() or rname
            for rname in region_names
        ]

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art11_data:
            if row.CountryCode != country_code:
                continue

            if row.Descriptor not in all_ids:
                continue
            
            regions_reported = set(row.SubRegions.split(','))

            if regions_reported.intersection(set(region_names)):
                return True

        return False

    def is_report_available_2018(self, region, descriptor, article):
        method_name = '_is_report_2018_' + article

        available = True

        if hasattr(self, method_name):
            check_method = getattr(self, method_name)
            available = check_method(region, descriptor)
            
        print("Report for %s %s %s is %s" 
                % (region, descriptor, article, available))

        return available

    def text_reports(self):
        reports = get_text_reports_2018(self.country_code)
        res = []

        for row in reports:
            file_url = row[0]
            report_date = row[1]
            report_date = report_date.date().isoformat()
            file_url_split = file_url.split('/')
            file_name = file_url_split[-1]
            res.append((file_name, file_url, report_date))

        return res

        # return sorted(res, key=lambda i: i[0])

    def __call__(self):
        self.art8_data = db.get_all_data_from_view_Art8(self.country_code)
        self.art9_data = db.get_all_data_from_view_Art9(self.country_code)
        self.art10_data = db.get_all_data_from_view_Art10(self.country_code)
        self.art11_data = db.get_all_data_from_view_art11(self.country_code)

        return self.index()


class NatDescCountryOverviewAssessments(NationalDescriptorCountryOverview,
                                        MSFDReportingHistoryMixin):
    """ Class declaration needed to be able to override HTML head title """

    implements(ICountryStartAssessments)

    def get_url_art12_2012(self):
        article = 'Article 12 (Art.8-9-10)'
        country_code = self.country_code
        report_type = 'Commission technical assessment - national'
        task_product = 'Assessment of 2012 Art. 8-9-10 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)

    def get_url_art12_2014(self):
        article = 'Article 12 (Art.11)'
        country_code = self.country_code
        report_type = 'Commission technical assessment - national'
        task_product = 'Assessment of 2014 Art. 11 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)

    def get_url_art12_2016(self):
        article = 'Article 16 (Art.13-14)'
        country_code = self.country_code
        report_type = 'Commission technical assessment - national'
        task_product = 'Assessment of 2016 Art. 13-14 reports'

        return self.get_msfd_url(article, country_code,
                                 report_type, task_product)


def get_crit_val(question, element, descriptor):
    """ Get the criteria value to be shown in the assessment data 2018 table
    """
    use_crit = question.use_criteria

    if 'targets' in use_crit:
        if use_crit == 'all-targets':
            return element.title

        if use_crit == '2018-targets' and element.year == '2018':
            return element.title

        return ''

    is_prim = element.is_primary(descriptor)
    crit = element.id

    # special case for D1.4 A09Ad2 we need to show all crits excluding D1C2
    # and D1C1 see google spreadhseet Assessments 17-07-2020 request
    if question.id == 'A09Ad2' and descriptor.id == 'D1.4' \
            and crit not in ('D1C1', 'D1C2'):
        return crit

    if use_crit == 'all':
        return crit

    if is_prim and use_crit == 'primary':
        return crit

    if not is_prim and use_crit == 'secondary':
        return crit

    return ''


def format_assessment_data(article, elements, questions, muids, data,
                           descriptor, article_weights, self):
    """ Builds a data structure suitable for display in a template

    This is used to generate the assessment data overview table for 2018

    TODO: this is doing too much. Need to be simplified and refactored.
    """
    answers = []
    phases = article_weights.values()[0].keys()
    phase_overall_scores = OverallScores(article_weights)
    descr_id = hasattr(descriptor, 'id') and descriptor.id or descriptor

    for question in questions:
        values = []
        choices = dict(enumerate(question.answers))
        q_scores = question.scores
        q_klass = question.klass

        if question.use_criteria == 'none':
            field_name = '{}_{}'.format(article, question.id)
            color_index = 0
            label = 'Not filled in'
            v = data.get(field_name, None)

            if v is not None:
                label = choices[v]
                color_index = ANSWERS_COLOR_TABLE[q_scores[v]]

            value = (label, color_index, u'All criteria')
            values.append(value)
        else:
            for element in elements:
                field_name = '{}_{}_{}'.format(
                    article, question.id, element.id
                )

                color_index = 0
                label = u'{}: Not filled in'.format(element.title)

                v = data.get(field_name, None)

                if v is not None:
                    label = u'{}: {}'.format(element.title, choices[v])
                    try:
                        color_index = ANSWERS_COLOR_TABLE[q_scores[v]]
                    except Exception:
                        logger.exception('Invalid color table')
                        color_index = 0
                        # label = 'Invalid color table'

                value = (
                    label,
                    color_index,
                    get_crit_val(question, element, descriptor)
                )

                values.append(value)

        summary_title = '{}_{}_Summary'.format(article, question.id)
        summary = t2rt(data.get(summary_title) or '')

        sn = '{}_{}_Score'.format(article, question.id)
        score = data.get(sn, {})

        conclusion = getattr(score, 'conclusion', '')
        score_value = getattr(score, 'score_value', 0)

        conclusion_color = CONCLUSION_COLOR_TABLE[score_value]

        weighted_score = getattr(score, 'final_score', 0)
        q_weight = getattr(score, 'weight',
                           float(question.score_weights.get(descr_id, 0)))
        max_weighted_score = q_weight
        is_not_relevant = getattr(score, 'is_not_relevant', False)

        # is_not_relevant is True if all answered options are 'Not relevant'
        # maximum overall score is incremented if the is_not_relevant is False

        if not is_not_relevant:
            p_score = getattr(phase_overall_scores, q_klass)
            p_score['score'] += weighted_score
            p_score['max_score'] += max_weighted_score

        qr = AssessmentRow(question.definition, summary, conclusion,
                           conclusion_color, score, values)
        answers.append(qr)

    # assessment summary and recommendations
    assess_sum = data.get('%s_assessment_summary' % article)
    recommend = data.get('%s_recommendations' % article)

    for phase in phases:
        # set the conclusion and color based on the score for each phase
        phase_scores = getattr(phase_overall_scores, phase)
        phase_score = phase_overall_scores.get_score_for_phase(phase)

        if (phase == 'consistency' and article == 'Art9'
                or phase_scores['max_score'] == 0):
            phase_scores['conclusion'] = ('-', 'Not relevant')
            phase_scores['color'] = 0
            continue

        if phase == 'consistency' and phase_scores['score'] == 0:
            phase_scores['conclusion'] = (0, 'Not consistent')
            phase_scores['color'] = 3
            continue

        phase_scores['conclusion'] = get_overall_conclusion(phase_score)
        phase_scores['color'] = \
            CONCLUSION_COLOR_TABLE[get_range_index(phase_score)]

    # for national descriptors and primary articles (Art 8, 9, 10)
    # override the coherence score with the score from regional descriptors
    if self.section == 'national-descriptors' and self.is_primary_article:
        phase_overall_scores.coherence = self.get_coherence_data(
            self.country_region_code, self.descriptor, article
        )

    # the overall score and conclusion for the whole article 2018
    overall_score_val, overall_score = phase_overall_scores.\
        get_overall_score(article)
    overall_conclusion = get_overall_conclusion(overall_score)
    overall_conclusion_color = CONCLUSION_COLOR_TABLE.get(overall_score_val, 0)

    assessment = Assessment(
        elements,
        answers,
        assess_sum or '-',
        recommend or '-',
        phase_overall_scores,
        overall_score,
        overall_conclusion,
        overall_conclusion_color
    )

    return assessment


class NationalDescriptorRegionView(BaseView):
    section = 'national-descriptors'


class NationalDescriptorArticleView(BaseView, AssessmentDataMixin):
    implements(INationaldescriptorArticleView)
    section = 'national-descriptors'

    assessment_data_2012_tpl = Template('./pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = Template('./pt/assessment-data-2018.pt')

    year = '2018'       # used by self.muids
    _questions = NAT_DESC_QUESTIONS

    @property
    def title(self):
        return u"Commission assessment / {} / 2018 / {} / {} / {} ".format(
            self.article,
            self.descriptor_title,
            self.country_title,
            self.country_region_name,
        )

    @property
    def criterias(self):
        return self.descriptor_obj.sorted_criterions()      # criterions

    @property
    def questions(self):
        qs = self._questions.get(self.article, [])

        return qs

    @db.use_db_session('2018')
    def get_file_version(self, date_assessed):
        """ Given the assessment date, returns the latest file
        """
        edit_url = self._country_folder.absolute_url() + '/edit'
        file_name = 'Date assessed not set'
        file_url = ''
        report_date = 'Not found'

        if not date_assessed:
            return file_name, edit_url, report_date, edit_url

        t = sql2018.ReportedInformation
        schemas = {
            'Art8': 'ART8_GES',
            'Art9': 'ART9_GES',
            'Art10': 'ART10_Targets',
        }
        count, data = db.get_all_records(
            t,
            t.CountryCode == self.country_code,
            t.Schema == schemas[self.article],
            order_by=t.ReportingDate
        )

        file_name = 'File not found'

        for row in data:
            if date_assessed >= row.ReportingDate:
                file_url = row.ReportedFileLink
                report_date = row.ReportingDate
            else:
                break

        if file_url:
            file_name = file_url.split('/')[-1]

        return file_name, file_url, report_date, edit_url

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

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

        # Assessment data 2012
        descriptor_criterions = get_descriptor(self.descriptor).criterions

        country_name = self._country_folder.title

        try:
            db_data_2012 = get_assessment_data_2012_db(
                country_name,
                self.descriptor,
                self.article
            )
            assessments_2012 = filter_assessment_data_2012(
                db_data_2012,
                self.country_region_code,       # TODO: this will need refactor
                descriptor_criterions,
            )

            self.assessment_data_2012 = self.assessment_data_2012_tpl(
                data=assessments_2012
            )

            if assessments_2012.get(country_name):
                score_2012 = assessments_2012[country_name].score
                conclusion_2012 = assessments_2012[country_name].overall_ass
            else:       # fallback
                ctry = assessments_2012.keys()[0]
                score_2012 = assessments_2012[ctry].score
                conclusion_2012 = assessments_2012[ctry].overall_ass

            report_by, assessors, assess_date, source_file = \
                get_assessment_head_data_2012(self.article,
                                              self.country_region_code,
                                              self._country_folder.id)
        except:
            logger.exception("Could not get assessment data for 2012")
            self.assessment_data_2012 = ''
            score_2012 = 0
            conclusion_2012 = 'Not found'
            report_by, assessors, assess_date, source_file = [
                'Not found'] * 3 + [('Not found', '')]

        # Assessment header 2012

        self.assessment_header_2012 = self.assessment_header_template(
            report_by=report_by,
            assessor_list=[],
            assessors=assessors,
            assess_date=assess_date,
            source_file=source_file,
            show_edit_assessors=False,
            show_file_version=False,
        )

        # Assessment data 2018
        data = self.context.saved_assessment_data.last()
        elements = self.questions[0].get_all_assessed_elements(
            self.descriptor_obj,
            muids=self.muids
        )

        article_weights = ARTICLE_WEIGHTS
        assessment = format_assessment_data(
            self.article,
            elements,
            self.questions,
            self.muids,
            data,
            self.descriptor_obj,
            article_weights,
            self
        )

        assessment.phase_overall_scores.coherence = self.get_coherence_data(
            self.country_region_code, self.descriptor, self.article
        )

        # score_2012 = score_2012
        conclusion_2012_color = CONCLUSION_COLOR_TABLE.get(score_2012, 0)

        change = (
            assessment.phase_overall_scores
            .get_range_index_for_phase('adequacy') - score_2012
        )

        # if 2018 adequacy is not relevant, change since 2012 is not relevant
        if assessment.phase_overall_scores.adequacy['conclusion'][0] == '-':
            change = 'Not relevant (-)'

        self.assessment_data_2018_html = self.assessment_data_2018_tpl(
            assessment=assessment,
            score_2012=score_2012,
            conclusion_2012=conclusion_2012,
            conclusion_2012_color=conclusion_2012_color,
            change_since_2012=change,
            can_comment=self.can_comment
        )

        # Assessment header 2018
        report_by_2018 = u'Commission'
        # assessors_2018 = self.context.saved_assessment_data.assessors
        assessors_2018 = getattr(
            self.context.saved_assessment_data, 'ass_new', 'Not assessed'
        )
        assess_date_2018 = data.get('assess_date', u'Not assessed')
        source_file_2018 = ('To be addedd...', '.')

        can_edit = self.check_permission('wise.msfd: Edit Assessment')
        show_edit_assessors = self.assessor_list and can_edit

        file_version = self.get_file_version(self.country_date_assessed)

        self.assessment_header_2018_html = self.assessment_header_template(
            report_by=report_by_2018,
            assessor_list=self.assessor_list,
            assessors=assessors_2018,
            assess_date=assess_date_2018,
            source_file=source_file_2018,
            show_edit_assessors=show_edit_assessors,
            show_file_version=True,
            file_version=file_version
        )

        return self.index()


class NationalDescriptorSecondaryArticleView(NationalDescriptorArticleView):
    """"""

    assessment_data_2018_tpl = Template(
        './pt/assessment-data-2018-secondary.pt'
    )
    assessment_header_template = Template(
        '../pt/assessment-header-secondary.pt'
    )

    pdf_assessments = _extract_pdf_assessments()

    implements(INationaldescriptorSecondaryArticleView)
    _descriptor = 'Not linked'

    @property
    def country_region_code(self):
        return 'No region'

    @property
    def descriptor_obj(self):
        return 'Not linked'

    @property
    def has_assessment(self):
        """ Article 7 will be not assessed, we do not show the 2018 and
        2012 assessment tables
        """

        if self.article == 'Art7':
            return False

        return True

    def source_pdf_assessment(self):
        for row in self.pdf_assessments:
            country = row[0]
            if country != self.country_code:
                continue

            article = row[1]
            if article != self.article:
                continue

            url = row[2]

            return url

        return None

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

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

        # Assessment data 2012
        # descriptor_criterions = get_descriptor(self.descriptor).criterions
        descriptor_criterions = []

        country_name = self._country_folder.title

        try:
            db_data_2012 = get_assessment_data_2012_db(
                country_name,
                self.descriptor,
                self.article
            )
            assessments_2012 = filter_assessment_data_2012(
                db_data_2012,
                self.country_region_code,
                descriptor_criterions,
            )
            self.assessment_data_2012 = self.assessment_data_2012_tpl(
                data=assessments_2012
            )

            if assessments_2012.get(country_name):
                score_2012 = assessments_2012[country_name].score
                conclusion_2012 = assessments_2012[country_name].overall_ass
            else:       # fallback
                ctry = assessments_2012.keys()[0]
                score_2012 = assessments_2012[ctry].score
                conclusion_2012 = assessments_2012[ctry].overall_ass

            report_by, assessors, assess_date, source_file = \
                get_assessment_head_data_2012(self.article,
                                              self.country_region_code,
                                              self._country_folder.id)
        except:
            logger.exception("Could not get assessment data for 2012")
            self.assessment_data_2012 = ''
            score_2012 = 100
            conclusion_2012 = 'Not found'
            report_by, assessors, assess_date, source_file = [
                'Not found'] * 3 + [('Not found', '')]

        # Assessment header 2012

        self.assessment_header_2012 = self.assessment_header_template(
            report_by=report_by,
            assessor_list=[],
            assessors=assessors,
            assess_date=assess_date,
            source_file=source_file,
            show_edit_assessors=False,
            show_file_version=False,
        )

        # Assessment data 2018
        data = self.context.saved_assessment_data.last()
        elements = self.questions[0].get_all_assessed_elements(
            self.descriptor_obj,
            country_name=self.country_name,
            country_code=self.country_code
        )
        article_weights = ARTICLE_WEIGHTS
        assessment = format_assessment_data(
            self.article,
            elements,
            self.questions,
            self.muids,
            data,
            self.descriptor_obj,
            article_weights,
            self
        )

        score_2012 = int(round(score_2012))
        conclusion_2012_color = CONCLUSION_COLOR_TABLE.get(score_2012, 0)
        change = int(
            assessment.phase_overall_scores
            .get_range_index_for_phase('adequacy') - score_2012
        )

        self.assessment_data_2018_html = self.assessment_data_2018_tpl(
            assessment=assessment,
            score_2012=score_2012,
            conclusion_2012=conclusion_2012,
            conclusion_2012_color=conclusion_2012_color,
            change_since_2012=change,
            can_comment=self.can_comment
        )

        # Assessment header 2018
        report_by_2018 = u'Commission'
        # assessors_2018 = self.context.saved_assessment_data.assessors
        assessors_2018 = getattr(
            self.context.saved_assessment_data, 'ass_new', 'Not assessed'
        )
        assess_date_2018 = data.get('assess_date', u'Not assessed')
        source_file_2018 = ('To be addedd...', '.')

        can_edit = self.check_permission('wise.msfd: Edit Assessment')
        show_edit_assessors = self.assessor_list and can_edit

        self.assessment_header_2018_html = self.assessment_header_template(
            report_by=report_by_2018,
            assessor_list=self.assessor_list,
            assessors=assessors_2018,
            assess_date=assess_date_2018,
            source_file=source_file_2018,
            show_edit_assessors=show_edit_assessors,
            show_file_version=False,
        )

        return self.index()

    @property
    def title(self):
        return u"Commission assessment: {} / {} / 2018".format(
            self.country_title,
            self.article,
        )
