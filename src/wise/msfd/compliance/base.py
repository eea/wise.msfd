from Acquisition import aq_inner
from plone.api.content import get_state
from plone.api.portal import get_tool
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql

from . import interfaces
from .nationaldescriptors.utils import row_to_dict

MAIN_FORMS = [
    # view name, (title, explanation)
    ('@@comp-start',
     ('Compliance Module',
      'Start Page'),
     ),
    ('national-descriptors-assessments/@@nat-desc-start',
     ('National descriptors',
      'Member states reports and Commission assessments'),
     ),
    ('@@comp-regional-descriptor',
     ('Regional descriptors',
      'Member states reports and Commission assessments'),
     ),
    ('@@comp-national-overviews',
     ('National overviews',
      'Overview for a Member state'),
     ),
    ('@@comp-regional-overviews',
     ('Regional overviews',
      'Overview for all Member states in a region',),
     ),
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


class Leaf(object):
    """ A generic leaf in a tree. Behaves somehow like a tree
    """

    children = ()

    def __repr__(self):
        return "<Leaf '%s'>" % self.name

    def __init__(self, name, children=None):
        self.name = name
        self.children = children or []

    def __getitem__(self, name):
        for c in self.children:
            if c.name == name:
                return c
        raise KeyError

    def __setitem__(self, name, v):
        v.name = name
        self.children.append(v)

    def add(self, item):
        if item not in self.children:
            self.children.append(item)


class BaseComplianceView(BrowserView):
    """ Base class for compliance views
    """

    main_forms = MAIN_FORMS

    report_header_template = ViewPageTemplateFile(
        'nationaldescriptors/pt/report-data-header.pt'
    )

    translate_snip = ViewPageTemplateFile('pt/translate-snip.pt')

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

        # res = db.get_unique_from_mapper(
        #     sql.MSFD11CommonLabel,
        #     'Text',
        #     sql.MSFD11CommonLabel.value == self.descriptor,
        #     sql.MSFD11CommonLabel.group == 'list-MonitoringProgramme',
        # )
        #
        # if not res:
        #     return ''
        #
        # return res[0]

    @property
    @db.use_db_session('session')
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

        return self.get_status(context)

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
