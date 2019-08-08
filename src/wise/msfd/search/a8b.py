from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.field import Fields

from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from .base import ItemDisplay, MultiItemDisplayForm
from .interfaces import IA81Form
from .utils import (data_to_xls, register_form, register_form_section,
                    register_subform)


@register_form
class A81bForm(EmbeddedForm):
    """ Main form for A81b.

    Allows selecting between Extraction of fish, seaweed, etc
    """

    record_title = title = 'Article 8.1b (Analysis of pressure impacts)'
    fields = Fields(IA81Form)

    def get_subform(self):
        klass = self.data.get('theme')

        return super(A81bForm, self).get_subform(klass)


# region Extraction of fish and shellfish
class A81bExtractionFishItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bExtractionFishShellfish
    order_field = 'MSFD8b_ExtractionFishShellfish_ID'


@register_subform(A81bForm)
class A81bExtractionFishSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D6/D3 - Extraction of fish and shellfish'
    mapper_class = sql.MSFD8bExtractionFishShellfish

    def get_subform(self):
        return A81bExtractionFishItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        extraction_ids = [row.MSFD8b_ExtractionFishShellfish_ID
                          for row in data]
        mc_a = sql.MSFD8bExtractionFishShellfishAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_ExtractionFishShellfish.in_(extraction_ids)
        )

        assesment_ids = [row.MSFD8b_ExtractionFishShellfish_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bExtractionFishShellfishAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_ExtractionFishShellfish_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bExtractionFishShellfishActivity
        kj = sql.MSFD8bExtractionFishShellfishActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_ExtractionFishShellfish_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_ExtractionFishShellfish_ActivityDescription,
                kj.MSFD8b_ExtractionFishShellfish_ActivityDescription_ID,
                kj.MarineUnitID,
                kj.Description,
                kj.Limitations,
                kj.MSFD8b_ExtractionFishShellfish
            ],
            kj,
            kj.MSFD8b_ExtractionFishShellfish.in_(extraction_ids)
        )

        mc_sum = sql.MSFD8bExtractionFishShellfishSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_ExtractionFishShellfish.in_(extraction_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bExtractionFS', data),
            ('MSFD8bExtractionFSAssesment', data_a),
            ('MSFD8bExtractionFSAssesmentInd', data_ai),
            ('MSFD8bExtractionFSActivity', data_ac),
            ('MSFD8bExtractionFSSumInfo', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bExtractionFishItemDisplay)
class A81bExtractionFishAssessment(ItemDisplay):
    title = 'Asessment of extraction of fish and shellfish'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bExtractionFishShellfishAssesment,
                'MSFD8b_ExtractionFishShellfish',
                self.context.item.MSFD8b_ExtractionFishShellfish_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bExtractionFishShellfishAssesmentIndicator,
            'MSFD8b_ExtractionFishShellfish_Assesment',
            self.item.MSFD8b_ExtractionFishShellfish_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO
# MSFD8bExtractionFishShellfishActivity is not directly related to
# MSFD8b_ExtractionFishShellfish table
# needs to be joined with MSFD8bExtractionFishShellfishActivityDescription
# table first
@register_form_section(A81bExtractionFishItemDisplay)
class A81bExtractionFishActivities(ItemDisplay):
    title = 'Activities producing extraction of fish and shellfish'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bExtractionFishShellfishActivity,
                sql.MSFD8bExtractionFishShellfishActivityDescription,
                'MSFD8b_ExtractionFishShellfish',
                self.context.item.MSFD8b_ExtractionFishShellfish_ID
            )


@register_form_section(A81bExtractionFishItemDisplay)
class A81bExtractionFishImpacts(ItemDisplay):
    title = 'Impacts produced by the extraction of fish and shellfish'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bExtractionFishShellfishSumInfo2ImpactedElement,
                'MSFD8b_ExtractionFishShellfish',
                self.context.item.MSFD8b_ExtractionFishShellfish_ID
            )
# endregion Extraction of fish and shellfish


# region Extraction of seaweed, maerl and other
class A81bExtractionSeaweedItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bExtractionSeaweedMaerlOther
    order_field = 'MSFD8b_ExtractionSeaweedMaerlOther_ID'


@register_subform(A81bForm)
class A81bExtractionSeaweedSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D6/D3 - Extraction of seaweed, maerl and other'
    mapper_class = sql.MSFD8bExtractionSeaweedMaerlOther

    def get_subform(self):
        return A81bExtractionSeaweedItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_ExtractionSeaweedMaerlOther_ID for row in data]
        mc_a = sql.MSFD8bExtractionSeaweedMaerlOtherAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_ExtractionSeaweedMaerlOther.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_ExtractionSeaweedMaerlOther_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bExtractionSeaweedMaerlOtherAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_ExtractionSeaweedMaerlOther_Assesment.in_(
                assesment_ids)
        )

        mc_ac = sql.MSFD8bExtractionSeaweedMaerlOtherActivity
        kj = sql.MSFD8bExtractionSeaweedMaerlOtherActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_ExtractionSeaweedMaerlOther_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription,
                kj.MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription_ID,
                kj.MarineUnitID,
                kj.ExtractionType,
                kj.Description,
                kj.Limitations,
                kj.MSFD8b_ExtractionSeaweedMaerlOther
            ],
            kj,
            kj.MSFD8b_ExtractionSeaweedMaerlOther.in_(base_ids)
        )

        mc_sum = sql.MSFD8bExtractionSeaweedMaerlOtherSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_ExtractionSeaweedMaerlOther.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bExtrSeaweedMaerlOther', data),
            ('MSFD8bExtrSeaweedAssesment', data_a),
            ('MSFD8bExtrSeaweedAssesIndicator', data_ai),
            ('MSFD8bExtrSeaweedActivity', data_ac),
            ('MSFD8bExtrSeaweedMaerlOtherSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bExtractionSeaweedItemDisplay)
class A81bExtractionSeaweedAssessment(ItemDisplay):
    title = 'Asessment of extraction of seaweed, maerl and other'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bExtractionSeaweedMaerlOtherAssesment,
                'MSFD8b_ExtractionSeaweedMaerlOther',
                self.context.item.MSFD8b_ExtractionSeaweedMaerlOther_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bExtractionSeaweedMaerlOtherAssesmentIndicator,
            'MSFD8b_ExtractionSeaweedMaerlOther_Assesment',
            self.item.MSFD8b_ExtractionSeaweedMaerlOther_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


# TODO
# MSFD8bExtractionSeaweedMaerlOtherActivity is not directly related to
# MSFD8b_ExtractionSeaweedMaerlOther table
# needs to be joined with MSFD8bExtractionSeaweedMaerlOtherActivityDescription
# table first
@register_form_section(A81bExtractionSeaweedItemDisplay)
class A81bExtractionSeaweedActivities(ItemDisplay):
    title = 'Activities producing extraction of seaweed, maerl and other'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bExtractionSeaweedMaerlOtherActivity,
                sql.MSFD8bExtractionSeaweedMaerlOtherActivityDescription,
                'MSFD8b_ExtractionSeaweedMaerlOther',
                self.context.item.MSFD8b_ExtractionSeaweedMaerlOther_ID
            )


@register_form_section(A81bExtractionSeaweedItemDisplay)
class A81bExtractionSeaweedImpacts(ItemDisplay):
    title = 'Impacts produced by the extraction of seaweed, maerl and other'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bExtractionSeaweedMaerlOtherSumInfo2ImpactedElement,
                'MSFD8b_ExtractionSeaweedMaerlOther',
                self.context.item.MSFD8b_ExtractionSeaweedMaerlOther_ID
            )
# endregion Extraction of seaweed, maerl and other


# region Hazardous substances
class A81bHazardousItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bHazardousSubstance
    order_field = 'MSFD8b_HazardousSubstances_ID'


@register_subform(A81bForm)
class A81bHazardousSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D8/D9 - Hazardous substances'
    mapper_class = sql.MSFD8bHazardousSubstance

    def get_subform(self):
        return A81bHazardousItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_HazardousSubstances_ID for row in data]
        mc_a = sql.MSFD8bHazardousSubstancesAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_HazardousSubstances.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_HazardousSubstances_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bHazardousSubstancesAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_HazardousSubstances_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bHazardousSubstancesActivity
        klass_join = sql.MSFD8bHazardousSubstancesActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_HazardousSubstances_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_HazardousSubstances_ActivityDescription,
                klass_join.MSFD8b_HazardousSubstances_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.HazardousSubstancesGroup,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_HazardousSubstances
            ],
            klass_join,
            klass_join.MSFD8b_HazardousSubstances.in_(base_ids)
        )

        mc_sum = sql.MSFD8bHazardousSubstancesSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_HazardousSubstances.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bHazardSubstance', data),
            ('MSFD8bHazardSubstancesAssesment', data_a),
            ('MSFD8bHazardSubstAssesIndicator', data_ai),
            ('MSFD8bHazardSubstancesActivity', data_ac),
            ('MSFD8bHazardSubstancesSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bHazardousItemDisplay)
class A81bHazardousAssessment(ItemDisplay):
    title = 'Asessment of hazardous substances'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bHazardousSubstancesAssesment,
                'MSFD8b_HazardousSubstances',
                self.context.item.MSFD8b_HazardousSubstances_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bHazardousSubstancesAssesmentIndicator,
            'MSFD8b_HazardousSubstances_Assesment',
            self.item.MSFD8b_HazardousSubstances_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO
# MSFD8bHazardousSubstancesActivity is not directly related to
# MSFD8b_HazardousSubstances table
# needs to be joined with MSFD8bHazardousSubstancesActivityDescription table
# first
@register_form_section(A81bHazardousItemDisplay)
class A81bHazardousActivities(ItemDisplay):
    title = 'Activities producing hazardous substances'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bHazardousSubstancesActivity,
                sql.MSFD8bHazardousSubstancesActivityDescription,
                'MSFD8b_HazardousSubstances',
                self.context.item.MSFD8b_HazardousSubstances_ID
            )


@register_form_section(A81bHazardousItemDisplay)
class A81bHazardousImpacts(ItemDisplay):
    title = 'Impacts produced by the hazardous substances'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bHazardousSubstancesSumInfo2ImpactedElement,
                'MSFD8b_HazardousSubstances',
                self.context.item.MSFD8b_HazardousSubstances_ID
            )
# endregion Hazardous substances


# region Hydrological processes
class A81bHydroItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bHydrologicalProcess
    order_field = 'MSFD8b_HydrologicalProcesses_ID'


@register_subform(A81bForm)
class A81bHydroSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D7 - Hydrological processes'
    mapper_class = sql.MSFD8bHydrologicalProcess

    def get_subform(self):
        return A81bHydroItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_HydrologicalProcesses_ID for row in data]
        mc_a = sql.MSFD8bHydrologicalProcessesAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_HydrologicalProcesses.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_HydrologicalProcesses_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bHydrologicalProcessesAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_HydrologicalProcesses_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bHydrologicalProcessesActivity
        klass_join = sql.MSFD8bHydrologicalProcessesActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_HydrologicalProcesses_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_HydrologicalProcesses_ActivityDescription,
                klass_join.MSFD8b_HydrologicalProcesses_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_HydrologicalProcesses
            ],
            klass_join,
            klass_join.MSFD8b_HydrologicalProcesses.in_(base_ids)
        )

        mc_sum = sql.MSFD8bHydrologicalProcessesSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_HydrologicalProcesses.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bHydrologicalProcess', data),
            ('MSFD8bHydroProcAssesment', data_a),
            ('MSFD8bHydroProcAssesIndicator', data_ai),
            ('MSFD8bHydroProcActivity', data_ac),
            ('MSFD8bHydroProcSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bHydroItemDisplay)
class A81bHydroAssessment(ItemDisplay):
    title = 'Asessment of hydrological processes'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bHydrologicalProcessesAssesment,
                'MSFD8b_HydrologicalProcesses',
                self.context.item.MSFD8b_HydrologicalProcesses_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bHydrologicalProcessesAssesmentIndicator,
            'MSFD8b_HydrologicalProcesses_Assesment',
            self.item.MSFD8b_HydrologicalProcesses_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO
# MSFD8bHydrologicalProcessesActivity is not directly related to
# MSFD8b_HydrologicalProcesses table
# needs to be joined with MSFD8bHydrologicalProcessesActivityDescription table
# first
@register_form_section(A81bHydroItemDisplay)
class A81bHydroActivities(ItemDisplay):
    title = 'Activities producing hydrological processes'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bHydrologicalProcessesActivity,
                sql.MSFD8bHydrologicalProcessesActivityDescription,
                'MSFD8b_HydrologicalProcesses',
                self.context.item.MSFD8b_HydrologicalProcesses_ID
            )


@register_form_section(A81bHydroItemDisplay)
class A81bHydroImpacts(ItemDisplay):
    title = 'Impacts produced by the hydrological processes'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bHydrologicalProcessesSumInfo2ImpactedElement,
                'MSFD8b_HydrologicalProcesses',
                self.context.item.MSFD8b_HydrologicalProcesses_ID
            )
# endregion Hydrological processes


# region Marine litter
class A81bMarineLitterItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bLitter
    order_field = 'MSFD8b_Litter_ID'


@register_subform(A81bForm)
class A81bMarineLitterSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D10 - Marine litter'
    mapper_class = sql.MSFD8bLitter

    def get_subform(self):
        return A81bMarineLitterItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_Litter_ID for row in data]
        mc_a = sql.MSFD8bLitterAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_Litter.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_Litter_Assesment_ID for row in data_a]
        mc_ai = sql.MSFD8bLitterAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_Litter_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bLitterActivity
        klass_join = sql.MSFD8bLitterActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_Litter_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_Litter_ActivityDescription,
                klass_join.MSFD8b_Litter_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_Litter
            ],
            klass_join,
            klass_join.MSFD8b_Litter.in_(base_ids)
        )

        mc_sum = sql.MSFD8bLitterSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_Litter.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bLitter', data),
            ('MSFD8bLitterAssesment', data_a),
            ('MSFD8bLitterAssesIndicator', data_ai),
            ('MSFD8bLitterActivity', data_ac),
            ('MSFD8bLitterSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bMarineLitterItemDisplay)
class A81bMarineLitterAssessment(ItemDisplay):
    title = 'Asessment of marine litter'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bLitterAssesment,
                'MSFD8b_Litter',
                self.context.item.MSFD8b_Litter_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bLitterAssesmentIndicator,
            'MSFD8b_Litter_Assesment',
            self.item.MSFD8b_Litter_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO
# MSFD8bLitterActivity is not directly related to
# MSFD8b_Litter table
# needs to be joined with MSFD8bLitterActivityDescription table first
@register_form_section(A81bMarineLitterItemDisplay)
class A81bMarineLitterActivities(ItemDisplay):
    title = 'Activities producing marine litter'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bLitterActivity,
                sql.MSFD8bLitterActivityDescription,
                'MSFD8b_Litter',
                self.context.item.MSFD8b_Litter_ID
            )


@register_form_section(A81bMarineLitterItemDisplay)
class A81bMarineLitterImpacts(ItemDisplay):
    title = 'Impacts produced by the marine litter'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bLitterSumInfo2ImpactedElement,
                'MSFD8b_Litter',
                self.context.item.MSFD8b_Litter_ID
            )
# endregion Marine litter


# region Microbial pathogens
class A81bMicrobialItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bMicrobialPathogen
    order_field = 'MSFD8b_MicrobialPathogens_ID'


@register_subform(A81bForm)
class A81bMicrobialSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D8 - Microbial pathogens'
    mapper_class = sql.MSFD8bMicrobialPathogen

    def get_subform(self):
        return A81bMicrobialItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_MicrobialPathogens_ID for row in data]
        mc_a = sql.MSFD8bMicrobialPathogensAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_MicrobialPathogens.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_MicrobialPathogens_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bMicrobialPathogensAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_MicrobialPathogens_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bMicrobialPathogensActivity
        klass_join = sql.MSFD8bMicrobialPathogensActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_MicrobialPathogens_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_MicrobialPathogens_ActivityDescription,
                klass_join.MSFD8b_MicrobialPathogens_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_MicrobialPathogens
            ],
            klass_join,
            klass_join.MSFD8b_MicrobialPathogens.in_(base_ids)
        )

        # TODO missing table MSFD8bMicrobialPathogenSumInfo2ImpactedElement
        # mc_sum = sql.MSFD8bMicrobialPathogenSumInfo2ImpactedElement
        # count, data_sum = db.get_all_records(
        #     mc_sum,
        #     mc_sum.MSFD8b_MicrobialPathogens.in_(base_ids)
        # )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bMicrobialPathogen', data),
            ('MSFD8bMicroPathAssesment', data_a),
            ('MSFD8bMicroPathAssesIndicator', data_ai),
            ('MSFD8bMicroPathActivity', data_ac),
            # ('MSFD8bMicroPathSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bMicrobialItemDisplay)
class A81bMicrobialAssessment(ItemDisplay):
    title = 'Asessment of microbial pathogens'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bMicrobialPathogensAssesment,
                'MSFD8b_MicrobialPathogens',
                self.context.item.MSFD8b_MicrobialPathogens_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bMicrobialPathogensAssesmentIndicator,
            'MSFD8b_MicrobialPathogens_Assesment',
            self.item.MSFD8b_MicrobialPathogens_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO
# MSFD8bMicrobialPathogensActivity is not directly related to
# MSFD8b_MicrobialPathogens table
# needs to be joined with MSFD8bMicrobialPathogensActivityDescription table
# first
@register_form_section(A81bMicrobialItemDisplay)
class A81bMicrobialActivities(ItemDisplay):
    title = 'Activities producing microbial pathogens'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bMicrobialPathogensActivity,
                sql.MSFD8bMicrobialPathogensActivityDescription,
                'MSFD8b_MicrobialPathogens',
                self.context.item.MSFD8b_MicrobialPathogens_ID
            )


# TODO
# missing table MSFD8bMicrobialPathogenSumInfo2ImpactedElement ??
# @register_form_section(A81bMicrobialItemDisplay)
# class A81bMicrobialImpacts(ItemDisplay):
#     title = 'Impacts produced by the microbial pathogens'
#
#     def get_db_results(self):
#         if self.context.item:
#             return db.get_related_record(
#                 sql.MSFD8bMicrobialPathogenSumInfo2ImpactedElement,
#                 'MSFD8b_MicrobialPathogens',
#                 self.context.item.MSFD8b_MicrobialPathogens_ID
#             )
# endregion Microbial pathogens


# region Non-indigenous species
class A81bNonIndigenousItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bNI
    order_field = 'MSFD8b_NIS_ID'


@register_subform(A81bForm)
class A81bNonIndigenousSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D2 - Non-indigenous species'
    mapper_class = sql.MSFD8bNI

    def get_subform(self):
        return A81bNonIndigenousItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_NIS_ID for row in data]
        mc_a = sql.MSFD8bNISAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_NIS.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_NIS_Assesment_ID for row in data_a]
        mc_ai = sql.MSFD8bNISAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_NIS_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bNISActivity
        klass_join = sql.MSFD8bNISActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_NIS_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_NIS_ActivityDescription,
                klass_join.MSFD8b_NIS_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_NIS
            ],
            klass_join,
            klass_join.MSFD8b_NIS.in_(base_ids)
        )

        mc_sum = sql.MSFD8bNISSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_NIS.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bNI', data),
            ('MSFD8bNISAssesment', data_a),
            ('MSFD8bNISAssesmentIndicator', data_ai),
            ('MSFD8bNISActivity', data_ac),
            ('MSFD8bNISSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bNonIndigenousItemDisplay)
class A81bNonIndigenousAssessment(ItemDisplay):
    title = 'Asessment of non-indigenous species'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNISAssesment,
                'MSFD8b_NIS',
                self.context.item.MSFD8b_NIS_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bNISAssesmentIndicator,
            'MSFD8b_NIS_Assesment',
            self.item.MSFD8b_NIS_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
# MSFD8bNISActivity is not directly related to
# MSFD8b_NIS table
# needs to be joined with MSFD8bNISActivityDescription table first
@register_form_section(A81bNonIndigenousItemDisplay)
class A81bNonIndigenousActivities(ItemDisplay):
    title = 'Activities producing non-indigenous species'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bNISActivity,
                sql.MSFD8bNISActivityDescription,
                'MSFD8b_NIS',
                self.context.item.MSFD8b_NIS_ID
            )


@register_form_section(A81bNonIndigenousItemDisplay)
class A81bNonIndigenousImpacts(ItemDisplay):
    title = 'Impacts produced by non-indigenous species'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNISSumInfo2ImpactedElement,
                'MSFD8b_NIS',
                self.context.item.MSFD8b_NIS_ID
            )
# endregion Non-indigenous species


# region Underwater noise
class A81bNoiseItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bNoise
    order_field = 'MSFD8b_Noise_ID'


@register_subform(A81bForm)
class A81bNoiseSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D11 - Underwater noise'
    mapper_class = sql.MSFD8bNoise

    def get_subform(self):
        return A81bNoiseItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_Noise_ID for row in data]
        mc_a = sql.MSFD8bNoiseAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_Noise.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_Noise_Assesment_ID for row in data_a]
        mc_ai = sql.MSFD8bNoiseAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_Noise_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bNoiseActivity
        klass_join = sql.MSFD8bNoiseActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_Noise_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_Noise_ActivityDescription,
                klass_join.MSFD8b_Noise_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_Noise
            ],
            klass_join,
            klass_join.MSFD8b_Noise.in_(base_ids)
        )

        mc_sum = sql.MSFD8bNoiseSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_Noise.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bNoise', data),
            ('MSFD8bNoiseAssesment', data_a),
            ('MSFD8bNoiseAssesIndicator', data_ai),
            ('MSFD8bNoiseActivity', data_ac),
            ('MSFD8bNoiseSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bNoiseItemDisplay)
class A81bNoiseAssessment(ItemDisplay):
    title = 'Asessment of underwater noise'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNoiseAssesment,
                'MSFD8b_Noise',
                self.context.item.MSFD8b_Noise_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bNoiseAssesmentIndicator,
            'MSFD8b_Noise_Assesment',
            self.item.MSFD8b_Noise_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bNoiseItemDisplay)
class A81bNoiseActivities(ItemDisplay):
    title = 'Activities producing underwater noise'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bNoiseActivity,
                sql.MSFD8bNoiseActivityDescription,
                'MSFD8b_Noise',
                self.context.item.MSFD8b_Noise_ID
            )


@register_form_section(A81bNoiseItemDisplay)
class A81bNoiseImpacts(ItemDisplay):
    title = 'Impacts produced by underwater noise'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNoiseSumInfo2ImpactedElement,
                'MSFD8b_Noise',
                self.context.item.MSFD8b_Noise_ID
            )
# endregion Underwater noise


# region Nutrients
class A81bNutrientItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bNutrient
    order_field = 'MSFD8b_Nutrients_ID'


@register_subform(A81bForm)
class A81bNutrientSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D5 - Nutrients'
    mapper_class = sql.MSFD8bNutrient

    def get_subform(self):
        return A81bNutrientItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_Nutrients_ID for row in data]
        mc_a = sql.MSFD8bNutrientsAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_Nutrients.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_Nutrients_Assesment_ID for row in data_a]
        mc_ai = sql.MSFD8bNutrientsAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_Nutrients_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bNutrientsActivity
        klass_join = sql.MSFD8bNutrientsActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_Nutrients_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_Nutrients_ActivityDescription,
                klass_join.MSFD8b_Nutrients_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_Nutrients
            ],
            klass_join,
            klass_join.MSFD8b_Nutrients.in_(base_ids)
        )

        mc_sum = sql.MSFD8bNutrientsSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_Nutrients.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bNutrient', data),
            ('MSFD8bNutrientsAssesment', data_a),
            ('MSFD8bNutriAssesIndicator', data_ai),
            ('MSFD8bNutrientsActivity', data_ac),
            ('MSFD8bNutrientsSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bNutrientItemDisplay)
class A81bNutrientAssessment(ItemDisplay):
    title = 'Asessment of nutrients'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNutrientsAssesment,
                'MSFD8b_Nutrients',
                self.context.item.MSFD8b_Nutrients_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bNutrientsAssesmentIndicator,
            'MSFD8b_Nutrients_Assesment',
            self.item.MSFD8b_Nutrients_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bNutrientItemDisplay)
class A81bNutrientActivities(ItemDisplay):
    title = 'Activities producing nutrients'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bNutrientsActivity,
                sql.MSFD8bNutrientsActivityDescription,
                'MSFD8b_Nutrients',
                self.context.item.MSFD8b_Nutrients_ID
            )


@register_form_section(A81bNutrientItemDisplay)
class A81bNutrientImpacts(ItemDisplay):
    title = 'Impacts produced by the nutrients'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bNutrientsSumInfo2ImpactedElement,
                'MSFD8b_Nutrients',
                self.context.item.MSFD8b_Nutrients_ID
            )
# endregion Nutrients


# region Physical damage
class A81bPhysicalDamageItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bPhysicalDamage
    order_field = 'MSFD8b_PhysicalDamage_ID'


@register_subform(A81bForm)
class A81bPhysicalDamageSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D6 - Physical damage'
    mapper_class = sql.MSFD8bPhysicalDamage

    def get_subform(self):
        return A81bPhysicalDamageItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_PhysicalDamage_ID for row in data]
        mc_a = sql.MSFD8bPhysicalDamageAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_PhysicalDamage.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_PhysicalDamage_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bPhysicalDamageAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_PhysicalDamage_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bPhysicalDamageActivity
        klass_join = sql.MSFD8bPhysicalDamageActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_PhysicalDamage_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_PhysicalDamage_ActivityDescription,
                klass_join.MSFD8b_PhysicalDamage_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_PhysicalDamage
            ],
            klass_join,
            klass_join.MSFD8b_PhysicalDamage.in_(base_ids)
        )

        mc_sum = sql.MSFD8bPhysicalDamageSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_PhysicalDamage.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bPhysicalDamage', data),
            ('MSFD8bPhysicalDamageAssesment', data_a),
            ('MSFD8bPhysicalAssesIndicator', data_ai),
            ('MSFD8bPhysicalDamageActivity', data_ac),
            ('MSFD8bPhysicalDamageSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bPhysicalDamageItemDisplay)
class A81bPhysicalDamageAssessment(ItemDisplay):
    title = 'Asessment of physical damage'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPhysicalDamageAssesment,
                'MSFD8b_PhysicalDamage',
                self.context.item.MSFD8b_PhysicalDamage_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bPhysicalDamageAssesmentIndicator,
            'MSFD8b_PhysicalDamage_Assesment',
            self.item.MSFD8b_PhysicalDamage_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bPhysicalDamageItemDisplay)
class A81bPhysicalDamageActivities(ItemDisplay):
    title = 'Activities producing physical damage'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bPhysicalDamageActivity,
                sql.MSFD8bPhysicalDamageActivityDescription,
                'MSFD8b_PhysicalDamage',
                self.context.item.MSFD8b_PhysicalDamage_ID
            )


@register_form_section(A81bPhysicalDamageItemDisplay)
class A81bPhysicalDamageImpacts(ItemDisplay):
    title = 'Impacts produced by the physical damage'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPhysicalDamageSumInfo2ImpactedElement,
                'MSFD8b_PhysicalDamage',
                self.context.item.MSFD8b_PhysicalDamage_ID
            )
# endregion Physical damage


# region Physical loss
class A81bPhysicalLosItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bPhysicalLos
    order_field = 'MSFD8b_PhysicalLoss_ID'


@register_subform(A81bForm)
class A81bPhysicalLosSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D6 - Physical loss'
    mapper_class = sql.MSFD8bPhysicalLos

    def get_subform(self):
        return A81bPhysicalLosItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_PhysicalLoss_ID for row in data]
        mc_a = sql.MSFD8bPhysicalLossAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_PhysicalLoss.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_PhysicalLoss_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bPhysicalLossAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_PhysicalLoss_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bPhysicalLossActivity
        klass_join = sql.MSFD8bPhysicalLossActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_PhysicalLoss_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_PhysicalLoss_ActivityDescription,
                klass_join.MSFD8b_PhysicalLoss_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_PhysicalLoss
            ],
            klass_join,
            klass_join.MSFD8b_PhysicalLoss.in_(base_ids)
        )

        mc_sum = sql.MSFD8bPhysicalLossSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_PhysicalLoss.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bPhysicalLos', data),
            ('MSFD8bPhysicalLossAssesment', data_a),
            ('MSFD8bPhysLossAssesIndicator', data_ai),
            ('MSFD8bPhysicalLossActivity', data_ac),
            ('MSFD8bPhysicalLossSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bPhysicalLosItemDisplay)
class A81bPhysicalLosAssessment(ItemDisplay):
    title = 'Asessment of physical loss'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPhysicalLossAssesment,
                'MSFD8b_PhysicalLoss',
                self.context.item.MSFD8b_PhysicalLoss_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bPhysicalLossAssesmentIndicator,
            'MSFD8b_PhysicalLoss_Assesment',
            self.item.MSFD8b_PhysicalLoss_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bPhysicalLosItemDisplay)
class A81bPhysicalLosActivities(ItemDisplay):
    title = 'Activities producing physical loss'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bPhysicalLossActivity,
                sql.MSFD8bPhysicalLossActivityDescription,
                'MSFD8b_PhysicalLoss',
                self.context.item.MSFD8b_PhysicalLoss_ID
            )


@register_form_section(A81bPhysicalLosItemDisplay)
class A81bPhysicalLosImpacts(ItemDisplay):
    title = 'Impacts produced by the physical loss'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPhysicalLossSumInfo2ImpactedElement,
                'MSFD8b_PhysicalLoss',
                self.context.item.MSFD8b_PhysicalLoss_ID
            )
# endregion Physical loss


# region Pollutant events
class A81bPollutantEventItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bPollutantEvent
    order_field = 'MSFD8b_PollutantEvents_ID'


@register_subform(A81bForm)
class A81bPollutantEventSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D8 - Pollutant events'
    mapper_class = sql.MSFD8bPollutantEvent

    def get_subform(self):
        return A81bPollutantEventItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_PollutantEvents_ID for row in data]
        mc_a = sql.MSFD8bPollutantEventsAssesment
        count, data_a = db.get_all_records(
            mc_a,
            mc_a.MSFD8b_PollutantEvents.in_(base_ids)
        )

        assesment_ids = [row.MSFD8b_PollutantEvents_Assesment_ID
                         for row in data_a]
        mc_ai = sql.MSFD8bPollutantEventsAssesmentIndicator
        count, data_ai = db.get_all_records(
            mc_ai,
            mc_ai.MSFD8b_PollutantEvents_Assesment.in_(assesment_ids)
        )

        mc_ac = sql.MSFD8bPollutantEventsActivity
        klass_join = sql.MSFD8bPollutantEventsActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_PollutantEvents_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_PollutantEvents_ActivityDescription,
                klass_join.MSFD8b_PollutantEvents_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_PollutantEvents
            ],
            klass_join,
            klass_join.MSFD8b_PollutantEvents.in_(base_ids)
        )

        mc_sum = sql.MSFD8bPollutantEventsSumInfo2ImpactedElement
        count, data_sum = db.get_all_records(
            mc_sum,
            mc_sum.MSFD8b_PollutantEvents.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bPollutantEvent', data),
            ('MSFD8bPollutantEventsAssesment', data_a),
            ('MSFD8bPolEventsAssesIndicator', data_ai),
            ('MSFD8bPollutantEventsActivity', data_ac),
            ('MSFD8bPollutantEventsSum', data_sum),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81bPollutantEventItemDisplay)
class A81bPollutantEventAssessment(ItemDisplay):
    title = 'Asessment of pollutant events'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPollutantEventsAssesment,
                'MSFD8b_PollutantEvents',
                self.context.item.MSFD8b_PollutantEvents_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8bPollutantEventsAssesmentIndicator,
            'MSFD8b_PollutantEvents_Assesment',
            self.item.MSFD8b_PollutantEvents_Assesment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Assesment Indicator', item


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bPollutantEventItemDisplay)
class A81bPollutantEventActivities(ItemDisplay):
    title = 'Activities producing pollutant events'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bPollutantEventsActivity,
                sql.MSFD8bPollutantEventsActivityDescription,
                'MSFD8b_PollutantEvents',
                self.context.item.MSFD8b_PollutantEvents_ID
            )


@register_form_section(A81bPollutantEventItemDisplay)
class A81bPollutantEventImpacts(ItemDisplay):
    title = 'Impacts produced by the pollutant event'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8bPollutantEventsSumInfo2ImpactedElement,
                'MSFD8b_PollutantEvents',
                self.context.item.MSFD8b_PollutantEvents_ID
            )
# endregion Pollutant events


# region Acidification
class A81bAcidificationItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1b
    """
    mapper_class = sql.MSFD8bAcidification
    order_field = 'MSFD8b_Acidification_ID'


@register_subform(A81bForm)
class A81bAcidificationSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1b form
    """
    title = 'D4 - Acidification'
    mapper_class = sql.MSFD8bAcidification

    def get_subform(self):
        return A81bAcidificationItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        base_ids = [row.MSFD8b_Acidification_ID for row in data]

        mc_ac = sql.MSFD8bAcidificationActivity
        klass_join = sql.MSFD8bAcidificationActivityDescription
        count, data_ac = db.get_all_records_join(
            [
                mc_ac.MSFD8b_Acidification_Activity_ID,
                mc_ac.Activity,
                mc_ac.ActivityRank,
                mc_ac.MSFD8b_Acidification_ActivityDescription,
                klass_join.MSFD8b_Acidification_ActivityDescription_ID,
                klass_join.MarineUnitID,
                klass_join.Description,
                klass_join.Limitations,
                klass_join.MSFD8b_Acidification
            ],
            klass_join,
            klass_join.MSFD8b_Acidification.in_(base_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8bAcidification', data),
            ('MSFD8bAcidificationActivity', data_ac),
        ]

        return data_to_xls(xlsdata)


#  TODO CHECK IF IMPLEMENTATION IS CORRECT
@register_form_section(A81bAcidificationItemDisplay)
class A81bAcidificationActivities(ItemDisplay):
    title = 'Activities producing acidification'

    blacklist = ['MSFD8b_Acidification_ActivityDescription']
    use_blacklist = True

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record_join(
                sql.MSFD8bAcidificationActivity,
                sql.MSFD8bAcidificationActivityDescription,
                'MSFD8b_Acidification',
                self.context.item.MSFD8b_Acidification_ID
            )
# endregion Acidification
