from Products.Five.browser import BrowserView

from . import interfaces

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
