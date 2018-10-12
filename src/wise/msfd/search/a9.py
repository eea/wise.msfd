from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import db, sql
from ..base import MarineUnitIDSelectForm
from ..db import get_all_records
from ..utils import data_to_xls, pivot_query, register_form
from .base import ItemDisplayForm


@register_form
class A9Form(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 9 form
    """

    record_title = title = 'Article 9 (GES determination)'
    mapper_class = sql.MSFD9Descriptor

    def get_subform(self):
        return A9ItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        descriptor_ids = [row.MSFD9_Descriptor_ID for row in data]

        t_features = sql.t_MSFD9_Features
        count, data_f = get_all_records(
            t_features,
            t_features.c.MSFD9_Descriptor.in_(descriptor_ids)
        )

        xlsdata = [
            ('MSFD9Descriptor', data),
            ('MSFD9_Features', data_f),
        ]

        return data_to_xls(xlsdata)


class A9ItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 9 (GES determination) form
    """
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    mapper_class = sql.MSFD9Descriptor
    order_field = 'MSFD9_Descriptor_ID'

    def get_extra_data(self):
        if not self.item:
            return {}

        desc_id = self.item.MSFD9_Descriptor_ID
        t = sql.t_MSFD9_Features

        total, res = db.get_table_records(
            [t.c.FeatureType, t.c.FeaturesPressuresImpacts],
            t.c.MSFD9_Descriptor == desc_id
        )
        res = pivot_query(res, 'FeatureType')

        return [
            ('Feature Types', res)
        ]
