from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import sql
from .. import db
from ..base import BasePublicPage, EmbeddedForm, MainFormWrapper
from ..db import (get_all_records, get_all_records_join,
                  get_item_by_conditions, get_item_by_conditions_art_6)
from ..interfaces import IMarineUnitIDsSelect
from ..sql_extra import MSCompetentAuthority
from ..utils import scan, db_objects_to_dict, group_data
from .a11 import StartArticle11Form
from .a1314 import StartArticle1314Form
from .a18 import StartArticle18Form
from .a4 import A4Form
from .base import MAIN_FORMS, ItemDisplayForm, MainForm
from .utils import data_to_xls, get_form


class StartView(BrowserView, BasePublicPage):
    main_forms = MAIN_FORMS
    name = 'msfd-start'


class StartMSCompetentAuthoritiesForm(MainForm):
    name = 'msfd-ca'

    record_title = title = 'Article 7 (Member States - Competent Authorities)'
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
    """ The implementation for the Article 9 (GES determination) form
    """

    mapper_class = MSCompetentAuthority
    order_field = 'C_CD'
    css_class = "left-side-form"

    blacklist = ('Import_Time', 'Import_FileName')
    use_blacklist = False

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


class StartA4Form(MainForm):
    name = 'msfd-mru'
    session_name = '2012'

    fields = Fields(interfaces.IStartArticles8910)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


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
    """ The implementation for the Article 9 (GES determination) form
    """
    mc = sql.MSFD4RegionalCooperation
    order_field = 'MSFD4_RegionalCooperation_ID'
    css_class = "left-side-form"

    # extra_data_template = ViewPageTemplateFile('pt/extra-data-simple.pt')
    # extra_data_pivot = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    # blacklist = ('MSFD4_Import_ID', 'MSFD4_Import_Time',
    #              'MSFD4_Import_FileName')
    # use_blacklist = False

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
            [mci.MSFD4_Import_ReportingCountry,
             mcr.RegionsSubRegions,mcr.Topic,
             mcr.NatureCoordination, mcr.RegionalCoherence,
             mcr.RegionalCoordinationProblems],
            mcr,
            mci.MSFD4_Import_ID,
            *conditions,
            page=page,
            r_codes=r_codes
        )

        return res

    # def get_extra_data(self):
    #     m = sql.MSFD4RegionalCooperation
    #     blacklist = ('MSFD4_RegionalCooperation_Import',
    #                  'MSFD4_RegionalCooperation_ID')
    #
    #     r_codes = self.get_form_data_by_key(self.context, 'region_subregions')
    #
    #     coops = db.get_all_columns_from_mapper(
    #         m,
    #         'MSFD4_RegionalCooperation_ID',
    #         m.MSFD4_RegionalCooperation_Import == self.item.MSFD4_Import_ID,
    #         # m.RegionsSubRegions.in_(r_codes)
    #     )
    #
    #     # filter results by regions
    #     filtered_coops = []
    #     for row in coops:
    #         if any(region in row.RegionsSubRegions for region in r_codes):
    #             filtered_coops.append(row)
    #
    #     rows = db_objects_to_dict(filtered_coops, excluded_columns=blacklist)
    #
    #     regcoop = group_data(rows, 'RegionsSubRegions')
    #     pivot_html = self.extra_data_pivot(extra_data=[
    #         ('Regional Cooperation', regcoop),
    #     ])
    #
    #     return [
    #         ('', pivot_html)
    #     ]


class StartArticle8910Form(MainForm):
    """ Select one of the article: 8(a,b,c,d)/9/10
    """

    name = 'msfd-c1'

    fields = Fields(interfaces.IArticleSelect)
    session_name = '2012'

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

        data = self.get_main_form().data
        klass = get_form(data['article'])

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


class StartArticle89102018Form(MainForm):
    record_title = 'Articles 8, 9, 10'
    name = 'msfd-c4'

    fields = Fields(interfaces.IArticleSelect2018)
    session_name = '2018'

    def get_subform(self):
        article = self.data['article']

        if article:
            if isinstance(article, tuple):
                klass = article[0]
            else:
                klass = article

            return klass(self, self.request)


StartArticle89102018View = wrap_form(StartArticle89102018Form, MainFormWrapper)

StartArticle18View = wrap_form(StartArticle18Form, MainFormWrapper)

# discover and register associated views

scan('a4')
scan('a8ac')
scan('a8b')
scan('a9')
scan('a10')
scan('a89102018')
