#pylint: skip-file
from __future__ import absolute_import
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm2012
from ..db import (get_all_records, get_available_marine_unit_ids,
                  get_marine_unit_ids)
from ..utils import group_query
from .base import ItemDisplayForm
from .interfaces import IA2012GesComponentsArt9, IAreaTypes

class A9Form(EmbeddedForm):
    """ Select the MarineUnitID for the Article 9 form
    """

    fields = Fields(IA2012GesComponentsArt9)
    fields['ges_components'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        # return A9MRUForm(self, self.request)

        return AreaTypesFormArt9(self, self.request)

    # def get_available_marine_unit_ids(self):
    #     return self.subform.get_available_marine_unit_ids()


class AreaTypesFormArt9(EmbeddedForm):
    record_title = 'Article 9 (GES determination)'

    fields = Fields(IAreaTypes)
    fields['area_types'].widgetFactory = CheckBoxFieldWidget
    session_name = '2012'
    mapper_class = sql.MSFD9Descriptor

    def get_subform(self):
        return A9MRUForm(self, self.request)

    def download_results(self):
        # muids = self.get_marine_unit_ids()
        _, muids = self.subform.get_available_marine_unit_ids()
        ges_comps = self.get_form_data_by_key(self, 'ges_components')

        count, data = get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids),
            self.mapper_class.ReportingFeature.in_(ges_comps),
            raw=True
        )

        descriptor_ids = [row.MSFD9_Descriptor_ID for row in data]

        t_features = sql.t_MSFD9_Features
        count, data_f = get_all_records(
            t_features,
            t_features.c.MSFD9_Descriptor.in_(descriptor_ids),
            raw=True
        )

        xlsdata = [
            ('MSFD9Descriptor', data),
            ('MSFD9_Features', data_f),
        ]

        return xlsdata


class A9MRUForm(MarineUnitIDSelectForm2012):
    mapper_class = sql.MSFD9Descriptor

    def get_available_marine_unit_ids(self, parent=None):
        data = {}
        parent = self.context

        # lookup values in the inheritance tree
        for crit in ['area_types', 'member_states', 'region_subregions']:
            while hasattr(parent, 'context'):
                if hasattr(parent, 'get_selected_' + crit):
                    data[crit] = getattr(parent, 'get_selected_' + crit)()
                    break

                parent = parent.context

            parent = parent.context

        _, all_mrus = get_marine_unit_ids(**data)

        count, res = get_available_marine_unit_ids(
            all_mrus, self.mapper_class
        )

        return count, [x[0] for x in res]

    def get_subform(self):

        return A9ItemDisplay(self, self.request)


class A9ItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 9 (GES determination) form
    """
    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    mapper_class = sql.MSFD9Descriptor
    order_field = 'MSFD9_Descriptor_ID'

    reported_date_info = {
        'mapper_class': sql.MSFD9Import,
        'col_import_id': 'MSFD9_Import_ID',
        'col_import_time': 'MSFD9_Import_Time',
        'col_filename': 'MSFD9_Import_FileName'
    }

    def get_import_id(self):
        import_id = self.item.MSFD9_Descriptors_Import

        return import_id

    def get_db_results(self):
        page = self.get_page()
        muid = self.get_marine_unit_id()

        args = [self.mapper_class, self.order_field]

        if muid:
            args.append(self.mapper_class.MarineUnitID == muid)

        ges_comps = self.get_form_data_by_key(self.context, 'ges_components')

        if ges_comps:
            args.append(self.mapper_class.ReportingFeature.in_(ges_comps))

        res = db.get_item_by_conditions(*args, page=page)

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        desc_id = self.item.MSFD9_Descriptor_ID
        t = sql.t_MSFD9_Features

        total, res = db.get_table_records(
            [t.c.FeatureType, t.c.FeaturesPressuresImpacts],
            t.c.MSFD9_Descriptor == desc_id
        )
        res = group_query(res, 'FeatureType')

        return [
            ('Feature Types', res)
        ]
