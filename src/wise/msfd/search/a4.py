from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import db, sql
from ..base import MarineUnitIDSelectForm
from ..sql_extra import (MSFD4GeographicalAreaID,
                         MSFD4GeograpicalAreaDescription)
from ..utils import db_objects_to_dict, pivot_data, register_form
from .base import ItemDisplayForm


@register_form
class A4Form(MarineUnitIDSelectForm):
    """ Main form for A4.
    """

    record_title = title = \
        'Article 4 (Geographic areas & regional cooperation)'
    mapper_class = MSFD4GeographicalAreaID

    def get_subform(self):
        return A4ItemDisplay(self, self.request)

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


class A4ItemDisplay(ItemDisplayForm):
    """ The implementation of the Article 10 fom
    """

    mapper_class = MSFD4GeographicalAreaID
    order_field = 'MarineUnitID'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-simple.pt')
    extra_data_pivot = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    blacklist = ('MSFD4_GegraphicalAreasID_Import',)

    # TODO: implement xls download

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

        total, imported = db.get_item_by_conditions(
            sql.MSFD4Import,
            'MSFD4_Import_ID',
            sql.MSFD4Import.MSFD4_Import_ID == import_id
        )
        assert total == 1

        m = sql.MSFD4RegionalCooperation
        coops = db.get_all_columns_from_mapper(
            m,
            'MSFD4_RegionalCooperation_ID',
            m.MSFD4_Import == imported
        )

        rows = db_objects_to_dict(coops, excluded_columns=blacklist)

        regcoop = pivot_data(rows, 'RegionsSubRegions')
        pivot_html = self.extra_data_pivot(extra_data=[
            ('Regional Cooperation', regcoop),
        ])

        return [
            ('Area description', desc_html),
            ('', pivot_html)
        ]
