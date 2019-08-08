from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.field import Fields

from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from .base import ItemDisplay, MultiItemDisplayForm
from .interfaces import IA81Form
from .utils import (data_to_xls, register_form, register_form_section,
                    register_subform)


@register_form
class A81aForm(EmbeddedForm):
    """ Main form for A81a.

    Allows selecting between Ecosystem, Functional, etc
    """

    record_title = title = \
        'Article 8.1a (Analysis of the environmental status)'
    fields = Fields(IA81Form)

    def get_subform(self):
        klass = self.data.get('theme')

        return super(A81aForm, self).get_subform(klass)


# region Ecosystem(s)
@register_subform(A81aForm)
class A81aEcoSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D4 - Ecosystem(s)'
    mapper_class = sql.MSFD8aEcosystem

    def get_subform(self):
        return A81aEcoItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        eco_ids = [row.MSFD8a_Ecosystem_ID for row in data]
        mc_pi = sql.MSFD8aEcosystemPressuresImpact
        count, data_pi = db.get_all_records(
            mc_pi,
            mc_pi.MSFD8a_Ecosystem.in_(eco_ids)
        )

        mc_sa = sql.MSFD8aEcosystemStatusAssessment
        count, data_sa = db.get_all_records(
            mc_sa,
            mc_sa.MSFD8a_Ecosystem.in_(eco_ids)
        )

        eco_sa_ids = [row.MSFD8a_Ecosystem_StatusAssessment_ID
                      for row in data_sa]
        mc_si = sql.MSFD8aEcosystemStatusIndicator
        count, data_si = db.get_all_records(
            mc_si,
            mc_si.MSFD8a_Ecosystem_StatusAssessment.in_(eco_sa_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aEcosystem', data),
            ('MSFD8aEcosystemPressuresImpact', data_pi),
            ('MSFD8aEcosysStatusAssessment', data_sa),
            ('MSFD8aEcosystemStatusIndicator', data_si),
        ]

        return data_to_xls(xlsdata)


class A81aEcoItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aEcosystem
    order_field = 'MSFD8a_Ecosystem_ID'


@register_form_section(A81aEcoItemDisplay)
class A81aEcosystemPressures(ItemDisplay):
    title = 'Pressures and impacts'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aEcosystemPressuresImpact,
                'MSFD8a_Ecosystem',
                self.context.item.MSFD8a_Ecosystem_ID
            )


@register_form_section(A81aEcoItemDisplay)
class A81aEcosystemAsessment(ItemDisplay):
    title = 'Status Asessment'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aEcosystemStatusAssessment,
                'MSFD8a_Ecosystem',
                self.context.item.MSFD8a_Ecosystem_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8aEcosystemStatusIndicator,
            'MSFD8a_Ecosystem_StatusAssessment',
            self.item.MSFD8a_Ecosystem_StatusAssessment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Status Indicator', item


# endregion Ecosystem


# region Functional Group(s)
@register_subform(A81aForm)
class A81aFunctSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D1 - Functional group(s)'
    mapper_class = sql.MSFD8aFunctional

    def get_subform(self):
        return A81aFunctItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        funct_ids = [row.MSFD8a_Functional_ID for row in data]
        mc_pi = sql.MSFD8aFunctionalPressuresImpact
        count, data_pi = db.get_all_records(
            mc_pi,
            mc_pi.MSFD8a_Functional.in_(funct_ids)
        )

        mc_sa = sql.MSFD8aFunctionalStatusAssessment
        count, data_sa = db.get_all_records(
            mc_sa,
            mc_sa.MSFD8a_Functional.in_(funct_ids)
        )

        funct_sa_ids = [row.MSFD8a_Functional_StatusAssessment_ID
                        for row in data_sa]
        mc_si = sql.MSFD8aFunctionalStatusIndicator
        count, data_si = db.get_all_records(
            mc_si,
            mc_si.MSFD8a_Functional_StatusAssessment.in_(funct_sa_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aFunctional', data),
            ('MSFD8aFunctionalPressuresImpact', data_pi),
            ('MSFD8aFunctStatusAssessment', data_sa),
            ('MSFD8aFunctionalStatusIndicator', data_si),
        ]

        return data_to_xls(xlsdata)


class A81aFunctItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aFunctional
    order_field = 'MSFD8a_Functional_ID'


@register_form_section(A81aFunctItemDisplay)
class A81aFunctionalGroupPressures(ItemDisplay):
    title = 'Pressures and impacts'

    blacklist = ['MSFD8a_Functional']
    use_blacklist = True

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aFunctionalPressuresImpact,
                'MSFD8a_Functional',
                self.context.item.MSFD8a_Functional_ID
            )


@register_form_section(A81aFunctItemDisplay)
class A81aFunctionalGroupAsessment(ItemDisplay):
    title = 'Status Asessment'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aFunctionalStatusAssessment,
                'MSFD8a_Functional',
                self.context.item.MSFD8a_Functional_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8aFunctionalStatusIndicator,
            'MSFD8a_Functional_StatusAssessment',
            self.item.MSFD8a_Functional_StatusAssessment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Status Indicator', item

# endregion Functional Group


# region Habitat(s)
@register_subform(A81aForm)
class A81aHabitatSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D6 - Habitat(s)'
    mapper_class = sql.MSFD8aHabitat

    def get_subform(self):
        return A81aHabitatItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        habitat_ids = [row.MSFD8a_Habitat_ID for row in data]
        mc_hpi = sql.MSFD8aHabitatPressuresImpact
        count, data_hpi = db.get_all_records(
            mc_hpi,
            mc_hpi.MSFD8a_Habitat.in_(habitat_ids)
        )

        mc_hsa = sql.MSFD8aHabitatStatusAssessment
        count, data_hsa = db.get_all_records(
            mc_hsa,
            mc_hsa.MSFD8a_Habitat.in_(habitat_ids)
        )

        habitat_sa_ids = [row.MSFD8a_Habitat_StatusAssessment_ID
                          for row in data_hsa]
        mc_hsi = sql.MSFD8aHabitatStatusIndicator
        count, data_hsi = db.get_all_records(
            mc_hsi,
            mc_hsi.MSFD8a_Habitat_StatusAssessment.in_(habitat_sa_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aHabitat', data),
            ('MSFD8aHabitatPressuresImpact', data_hpi),
            ('MSFD8aHabitatStatusAssessment', data_hsa),
            ('MSFD8aHabitatStatusIndicator', data_hsi),
        ]

        return data_to_xls(xlsdata)


class A81aHabitatItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aHabitat
    order_field = 'MSFD8a_Habitat_ID'


@register_form_section(A81aHabitatItemDisplay)
class A81aHabitatPressures(ItemDisplay):
    title = 'Pressures and impacts'

    blacklist = ['MSFD8a_Habitat']
    use_blacklist = True

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aHabitatPressuresImpact,
                'MSFD8a_Habitat',
                self.context.item.MSFD8a_Habitat_ID
            )


@register_form_section(A81aHabitatItemDisplay)
class A81aHabitatAsessment(ItemDisplay):
    title = 'Status Asessment'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aHabitatStatusAssessment,
                'MSFD8a_Habitat',
                self.context.item.MSFD8a_Habitat_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8aHabitatStatusIndicator,
            'MSFD8a_Habitat_StatusAssessment',
            self.item.MSFD8a_Habitat_StatusAssessment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Status Indicator', item

# endregion Habitat(s)


# region Species(s)
@register_subform(A81aForm)
class A81aSpeciesSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D1 - Species(s)'
    mapper_class = sql.MSFD8aSpecy

    def get_subform(self):
        return A81aSpeciesItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        species_ids = [row.MSFD8a_Species_ID for row in data]
        mc_spi = sql.MSFD8aSpeciesPressuresImpact
        count, data_spi = db.get_all_records(
            mc_spi,
            mc_spi.MSFD8a_Species.in_(species_ids)
        )

        mc_ssa = sql.MSFD8aSpeciesStatusAssessment
        count, data_ssa = db.get_all_records(
            mc_ssa,
            mc_ssa.MSFD8a_Species.in_(species_ids)
        )

        species_sa_ids = [row.MSFD8a_Species_StatusAssessment_ID
                          for row in data_ssa]
        mc_ssi = sql.MSFD8aSpeciesStatusIndicator
        count, data_ssi = db.get_all_records(
            mc_ssi,
            mc_ssi.MSFD8a_Species_StatusAssessment.in_(species_sa_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aSpecy', data),
            ('MSFD8aSpeciesPressuresImpact', data_spi),
            ('MSFD8aSpeciesStatusAssessment', data_ssa),
            ('MSFD8aSpeciesStatusIndicator', data_ssi),
        ]

        return data_to_xls(xlsdata)


class A81aSpeciesItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aSpecy
    order_field = 'MSFD8a_Species_ID'


@register_form_section(A81aSpeciesItemDisplay)
class A81aSpeciesPressures(ItemDisplay):
    title = 'Pressures and impacts'

    blacklist = ['MSFD8a_Species']
    use_blacklist = True

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aSpeciesPressuresImpact,
                'MSFD8a_Species',
                self.context.item.MSFD8a_Species_ID
            )


@register_form_section(A81aSpeciesItemDisplay)
class A81aSpeciesAsessment(ItemDisplay):
    title = 'Status Asessment'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aSpeciesStatusAssessment,
                'MSFD8a_Species',
                self.context.item.MSFD8a_Species_ID
            )

    def get_extra_data(self):
        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8aSpeciesStatusIndicator,
            'MSFD8a_Species_StatusAssessment',
            self.item.MSFD8a_Species_StatusAssessment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        return 'Status Indicator', item

# endregion Species(s)


# region Other(s)
@register_subform(A81aForm)
class A81aOtherSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D4 - Other(s)'
    mapper_class = sql.MSFD8aOther

    def get_subform(self):
        return A81aOtherItemDisplay(self, self.request)

    # TODO MSFD8aOtherPressuresImpact table is missing
    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        other_ids = [row.MSFD8a_Other_ID for row in data]
        mc_other_sa = sql.MSFD8aOtherStatusAssessment
        count, data_other_sa = db.get_all_records(
            mc_other_sa,
            mc_other_sa.MSFD8a_Other.in_(other_ids)
        )

        other_status_ids = [row.MSFD8a_Other_StatusAssessment_ID
                            for row in data_other_sa]
        mc_other_si = sql.MSFD8aOtherStatusIndicator
        count, data_other_si = db.get_all_records(
            mc_other_si,
            mc_other_si.MSFD8a_Other_StatusAssessment.in_(other_status_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aOther', data),
            ('MSFD8aOtherStatusAssessment', data_other_sa),
            ('MSFD8aOtherStatusIndicator', data_other_si),
        ]

        return data_to_xls(xlsdata)


class A81aOtherItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aOther
    order_field = 'MSFD8a_Other_ID'

# TODO
# MSFD8aOtherPressuresImpact table is missing?
# @register_form_section(A81aOtherItemDisplay)
# class A81aOtherPressures(ItemDisplay):
#     title = 'Pressures and impacts'
#
#     def get_db_results(self):
#         if self.context.item:
#             return db.get_related_record(
#                 sql.MSFD8aOtherPressuresImpact,
#                 'MSFD8a_Other',
#                 self.context.item.MSFD8a_Other_ID
#             )


@register_form_section(A81aOtherItemDisplay)
class A81aOtherAsessment(ItemDisplay):
    title = 'Status Asessment'

    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8aOtherStatusAssessment,
                'MSFD8a_Other',
                self.context.item.MSFD8a_Other_ID
            )

    def get_extra_data(self):

        if not self.item:
            return {}

        count, item = db.get_related_record(
            sql.MSFD8aOtherStatusIndicator,
            'MSFD8a_Other_StatusAssessment',
            self.item.MSFD8a_Other_StatusAssessment_ID
        )
        # ft = pivot_data(res, 'FeatureType')

        if count:
            return 'Status Indicator', item

        return {}

# endregion Other(s)


# region Nis Inventory(s)
@register_subform(A81aForm)
class A81aNisSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D2 - NIS Inventory'
    mapper_class = sql.MSFD8aNISInventory

    def get_subform(self):
        return A81aNisItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class, self.mapper_class.MarineUnitID.in_(muids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aNISInventory', data),
        ]

        return data_to_xls(xlsdata)


class A81aNisItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aNISInventory
    order_field = 'MSFD8a_NISInventory_ID'

    # def get_db_results(self):
    #     # if self.context.item:
    #         return db.get_related_record(
    #             self.mapper_class,
    #             'MarineUnitID',
    #             self.item.MSFD8a_NISInventory_ID
    #         )

# endregion Nis Inventory(s)


# region Physical
@register_subform(A81aForm)
class A81aPhysicalSubForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID for the Article 8.1a form
    """
    title = 'D4 - Physical'
    mapper_class = sql.MSFD8aPhysical

    def get_subform(self):
        return A81aPhysicalItemDisplay(self, self.request)

    def download_results(self):
        muids = self.get_marine_unit_ids()
        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD8aPhysical', data),
        ]

        return data_to_xls(xlsdata)


class A81aPhysicalItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1a
    """
    mapper_class = sql.MSFD8aPhysical
    order_field = 'MSFD8a_Physical_ID'

    # def get_db_results(self):
    #     # if self.context.item:
    #         return db.get_related_record(
    #             self.mapper_class,
    #             'MarineUnitID',
    #             self.item.MSFD8a_NISInventory_ID
    #         )

# endregion Physical


# Article 8.1c
@register_form
class A81cForm(MarineUnitIDSelectForm):
    """ Main form for A81c.

    Class for Article 8.1c Economic and social analysis
    """

    record_title = title = 'Article 8.1c (Economic and social analysis)'
    mapper_class = sql.MSFD8cUs

    def get_subform(self):
        return A81cEconomicItemDisplay(self, self.request)


class A81cEconomicItemDisplay(MultiItemDisplayForm):
    """ Group the multiple items together for A8.1c
    """
    mapper_class = sql.MSFD8cUs
    order_field = 'MSFD8c_Uses_ID'

    # TODO: need to filter on topic

    def download_results(self):
        muids = self.get_marine_unit_ids()

        count, data = db.get_all_records(
            self.mapper_class,
            self.mapper_class.MarineUnitID.in_(muids)
        )

        uses_ids = [row.MSFD8c_Uses_ID for row in data]

        mc_pressure = sql.MSFD8cPressure
        count, data_p = db.get_all_records(
            mc_pressure,
            mc_pressure.MSFD8c_Uses_ID.in_(uses_ids)
        )

        mc_depend = sql.MSFD8cDepend
        count, data_d = db.get_all_records(
            mc_depend,
            mc_depend.MSFD8c_Uses_ID.in_(uses_ids)
        )

        xlsdata = [
            ('MSFD8cUs', data),
            ('MSFD8cPressure', data_p),
            ('MSFD8cDepend', data_d),
        ]

        return data_to_xls(xlsdata)


@register_form_section(A81cEconomicItemDisplay)
class A81cEconomicPressures(ItemDisplay):
    title = 'Pressures produces by the activities'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8cPressure,
                'MSFD8c_Uses_ID',
                self.context.item.MSFD8c_Uses_ID
            )


@register_form_section(A81cEconomicItemDisplay)
class A81aEconomicDependencies(ItemDisplay):
    title = 'Dependencies of activities on features'

    def get_db_results(self):
        if self.context.item:
            return db.get_related_record(
                sql.MSFD8cDepend,
                'MSFD8c_Uses_ID',
                self.context.item.MSFD8c_Uses_ID
            )
