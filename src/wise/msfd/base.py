# pylint: skip-file
"""base.py"""
from __future__ import absolute_import
import re

from zope.browserpage.viewpagetemplatefile import \
    ViewPageTemplateFile as Z3ViewPageTemplateFile
from zope.component import queryMultiAdapter
from zope.interface import implementer

from Acquisition import aq_inner
from plone.api.portal import get_tool
from plone.z3cform.layout import FormWrapper
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.interfaces import (
    IEditAssessmentForm, IEditAssessmentFormCrossCutting,
    IEditAssessmentFormSecondary)
from z3c.form.field import Fields
from z3c.form.form import Form

from six.moves import range

from . import sql, sql2018
from .db import (get_all_specific_columns, get_available_marine_unit_ids,
                 get_marine_unit_ids, threadlocals, use_db_session)
from .interfaces import IEmbeddedForm, IMainForm, IMarineUnitIDSelect
from .labels import DISPLAY_LABELS
from .utils import (all_values_from_field, get_obj_fields, print_value,
                    TRANSFORMS)
from .widget import MarineUnitIDSelectFieldWidget


re_art11_name_clean = re.compile(r'^Q\d+\w\s+')


class BaseUtil(object):
    """ Generic utilities for search views
    """

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
        article = getattr(self, 'article', 'ALL')
        all_labels = DISPLAY_LABELS['ALL']
        art_labels = DISPLAY_LABELS.get(article, {})
        labels = all_labels.copy()
        labels.update(art_labels)

        if text in labels:
            return labels[text]

        text = text.replace('_', ' ')

        if re_art11_name_clean.match(text):
            text = re_art11_name_clean.sub('', text)

        for l in range(len(text) - 1):
            if text[l].islower() and text[l + 1].isupper():
                text = (text[:(l + 1)] + ' ' + text[l+1].lower() +
                        text[(l + 2):])

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

    def get_import_id(self):
        """ This method needs to be overridden, to return the import ID
        of the displayed item
        """

        return 0

    def _find_reported_date_info(self):
        context = self

        while hasattr(context, 'context'):
            if hasattr(context, 'reported_date_info'):
                return context.reported_date_info

            context = context.context

        if hasattr(context, 'reported_date_info'):
            return context.reported_date_info

        return {}

    @use_db_session('2018')
    def get_reported_date_from_db(self, filename):
        """get_reported_date_from_db"""
        mc = sql2018.ReportingHistory

        count, data = get_all_specific_columns(
            [mc.DateReleased],
            mc.FileName == filename
        )

        if not count:
            return None

        date = data[0].DateReleased

        return date

    def format_reported_date(self, reported_date):
        """format_reported_date"""
        try:
            reported_date = reported_date.strftime('%Y %b %d')
        except:
            pass

        return reported_date

    @use_db_session('2018')
    def get_reported_date_2018(self):
        """get_reported_date_2018"""
        not_available = 'Not available'
        reported_date_info = self._find_reported_date_info()

        if not reported_date_info:
            return not_available

        import_id = self.get_import_id()
        mc = reported_date_info['mapper_class']
        col_import_id = reported_date_info['col_import_id']
        col_import_time = reported_date_info['col_import_time']

        count, data = get_all_specific_columns(
            [getattr(mc, col_import_time)],
            getattr(mc, col_import_id) == import_id
        )

        if not count:
            return not_available

        reported_date = data[0]
        reported_date = getattr(reported_date, col_import_time)
        reported_date = self.format_reported_date(reported_date)

        return reported_date

    def get_reported_date(self):
        """get_reported_date"""
        not_available = 'Not available'
        reported_date_info = self._find_reported_date_info()

        if not reported_date_info:
            return not_available

        import_id = self.get_import_id()
        mc = reported_date_info['mapper_class']
        col_import_id = reported_date_info['col_import_id']
        # col_import_time = reported_date_info['col_import_time']
        col_filename = reported_date_info['col_filename']

        count, data = get_all_specific_columns(
            [getattr(mc, col_filename)],
            getattr(mc, col_import_id) == import_id
        )

        if not count:
            return not_available

        filename = getattr(data[0], col_filename)

        reported_date = self.get_reported_date_from_db(filename)

        # reported_date = data[0]
        # reported_date = getattr(reported_date, col_import_time)

        if not reported_date:
            return not_available

        reported_date = self.format_reported_date(reported_date)

        return reported_date

    def get_current_country(self):
        """get_current_country"""
        country_2012 = self.get_current_country_2012()

        if country_2012:
            return country_2012

        country_2018 = self.get_current_country_2018()

        if country_2018:
            return country_2018

        return ''

    @use_db_session('2018')
    def get_current_country_2018(self):
        """get_current_country_2018"""
        mc = sql2018.MarineReportingUnit
        try:
            mru = self.get_marine_unit_id()
        except:
            return ''

        count, data = get_all_specific_columns(
            [mc.CountryCode],
            mc.MarineReportingUnitId == mru
        )

        if not count:
            return ''

        country_code = data[0]
        print_value = self.print_value(country_code.CountryCode, 'CountryCode')

        return print_value

    @use_db_session('2012')
    def get_current_country_2012(self):
        """get_current_country_2012"""
        """ Get the country for the current selected MarineUnitID

        :return: Germany
        """

        mc = sql.t_MSFD4_GegraphicalAreasID
        try:
            mru = self.get_marine_unit_id()
        except:
            return ''

        count, data = get_all_specific_columns(
            [mc.c.MemberState],
            mc.c.MarineUnitID == mru
        )

        if not count:
            return ''

        country_code = data[0]
        print_value = self.print_value(country_code.MemberState, 'CountryCode')

        return print_value

    def get_obj_fields(self, obj, use_blacklist=True):
        """ Inspect an SA object and return its field names

        Some objects have _field attribute (Article 6 Regional Cooperation),
        where we do not need to order the fields or use blacklist,
        because the columns and order are specified manually
        """

        if hasattr(obj, '_fields'):
            return obj._fields

        return get_obj_fields(obj, use_blacklist=use_blacklist)

    def print_value(self, value, field_name=None):
        """print_value"""
        if not field_name:
            return print_value(value)

        if field_name in TRANSFORMS:
            try:
                value = value.strip()
            except AttributeError:
                # do not strip, value is not string
                pass

            transformer = TRANSFORMS.get(field_name)

            return transformer(value)

        # if 'Code' in field_name:
        #     return value

        # 'blacklist_labels' is a list of field names, for these fields
        # we will print the original value

        if field_name in getattr(self, 'blacklist_labels', []):
            return value

        return print_value(value)

    def get_main_form(self):
        """ Crawl back form chain to get to the main form
        """

        context = self

        while not IMainForm.providedBy(context):
            context = context.context

        return context

    def get_record_title(self):
        """get_record_title"""
        context = self

        while not hasattr(context, 'record_title'):
            context = context.context

        return context.record_title

    def get_form_data_by_key(self, context, key):
        """get_form_data_by_key"""
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
                    # Art9 2012 Art6 strange error
                    try:
                        field.default = value
                    except:
                        continue
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

                default_impl.__name__ = default
                setattr(cls,
                        default,
                        default_impl
                        )

            if not hasattr(cls, selected):
                def selected_impl(self):
                    local_name = name[:]

                    return self.data[local_name]

                selected_impl.__name__ = selected
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


@implementer(IEditAssessmentForm)
class EditAssessmentFormWrapper(MainFormWrapper):
    """ Wrapper for EditAssessmentDataForm

    Needed to override the page title """


@implementer(IEditAssessmentFormSecondary)
class EditAssessmentFormWrapperSecondary(MainFormWrapper):
    """ Wrapper for EditAssessmentDataForm

    Needed to override the page title """


@implementer(IEditAssessmentFormCrossCutting)
class EditAssessmentFormWrapperCrossCutting(MainFormWrapper):
    """ Wrapper for EditAssessmentDataForm

    Needed to override the page title """


@implementer(IEmbeddedForm)
class EmbeddedForm(BaseEnhancedForm, Form, BaseUtil):
    """ Our most basic super-smart-superclass for forms

    It can embed other children forms
    """

    ignoreContext = True

    template = ViewPageTemplateFile('pt/subform.pt')
    subform_class = None

    def __init__(self, context, request):
        Form.__init__(self, context, request)
        self.__parent__ = self.context
        self.data = {}

    def update(self):
        """update"""
        super(EmbeddedForm, self).update()
        self.data, errors = self.extractData()

        has_values = list(self.data.values()) and all(self.data.values())

        if (not errors) and has_values:
            subform = self.get_subform()

            if subform is not None:
                self.subform = subform

    def get_subform(self, klass=None):
        """get_subform"""
        if klass is None:
            klass = self.subform_class

        if klass is None:
            return None

        return klass(self, self.request)

    def extras(self):
        """extras"""
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

        if (not (errors or (None in list(self.data.values())))) and \
                list(self.data.values()):
            subform = self.get_subform()

            if subform is not None:
                self.subform = subform

    def updateWidgets(self, prefix=None):
        """ updateWidgets"""
        super(MarineUnitIDSelectForm, self).updateWidgets(prefix=prefix)

        widget = self.widgets["marine_unit_id"]
        widget.template = Z3ViewPageTemplateFile("search/pt/marine-widget.pt")

    def get_available_marine_unit_ids(self):
        """get_available_marine_unit_ids"""
        # filter available records based on the parent selected MUIDs
        assert self.mapper_class

        # Get selected marineunitids. Method from base class
        ids = self.get_marine_unit_ids()

        count, res = get_available_marine_unit_ids(
            ids, self.mapper_class
        )

        return (count, [x[0] for x in res])


class MarineUnitIDSelectForm2012(MarineUnitIDSelectForm):
    """ Something like a subclass for MarineUnitIDSelectForm
        needed for Art 8, 9, 10 year 2012
        to override the 'get_available_marine_unit_ids' method
    """

    def get_available_marine_unit_ids(self, parent=None):
        """get_available_marine_unit_ids"""
        data = {}

        if not parent:
            # find AreaTypes form
            context = self

            while hasattr(context, 'context'):
                if hasattr(context, 'get_selected_area_types'):
                    parent = context

                    break
                context = context.context

        # lookup values in the inheritance tree

        for crit in ['area_types', 'member_states', 'region_subregions']:
            data[crit] = getattr(parent, 'get_selected_' + crit)()
            parent = parent.context

        _, all_mrus = get_marine_unit_ids(**data)

        count, res = get_available_marine_unit_ids(
            all_mrus, self.mapper_class
        )

        return count, [x[0] for x in res]


class BasePublicPage(object):
    """ TODO: explain purpose of this page
    """

    def check_permission(self, permission, context=None):
        """check_permission"""
        tool = get_tool('portal_membership')

        if context is None:
            context = self.context

        return bool(tool.checkPermission(permission, aq_inner(context)))

    @property
    def is_search(self):
        """is_search"""
        return hasattr(self, '_compliance_folder')
