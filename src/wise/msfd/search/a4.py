from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from .. import db, sql2018
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..sql_extra import (MSFD4GeographicalAreaID,
                         MSFD4GeograpicalAreaDescription)
from . import interfaces
from .base import ItemDisplayForm
from .utils import data_to_xls


class A4MemberStatesForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStatesArt4)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A4Form2018to2024(self, self.request)


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
            conditions.append(mapper_class.Region.in_(regions))

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


class A4Form(MarineUnitIDSelectForm):
    """ MRU form for reporting cycle 2012-2018
    """

    # Geographic areas & regional cooperation
    record_title = title = 'Article 4 (Reporting cycle 2012-2018)'
    mapper_class = MSFD4GeographicalAreaID
    session_name = '2012'

    # @property
    # def display_klass(self):
    #     ctx = self.context
    #
    #     while ctx:
    #         if hasattr(ctx, 'display_klass'):
    #             return ctx.display_klass
    #
    #         ctx = getattr(ctx, 'context', None)
    #
    #     return None

    def get_subform(self):
        return A4ItemDisplay2012to2018(self, self.request)
        # display_klass = self.display_klass

        # return display_klass(self, self.request)

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


class A4ItemDisplay2012to2018(ItemDisplayForm):

    mapper_class = MSFD4GeographicalAreaID
    order_field = 'MarineUnitID'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-simple.pt')
    extra_data_pivot = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    blacklist = ('MSFD4_GegraphicalAreasID_Import',)

    # TODO: add to blacklist MSFD4 Gegraphical Areas ID Import
    def get_extra_data(self):
        if not self.item:
            return []

        blacklist = ['MSFD4_RegionalCooperation_ID',
                     'MSFD4_RegionalCooperation_Import',
                     'MSFD4_GeograpicalAreasDescription_Import',
                     ]

        import_id = self.item.MSFD4_GegraphicalAreasID_Import
        m = MSFD4GeograpicalAreaDescription
        [desc] = db.get_all_columns_from_mapper(
            m,
            'MSFD4_GeograpicalAreasDescription_Import',
            m.MSFD4_GeograpicalAreasDescription_Import == import_id
        )
        desc_html = self.data_template(item=desc, blacklist=blacklist)

        return [
            ('Area description', desc_html),
            # ('', pivot_html)
        ]


class A4ItemDisplay2018to2024(ItemDisplayForm):

    mapper_class = sql2018.MRUsPublication
    order_field = 'thematicId'

    def get_current_country(self):
        country_code = self.item.Country

        return self.print_value(country_code)

    @db.use_db_session('2018')
    def get_db_results(self):
        page = self.get_page()
        muid = self.get_marine_unit_id()

        col_names = ('Country', 'Region', 'thematicId', 'nameTxtInt',
                     'nameText', 'spZoneType', 'legisSName', 'Area')
        columns = [getattr(self.mapper_class, name) for name in col_names]

        conditions = []
        if muid:
            conditions.append(self.mapper_class.thematicId == muid)

        sess = db.session()

        q = sess.query(*columns).filter(
            *conditions
        ).order_by(getattr(self.mapper_class, self.order_field))

        count = q.count()

        item = q.offset(page).limit(1).first()

        return count, item

