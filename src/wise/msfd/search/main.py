from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db
from ..base import EmbededForm, MainFormWrapper
from ..db import get_all_records, get_item_by_conditions
from ..interfaces import IMarineUnitIDsSelect
from ..sql_extra import MSCompetentAuthority
from ..utils import data_to_xls, get_form, scan
from .a11 import StartArticle11Form
from .a1314 import StartArticle1314Form
from .base import MAIN_FORMS, ItemDisplayForm, MainForm


class StartView(BrowserView):
    main_forms = MAIN_FORMS
    name = 'msfd-start'


class StartMSCompetentAuthoritiesForm(MainForm):
    name = 'msfd-ca'

    record_title = title = 'Member States - Competent Authorities'
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget
    session_name = 'session'

    def get_subform(self):
        return CompetentAuthorityItemDisplay(self, self.request)

    def download_results(self):
        c_codes = self.data.get('member_states')
        count, data = get_all_records(
            MSCompetentAuthority,
            MSCompetentAuthority.C_CD.in_(c_codes)
        )

        xlsdata = [
            ('MSCompetentAuthority', data),
        ]

        return data_to_xls(xlsdata)


StartMSCompetentAuthoritiesView = wrap_form(StartMSCompetentAuthoritiesForm,
                                            MainFormWrapper)


class CompetentAuthorityItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 9 (GES determination) form
    """
    mapper_class = MSCompetentAuthority
    order_field = 'C_CD'
    css_class = "left-side-form"

    # TODO: implement excel download method
    def get_db_results(self):
        page = self.get_page()

        args = [self.mapper_class, self.order_field]
        c_codes = self.context.data.get('member_states')

        if c_codes:
            args.append(self.mapper_class.C_CD.in_(c_codes))

        res = get_item_by_conditions(*args, page=page)

        return res


class StartArticle8910Form(MainForm):
    """ Select one of the article: 8(a,b,c,d)/9/10
    """

    name = 'msfd-c1'

    fields = Fields(interfaces.IArticleSelect)
    session_name = 'session'

    def get_subform(self):
        if self.data['article']:
            return RegionForm(self, self.request)


class RegionForm(EmbededForm):
    """ Select the memberstate, region, area form
    """

    fields = Fields(interfaces.IStartArticles8910)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


class MemberStatesForm(EmbededForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return AreaTypesForm(self, self.request)


class AreaTypesForm(EmbededForm):

    fields = Fields(interfaces.IAreaTypes)
    fields['area_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        # needed for marine unit ids vocabulary
        # TODO: is this still needed?
        self.data['member_states'] = self.context.data['member_states']
        self.data['region_subregions'] = \
            self.context.context.data['region_subregions']

        data = self.get_main_form().data

        if data['article'] == 'a4form':
            klass = get_form(data['article'])

            return klass(self, self.request)

        return MarineUnitIDsForm(self, self.request)

    def get_available_marine_unit_ids(self):
        return self.subform.get_available_marine_unit_ids()


StartArticle8910View = wrap_form(StartArticle8910Form, MainFormWrapper)


class MarineUnitIDsForm(EmbededForm):
    """ Select the MarineUnitID based on MemberState, Region and Area
    """

    fields = Fields(IMarineUnitIDsSelect)
    fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        data = self.get_main_form().data
        klass = get_form(data['article'])

        return super(MarineUnitIDsForm, self).get_subform(klass)

    def get_available_marine_unit_ids(self):
        marine_unit_ids = self.data.get('marine_unit_ids')

        if marine_unit_ids:
            data = self.data
        else:
            data = {}
            parent = self.context

            # lookup values in the inheritance tree

            for crit in ['area_types', 'member_states', 'region_subregions']:
                data[crit] = getattr(parent, 'get_selected_' + crit)()
                parent = parent.context

        return db.get_marine_unit_ids(**data)


StartArticle11View = wrap_form(StartArticle11Form, MainFormWrapper)
StartArticle1314View = wrap_form(StartArticle1314Form, MainFormWrapper)


class StartArticle89102018Form(MainForm):
    record_title = 'Articles 8, 9, 10'
    name = 'msfd-c4'

    fields = Fields(interfaces.IArticleSelect2018)
    session_name = 'session_2018'

    def get_subform(self):
        article = self.data['article']

        if article:
            if isinstance(article, tuple):
                klass = article[0]
            else:
                klass = article

            return klass(self, self.request)


StartArticle89102018View = wrap_form(StartArticle89102018Form, MainFormWrapper)

# discover and register associated views

scan('a4')
scan('a8ac')
scan('a8b')
scan('a9')
scan('a10')
scan('a89102018')
