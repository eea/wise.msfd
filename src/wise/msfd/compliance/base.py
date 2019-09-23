import logging
from collections import namedtuple
from datetime import datetime

import lxml.etree
from sqlalchemy.orm import aliased
from zope.component import getMultiAdapter
from zope.dottedname.resolve import resolve
from zope.interface import implements
from zope.security import checkPermission

from Acquisition import aq_inner
from eea.cache import cache
from plone.api import user
from plone.api.content import get_state
from plone.api.portal import get_tool
from plone.api.user import get_roles
from plone.memoize import ram
from plone.memoize.view import memoize
from Products.Five.browser import BrowserView
from wise.msfd import db, sql, sql2018
from wise.msfd.base import BasePublicPage
from wise.msfd.compliance.scoring import Score  # , compute_score
from wise.msfd.compliance.utils import get_assessors
from wise.msfd.compliance.vocabulary import ASSESSED_ARTICLES  # , REGIONS
from wise.msfd.gescomponents import (get_descriptor, get_features,
                                     get_marine_units, sorted_criterions)
from wise.msfd.translation.interfaces import ITranslationContext
from wise.msfd.utils import (Tab, _parse_files_in_location, natural_sort_key,
                             row_to_dict, timeit)

from . import interfaces
from .interfaces import ICountryDescriptorsFolder

# from time import time


logger = logging.getLogger('wise.msfd')
edw_logger = logging.getLogger('edw.logger')
edw_logger.setLevel('WARNING')

STATUS_COLORS = {
    "approved": "success",
    "not_started": "default",
    "in_work": "danger",
    "in_draft_review": "warning",
    "in_draft_review_com": "warning-2",
    "in_final_review": "primary",
    "in_final_review_tl": "primary",
    "in_final_review_com": "success-2",
}

PROCESS_STATUS_COLORS = {
    "notstarted": "default",
    "phase1": "warning",
    "phase2": "primary",
    "phase3": "success",
}

MAIN_FORMS = [Tab(*x) for x in [
    # view name, (title, explanation)
    ('@@comp-start',
     'compliance-start',    # section name
     'Assessment Module',
     'Start Page',
     '',
     lambda view: True,
     ),
    ('national-descriptors-assessments/@@nat-desc-start',
     'national-descriptors',
     'Descriptor - national',
     'Member states reports and Commission assessments',
     '',
     lambda view: True,
     ),
    ('regional-descriptors-assessments/@@reg-desc-start',
     'regional-descriptors',
     'Descriptor - regional',
     'Member states reports and Commission assessments',
     '',
     lambda view: True,
     ),
    ('@@comp-national-overviews',
     'national-overviews',
     'Overview - national',
     'Overview for a Member state',
     '',
     lambda view: True,
     ),
    ('@@comp-regional-overviews',
     'regional-overviews',
     'Overview - regional',
     'Overview for all Member states in a region',
     '',
     lambda view: True,
     ),

    ('help',
     'help-section',
     '<span class="fa fa-question-circle fa-lg"></span>',
     '<span>&nbsp;</span>',
     'manage-users',
     lambda view: True,
     ),

    ('@@compliance-admin',
     'compliance-admin',
     '<span class="fa fa-cogs fa-lg"></span>',
     '<span>&nbsp;</span>',
     'manage-users',
     lambda view: view.is_search and view.check_permission(
         'wise.msfd: Manage Compliance')
     )
]
]


class Container(object):
    """ A container can render its children forms and views
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.children = []

    def __call__(self):
        self.update()

        return self.render()

    def update(self):
        pass

    def render(self):
        lines = []

        for child in self.children:
            lines.append(child())

        # TODO: maybe use a template for this?

        return u'\n'.join(lines)


def report_data_cache_key(func, self, *args, **kwargs):
    _args = args

    if not _args:
        region = getattr(self, 'country_region_code',
                         ''.join(getattr(self, 'regions', '')))

        country = self.country_code
        year = self.year
    else:
        country = _args[0]
        region = _args[1]
        year = _args[2]

    res = '_cache_' + func.__name__ + '_'.join([country, region, year])
    res = res.replace('.', '').replace('-', '')

    return res


class SecurityMixin:

    def check_permission(self, permission, context=None):

        tool = get_tool('portal_membership')

        if context is None:
            context = self.context

        return bool(tool.checkPermission(permission, aq_inner(context)))

    @property
    def read_only_access(self):
        can_edit = self.check_permission('wise.msfd: Edit Assessment')

        return not can_edit

    def can_manage(self):
        return self.check_permission('wise.msfd: Manage Compliance')

    def can_view_assessment_data(self, context=None):
        return self.check_permission('wise.msfd: View Assessment Data',
                                     context)

    def can_edit_assessment_data(self, context=None):
        return self.check_permission('wise.msfd: Edit Assessment', context)


class BaseComplianceView(BrowserView, BasePublicPage, SecurityMixin):
    """ Base class for compliance views
    """

    tabs_type = 'tab'
    main_forms = MAIN_FORMS
    _translatables = None
    status_colors = STATUS_COLORS
    process_status_colors = PROCESS_STATUS_COLORS

    def get_current_user_roles(self, context=None):
        current_user = user.get_current().getId()
        params = {
            "username": current_user
        }

        if context:
            params['obj'] = context

        roles = get_roles(**params)

        return roles

    def _get_user_group(self, user):
        """ Returns the color according to the role of the user, EC or TL
        """

        roles = get_roles(username=user, obj=self.context)

        if 'Editor' in roles:
            return 'dark'

        return 'light'

    @property
    def can_comment(self):
        return self.check_permission('Add portal content', self.context)

    @property
    def assessor_list(self):
        assessors = get_assessors()

        if not assessors:
            return []

        assessors_list = [x.strip() for x in assessors.split(',')]

        return assessors_list

    @property
    def json_map_url(self):
        return self.root_url() + '/@@json-map'

    _descriptor = None      # can be overriden

    @property
    def colspan(self):
        return 42

    @property
    def country_name(self):
        """ Get country name based on country code

        :return: ex: 'Latvia'
        """

        return self._country_folder.Title()

    # @property
    # def desc_label(self):
    #     """ Get the label(text) for a descriptor
    #
    #     :return: 'D5 Eutrophication'
    #     """
    #
    #     res = self._descriptor_folder.Title()
    #
    #     return res

    @property
    def descriptor_label(self):
        # same as desc_label

        return self._descriptor_folder.Title()

    @property
    @db.use_db_session('2012')
    def regions(self):
        """ Get all regions and subregions for a country

        :return: ['BAL', 'ANS']

        TODO: do we need a 2018 compatible version?
        """

        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code
        )

        res = [row_to_dict(t, r) for r in res]
        regions = set([x['RegionSubRegions'] for x in res])

        return regions

    @property
    @timeit
    @cache(report_data_cache_key)
    def muids(self):
        """ Get all Marine Units for a country

        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """

        return get_marine_units(self.country_code,
                                self.country_region_code,
                                self.year)

    def get_parent_by_iface(self, iface):
        for parent in self.request.other['PARENTS']:
            if iface.providedBy(parent):
                return parent

        raise ValueError('Parent not found: {}'.format(iface))

    def root_url(self):
        root = self.get_parent_by_iface(interfaces.IComplianceModuleFolder)

        return root and root.absolute_url() or ''

    @property
    def _article_assessment(self):
        return self.get_parent_by_iface(
            interfaces.INationalDescriptorAssessment
        )

    @property
    def article(self):
        return self._article_assessment.getId().capitalize()

    @property
    def _descriptor_folder(self):
        return self.get_parent_by_iface(
            interfaces.IDescriptorFolder
        )

    @property
    def descriptor(self):
        if self._descriptor:        # can be bypassed for D1
            return self._descriptor

        return self._descriptor_folder.getId().upper()

    @property
    def _country_folder(self):
        return self.get_parent_by_iface(
            interfaces.ICountryDescriptorsFolder
        )

    @property
    def country_code(self):
        return self._country_folder.getId().upper()

    @property
    def country_title(self):
        return self._country_folder.title

    @property
    def _countryregion_folder(self):
        return self.get_parent_by_iface(
            interfaces.INationalRegionDescriptorFolder
        )

    @property
    def country_region_code(self):
        return self._countryregion_folder.getId().upper()

    @property
    def country_region_name(self):
        # return REGIONS[self.country_region_code]

        return self._countryregion_folder.title

    @property
    def article_name(self):
        art_name = [x[1] for x in ASSESSED_ARTICLES if x[0] == self.article]

        if art_name:
            return art_name[0]

        return self.article

    @property       # TODO: memoize
    def descriptor_obj(self):
        return get_descriptor(self.descriptor)

    @property
    def descriptor_title(self):
        return self.descriptor_obj.template_vars['title']

    @property
    def _national_descriptors_folder(self):
        return self.get_parent_by_iface(
            interfaces.INationalDescriptorsFolder
        )

    @property
    def _compliance_folder(self):
        return self.get_parent_by_iface(
            interfaces.IComplianceModuleFolder
        )

    def get_wf_state_id(self, context):
        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]  # assumes one wf
        wf_state = wf.states[state]
        wf_state_id = wf_state.id or state

        return wf_state_id

    def process_phase(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return state, title

    def get_status_color(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        wf_state_id = wf_state.id or state

        return self.status_colors.get(wf_state_id, "secondary")

    def get_status(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return title

    # @cache(key=lambda ast: '/'.join(ast.getPhysicalPath()),
    #        dependencies='')
    def has_new_comments(self, assessment):
        """ Returns True/False/None if assessment has new comments.

        True: has new comments
        False: doesn't have new comments
        None: this assessment has never been seen
        """

        token = '-'.join(assessment.getPhysicalPath())
        token = 's-' + token

        last_seen = self.request.cookies.get(token)

        if not last_seen:
            return None

        last_seen = float(last_seen[:10] + '.' + last_seen[10:])
        dt = datetime.utcfromtimestamp(last_seen)

        latest_from_folders = []

        for folder_id in ('tl', 'ec'):
            q_folders = assessment[folder_id].contentValues()

            if q_folders:
                # TODO: we rely on ordered folders, not sure if correct
                latest = [
                    folder.contentValues()[-1].modification_date.utcdatetime()

                    for folder in q_folders

                    if folder.contentValues()
                ]
                latest = latest and max(latest) or None
                latest_from_folders.append(latest)

        try:
            latest = latest_from_folders and max(latest_from_folders) or None
        except:
            logger.exception("Error in getting latest seen")
            latest = None

        if not latest:
            return None

        return latest > dt

    def get_transitions(self):
        wftool = get_tool('portal_workflow')
        transitions = wftool.listActionInfos(object=self.context)

        return [t for t in transitions if t['allowed']]

    @memoize
    def translate_view(self):
        return getMultiAdapter((self.context, self.request),
                               name="translation-view")

    def translate_value(self, fieldname, value, source_lang):
        is_translatable = fieldname in self.TRANSLATABLES

        v = self.translate_view()

        # source_lang = self.country_code

        return v.translate(source_lang=source_lang,
                           value=value,
                           is_translatable=is_translatable)


Target = namedtuple('Target', ['id', 'title', 'definition', 'year'])


def _a10_ids_cachekey(method, self, descriptor, **kwargs):
    muids = [m.id for m in kwargs['muids']]
    key = '{}-{}-{}'.format(
        method.__name__, descriptor.id, ','.join(muids)
    )

    return key


def get_weights_from_xml(node):
    """ Initialize with values from questions xml
    """

    score_weights = {}

    for wn in node.iterchildren('score-weight'):
        desc = wn.get('descriptor')
        weight = wn.get('value')
        score_weights[desc] = weight

    return score_weights


class AssessmentQuestionDefinition:
    """ A definition for a single assessment question.

    Pass an <assessment-question> node to initialize it
    """

    def __init__(self, article, node, root, position):
        # self.node = node
        self.article = article
        self.id = node.get('id')
        self.klass = node.get('class')
        self.use_criteria = node.get('use-criteria')
        self.definition = u"{}: {}".format(
            self.id, node.find('definition').text.strip())
        self.answers = [x.strip()
                        for x in node.xpath('answers/option/text()')]
        self.scores = [s.strip()
                       for s in node.xpath('answers/option/@score')]
        self.score_weights = get_weights_from_xml(node)

        sn = node.find('scoring')
        self.score_method = resolve(sn.get('determination-method'))

    def calculate_score(self, descriptor, values):
        score_obj = Score(self, descriptor, values)

        # if all options are 'Not relevant' return None, so the question will
        # behave like not answered and it will not count towards overall score
        # if score_obj.max_score == 0:
        #     return None

        return score_obj

    def _art_89_ids(self, descriptor, **kwargs):
        return sorted_criterions(descriptor.criterions)

    @db.use_db_session('2012')
    def __get_a10_2012_targets(self, ok_ges_ids, muids):
        sess = db.session()

        T = sql.MSFD10Target
        dt = sql.t_MSFD10_DESCrit

        D_q = sess.query(dt).join(T)
        D_a = aliased(dt, alias=D_q.subquery())

        targets = sess\
            .query(T)\
            .order_by(T.ReportingFeature)\
            .filter(T.MarineUnitID.in_(muids))\
            .filter(T.Topic == 'EnvironmentalTarget')\
            .join(D_a)\
            .filter(D_a.c.GESDescriptorsCriteriaIndicators.in_(ok_ges_ids))\
            .distinct()\
            .all()

        res = [Target(r.ReportingFeature.replace(' ', '_').lower(),
                      r.ReportingFeature,
                      r.Description,
                      '2012')

               for r in targets]

        # sort Targets and make them distinct
        res_sorted = sorted(set(res), key=lambda _x: natural_sort_key(_x.id))

        return res_sorted

    def __get_a10_2018_targets(self, descr_obj, ok_ges_ids, muids):
        targets = self.__get_a10_2018_targets_from_table(ok_ges_ids, muids)
        # targets = self.__get_a10_2018_targets_from_view(
        #     descr_obj, ok_ges_ids,muids
        # )

        res = [Target(t.TargetCode.encode('ascii', errors='ignore'),
                      t.TargetCode,
                      t.Description,
                      '2018')

               for t in targets]

        # sort Targets and make them distinct
        res_sorted = sorted(set(res), key=lambda _x: natural_sort_key(_x.id))

        return res_sorted

    @db.use_db_session('2018')
    def __get_a10_2018_targets_from_table(self, ok_ges_ids, muids):
        T = sql2018.ART10TargetsTarget
        MU = sql2018.ART10TargetsMarineUnit
        t_MRU = T.ART10_Targets_MarineUnit
        G = sql2018.ART10TargetsTargetGESComponent
        sess = db.session()

        q = sess \
            .query(T) \
            .filter(t_MRU.has(MU.MarineReportingUnit.in_(muids))) \
            .join(G) \
            .filter(G.GESComponent.in_(ok_ges_ids))

        res = [x for x in q]

        return res

    @db.use_db_session('2018')
    def __get_a10_2018_targets_from_view(self, descr_obj, ok_ges_ids, muids):
        t = sql2018.t_V_ART10_Targets_2018
        descriptor = descr_obj.id
        sess = db.session()

        q = sess.query(t).filter(t.c.MarineReportingUnit.in_(muids))

        ges_filtered = []

        for row in q:
            ges_comps = getattr(row, 'GESComponents', ())
            ges_comps = set([g.strip() for g in ges_comps.split(',')])

            if ges_comps.intersection(ok_ges_ids):
                ges_filtered.append(row)

        if descriptor.startswith('D1.'):
            feature_filtered = []
            ok_features = set([f.name for f in get_features(descriptor)])

            for row in ges_filtered:
                feats = set(row.Features.split(','))

                if feats.intersection(ok_features):
                    feature_filtered.append(row)

            ges_filtered = feature_filtered

        return ges_filtered

    @ram.cache(_a10_ids_cachekey)
    def _art_10_ids(self, descriptor, **kwargs):
        muids = [x.id for x in kwargs['muids']]
        ok_ges_ids = descriptor.all_ids()

        if descriptor.id.startswith('D1.'):
            ok_ges_ids.add('D1')

        targets_2018 = self.__get_a10_2018_targets(descriptor, ok_ges_ids,
                                                   muids)
        # targets_2012 = self.__get_a10_2012_targets(ok_ges_ids, muids)
        targets_all = targets_2018

        return targets_all

    def get_assessed_elements(self, descriptor, **kwargs):
        """ Get a list of filtered assessed elements for this question.
        """

        res = self.get_all_assessed_elements(descriptor, **kwargs)

        if self.article in ['Art8', 'Art9']:
            res = filtered_criterias(res, self, descriptor)
        else:
            res = filtered_targets(res, self)

        return sorted_criterions(res)

    def get_all_assessed_elements(self, descriptor, **kwargs):
        """ Get a list of unfiltered assessed elements for this question.

        For Articles 8, 9 it returns a list of criteria elements
        For Article 10 it returns a list of targets

        Return a list of identifiable elements that need to be assessed.
        """
        impl = {
            'Art8': self._art_89_ids,
            'Art9': self._art_89_ids,
            'Art10': self._art_10_ids,
        }

        return impl[self.article](descriptor, **kwargs)


def filtered_questions(questions, phase):
    """ Get the questions appropriate for the phase
    """

    if phase == 'phase3':
        res = [q for q in questions if q.klass == 'coherence']
    else:
        res = [q for q in questions if q.klass != 'coherence']

    return res


def filtered_criterias(criterias, question, descriptor):
    crits = []

    if question.use_criteria == 'primary':
        crits = [c for c in criterias if c.is_primary(descriptor) is True]

    if question.use_criteria == 'secondary':
        crits = [c for c in criterias if c.is_primary(descriptor) is False]

    if question.use_criteria == 'all':
        crits = criterias

    if question.use_criteria == 'none':
        crits = []

    return sorted_criterions(crits)


def filtered_targets(targets, question):
    _targets = []

    if question.use_criteria == 'all-targets':
        _targets = targets

    if question.use_criteria == '2018-targets':
        _targets = [t for t in targets if t.year == '2018']

    return _targets


def parse_question_file(fpath):
    res = []

    root = lxml.etree.parse(fpath).getroot()
    article_id = root.get('article')

    for i, qn in enumerate(root.iterchildren('assessment-question')):
        q = AssessmentQuestionDefinition(article_id, qn, root, i)
        res.append(q)

    return article_id, res


def get_questions(location='compliance/nationaldescriptors/data'):
    def check_filename(fname):
        return fname.startswith('questions_')

    return _parse_files_in_location(location,
                                    check_filename, parse_question_file)


class BaseArticle2012(BrowserView):

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids):

        BrowserView.__init__(self, context, request)

        self.country_code = country_code
        self.region_code = region_code
        self.descriptor = descriptor
        self.article = article
        self.muids = muids


class TranslationContext(object):
    implements(ITranslationContext)

    def __init__(self, context):
        self.context = context

    @property
    def language(self):
        for context in self.context.REQUEST.PARENTS:
            if ICountryDescriptorsFolder.providedBy(context):
                return context.getId().upper()

        return 'EN'
