# pylint: skip-file
from __future__ import absolute_import

from wise.msfd.sql import t_MS_CompetentAuthorities
from wise.msfd.db import get_competent_auth_data
from wise.msfd.search.base import ItemDisplayForm


class CompetentAuthorityItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 7
    """

    mapper_class = t_MS_CompetentAuthorities
    order_field = 'C_CD'
    css_class = "left-side-form"

    blacklist = ('Import_Time', 'Import_FileName', 'C_CD', 'METADATA', 'URL')
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

        if country == country_code:
            country = self.print_value(country_code)

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
