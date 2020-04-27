from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm2012
from ..utils import group_query
from .base import ItemDisplayForm
from .interfaces import IA2012GesComponentsArt10
from .utils import data_to_xls


class A10Form(EmbeddedForm):
    """ Select the MarineUnitID for the Article 10 form
    """

    record_title = title = 'Article 10 (Targets)'
    mapper_class = sql.MSFD10Target
    fields = Fields(IA2012GesComponentsArt10)
    fields['ges_components'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A10MRUForm(self, self.request)

    def download_results(self):
        # muids = self.get_marine_unit_ids()
        _, muids = self.subform.get_available_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        target_ids = [row.MSFD10_Target_ID for row in data]

        mapper_class_features_pres = sql.t_MSFD10_FeaturesPressures
        count_fp, data_fp = db.get_table_records(
            [mapper_class_features_pres],
            mapper_class_features_pres.c.MSFD10_Target.in_(target_ids)
        )
        data_fp = [x for x in data_fp]

        mapper_class_des_crit = sql.t_MSFD10_DESCrit
        count_dc, data_dc = db.get_all_records(
            mapper_class_des_crit,
            mapper_class_des_crit.c.MSFD10_Target.in_(target_ids)
        )

        xlsdata = [
            ('MSFD10Target', data),      # worksheet title, row data
            ('MSFD10_FeaturesPressures', data_fp),
            ('MSFD10_DESCrit', data_dc),
        ]

        return xlsdata


class A10MRUForm(MarineUnitIDSelectForm2012):
    mapper_class = sql.MSFD10Target

    def get_subform(self):
        return A10ItemDisplay(self, self.request)


class A10ItemDisplay(ItemDisplayForm):
    """ The implementation of the Article 10 fom
    """

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    mapper_class = sql.MSFD10Target
    order_field = 'MSFD10_Target_ID'

    # TODO: the MSFD10_DESCrit is not ORM mapped yet
    # this query is not finished!!!!
    # 8 aug 2019: looks finished?

    reported_date_info = {
        'mapper_class': sql.MSFD10Import,
        'col_import_id': 'MSFD10_Import_ID',
        'col_import_time': 'MSFD10_Import_Time',
        'col_filename': 'MSFD10_Import_FileName'
    }

    def get_import_id(self):
        import_id = self.item.MSFD10_Targets_Import

        return import_id

    def get_db_results(self):
        page = self.get_page()
        muid = self.get_marine_unit_id()
        ges_comps = self.get_form_data_by_key(self.context, 'ges_components')
        t = sql.t_MSFD10_DESCrit

        args = [self.mapper_class, self.order_field]

        if muid:
            args.append(self.mapper_class.MarineUnitID == muid)

        c, r = db.get_table_records(
            [t.c.MSFD10_Target],
            t.c.MarineUnitID == muid,
            t.c.GESDescriptorsCriteriaIndicators.in_(ges_comps)
        )
        target_ids = [x.MSFD10_Target for x in r]
        args.append(self.mapper_class.MSFD10_Target_ID.in_(target_ids))

        res = db.get_item_by_conditions(*args, page=page)

        return res

    def get_extra_data(self):
        if not self.item:
            return {}

        target_id = self.item.MSFD10_Target_ID

        t = sql.t_MSFD10_FeaturesPressures
        c, res = db.get_table_records([
            t.c.FeatureType,
            t.c.PhysicalChemicalHabitatsFunctionalPressures,
        ], t.c.MSFD10_Target == target_id)
        ft = group_query(res, 'FeatureType')

        t = sql.t_MSFD10_DESCrit
        c, res = db.get_table_records(
            [t.c.GESDescriptorsCriteriaIndicators],
            t.c.MSFD10_Target == target_id
        )
        fr = group_query(res, 'GESDescriptorsCriteriaIndicators')

        return [
            ('Feature Type', ft),
            ('Criteria Indicators', fr),
        ]
