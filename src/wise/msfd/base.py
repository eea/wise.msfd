from zope.browserpage.viewpagetemplatefile import \
    ViewPageTemplateFile as Z3ViewPageTemplateFile
from zope.component import queryMultiAdapter
from zope.interface import implements

# from eea.cache import cache
from plone.z3cform.layout import FormWrapper
# from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from .db import get_available_marine_unit_ids, threadlocals
from .interfaces import IEmbeddedForm, IMainForm, IMarineUnitIDSelect
from .utils import all_values_from_field, get_obj_fields, print_value
from .widget import MarineUnitIDSelectFieldWidget


class BaseUtil(object):
    """ Generic utilities for search views
    """

    # value_template = ViewPageTemplateFile('pt/value-display.pt')

    def title_as_id(self, text):
        """ Given some text, return an id
        """

        return text.replace(' ', '_')\
            .replace('/', '-')\
            .replace(',', '')\
            .lower()

    def name_as_title(self, text):
        """ Given a "CamelCase" text, changes it to "Title Text"

        This is used to transform the database column names to usable labels
        """
        text = text.replace('_', ' ')

        for l in range(len(text) - 1):
            if text[l].islower() and text[l + 1].isupper():
                text = text[:(l + 1)] + ' ' + \
                    text[(l + 1):]

        return text

    def form_name(self):
        """ Returns an auto-generated form name, based on class name
        """

        return self.__class__.__name__.lower()

    def get_marine_unit_ids(self):
        """ Return the selected ids by looking up for data in parent forms
        """

        parent = self

        while True:
            if not hasattr(parent, 'data'):
                return []
            ids = parent.data.get('marine_unit_ids')

            if ids:
                break
            else:
                parent = parent.context

        return ids

    def get_marine_unit_id(self):
        """ Return the current selected MarineUnitID looking up data in parents
        """

        parent = self

        while True:
            mid = parent.data.get('marine_unit_id')

            if mid:
                break
            else:
                parent = parent.context

        return mid

    def get_obj_fields(self, obj):
        """ Inspect an SA object and return its field names
        """

        return get_obj_fields(obj)

    def print_value(self, value):
        return print_value(value)

    def get_main_form(self):
        """ Crawl back form chain to get to the main form
        """

        context = self

        while not IMainForm.providedBy(context):
            context = context.context

        return context

    def get_record_title(self):
        context = self

        while not hasattr(context, 'record_title'):
            context = context.context

        return context.record_title

    def get_form_data_by_key(self, context, key):
        while context:
            data = getattr(context, 'data', None)

            if data:
                value = data.get(key, None)

                if value:
                    return value
            context = getattr(context, 'context', None)

        return None

    def get_flattened_data(self, context):
        """ Return all form data from all present forms
        """
        res = {}

        while context:
            data = getattr(context, 'data', None)

            if data:
                res.update(data)

            if IMainForm.providedBy(context):
                break

            context = getattr(context, 'context', None)

        return res


class BaseEnhancedForm(object):
    """ Provides a set of default behaviors for enhanced forms
    """

    def extractData(self):
        """ Override to be able to provide defaults
        """
        data, errors = Form.extractData(self)

        for k, v in data.items():
            if not v:
                default = getattr(self, 'default_' + k, None)

                if default:
                    value = data[k] = default()

                    if not value:
                        continue
                    widget = self.widgets[k]
                    widget.value = value
                    field = widget.field.bind(self.context)
                    field.default = value
                    widget.field = field
                    widget.ignoreRequest = True
                    widget.update()

        return data, errors

    def __new__(cls, context, request):
        # introspect the class to automatically set
        # default_X and get_selected_X methods

        for name in cls.fields:
            # print "Setting default field", name
            default = 'default_' + name
            selected = 'get_selected_' + name

            if not hasattr(cls, default):
                def default_impl(self):
                    local_name = name[:]
                    field = self.fields[local_name]

                    return all_values_from_field(self, field)

                default_impl.func_name = default
                setattr(cls,
                        default,
                        default_impl
                        )

            if not hasattr(cls, selected):
                def selected_impl(self):
                    local_name = name[:]

                    return self.data[local_name]

                selected_impl.func_name = selected
                setattr(cls,
                        selected,
                        selected_impl
                        )

        return object.__new__(cls)


class MainFormWrapper(FormWrapper):
    """ Override mainform wrapper to be able to return XLS file
    """

    index = ViewPageTemplateFile('pt/layout.pt')

    def __init__(self, context, request):
        FormWrapper.__init__(self, context, request)
        threadlocals.session_name = self.form.session_name

    def render(self):
        if 'text/html' not in self.request.response.getHeader('Content-Type'):
            return self.contents

        return super(MainFormWrapper, self).render()


class EmbeddedForm(BaseEnhancedForm, Form, BaseUtil):
    """ Our most basic super-smart-superclass for forms

    It can embed other children forms
    """

    implements(IEmbeddedForm)
    ignoreContext = True

    template = ViewPageTemplateFile('pt/subform.pt')
    subform_class = None

    def __init__(self, context, request):
        Form.__init__(self, context, request)
        self.__parent__ = self.context      # = context
        # self.request = request
        self.data = {}

    def update(self):
        super(EmbeddedForm, self).update()

        self.data, errors = self.extractData()

        has_values = self.data.values() and all(self.data.values())

        if (not errors) and has_values:
            subform = self.get_subform()

            if subform is not None:
                self.subform = subform

    def get_subform(self, klass=None):
        if klass is None:
            klass = self.subform_class

        if klass is None:
            return None

        return klass(self, self.request)

    def extras(self):
        extras = queryMultiAdapter((self, self.request), name='extras')

        if extras:
            return extras()


class MarineUnitIDSelectForm(EmbeddedForm):
    """ Base form for displaying information for a single MarineUnitID
    """

    template = ViewPageTemplateFile('pt/marine-unit-id-form.pt')
    fields = Fields(IMarineUnitIDSelect)
    fields['marine_unit_id'].widgetFactory = MarineUnitIDSelectFieldWidget
    mapper_class = None         # what type of objects are we focused on?

    css_class = "left-side-form"

    def update(self):
        # Override the default to be able to have a default marine unit id
        super(MarineUnitIDSelectForm, self).update()

        self.data, errors = self.extractData()

        if (not (errors or (None in self.data.values()))) and \
                self.data.values():
            subform = self.get_subform()

            if subform is not None:
                self.subform = subform

    def updateWidgets(self, prefix=None):
        """ """
        super(MarineUnitIDSelectForm, self).updateWidgets(prefix=prefix)

        widget = self.widgets["marine_unit_id"]
        widget.template = Z3ViewPageTemplateFile("search/pt/marine-widget.pt")

    def get_available_marine_unit_ids(self):
        # filter available records based on the parent selected MUIDs
        assert self.mapper_class

        # Get selected marineunitids. Method from base class
        ids = self.get_marine_unit_ids()

        # print "Parent available MUIDS", ids

        count, res = get_available_marine_unit_ids(
            ids, self.mapper_class
        )

        return (count, [x[0] for x in res])
