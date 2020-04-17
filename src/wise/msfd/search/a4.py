from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from .. import db, sql, sql2018
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..sql_extra import (MSFD4GeographicalAreaID,
                         MSFD4GeograpicalAreaDescription)
from ..utils import db_objects_to_dict, group_data
from . import interfaces
from .base import ItemDisplayForm
from .utils import data_to_xls


class A4MemberStatesForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt4)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A4ItemDisplay2018to2024(self, self.request)


class A4Form2018to2024(MarineUnitIDSelectForm):
    """ MRU form for reporting cycle 2018-2024
    """

    record_title = title = 'Article 4 (Reporting cycle 2018-2024)'
    session_name = '2018'

    @db.use_db_session('2018')
    def get_available_marine_unit_ids(self):
        data = self.get_flattened_data(self)
        regions = data['region_subregions']
        countries = data['member_states']

        mapper_class = sql2018.MRUsPublication
        conditions = []

        if regions:
            conditions.append(mapper_class.rZoneId.in_(regions))

        if countries:
            conditions.append(mapper_class.Country.in_(countries))

        res = db.get_unique_from_mapper(
            mapper_class,
            'thematicId',
            *conditions
        )
        # res = [x.thematicId for x in res]

        return len(res), res

    def get_subform(self):
        return A4ItemDisplay2018to2024(self, self.request)


class A4Form(ItemDisplayForm):
    """ MRU form for reporting cycle 2012-2018
    """

    # Geographic areas & regional cooperation
    record_title = title = 'Article 4 (Marine Units)'
    mapper_class = MSFD4GeograpicalAreaDescription
    session_name = '2012'
    order_field = 'MSFD4_GeograpicalAreasDescription_Import'
    css_class = "left-side-form"

    blacklist_labels = ('MarineUnitID')

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    # extra_data_template = ViewPageTemplateFile('pt/extra-data-simple.pt')
    blacklist = ('MSFD4_GeograpicalAreasDescription_Import', 'MemberState')

    reported_date_info = {
        'mapper_class': sql.MSFD4Import,
        'col_import_id': 'MSFD4_Import_ID',
        'col_import_time': 'MSFD4_Import_Time',
        'col_filename': 'MSFD4_Import_FileName'
    }

    def get_reported_date(self):
        reported_date = super(A4Form, self).get_reported_date()
        default = 'Not available'

        if reported_date != default:
            return reported_date

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
        import_id = self.item.MSFD4_GeograpicalAreasDescription_Import

        return import_id

    def get_current_country(self):
        import_id = self.item.MSFD4_GeograpicalAreasDescription_Import

        _, country_code = db.get_related_record(
            sql.MSFD4Import,
            'MSFD4_Import_ID',
            import_id
        )
        country_code = country_code.MSFD4_Import_ReportingCountry

        return self.print_value(country_code)

    def get_db_results(self):
        klass_join = sql.MSFD4Import
        page = self.get_page()
        countries = self.get_form_data_by_key(self, 'member_states')

        args = [
            self.mapper_class,
            klass_join,
            self.order_field
        ]

        if countries:
            args.append(klass_join.MSFD4_Import_ReportingCountry.in_(
                countries))

        res = db.get_item_by_conditions_joined(
            *args,
            page=page
        )

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        mc = MSFD4GeographicalAreaID
        excluded_columns = ('MSFD4_GegraphicalAreasID_Import', )
        id_import = self.item.MSFD4_GeograpicalAreasDescription_Import

        res = []
        conditions = []

        regions = self.get_form_data_by_key(self, 'region_subregions')
        if regions:
            conditions.append(mc.RegionSubRegions.in_(regions))

        area_types = self.get_form_data_by_key(self, 'area_types')
        if area_types:
            conditions.append(mc.AreaType.in_(area_types))

        count, data = db.get_all_records(
            mc,
            mc.MSFD4_GegraphicalAreasID_Import == id_import,
            *conditions
        )

        data = db_objects_to_dict(data, excluded_columns)
        res.append(('MSFD4 GegraphicalAreasID', {'': data}))

        return res

    def get_marine_unit_ids(self):
        return self.get_available_marine_unit_ids()

    def get_available_marine_unit_ids(self):
        # Copied from MarineUnitIdsForm because we no longer have it in the
        # inheritance chain
        data = {}
        parent = self.context

        # lookup values in the inheritance tree

        for crit in ['area_types', 'member_states', 'region_subregions']:
            data[crit] = getattr(parent, 'get_selected_' + crit)()
            parent = parent.context

        return db.get_marine_unit_ids(**data)

    def download_results(self):
        mc = MSFD4GeographicalAreaID
        _, muids = self.get_marine_unit_ids()

        count, data = db.get_all_records(
            mc,
            mc.MarineUnitID.in_(muids)
        )
        import_ids = [x.MSFD4_GegraphicalAreasID_Import for x in data]

        md = MSFD4GeograpicalAreaDescription
        count, data_descr = db.get_all_records(
            md,
            md.MSFD4_GeograpicalAreasDescription_Import.in_(import_ids)
        )

        xlsdata = [
            ('MSFD4GeographicalAreaID', data),
            ('MSFD4GeograpicalAreaDescription', data_descr)
        ]

        return data_to_xls(xlsdata)


class A4ItemDisplay2018to2024(ItemDisplayForm):
    record_title = title = 'Article 4 (Marine Units)'
    session_name = '2018'
    css_class = "left-side-form"

    mapper_class = sql2018.MRUsPublication
    order_field = 'thematicId'

    data_template = ViewPageTemplateFile('pt/item-display-rows.pt')
    blacklist = ('Country', )
    blacklist_labels = ('thematicId', 'legisSName', 'nameText', '')

    @db.use_db_session('2018')
    def get_reported_date(self):
        country_code = self.item[0]['Country']

        mc = sql2018.ReportingHistory
        data = db.get_all_columns_from_mapper(
            mc,
            'DateReleased',
            mc.CountryCode == country_code,
            mc.ReportingObligation == 'MSFD - Article 4 - Spatial data'
        )

        if not len(data):
            return 'Not available'

        reported_date = data[0].DateReleased
        reported_date = self.format_reported_date(reported_date)

        return reported_date

    def get_current_country(self):
        country_code = self.item[0]['Country']

        return self.print_value(country_code)

    @db.use_db_session('2018')
    def get_db_results(self):
        page = self.get_page()
        form_data = self.get_flattened_data(self)
        regions = form_data['region_subregions']
        countries = form_data['member_states']

        col_names = ('Country', 'rZoneId', 'thematicId', 'nameTxtInt',
                     'nameText', 'spZoneType', 'legisSName', 'Area')
        columns = [getattr(self.mapper_class, name) for name in col_names]

        mapper_class = sql2018.MRUsPublication
        conditions = []

        if regions:
            conditions.append(mapper_class.rZoneId.in_(regions))

        if countries:
            conditions.append(mapper_class.Country.in_(countries))

        sess = db.session()

        self.data_download = sess.query(*columns).filter(
            *conditions
        ).order_by(getattr(self.mapper_class, self.order_field))

        data = db_objects_to_dict(self.data_download)
        data_grouped = group_data(data, 'Country', remove_pivot=False)

        pages = sorted(data_grouped.keys())
        count = len(pages)
        current_country = pages[page]

        items = data_grouped[current_country]

        return count, items

    @db.use_db_session('2018')
    def download_results(self):
        data = [x for x in self.data_download]

        xlsdata = [
            ('MRUsPublication', data),
        ]

        return data_to_xls(xlsdata)
