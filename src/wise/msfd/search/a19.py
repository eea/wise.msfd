
from datetime import datetime

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql, sql2018
from ..base import EmbeddedForm
from ..db import threadlocals
from ..utils import db_objects_to_dict
from .base import ItemDisplayForm, MainForm
from .utils import data_to_xls, register_form_art19


class StartArticle19Form(MainForm):
    """ Start class for Article 19
    """

    name = 'msfd-c6'
    session_name = '2012'

    fields = Fields(interfaces.IArticle19ReportingPeriod)

    def get_subform(self):
        klass = self.data.get('reporting_period')
        session_name = klass.session_name
        threadlocals.session_name = session_name

        return klass(self, self.request)


@register_form_art19
class Article192012(EmbeddedForm):
    """ Article 19 reporting year 2012
    """

    title = '2012 reporting exercise'
    session_name = '2012'

    fields = Fields(interfaces.IRegionSubregionsArt19)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):

        return Article19MemberStates(self, self.request)


class Article19MemberStates(EmbeddedForm):

    fields = Fields(interfaces.ICountryArt19)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):

        return Article19Display(self, self.request)


class Article19Display(ItemDisplayForm):
    record_title = title = "Article 19.3"

    mapper_class = sql.t_MetadataFeatures
    css_class = 'left-side-form'

    def get_reported_date(self):
        date = self.item.DateStamp
        try:
            date = datetime.strptime(date, '%d%m%Y').strftime('%Y %b %d')
        except:
            pass

        return date

    def get_current_country(self):
        report_id = self.item.IdMetadataArt19_3

        _, res = db.get_related_record(
            sql.MetadataArt193,
            'Id',
            report_id
        )

        country = self.print_value(res.Country)

        return country

    def download_results(self):
        mc_ids = sql.MetadataArt193
        mc = self.mapper_class

        countries = self.get_form_data_by_key(self, 'member_states')
        regions = self.get_form_data_by_key(self, 'region_subregions')

        conditions = []

        if regions:
            conditions.append(mc_ids.Region.in_(regions))

        if countries:
            conditions.append(mc_ids.Country.in_(countries))

        _, metadata = db.get_all_records(
            mc_ids,
            *conditions
        )
        ids_needed = [x.Id for x in metadata]

        _, metadata_features = db.get_all_records(
            mc,
            mc.c.IdMetadataArt19_3.in_(ids_needed)
        )

        xlsdata = [
            ('MetadataArt193', metadata),  # worksheet title, row data
            ('MetadataFeatures', metadata_features)
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        mc_ids = sql.MetadataArt193
        mc = self.mapper_class

        countries = self.get_form_data_by_key(self, 'member_states')
        regions = self.get_form_data_by_key(self, 'region_subregions')

        conditions = []

        if regions:
            conditions.append(mc_ids.Region.in_(regions))

        if countries:
            conditions.append(mc_ids.Country.in_(countries))

        ids_needed = db.get_unique_from_mapper(
            mc_ids,
            'Id',
            *conditions
        )

        sess = db.session()

        q = sess.query(mc).filter(
            mc.c.IdMetadataArt19_3.in_(ids_needed)
        ).order_by(mc.c.IdMetadataArt19_3)

        total = q.count()
        item = q.offset(page).limit(1).first()

        return [total, item]

