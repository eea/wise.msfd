from __future__ import absolute_import
import logging
import re
from collections import defaultdict
from datetime import datetime

from zope.interface import implements

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.base import BasePublicPage
from wise.msfd.utils import Tab
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from . import interfaces
from .. import sql2018
from ..base import BaseEnhancedForm, BaseUtil, EmbeddedForm
from ..db import (get_item_by_conditions, get_related_record,
                  latest_import_ids_2018, use_db_session)
from ..interfaces import IMainForm
from .utils import data_to_xls, get_registered_form_sections

logger = logging.getLogger('wise.msfd')


class ItemDisplayForm(EmbeddedForm):
    """ Generic form for displaying records
    """

    implements(interfaces.IItemDisplayForm)

    fields = Fields(interfaces.IRecordSelect)

    template = ViewPageTemplateFile('pt/item-display-form.pt')
    data_template = ViewPageTemplateFile('pt/item-display.pt')
    extra_data = None
    extra_data_template = ViewPageTemplateFile('pt/extra-data.pt')

    mapper_class = None     # This will be used to retrieve the item
    order_field = None      # This will be used to properly page between items

    def update(self):
        super(ItemDisplayForm, self).update()

        if not self.get_main_form().reset_page:
            self.data['page'] = self.widgets['page'].value
        else:
            self.widgets['page'].value = 0
            self.data['page'] = 0

        self.count, self.item = self.get_db_results()

        if self.count == (int(self.data['page']) + 1):
            del self.actions['next']

        if int(self.data['page']) == 0:
            del self.actions['prev']

    def updateWidgets(self, prefix=None):
        super(ItemDisplayForm, self).updateWidgets()
        self.widgets['page'].mode = 'hidden'

    @buttonAndHandler(u'Prev', name='prev')
    def handle_prev(self, action):
        value = int(self.widgets['page'].value)
        self.widgets['page'].value = max(value - 1, 0)

    @buttonAndHandler(u'Next', name='next')
    def handle_next(self, action):
        value = int(self.widgets['page'].value)
        self.widgets['page'].value = value + 1

    def get_extra_data(self):
        return []

    def extras(self):
        return self.extra_data_template()

    def get_page(self):
        page = self.data.get('page')

        if page:
            return int(page)
        else:
            return 0

    def get_db_results(self):
        page = self.get_page()
        muid = self.get_marine_unit_id()

        args = [self.mapper_class, self.order_field]

        if muid:
            args.append(self.mapper_class.MarineUnitID == muid)

        res = get_item_by_conditions(*args, page=page)

        return res

    @use_db_session('2018')
    def latest_import_ids_2018(self):
        latest_ids = latest_import_ids_2018()

        return latest_ids

    # def item_title(self, item):
    #     state = inspect(item)
    #
    #     if state.identity:
    #         id = state.identity[0]
    #     else:
    #         id = 0
    #
    #     return (item.__class__.__name__, id)


class ItemDisplayForm2018(ItemDisplayForm):
    reported_date_info = {
        'mapper_class': sql2018.ReportedInformation,
        'col_import_id': 'Id',
        'col_import_time': 'ReportingDate'
    }

    def get_import_id(self):
        import_id = self.item.IdReportedInformation

        return import_id

    def get_reported_date(self):
        return self.get_reported_date_2018()

    def get_current_country(self):
        report_id = self.get_import_id()

        _, res = get_related_record(
            sql2018.ReportedInformation,
            'Id',
            report_id
        )

        country = self.print_value(res.CountryCode)

        return country


class MultiItemDisplayForm(ItemDisplayForm):
    template = ViewPageTemplateFile('pt/multi-item-display.pt')

    fields = Fields(interfaces.IRecordSelect)

    def get_sections(self):

        klasses = get_registered_form_sections(self)
        views = [k(self, self.request) for k in klasses]

        return views


class ItemDisplay(BrowserView, BaseUtil):
    """ A not-registered view that will render inline (a database result)
    """

    index = ViewPageTemplateFile('pt/simple-item-display.pt')

    data_template = ViewPageTemplateFile('pt/item-display.pt')
    extra_data_template = ViewPageTemplateFile('pt/extra-data.pt')

    data = {}

    def __init__(self, context, request):
        self.__parent__ = self.context = context
        self.request = request

        self.count = 0
        self.item = None

        res = self.get_db_results()

        if res:
            self.count, self.item = res

    def __call__(self):

        if not self.item:
            return ''

        return self.index()

    def get_db_results(self):
        raise NotImplementedError

    def get_page(self):
        page = self.context.data.get('page')

        if page:
            return int(page)
        else:
            return 0

    def get_extra_data(self):
        return []

    def extras(self):
        return self.extra_data_template()


def true(view):
    return True


MAIN_FORMS = (
    Tab('msfd-start', 'msfd-start', 'Start',
        'About MSFD reporting data explorer', '', '', true),
    Tab('msfd-mru', 'msfd-mru', 'Article 4', 'Marine Units',
        ' Geographical areas used by Member States for the implementation of\n\
        the Directive compatible with the marine regions and subregions listed\n\
        in the Directive.',
        '', true),
    # Tab('msfd-rc', 'msfd-rc', 'Article 6', 'Regional cooperation',
    #     'Member States coordination with third countries having sovereignty or\n\
    #     jurisdiction over waters in the same marine region or subregion.',
    #     '', true),
    Tab('msfd-ca', 'msfd-ca', 'Article 7', 'Competent Authorities',
        'Member States authority or authorities for the implementation of the\n\
        Directive with respect to their marine waters.',
        '', true),
    Tab('msfd-a8', 'msfd-a8', 'Article 8', 'Assessments',
        'Assessments of Member States marine waters comprising: a) analysis of\n\
        the essential features and characteristics, b) analysis of the\n\
        predominant pressures and impacts, and c) economic and social analysis\n\
        of the use of those waters.', '', true),
    Tab('msfd-a9', 'msfd-a9', 'Article 9',
        'Determination of good environmental status',
        'Determination of the good environmental status of the Descriptors,\n\
        for Member States marine waters and in respect of each marine region\n\
        or subregion.', '', true),
    Tab('msfd-a10', 'msfd-a10', 'Article 10',
        'Establishment of environmental targets',
        'Environmental targets and associated indicators for Member States\n\
        marine waters to guide progress towards achieving good environmental\n\
        status in their marine environment.', '', true),
    Tab('msfd-c2', 'msfd-c2', 'Article 11', 'Monitoring programmes',
        'Programmes established by Member States to monitor the environmental\n\
        status of their marine waters.', '', true),
    Tab('msfd-c3', 'msfd-c3', 'Articles 13 & 18',
        'Programmes of measures & Progress of PoM',
        'Measures to be taken in order to achieve or maintain good environmental\n\
        status, and progress in the implementation of the programmes of measures.',
        '', true),
    Tab('msfd-a14', 'msfd-a14', 'Article 14',
        'Exceptions',
        'Exceptions reported whenever good environmental status cannot be achieved.',
        '', true),
    # Tab('msfd-c4', 'msfd-c4', 'Articles <br/>8, 9 & 10',
    #     '2018 reporting exercise', '', true),
    # Tab('msfd-c5', 'msfd-c5', 'Article 18',
    #     'Progress on the implementation of PoM', '', true),
    Tab('msfd-c6', 'msfd-c6', 'Article 19.3', 'Datasets used',
        'Access to data resulting from the GES assessments and the monitoring\n\
        programmes.', '', true),
)


class MainForm(BaseEnhancedForm, BasePublicPage, Form):
    """ The main forms need to inherit from this class
    """

    implements(IMainForm)
    template = ViewPageTemplateFile('../pt/mainform.pt')
    ignoreContext = True
    reset_page = False
    subform = None
    subform_content = None
    should_download = False     # flag that signals download button is hit
    main_forms = MAIN_FORMS
    # method = 'get'

    def __init__(self, context, request):
        Form.__init__(self, context, request)

    @buttonAndHandler(u'Apply filters', name='continue')
    def handle_continue(self, action):
        self.reset_page = True

    @buttonAndHandler(u'Download as spreadsheet', name='download')
    def handle_download(self, action):
        self.should_download = True

    @property
    def title(self):
        return [x[1] for x in self.main_forms if x[0] == self.name][0]

    @property
    def main_title(self):
        return [x[2] for x in self.main_forms if x[0] == self.name][0]

    @property
    def subtitle(self):
        return [x[3] for x in self.main_forms if x[0] == self.name][0]

    @property
    def spreadsheet_title(self):
        title = [x[2] for x in self.main_forms if x[0] == self.name][0]

        title_from_subforms = self.find_spreadsheet_title()

        if title_from_subforms:
            title = title_from_subforms

        title = re.sub(r"[^a-zA-Z0-9]+", "_", title)

        return title

    def update(self):
        super(MainForm, self).update()
        self.data, self.errors = self.extractData()

        has_values = list(self.data.values()) and all(self.data.values())

        if has_values:
            self.subform = self.get_subform()

            if self.subform:
                # we need to update and "execute" the subforms to be able to
                # discover them, because the decision process regarding
                # discovery is done in the update() method of subforms
                self.subform_content = self.subform()
                # self.subform.update()

    # @cache(request_cache_key)
    def render(self):
        blacklist_labels, download_action = self.find_download_action()

        if download_action in (None, False):
            del self.actions['download']

        if download_action and self.should_download:
            # TODO: need to implement this as xls response

            data = download_action()
            data_xls = data_to_xls(data, blacklist_labels)

            sh = self.request.response.setHeader

            sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
               'spreadsheetml.sheet')

            logger.info("Spreadsheet title: %s", self.spreadsheet_title)
            fname = self.spreadsheet_title or 'marinedb'
            fname = fname + '_' + str(datetime.now().replace(microsecond=0))
            fname = fname.replace(' ', '_').replace('(', '').replace(')', '')\
                .replace('&', '_')
            sh('Content-Disposition', 'attachment; filename=%s.xlsx' % fname)

            return data_xls.read()

        return super(MainForm, self).render()

    def find_download_action(self):
        """ Look for a download method in all subform children
        """
        ctx = self

        while hasattr(ctx, 'subform'):

            if hasattr(ctx, 'download_results'):
                return (getattr(ctx, 'blacklist_labels', []),
                        ctx.download_results)

            ctx = ctx.subform

        if hasattr(ctx, 'download_results'):
            return getattr(ctx, 'blacklist_labels', []), ctx.download_results

    def find_spreadsheet_title(self):
        """ Not used, just an experiment to provide custom spreadsheet titles
            across all articles

        """
        ctx = self.subform

        while hasattr(ctx, 'subform'):

            if hasattr(ctx, 'record_title'):
                return ctx.record_title

            ctx = ctx.subform

        if hasattr(ctx, 'record_title'):
            return ctx.record_title
