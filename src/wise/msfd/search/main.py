from __future__ import absolute_import
from plone.z3cform.layout import wrap_form
from Products.Five.browser import BrowserView
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import sql
from .. import db
from ..base import BasePublicPage, EmbeddedForm, MainFormWrapper
from ..db import (get_competent_auth_data, get_all_records,
                  get_all_records_join, get_item_by_conditions_art_6,
                  threadlocals)
from ..interfaces import IMarineUnitIDsSelect
from ..sql import t_MS_CompetentAuthorities
from ..utils import scan
from .a11 import StartArticle11Form
from .a1314 import StartArticle1314Form, StartArticle14Form
from .a19 import StartArticle19Form
from .a4 import A4Form, A4MemberStatesForm
from .a9 import A9Form
from .a10 import A10Form
from .base import MAIN_FORMS, ItemDisplayForm, MainForm
from .utils import (data_to_xls, get_form, register_form_art4,
                    register_form_a8_2012, register_form_art8,
                    register_form_a9_2012, register_form_art9,
                    register_form_a10_2012, register_form_art10)


class StartView(BrowserView, BasePublicPage):
    main_forms = MAIN_FORMS
    name = 'msfd-start'


class StartMSCompetentAuthoritiesForm(MainForm):
    name = 'competent-authorities'

    record_title = title = 'Article 7 (Competent Authorities)'
    fields = Fields(interfaces.IMemberStatesArt7)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget
    session_name = '2012'

    def get_subform(self):
        return CompetentAuthorityItemDisplay(self, self.request)


StartMSCompetentAuthoritiesView = wrap_form(StartMSCompetentAuthoritiesForm,
                                            MainFormWrapper)


class CompetentAuthorityItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 7
    """

    mapper_class = t_MS_CompetentAuthorities
    order_field = 'C_CD'
    css_class = "left-side-form"

    blacklist = ('Import_Time', 'Import_FileName', 'C_CD')
    blacklist_labels = ('C_CD', )
    use_blacklist = False

    def get_reported_date(self):
        not_available = 'Not available'
        filename = self.item.Import_FileName

        reported_date = self.get_reported_date_from_db(filename)

        if not reported_date:
            return not_available

        reported_date = self.format_reported_date(reported_date)

        return reported_date

    def get_current_country(self):
        country_code = self.item.C_CD

        if not country_code:
            return ''

        country = self.print_value(country_code, 'CountryCode')

        return country

    def download_results(self):
        c_codes = self.context.data.get('member_states')
        conditions = [t_MS_CompetentAuthorities.c.C_CD.in_(c_codes)]
        cnt, data = get_competent_auth_data(*conditions, raw=True)

        xlsdata = [
            ('MSCompetentAuthority', data),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()

        conditions = []
        c_codes = self.context.data.get('member_states')

        if c_codes:
            conditions.append(self.mapper_class.c.C_CD.in_(c_codes))

        cnt, data = get_competent_auth_data(*conditions)

        return cnt, data[page]


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
    name = 'marine-units'
    session_name = '2012'

    fields = Fields(interfaces.IStartArticle4)

    def get_subform(self):
        klass = self.data.get('reporting_cycle')

        return klass(self, self.request)


StartArticle4View = wrap_form(StartA4Form, MainFormWrapper)


class StartRegionalCoopForm(EmbeddedForm):
    record_title = title = 'Article 6 (Regional cooperation)'
    fields = Fields(interfaces.IRegionSubregionsArt6)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget
    session_name = '2012'

    def get_subform(self):
        return RegionalCoopForm(self, self.request)


@register_form_a8_2012
class RegionalCoopFormArt8(StartRegionalCoopForm):
    topic = 'Art8'


@register_form_a9_2012
class RegionalCoopFormArt9(StartRegionalCoopForm):
    topic = 'Art9'


@register_form_a10_2012
class RegionalCoopFormArt10(StartRegionalCoopForm):
    topic = 'Art10'


class RegionalCoopForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt6)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return RegionalCoopItemDisplay(self, self.request)


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

    blacklist = ('MSFD4_Import_ID', 'MSFD4_Import_ReportingCountry')
    blacklist_labels = ('Topic', )

    def get_reported_date(self):
        rep_date = super(RegionalCoopItemDisplay, self).get_reported_date()
        default = 'Not available'

        if rep_date != default:
            return rep_date

        import_id = self.get_import_id()
        t = sql.t_MSFD4_ReportingInformation

        count, data = db.get_all_specific_columns(
            [t.c.ReportingDate],
            t.c.MSFD4_ReportingInformation_Import == import_id
        )

        if count:
            return self.format_reported_date(data[0].ReportingDate)

        return default

    def get_import_id(self):
        import_id = self.item.MSFD4_Import_ID

        return import_id

    def get_current_country(self):
        country_code = self.item.MSFD4_Import_ReportingCountry

        if not country_code:
            return ''

        country = self.print_value(country_code, 'CountryCode')

        return country

    def download_results(self):
        mci = sql.MSFD4Import
        mcr = sql.MSFD4RegionalCooperation
        c_codes = self.get_form_data_by_key(self, 'member_states')

        import_ids = db.get_unique_from_mapper(
            sql.MSFD4Import,
            'MSFD4_Import_ID',
            sql.MSFD4Import.MSFD4_Import_ReportingCountry.in_(c_codes),
            raw=True
        )
        cols = [mci.MSFD4_Import_ReportingCountry] + self.get_obj_fields(mcr)

        count, data = get_all_records_join(
            cols,
            mcr,
            mcr.MSFD4_RegionalCooperation_Import.in_(import_ids),
            mcr.Topic == self.context.context.topic,
            raw=True
        )

        xlsdata = [
            ('RegionalCooperation', data),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        mci = sql.MSFD4Import
        mcr = sql.MSFD4RegionalCooperation
        conditions = [
            mcr.Topic == self.context.context.topic
        ]

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


class StartArticle8Form(MainForm):
    """ Select one of the articles: 8(a,b,c,d)/9/10
    """

    name = 'assessments'
    session_name = '2012'

    fields = Fields(interfaces.IReportingPeriodSelectA8)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        threadlocals.session_name = session_name

        return klass(self, self.request)


class StartArticle9Form(MainForm):
    """ Select one of the articles: 8(a,b,c,d)/9/10
    """

    name = 'determination-of-good-environmental-status'
    session_name = '2012'

    fields = Fields(interfaces.IReportingPeriodSelectA9)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        threadlocals.session_name = session_name

        return klass(self, self.request)


class StartArticle10Form(MainForm):
    """ Select one of the articles: 8(a,b,c,d)/9/10
    """

    name = 'establishment-of-environmental-targets'
    session_name = '2012'

    fields = Fields(interfaces.IReportingPeriodSelectA10)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        threadlocals.session_name = session_name

        return klass(self, self.request)


@register_form_art8
class StartArticle82012Form(EmbeddedForm):
    """ Select one of the article: 8(a,b,c,d)/9/10
    """
    title = "2012 reporting exercise"

    fields = Fields(interfaces.IArticleSelectA8)
    session_name = '2012'
    permission = 'zope2.View'

    def get_subform(self):
        # if self.data['article']:
        #     return RegionForm(self, self.request)

        article = self.get_form_data_by_key(self, 'article')
        if article == 'a81cform':
            return RegionForm(self, self.request)

        klass = get_form(article)

        return super(StartArticle82012Form, self).get_subform(klass)


class RegionForm(EmbeddedForm):
    """ Select the memberstate, region, area form
    """

    fields = Fields(interfaces.IRegionSubregions)
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


class MemberStatesFormArt9(EmbeddedForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        # return AreaTypesForm(self, self.request)

        return A9Form(self, self.request)


class AreaTypesForm(EmbeddedForm):

    fields = Fields(interfaces.IAreaTypes)
    fields['area_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        main_form = self.get_main_form().name

        if main_form == 'marine-units':
            return A4Form(self, self.request)

        # if main_form == 'determination-of-good-environmental-status':
        #     return A9Form(self, self.request)

        if main_form == 'establishment-of-environmental-targets':
            return A10Form(self, self.request)

        if main_form == 'assessments':
            # For Art 8.1a and 8.1b we return the theme class
            klass = self.get_flattened_data(self).get('theme')

            if klass:
                return super(AreaTypesForm, self).get_subform(klass)

        article = self.get_form_data_by_key(self, 'article')
        klass = get_form(article)

        return super(AreaTypesForm, self).get_subform(klass)

    def get_available_marine_unit_ids(self):
        return self.subform.get_available_marine_unit_ids()


StartArticle8View = wrap_form(StartArticle8Form, MainFormWrapper)


@register_form_art9
class StartArticle92012Form(EmbeddedForm):
    title = "2012 reporting exercise"
    permission = "zope2.View"
    session_name = "2012"

    fields = Fields(interfaces.IReportTypeArt9)

    def get_subform(self):
        klass = self.get_form_data_by_key(self, 'report_type')

        return klass(self, self.request)


@register_form_a9_2012
class Article92012Form(EmbeddedForm):
    title = "Article 9 (GES determination)"

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesFormArt9(self, self.request)


StartArticle9View = wrap_form(StartArticle9Form, MainFormWrapper)


@register_form_art10
class StartArticle102012Form(EmbeddedForm):
    title = "2012 reporting exercise"
    permission = "zope2.View"
    session_name = "2012"

    fields = Fields(interfaces.IReportTypeArt10)

    def get_subform(self):
        klass = self.get_form_data_by_key(self, 'report_type')

        return klass(self, self.request)


@register_form_a10_2012
class Article102012Form(RegionForm):
    title = "Article 10 (Targets)"


StartArticle10View = wrap_form(StartArticle10Form, MainFormWrapper)


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
StartArticle14View = wrap_form(StartArticle14Form, MainFormWrapper)


@register_form_art8
class StartArticle82018Form(EmbeddedForm):
    title = "2018 reporting exercise"
    record_title = 'Article 8'

    fields = Fields(interfaces.IArticleSelectA82018)
    session_name = '2018'
    permission = 'zope2.View'  # 'wise.ViewReports'

    def get_subform(self):
        article = self.data['article']

        if article:
            if isinstance(article, tuple):
                klass = article[0]
            else:
                klass = article

            return klass(self, self.request)


# StartArticle89102018View = wrap_form(StartArticle89102018Form, MainFormWrapper)

StartArticle19View = wrap_form(StartArticle19Form, MainFormWrapper)

# discover and register associated views

scan('a4')
scan('a8ac')
scan('a8b')
scan('a9')
scan('a10')
scan('a89102018')
scan('a18')
scan('a112020')
