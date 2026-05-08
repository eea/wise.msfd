# pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2018
from wise.msfd.base import EmbeddedForm, MarineUnitIDSelectForm
from wise.msfd.utils import db_objects_to_dict, group_data
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm


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


class A4ItemDisplay2018to2024(ItemDisplayForm):
    record_title = title = 'Article 4 (Marine Units)'
    session_name = '2018'
    css_class = "left-side-form"

    mapper_class = sql2018.MRUsPublication
    order_field = 'thematicId'

    data_template = ViewPageTemplateFile('../pt/item-display-rows.pt')
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

        return self.print_value(country_code, 'CountryCode')

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

        return xlsdata
