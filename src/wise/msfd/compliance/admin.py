import logging
from collections import namedtuple
from datetime import datetime
from io import BytesIO

from zope.interface import alsoProvides

import xlsxwriter
from eea.cache import cache
from plone import api
from plone.api import portal
from plone.api.content import get_state, transition
from plone.api.portal import get_tool
from plone.dexterity.utils import createContentInContainer as create
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault
from Products.CMFPlacefulWorkflow.WorkflowPolicyConfig import \
    WorkflowPolicyConfig
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import db, sql2018
from wise.msfd.compliance.assessment import AssessmentDataMixin
from wise.msfd.compliance.vocabulary import (get_regions_for_country,
                                             REGIONAL_DESCRIPTORS_REGIONS)
from wise.msfd.compliance.regionaldescriptors.base import COUNTRY
from wise.msfd.gescomponents import (get_all_descriptors, get_descriptor,
                                     get_marine_units)
from wise.msfd.labels import get_indicator_labels
from wise.msfd.translation import Translation, get_detected_lang
from wise.msfd.translation.interfaces import ITranslationsStorage

from . import interfaces
from .base import (_get_secondary_articles, BaseComplianceView,
                   NAT_DESC_QUESTIONS, REG_DESC_QUESTIONS,
                   report_data_cache_key)

logger = logging.getLogger('wise.msfd')

CONTRIBUTOR_GROUP_ID = 'extranet-wisemarine-msfd-tl'
REVIEWER_GROUP_ID = 'extranet-wisemarine-msfd-reviewers'
EDITOR_GROUP_ID = 'extranet-wisemarine-msfd-editors'


def get_wf_state_id(context):
    state = get_state(context)
    wftool = get_tool('portal_workflow')
    wf = wftool.getWorkflowsFor(context)[0]  # assumes one wf
    wf_state = wf.states[state]
    wf_state_id = wf_state.id or state

    return wf_state_id


class ToPDB(BrowserView):
    def __call__(self):
        import pdb
        pdb.set_trace()

        return 'ok'


class BootstrapCompliance(BrowserView):
    """ Bootstrap the compliance module by creating all needed country folders
    """

    @property
    def debug(self):
        return 'production' not in self.request.form

    @db.use_db_session('2018')
    def _get_countries(self):
        """ Get a list of (code, name) countries
        """

        count, res = db.get_all_records(
            sql2018.LCountry
        )
        countries = [(x.Code, x.Country) for x in res]

        if self.debug:
            countries = [x for x in countries if x[0] in ('LV', 'NL', 'DE')]

        return countries

    @db.use_db_session('2018')
    def _get_countries_names(self, country_codes):
        result = []
        all_countries = self._get_countries()

        for code in country_codes:
            result.extend([x for x in all_countries if x[0] == code])

        return result

    def _get_descriptors(self):
        """ Get a list of (code, description) descriptors
        """

        descriptors = get_all_descriptors()

        debug_descriptors = ('D1.1', 'D4', 'D5', 'D6')

        if self.debug:
            descriptors = [x for x in descriptors if x[0] in debug_descriptors]

        return descriptors

    @db.use_db_session('2018')
    def _get_articles(self):
        # articles = db.get_unique_from_mapper(
        #     sql2018.LMSFDArticle,
        #     'MSFDArticle'
        # )
        # return articles

        return ['Art8', 'Art9', 'Art10']

    def set_layout(self, obj, name):
        ISelectableBrowserDefault(obj).setLayout(name)

    def set_policy(self, context, name):
        logger.info("Set placeful workflow policy for %s", context.getId())
        config = WorkflowPolicyConfig(
            workflow_policy_in='compliance_section_policy',
            workflow_policy_below='compliance_section_policy',
        )
        context._setObject(config.id, config)

    @db.use_db_session('2018')
    def get_country_regions(self, country_code):
        regions = get_regions_for_country(country_code)

        return regions

    def get_group(self, code):
        if '.' in code:
            code = 'd1'
        code = code.lower()

        return "{}-{}".format(CONTRIBUTOR_GROUP_ID, code)

    def create_comments_folder(self, content):
        for id, title, trans in [
            (u'tl', 'Discussion track with Topic Leads', 'open_for_tl'),
            (u'ec', 'Discussion track with EC', 'open_for_ec'),
        ]:
            if id not in content.contentIds():
                dt = create(content,
                            'wise.msfd.commentsfolder',
                            id=id,
                            title=title)
                transition(obj=dt, transition=trans)

    def make_country(self, parent, country_code, name):

        if country_code.lower() in parent.contentIds():
            cf = parent[country_code.lower()]
        else:
            cf = create(parent,
                        'wise.msfd.countrydescriptorsfolder',
                        title=name,
                        id=country_code)

        for regid, region in self.get_country_regions(country_code):
            if regid.lower() in cf.contentIds():
                reg = cf[regid.lower()]
            else:
                reg = create(cf,
                             'Folder',
                             title=region,
                             id=regid.lower())
                alsoProvides(reg, interfaces.INationalRegionDescriptorFolder)
                self.set_layout(reg, '@@nat-desc-reg-view')

            for desc_code, description in self._get_descriptors():
                if desc_code.lower() in reg.contentIds():
                    df = reg[desc_code.lower()]
                else:
                    df = create(reg, 'Folder', title=description, id=desc_code)
                    alsoProvides(df, interfaces.IDescriptorFolder)

                for art in self._get_articles():
                    if art.lower() in df.contentIds():
                        nda = df[art.lower()]
                    else:
                        nda = create(df,
                                     'wise.msfd.nationaldescriptorassessment',
                                     title=art)
                        lr = nda.__ac_local_roles__

                        group = self.get_group(desc_code)

                        lr[group] = ['Contributor']

                        logger.info("Created NationalDescriptorAssessment %s",
                                    nda.absolute_url())

                        self.set_layout(nda, '@@nat-desc-art-view')

                    self.create_comments_folder(nda)

        return cf

    def make_region(self, parent, region):
        code, name = region.code.lower(), region.title

        if code.lower() in parent.contentIds():
            rf = parent[code.lower()]
        else:
            rf = create(parent,
                        'wise.msfd.regiondescriptorsfolder',
                        title=name,
                        id=code)

            rf._subregions = region.subregions
            rf._countries_for_region = self._get_countries_names(
                region.countries
            )
            self.set_layout(rf, '@@reg-region-start')
            alsoProvides(rf, interfaces.IRegionalDescriptorRegionsFolder)

        for desc_code, description in self._get_descriptors():
            if desc_code.lower() in rf.contentIds():
                df = rf[desc_code.lower()]
            else:
                df = create(rf, 'Folder', title=description, id=desc_code)
                alsoProvides(df, interfaces.IDescriptorFolder)

            for art in self._get_articles():
                if art.lower() in df.contentIds():
                    rda = df[art.lower()]
                else:
                    rda = create(df,
                                 'wise.msfd.regionaldescriptorassessment',
                                 title=art)

                    lr = rda.__ac_local_roles__
                    group = self.get_group(desc_code)
                    lr[group] = ['Contributor']

                    logger.info("Created RegionalDescriptorArticle %s",
                                rda.absolute_url())

                    self.set_layout(rda, '@@reg-desc-art-view')
                    alsoProvides(rda, interfaces.IRegionalDescriptorAssessment)

                self.create_comments_folder(rda)

        return rf

    def setup_nationaldescriptors(self, parent):
        # National Descriptors Assessments

        if 'national-descriptors-assessments' in parent.contentIds():
            nda = parent['national-descriptors-assessments']
        else:
            nda = create(parent,
                         'Folder', title=u'National Descriptors Assessments')
            self.set_layout(nda, '@@nat-desc-start')
            alsoProvides(nda, interfaces.INationalDescriptorsFolder)

        for code, country in self._get_countries():
            self.make_country(nda, code, country)

    def setup_regionaldescriptors(self, parent):
        # Regional Descriptors Assessments

        if 'regional-descriptors-assessments' in parent.contentIds():
            rda = parent['regional-descriptors-assessments']
        else:
            rda = create(parent,
                         'Folder', title=u'Regional Descriptors Assessments')
            self.set_layout(rda, '@@reg-desc-start')
            alsoProvides(rda, interfaces.IRegionalDescriptorsFolder)

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            self.make_region(rda, region)

    def setup_nationalsummaries(self, parent):
        if 'national-summaries' in parent.contentIds():
            ns = parent['national-summaries']
        else:
            ns = create(parent,
                        'Folder', title=u'National summaries')
            self.set_layout(ns, '@@nat-summary-start')
            alsoProvides(ns, interfaces.INationalSummaryFolder)

        for code, country in self._get_countries():
            if code.lower() in ns.contentIds():
                cf = ns[code.lower()]
            else:
                # national_summary type used for Assessment summary/pdf export
                cf = create(ns,
                            'national_summary',
                            title=country,
                            id=code)

            self.set_layout(cf, 'assessment-summary')
            alsoProvides(cf, interfaces.INationalSummaryCountryFolder)
            # self.create_comments_folder(cf)

            # create the overview folder
            # if 'overview' in cf.contentIds():
            #     of = cf['overview']
            # else:
            #     of = create(cf,
            #                 'wise.msfd.nationalsummaryoverview',
            #                 title='National summary overview',
            #                 id='overview')
            #
            # self.set_layout(of, 'sum-country-start')
            # alsoProvides(of, interfaces.INationalSummaryOverviewFolder)

    def setup_regionalsummaries(self, parent):
        if 'regional-summaries' in parent.contentIds():
            ns = parent['regional-summaries']
        else:
            ns = create(parent,
                        'Folder',
                        title=u'Regional summaries')
            self.set_layout(ns, 'reg-summary-start')
            alsoProvides(ns, interfaces.IRegionalSummaryFolder)

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            code, name = region.code.lower(), region.title

            if code not in ns.contentIds():
                rf = create(ns,
                            'wise.msfd.regionalsummaryfolder',
                            title=name,
                            id=code)

                rf._subregions = region.subregions
                rf._countries_for_region = self._get_countries_names(
                    region.countries
                )
                self.set_layout(rf, '@@sum-region-start')
                alsoProvides(rf, interfaces.IRegionalSummaryRegionFolder)

    def setup_secondary_articles(self, parent):
        if 'national-descriptors-assessments' not in parent.contentIds():
            return

        nda_parent = parent['national-descriptors-assessments']
        country_ids = nda_parent.contentIds()

        for country in country_ids:
            country_folder = nda_parent[country]

            for article in _get_secondary_articles():
                if article.lower() in country_folder.contentIds():
                    nda = country_folder[article.lower()]
                else:
                    nda = create(country_folder,
                                 'wise.msfd.nationaldescriptorassessment',
                                 title=article)

                    logger.info("Created NationalDescriptorAssessment %s",
                                nda.absolute_url())

                alsoProvides(
                    nda,
                    interfaces.INationalDescriptorAssessmentSecondary
                )
                self.set_layout(nda, '@@nat-desc-art-view-secondary')

                self.create_comments_folder(nda)

    def __call__(self):

        # if 'compliance-module' in self.context.contentIds():
        #     self.context.manage_delObjects(['compliance-module'])

        if 'compliance-module' in self.context.contentIds():
            cm = self.context['compliance-module']
        else:
            cm = create(self.context, 'Folder', title=u'Compliance Module')

            self.set_layout(cm, '@@comp-start')
            self.set_policy(cm, 'compliance_section_policy')

            alsoProvides(cm, interfaces.IComplianceModuleFolder)

            lr = cm.__ac_local_roles__
            lr[REVIEWER_GROUP_ID] = [u'Reviewer']
            lr[EDITOR_GROUP_ID] = [u'Editor']

        # Contributor: TL
        # Reviewer: EC
        # Editor: Milieu

        # self.setup_nationaldescriptors(cm)
        DEFAULT = 'regional,nationalsummary,regionalsummary,secondary'
        targets = self.request.form.get('setup', DEFAULT)

        if targets:
            targets = targets.split(',')
        else:
            targets = DEFAULT

        if "regional" in targets:
            self.setup_regionaldescriptors(cm)

        if "nationalsummary" in targets:
            self.setup_nationalsummaries(cm)

        if "secondary" in targets:
            self.setup_secondary_articles(cm)

        if 'regionalsummary' in targets:
            self.setup_regionalsummaries(cm)

        return cm.absolute_url()


class CleanupCache(BrowserView):
    """ Remove the persistent cache that we have saved in objects
    """

    def __call__(self):
        brains = api.content.find(context=self.context, depth=10000)

        for brain in brains:
            obj = brain.getObject()
            print "For obj", obj

            for name in obj.__dict__.keys():

                if name.startswith('_cache_'):
                    logger.info("Cleaning up %r: %s", obj, name)
                    delattr(obj, name)

        return "done"


User = namedtuple('User', ['username', 'fullname', 'email'])


class ComplianceAdmin(BaseComplianceView):
    """"""

    name = 'admin'
    section = 'compliance-admin'

    @property
    def get_descriptors(self):
        descriptors = get_all_descriptors()

        return descriptors

    def get_users_by_group_id(self, group_id):
        groups_tool = getToolByName(self.context, 'portal_groups')

        g = groups_tool.getGroupById(group_id)
        members = g.getGroupMembers()

        if not members:
            return []

        res = []

        for x in members:
            user = User(x.getProperty('id'),
                        x.getProperty('fullname'),
                        x.getProperty('email'), )
            res.append(user)

        return res

    # @cache      #TODO
    def get_groups_for_desc(self, descriptor):
        descriptor = descriptor.split('.')[0]
        group_id = '{}-{}'.format(CONTRIBUTOR_GROUP_ID, descriptor.lower())

        return self.get_users_by_group_id(group_id)

    @property
    def get_reviewers(self):
        group_id = REVIEWER_GROUP_ID

        return self.get_users_by_group_id(group_id)

    @property
    def get_editors(self):
        group_id = EDITOR_GROUP_ID

        return self.get_users_by_group_id(group_id)


class AdminScoring(BaseComplianceView, AssessmentDataMixin):
    name = 'admin-scoring'
    section = 'compliance-admin'

    questions = NAT_DESC_QUESTIONS
    questions_reg = REG_DESC_QUESTIONS

    def descriptor_obj(self, descriptor):
        return get_descriptor(descriptor)

    def get_available_countries(self, region_folder):
        res = [
            # id, title, definition, is_primary
            COUNTRY(x[0], x[1], "", lambda _: True)
            for x in region_folder._countries_for_region
        ]

        return res

    @cache(report_data_cache_key)
    def muids(self, country_code, country_region_code, year):
        """ Get all Marine Units for a country

        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """

        return get_marine_units(country_code,
                                country_region_code,
                                year)

    @property
    def get_descriptors(self):
        """Exclude first item, D1 """
        descriptors = get_all_descriptors()

        return descriptors[1:]

    @property
    def ndas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        for brain in brains:
            obj = brain.getObject()
            # safety check to exclude secondary articles
            obj_title = obj.title.capitalize()

            if obj_title in _get_secondary_articles():
                continue

            yield obj

    @property
    def ndas_sec(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        for brain in brains:
            obj = brain.getObject()
            # safety check to exclude primary articles
            obj_title = obj.title.capitalize()

            if obj_title not in _get_secondary_articles():
                continue

            yield obj

    def reset_assessment_data(self):
        """ Completely erase the assessment data from the system

        TODO: when implementing the regional descriptors, make sure to adjust
        """

        for obj in self.ndas:
            logger.info('Reset assessment data for %s', obj.absolute_url())

            if hasattr(obj, 'saved_assessment_data'):
                del obj.saved_assessment_data
                obj._p_changed = True

    def recalculate_score_for_objects(self, objects, questions):
        for obj in objects:
            if hasattr(obj, 'saved_assessment_data') \
                    and obj.saved_assessment_data:

                logger.info('recalculating scores for %r', obj)

                data = obj.saved_assessment_data.last()
                new_overall_score = 0
                scores = {k: v for k, v in data.items()
                          if '_Score' in k and v is not None}

                for q_id, score in scores.items():
                    id_ = score.question.id
                    article = score.question.article
                    _question = [
                        x

                        for x in questions[article]

                        if x.id == id_
                    ][0]

                    # new_score_weight = _question.score_weights
                    # _question.score_weights = new_score_weight

                    values = score.values
                    descriptor = score.descriptor

                    new_score = _question.calculate_score(descriptor,
                                                          values)

                    data[q_id] = new_score
                    new_overall_score += getattr(new_score,
                                                 'weighted_score', 0)

                data['OverallScore'] = new_overall_score
                obj.saved_assessment_data._p_changed = True

    def recalculate_scores(self):
        self.recalculate_score_for_objects(self.ndas, self.questions)
        self.recalculate_score_for_objects(self.rdas, self.questions_reg)

    def get_data(self, obj):
        """ Get assessment data for a country assessment object
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article = obj
        descr = obj.aq_parent
        region = obj.aq_parent.aq_parent
        country = obj.aq_parent.aq_parent.aq_parent
        d_obj = self.descriptor_obj(descr.id.upper())
        muids = self.muids(country.id.upper(), region.id.upper(), '2018')
        data = obj.saved_assessment_data.last()

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                last_change_name = "{}_{}_Last_update".format(article.title,
                                                              val.question.id)
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                for i, v in enumerate(val.values):
                    options = ([o.title
                                for o in val.question.get_assessed_elements(
                                    d_obj, muids=muids)] or ['All criteria'])

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue
                        option = 'ERROR with options: {} / index: {}'.format(
                            ', '.join(options), i
                        )

                    answer = val.question.answers[v]

                    yield (country.title, region.title, d_obj.id,
                           article.title, val.question.id, option, answer,
                           val.question.scores[v], state, last_change)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                last_change_name = "{}_{}_Last_update".format(article_id,
                                                              question_id)
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country.title, region.title, d_obj.id, article_id,
                       question_id, 'Summary', val, ' ', state, last_change)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country.title, region.title, d_obj.id, article_id,
                       ' ', 'Assessment Summary', val, '', state, last_change)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country.title, region.title, d_obj.id, article_id,
                       ' ', 'Recommendations', val, '', state, last_change)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                last_change_name = "{}_assess_summary_last_upd".format(
                    article_id
                )
                last_change = data.get(last_change_name, '')
                last_change = last_change and last_change.isoformat() or ''

                yield (country.title, region.title, d_obj.id, article_id,
                       ' ', 'Progress', val, '', state, last_change)

    def get_data_sec(self, obj):
        """ Get assessment data for a country assessment object
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article = obj
        country = obj.aq_parent
        data = obj.saved_assessment_data.last()
        d_obj = 'Not linked'
        muids = []

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                for i, v in enumerate(val.values):
                    options = ([o.title
                                for o in val.question.get_assessed_elements(
                                    d_obj, muids=muids)] or ['All criteria'])

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue

                    answer = val.question.answers[v]

                    yield (country.title, article.title, val.question.id,
                           option, answer, val.question.scores[v], state)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                yield (country.title, article_id, question_id,
                       'Summary', val, ' ', state)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                yield (country.title, article_id, ' ',
                       'Assessment Summary', val, '', state)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                yield (country.title, article_id, ' ',
                       'Recommendations', val, '', state)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                yield (country.title, article_id, ' ',
                       'Progress', val, '', state)

    def get_data_rda(self, obj):
        """ Get assessment data for a regional descriptor assessment
        """

        if not (hasattr(obj, 'saved_assessment_data')
                and obj.saved_assessment_data):

            return

        state = get_wf_state_id(obj)
        article = obj
        descr = obj.aq_parent
        region = obj.aq_parent.aq_parent
        d_obj = self.descriptor_obj(descr.id.upper())
        data = obj.saved_assessment_data.last()

        for k, val in data.items():
            if not val:
                continue

            if '_Score' in k:
                for i, v in enumerate(val.values):
                    options = (
                        [o.title for o in self.get_available_countries(region)]
                        or ['All criteria']
                    )

                    # TODO IndexError: list index out of range
                    # investigate this
                    # Possible cause of error: D9C2 was removed and some old
                    # questions have answered it
                    try:
                        option = options[i]
                    except IndexError:
                        continue

                    answer = val.question.answers[v]

                    yield (region.title, d_obj.id,
                           article.title, val.question.id, option, answer,
                           val.question.scores[v], state)

            elif '_Summary' in k:
                article_id, question_id, _ = k.split('_')
                yield (region.title, d_obj.id,
                       article_id, question_id, 'Summary', val, ' ', state)

            elif '_assessment_summary' in k:
                article_id, _, __ = k.split('_')
                yield (region.title, d_obj.id,
                       article_id, ' ', 'Assessment Summary', val, '', state)

            elif '_recommendations' in k:
                article_id, _ = k.split('_')
                yield (region.title, d_obj.id,
                       article_id, ' ', 'Recommendations', val, '', state)

            elif '_progress' in k:
                article_id, _ = k.split('_')
                yield (region.title, d_obj.id,
                       article_id, ' ', 'Progress', val, '', state)

    def data_to_xls(self, all_data):
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        for sheetname, labels, data in all_data:
            worksheet = workbook.add_worksheet(sheetname)

            for i, label in enumerate(labels):
                worksheet.write(0, i, label)

            x = 0

            for objdata in data:
                for row in objdata:
                    x += 1

                    for iv, value in enumerate(row):
                        worksheet.write(x, iv, value)

        workbook.close()
        out.seek(0)

        return out

    def export_scores(self, context):
        # National descriptors data
        nda_labels = ('Country', 'Region', 'Descriptor', 'Article', 'Question',
                      'Option', 'Answer', 'Score', 'State', 'Last change')
        nda_xlsdata = (self.get_data(nda) for nda in self.ndas)

        # Regional descriptors data
        rda_labels = ('Region', 'Descriptor', 'Article', 'Question',
                      'Option', 'Answer', 'Score', 'State')
        rda_xlsdata = (self.get_data_rda(rda) for rda in self.rdas)

        # Secondary Articles 3 & 4, 7
        sec_labels = ('Country', 'Article', 'Question',
                      'Option', 'Answer', 'Score', 'State')
        sec_xlsdata = (self.get_data_sec(sec) for sec in self.ndas_sec)

        all_data = [
            ('National descriptors', nda_labels, nda_xlsdata),
            ('Regional descriptors', rda_labels, rda_xlsdata),
            ('Articles 3 & 4, 7', sec_labels, sec_xlsdata)
        ]

        xlsio = self.data_to_xls(all_data)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
                           'spreadsheetml.sheet')
        fname = "-".join(['Assessment_Scores',
                          str(datetime.now().replace(microsecond=0))])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def __call__(self):

        msgs = IStatusMessage(self.request)

        if 'export-scores' in self.request.form:
            return self.export_scores(self.context)

        if 'reset-assessments' in self.request.form:
            self.reset_assessment_data()
            msgs.add('Assessments reseted successfully!', type='warning')
            logger.info('Reset score finished!')

        if 'recalculate-scores' in self.request.form:
            self.recalculate_scores()
            msgs.add('Scores recalculated successfully!', type='info')
            logger.info('Recalculating score finished!')

        return self.index()


class SetupAssessmentWorkflowStates(BaseComplianceView):

    @property
    def ndas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
        )

        for brain in brains:
            obj = brain.getObject()
            yield obj

    def __call__(self):
        changed = 0
        not_changed = 0

        logger.info("Changing workflow states to not_started...")

        for nda in self.ndas:
            state = get_wf_state_id(nda)

            if hasattr(nda, 'saved_assessment_data'):
                data = nda.saved_assessment_data.last()

                if data:
                    not_changed += 1

                    continue

            if state == 'in_work':
                changed += 1
                logger.info("State changing for {}".format(nda.__repr__()))
                transition(obj=nda, to_state='not_started')

        logger.info("States changed: {}, Not changed: {}".format(
            changed, not_changed)
        )

        return "Done"


class TranslateIndicators(BrowserView):

    def __call__(self):
        labels = get_indicator_labels().values()
        site = portal.get()
        storage = ITranslationsStorage(site)

        count = 0

        for label in labels:
            lang = get_detected_lang(label)

            if (not lang) or (lang == 'en'):
                continue

            lang = lang.upper()

            langstore = storage.get(lang, None)

            if langstore is None:
                continue

            if label not in langstore:
                langstore[label] = u''
                logger.info('Added %r to translation store for lang %s',
                            label, lang)
                count = +1

        return "Added %s labels" % count


class MigrateTranslationStorage(BrowserView):

    def __call__(self):
        site = portal.get()
        storage = ITranslationsStorage(site)
        count = 0

        for langstore in storage.values():
            for original, translated in langstore.items():
                count = +1

                if hasattr(translated, 'text'):
                    translated = translated.text
                translated = Translation(translated, 'original')

                if not translated.text.startswith('?'):
                    translated.approved = True

                langstore[original] = translated

        return "Migrated {} strings".format(count)
