# pylint: skip-file
from __future__ import absolute_import
from datetime import datetime
from types import SimpleNamespace

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql, sql2018
from ..base import EmbeddedForm
from ..db import threadlocals
from .base import ItemDisplayForm, MainForm, ItemDisplayForm2018
from .utils import register_form_art19
from .a112020 import A11MonitoringProgrammeForm2020, A112020Mixin


class StartArticle19Form(MainForm):
    """ Start class for Article 19
    """

    name = 'datasets-used'
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

    title = '2012 Article 19.3'
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

    blacklist = ('IdMetadataArt19_3', )

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

        country = self.print_value(res.Country, 'CountryCode')

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
            *conditions,
            raw=True
        )
        ids_needed = [x.Id for x in metadata]

        _, metadata_features = db.get_all_records(
            mc,
            mc.c.IdMetadataArt19_3.in_(ids_needed),
            raw=True
        )

        xlsdata = [
            ('MetadataArt193', metadata),  # worksheet title, row data
            ('MetadataFeatures', metadata_features)
        ]

        return xlsdata

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


class A11DataAccessDisplay2020(ItemDisplayForm2018, A112020Mixin):
    css_class = 'left-side-form'
    title = "Data Access Monitoring Programmes display"
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql2018.ART11ProgrammesMonitoringProgramme
    blacklist_labels = ('ProgrammeCode', 'RelatedIndicator_code')
    blacklist = ('Id', 'IdReportedInformation', 'keys')
    mp_dataaccess = sql2018.ART11ProgrammesMonitoringProgrammeDataAcces

    def get_db_results(self):
        page = self.get_page()
        prog_codes = self.get_programme_codes_needed()

        reportinfo_ids = db.get_unique_from_mapper(
            self.mapper_class,
            'IdReportedInformation',
            self.mapper_class.ProgrammeCode.in_(prog_codes)
        )
        count = len(reportinfo_ids)
        reportid_needed = reportinfo_ids[page]

        mon_prog_ids = db.get_unique_from_mapper(
            self.mapper_class,
            'Id',
            self.mapper_class.IdReportedInformation==(reportid_needed)
        )
        data_access = db.get_unique_from_mapper(
            self.mp_dataaccess,
            'DataAccess',
            self.mp_dataaccess.IdMonitoringProgramme.in_(mon_prog_ids)
        )

        _item = SimpleNamespace(
            IdReportedInformation=reportid_needed,
            DataAccess=data_access
        )
        _item.keys = lambda: _item.__dict__.keys()

        return count, _item


@register_form_art19
class A11DataAccessForm2020(A11MonitoringProgrammeForm2020):
    record_title = 'Data access (Article 11 Monitoring Programmes)'
    title = "2020 Article 11 Monitoring programmes"
    session_name = '2018'

    @property
    def display_class(self):
        return A11DataAccessDisplay2020
