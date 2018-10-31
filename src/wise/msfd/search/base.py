from zope.interface import implements

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form

from . import interfaces
from ..base import BaseEnhancedForm, BaseUtil, EmbeddedForm
from ..db import get_item_by_conditions
from ..interfaces import IMainForm
from ..utils import get_registered_form_sections


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

    # def item_title(self, item):
    #     state = inspect(item)
    #
    #     if state.identity:
    #         id = state.identity[0]
    #     else:
    #         id = 0
    #
    #     return (item.__class__.__name__, id)


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


MAIN_FORMS = (
    ('msfd-start', ('Start', 'About search engine')),
    ('msfd-ca', ('Article 7', 'Competent Authorities')),
    ('msfd-c1', ('Articles 4, 8, 9 & 10', '2012 reporting exercise')),
    ('msfd-c2', ('Article 11', '2014 reporting exercise')),
    ('msfd-c3', ('Articles 13 & 14', '2015 reporting exercise')),
    ('msfd-c4', ('Articles 8, 9 & 10', '2018 reporting exercise')),
)


class MainForm(BaseEnhancedForm, Form):
    """ The main forms need to inherit from this clas
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

    @buttonAndHandler(u'Download as XLS', name='download')
    def handle_download(self, action):
        self.should_download = True

    @property
    def title(self):
        return [x[1] for x in self.main_forms if x[0] == self.name][0]

    def update(self):
        super(MainForm, self).update()
        self.data, self.errors = self.extractData()

        has_values = self.data.values() and all(self.data.values())

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
        download_action = self.find_download_action()

        if download_action in (None, False):
            del self.actions['download']

        if download_action and self.should_download:
            # TODO: need to implement this as xls response

            data = download_action()

            sh = self.request.response.setHeader

            sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
               'spreadsheetml.sheet')
            sh('Content-Disposition', 'attachment; filename=marinedb.xlsx')

            return data.read()

        return super(MainForm, self).render()

    def find_download_action(self):
        """ Look for a download method in all subform children
        """

        ctx = self

        while hasattr(ctx, 'subform'):

            if hasattr(ctx, 'download_results'):
                return ctx.download_results

            ctx = ctx.subform

        if hasattr(ctx, 'download_results'):
            return ctx.download_results
