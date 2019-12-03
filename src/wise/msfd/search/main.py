from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import sql
from .. import db
from ..base import BasePublicPage, EmbeddedForm, MainFormWrapper
from ..db import (get_all_records, get_all_records_join,
                  get_item_by_conditions, get_item_by_conditions_art_6,
                  threadlocals)
from ..interfaces import IMarineUnitIDsSelect
from ..sql_extra import MSCompetentAuthority
from ..utils import scan
from .a11 import StartArticle11Form
from .a1314 import StartArticle1314Form
from .a18 import StartArticle18Form
from .a4 import A4Form, A4MemberStatesForm
from .base import MAIN_FORMS, ItemDisplayForm, MainForm
from .utils import (data_to_xls, get_form, register_form_art4,
                    register_form_art8910)


class StartView(BrowserView, BasePublicPage):
    main_forms = MAIN_FORMS
    name = 'msfd-start'


class StartMSCompetentAuthoritiesForm(MainForm):
    name = 'msfd-ca'

    record_title = title = 'Article 7 (Competent Authorities)'
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget
    session_name = '2012'

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
    """ The implementation for the Article 7
    """

    mapper_class = MSCompetentAuthority
    order_field = 'C_CD'
    css_class = "left-side-form"

    blacklist = ('Import_Time', 'Import_FileName')
    use_blacklist = False

    def get_reported_date(self):
        not_available = 'Not available'
        filename = self.item.Import_FileName

        reported_date = self.get_reported_date_from_db(filename)

        if not reported_date:
            return not_available

        return reported_date

    def get_current_country(self):
        country_code = self.item.C_CD

        if not country_code:
            return ''

        country = self.print_value(country_code)

        return country

    def get_db_results(self):
        page = self.get_page()

        args = [self.mapper_class, self.order_field]
        c_codes = self.context.data.get('member_states')

        if c_codes:
            args.append(self.mapper_class.C_CD.in_(c_codes))

        res = get_item_by_conditions(*args, page=page)

        return res


@register_form_art4
class A4Form2012to2018(EmbeddedForm):
    title = "2012-2018 reporting cycle"

    fields = Fields(interfaces.IStartArticles8910)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


@register_form_art4
class A4Form2018to2024(EmbeddedForm):
    title = "2018-2024 reporting cycle"

    fields = Fields(interfaces.IStartArticles8910)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A4MemberStatesForm(self, self.request)


class StartA4Form(MainForm):
    name = 'msfd-mru'
    session_name = '2012'

    fields = Fields(interfaces.IStartArticle4)

    def get_subform(self):
        klass = self.data.get('reporting_cycle')

        return klass(self, self.request)


StartArticle4View = wrap_form(StartA4Form, MainFormWrapper)


class StartRegionalCoopForm(MainForm):
    name = 'msfd-rc'

    record_title = title = 'Article 6 (Regional cooperation)'
    fields = Fields(interfaces.IRegionSubregionsArt6)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget
    session_name = '2012'

    def get_subform(self):
        return RegionalCoopForm(self, self.request)


StartRegionalCoopView = wrap_form(StartRegionalCoopForm,
                                  MainFormWrapper)


class RegionalCoopForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt6)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return RegionalCoopItemDisplay(self, self.request)

    def download_results(self):
        mci = sql.MSFD4Import
        mcr = sql.MSFD4RegionalCooperation
        c_codes = self.data.get('member_states')

        import_ids = db.get_unique_from_mapper(
            sql.MSFD4Import,
            'MSFD4_Import_ID',
            sql.MSFD4Import.MSFD4_Import_ReportingCountry.in_(c_codes)
        )
        cols = [mci.MSFD4_Import_ReportingCountry] + self.get_obj_fields(mcr)

        count, data = get_all_records_join(
            cols,
            mcr,
            mcr.MSFD4_RegionalCooperation_Import.in_(import_ids)
        )

        xlsdata = [
            ('RegionalCooperation', data),
        ]

        return data_to_xls(xlsdata)


class RegionalCoopItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 6 display form
    """

    mc = sql.MSFD4RegionalCooperation
    order_field = 'MSFD4_RegionalCooperation_ID'
    css_class = "left-side-form"

    reported_date_info = {
        'mapper_class': sql.MSFD4Import,
        'col_import_id': 'MSFD4_Import_ID',
        'col_import_time': 'MSFD4_Import_Time',
        'col_filename': 'MSFD4_Import_FileName'
    }

    blacklist = ('MSFD4_Import_ID', )
    blacklist_labels = ('Topic', )

    def get_import_id(self):
        import_id = self.item.MSFD4_Import_ID

        return import_id

    def get_current_country(self):
        country_code = self.item.MSFD4_Import_ReportingCountry

        if not country_code:
            return ''

        country = self.print_value(country_code)

        return country

    def get_db_results(self):
        page = self.get_page()
        mci = sql.MSFD4Import
        mcr = sql.MSFD4RegionalCooperation
        conditions = []

        c_codes = self.get_form_data_by_key(self.context, 'member_states')
        r_codes = self.get_form_data_by_key(self.context, 'region_subregions')

        if c_codes:
            conditions.append(mci.MSFD4_Import_ReportingCountry.in_(c_codes))

        res = get_item_by_conditions_art_6(
            [mci.MSFD4_Import_ID,
             mci.MSFD4_Import_ReportingCountry,
             mcr.RegionsSubRegions, mcr.Topic,
             mcr.NatureCoordination, mcr.RegionalCoherence,
             mcr.RegionalCoordinationProblems],
            mcr,
            mci.MSFD4_Import_ID,
            *conditions,
            page=page,
            r_codes=r_codes
        )

        return res


class StartArticle8910Form(MainForm):
    """ Select one of the articles: 8(a,b,c,d)/9/10
    """

    name = 'msfd-c14'
    session_name = '2012'

    fields = Fields(interfaces.IReportingPeriodSelect)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        threadlocals.session_name = session_name

        return klass(self, self.request)


@register_form_art8910
class StartArticle89102012Form(EmbeddedForm):
    """ Select one of the article: 8(a,b,c,d)/9/10
    """
    title = "2012 reporting exercise"
    # name = 'msfd-c1'

    fields = Fields(interfaces.IArticleSelect)
    session_name = '2012'
    permission = 'zope2.View'

    def get_subform(self):
        if self.data['article']:
            return RegionForm(self, self.request)


class RegionForm(EmbeddedForm):
    """ Select the memberstate, region, area form
    """

    fields = Fields(interfaces.IStartArticles8910)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)

    # if hasattr(context, 'get_selected_region_subregions'):
    #     regions = context.get_selected_region_subregions()
    #
    #     if regions:
    #         conditions.append(t.c.RegionSubRegions.in_(regions))


class MemberStatesForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return AreaTypesForm(self, self.request)


class AreaTypesForm(EmbeddedForm):

    fields = Fields(interfaces.IAreaTypes)
    fields['area_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        # needed for marine unit ids vocabulary
        # TODO: is this still needed?
        # self.data['member_states'] = self.context.data['member_states']
        # self.data['region_subregions'] = \
        #     self.context.context.data['region_subregions']

        # data = self.get_main_form().data
        # if data['article'] == 'a4form':
        #     klass = get_form(data['article'])
        #
        #     return klass(self, self.request)

        if self.get_main_form().name == 'msfd-mru':
            return A4Form(self, self.request)

        # data = self.get_main_form().data
        # klass = get_form(data['article'])

        article = self.get_form_data_by_key(self, 'article')
        klass = get_form(article)

        return super(AreaTypesForm, self).get_subform(klass)

        # return MarineUnitIDsForm(self, self.request)

    def get_available_marine_unit_ids(self):
        return self.subform.get_available_marine_unit_ids()


StartArticle8910View = wrap_form(StartArticle8910Form, MainFormWrapper)


class MarineUnitIDsForm(EmbeddedForm):
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


@register_form_art8910
class StartArticle89102018Form(EmbeddedForm):
    title = "2018 reporting exercise"
    record_title = 'Articles 8, 9, 10'
    # name = 'msfd-c4'

    fields = Fields(interfaces.IArticleSelect2018)
    session_name = '2018'
    permission = 'wise.ViewReports'

    def get_subform(self):
        article = self.data['article']

        if article:
            if isinstance(article, tuple):
                klass = article[0]
            else:
                klass = article

            return klass(self, self.request)


# StartArticle89102018View = wrap_form(StartArticle89102018Form, MainFormWrapper)

StartArticle18View = wrap_form(StartArticle18Form, MainFormWrapper)

# discover and register associated views

scan('a4')
scan('a8ac')
scan('a8b')
scan('a9')
scan('a10')
scan('a89102018')
