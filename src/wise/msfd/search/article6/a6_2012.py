#pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from wise.msfd import sql, db
from wise.msfd.db import get_all_records_join, get_item_by_conditions_art_6
from wise.msfd.search.base import ItemDisplayForm


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
