import logging
import os

import lxml.etree
from pkg_resources import resource_filename
from zope.dottedname.resolve import resolve

from Acquisition import aq_inner
from plone.api.content import get_state
from plone.api.portal import get_tool
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql
from wise.msfd.compliance.scoring import compute_score
from wise.msfd.utils import Tab

from . import interfaces
from .nationaldescriptors.utils import row_to_dict

logger = logging.getLogger('wise.msfd')

MAIN_FORMS = [Tab(*x) for x in [
    # view name, (title, explanation)
    ('@@comp-start',
     'compliance-start',    # section name
     'Compliance Module',
     'Start Page',
     ),
    ('national-descriptors-assessments/@@nat-desc-start',
     'national-descriptors',
     'National descriptors',
     'Member states reports and Commission assessments',
     ),
    ('regional-descriptors-assessments/@@reg-desc-start',
     'regional-descriptors',
     'Regional descriptors',
     'Member states reports and Commission assessments',
     ),
    ('@@comp-national-overviews',
     'national-overviews',
     'National overviews',
     'Overview for a Member state',
     ),
    ('@@comp-regional-overviews',
     'regional-overviews',
     'Regional overviews',
     'Overview for all Member states in a region',
     ),
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


class BaseComplianceView(BrowserView):
    """ Base class for compliance views
    """

    tabs_type = 'tab'
    main_forms = MAIN_FORMS

    report_header_template = ViewPageTemplateFile(
        'nationaldescriptors/pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        'nationaldescriptors/pt/assessment-header.pt'
    )

    translate_snip = ViewPageTemplateFile('pt/translate-snip.pt')

    def translate_value(self, value):
        # TODO: implement getting the translation from annotations

        translated = u'dummy translated: {}'.format(value)

        return self.translate_snip(text=value, translation=translated)

    @property
    def colspan(self):
        return 42

    @property
    def country_name(self):
        """ Get country name based on country code
        :return: 'Latvia'
        """

        name = self._country_folder.Title()

        return name

    @property
    def desc_label(self):
        """ Get the label(text) for a descriptor
        :return: 'D5 Eutrophication'
        """

        res = self._descriptor_folder.Title()

        return res

    @property
    @db.use_db_session('2012')
    def regions(self):
        """ Get all regions and subregions for a country
        :return: ['BAL', 'ANS']
        """

        t = sql.t_MSFD4_GegraphicalAreasID
        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code
        )

        res = [row_to_dict(t, r) for r in res]
        regions = set([x['RegionSubRegions'] for x in res])

        return regions

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
    def _national_descriptors_folder(self):
        return self.get_parent_by_iface(
            interfaces.INationalDescriptorsFolder
        )

    @property
    def _compliance_folder(self):
        return self.get_parent_by_iface(
            interfaces.IComplianceModuleFolder
        )

    def process_phase(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return state, title

    def get_status(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return title

    def get_transitions(self):
        wftool = get_tool('portal_workflow')
        transitions = wftool.listActionInfos(object=self.context)
        print transitions

        return [t for t in transitions if t['allowed']]

    def check_permission(self, permission, context=None):

        tool = get_tool('portal_membership')

        if context is None:
            context = self.context

        return bool(tool.checkPermission(permission, aq_inner(context)))


def get_element_by_id(root, id):
    if id.startswith('#'):
        id = id[1:]
    el = root.xpath('//*[@id = "' + id + '"]')[0]

    return el


class ElementDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        self.definition = node.text.strip()


class MetodologicalStandardDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        self.definition = node.text.strip()


class CriteriaAssessmentDefinition:
    def __init__(self, node, root):
        self.id = node.get('id')
        defn = node.find('definition')
        self.definition = defn.text.strip()

        # TODO: there are some edge cases. Handle them?
        self.is_primary = bool(['false', 'true'].index(node.get('primary',
                                                                'false')))

        self.elements = []

        for eid in node.xpath('uses-element/@href'):
            el = get_element_by_id(root, eid)
            self.elements.append(ElementDefinition(el, root))

        msid = node.xpath('uses-methodological-standard/@href')[0]
        mel = get_element_by_id(root, msid)
        self.methodological_standard = MetodologicalStandardDefinition(
            mel, root
        )

    @property
    def title(self):
        return u"{} - {}".format(self.id,
                                 self.is_primary and 'Primary' or 'Secondary')


class AssessmentQuestionDefinition:
    """ A definition for a single assessment question.

    Pass an <assessment-question> node to initialize it
    """

    def __init__(self, node, root):
        self.id = node.get('id')
        self.klass = node.get('class')
        self.use_criteria = node.get('use-criteria')
        self.definition = node.find('definition').text.strip()
        self.answers = [x.strip()
                        for x in node.xpath('answers/option/text()')]

        self.score_weights = {}

        for wn in node.iterchildren('score-weight'):
            desc = wn.get('descriptor')
            weight = wn.get('value')
            self.score_weights[desc] = weight

        sn = node.find('scoring')
        self.score_method_factory = resolve(sn.get('determination-method'))
        self.score_method_args = sn.get('determination-method-args')

        factory_method = self.score_method_factory
        method = factory_method(self.score_method_args)
        self.score_method = method

        self.scores = []

        for onode in sn.iterchildren('option'):
            si = (int(onode.get('score')), onode.text.strip())
            self.scores.append(si)

    def calculate_score(self, descriptor, values):
        return compute_score(self, descriptor, values)


def parse_elements_file(fpath):
    # Note: this parsing is pretty optimistic that there's a single descriptor
    # in the file. Keep that true
    res = []

    try:
        root = lxml.etree.parse(fpath).getroot()
    except:
        logger.exception('Could not parse file: %s', fpath)

        return

    desc_id = root.get('id')

    for critn in root.iterchildren('criteria'):

        crit = CriteriaAssessmentDefinition(critn, root)
        res.append(crit)

    return desc_id, res


def _parse_files_in_location(location, check_filename, parser):
    dirpath = resource_filename('wise.msfd', location)
    out = {}

    for fname in os.listdir(dirpath):
        if check_filename(fname):
            fpath = os.path.join(dirpath, fname)
            logger.info("Parsing file: %s", fname)
            try:
                res = parser(fpath)
            except:
                logger.exception('Could not parse file: %s', fpath)

                continue

            if res:
                desc, elements = res
                out[desc] = elements

    return out


def get_descriptor_elements(location):
    """ Parse the descriptor elements in a location and build a mapping struct

    The location argument should be a path relative to wise.msfd package.
    The return data is used to build the automatic forms.
    """
    def check_filename(fname):
        return fname.endswith('_elements.xml')

    return _parse_files_in_location(location,
                                    check_filename, parse_elements_file)


def parse_question_file(fpath):
    res = []

    root = lxml.etree.parse(fpath).getroot()
    article_id = root.get('article')

    for qn in root.iterchildren('assessment-question'):
        q = AssessmentQuestionDefinition(qn, root)
        res.append(q)

    return article_id, res


def get_questions(location):
    def check_filename(fname):
        return fname.startswith('questions_')

    return _parse_files_in_location(location,
                                    check_filename, parse_question_file)


class BaseArticle2012(BrowserView):

    def __init__(self, context, request, country_code,
                 descriptor, article,  muids, colspan):

        BrowserView.__init__(self, context, request)

        self.country_code = country_code
        self.descriptor = descriptor
        self.article = article
        self.muids = muids
        # self.colspan = colspan
