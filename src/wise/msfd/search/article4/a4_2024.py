# pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from wise.msfd import db, sql2024
from wise.msfd.base import EmbeddedForm
from wise.msfd.utils import db_objects_to_dict, group_data
from wise.msfd.search import interfaces
from wise.msfd.search.base import ItemDisplayForm


class A4MemberStatesForm2024to2030(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt4)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A4ItemDisplay2024to2030(self, self.request)


class A4ItemDisplay2024to2030(ItemDisplayForm):
    record_title = title = 'Article 4 (Marine Units)'
    session_name = '2024'
    css_class = "left-side-form"

    mapper_class = sql2024.t_ART4_GEO_GeographicalBoundaries
    order_field = 'CountryCode'

    data_template = ViewPageTemplateFile('../pt/item-display-rows.pt')
    blacklist = ('CountryCode', 'ReportingDate')
    blacklist_labels = (
        'thematicId', 'legisSName', 'nameText', 'nameTxtInt',
        'MarineReportingUnitId', 'MarineReportingUnitIdOld',
        'MarineReportingUnitName', 'legisName', 'legisLink',
    )

    excluded_columns = (
        'MarineReportingUnitGeometry',
        'localId', 'namespace', 'versionId',
        'nameTxtLan', 'themaIdSch', 'beginLife',
        'rZoneIdSch', 'SnapshotId',
        'Comment', 'legisDateT',
    )

    @db.use_db_session('2024')
    def get_reported_date(self):
        return self.format_reported_date(self.item[0]['ReportingDate'])

    def get_current_country(self):
        country_code = self.item[0]['CountryCode']

        return self.print_value(country_code, 'CountryCode')

    @db.use_db_session('2024')
    def get_db_results(self):
        page = self.get_page()
        form_data = self.get_flattened_data(self)
        regions = form_data['region_subregions']
        countries = form_data['member_states']

        mapper_class = sql2024.t_ART4_GEO_GeographicalBoundaries
        conditions = []

        if regions:
            conditions.append(mapper_class.c.RegionSubRegion.in_(regions))

        if countries:
            conditions.append(mapper_class.c.CountryCode.in_(countries))

        sess = db.session()

        columns = [
            c for c in mapper_class.c
            if c.name not in self.excluded_columns
        ]

        self.data_download = sess.query(*columns).filter(
            *conditions
        ).order_by(
            mapper_class.c.CountryCode,
            mapper_class.c.MarineReportingUnitId
        )

        data = db_objects_to_dict(self.data_download)
        data_grouped = group_data(data, 'CountryCode', remove_pivot=False)

        pages = sorted(data_grouped.keys())
        count = len(pages)

        if not count:
            return 0, []

        current_country = pages[page]

        items = data_grouped[current_country]

        return count, items

    @db.use_db_session('2024')
    def download_results(self):
        data = [x for x in self.data_download]

        xlsdata = [
            ('ART4_GEO_GeographicalBoundaries', data),
        ]

        return xlsdata
