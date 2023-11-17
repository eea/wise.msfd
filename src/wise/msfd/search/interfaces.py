from __future__ import absolute_import
from zope.interface import Attribute, Interface
from zope.schema import Choice, Int, List

from ..interfaces import IEmbeddedForm


class IItemDisplayForm(IEmbeddedForm):
    data_template = Attribute(u"Template to be used to show item data")
    extra_data_template = Attribute(u"Template for any extra item data")

    def set_item():
        """ Called from update() to set self.item
        """

    def get_db_results():
        """ Actual DB query implementation to get item
        """

    def get_extra_data():
        """ Return extra data as HTML for this item
        """


class IArticleSelectA8(Interface):
    article = Choice(title=u"Report type",
                     required=False,
                     default='',
                     vocabulary="wise_search_articles_a8")


class IReportingPeriodSelectA8(Interface):
    reporting_period = Choice(title=u"Reporting period",
                              required=False,
                              vocabulary="wise_search_reporting_period_a8")


class IReportingPeriodSelectA9(Interface):
    reporting_period = Choice(title=u"Reporting period",
                              required=False,
                              vocabulary="wise_search_reporting_period_a9")


class IReportingPeriodSelectA10(Interface):
    reporting_period = Choice(title=u"Reporting period",
                              required=False,
                              vocabulary="wise_search_reporting_period_a10")


class IRecordSelect(Interface):
    """ We use a pagination based record selection
    """

    page = Int(title=u'Record page', required=False, default=0)


class IRegionSubregions(Interface):
    region_subregions = List(
        title=u"Region and Subregion",
        value_type=Choice(vocabulary="wise_search_region_subregions"),
        required=False,
    )


class IMemberStates(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_member_states"),
        required=False,
    )


class IMemberStatesArt4(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_member_states_art4"),
        required=False,
    )


class IMemberStatesArt6(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_member_states_art6"),
        required=False,
    )


class IMemberStatesArt7(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_member_states_art7"),
        required=False,
    )


class IAreaTypes(Interface):
    area_types = List(
        title=u"Area Type",
        value_type=Choice(vocabulary="wise_search_area_type"),
        required=False,
    )


class IStartArticles8910(IRegionSubregions):
    pass


class IA81Form(Interface):

    theme = Choice(
        title=u"Select theme",
        required=False,
        vocabulary='wise_search_a81_forms'
    )


class IStartArticle13(Interface):
    reporting_period = Choice(
        title=u"Reporting period",
        vocabulary="wise_search_a13_reporting_period",
        required=False,
    )


class IStartArticles1314(Interface):
    report_type = Choice(
        title=u"Report Type",
        vocabulary="wise_search_a1314_report_types",
        required=False,
    )


class IArticles1314Region(Interface):
    region_subregions = List(
        title=u"Region and Subregion",
        value_type=Choice(vocabulary="wise_search_a1314_regions"),
        required=False,
    )


class IStartArticle11(Interface):
    monitoring_programme_info_type = Choice(
        title=u"Information Type",
        vocabulary="wise_search_monitoring_programme_info_types",
        required=False
    )


class IArticle11MonitoringProgrammeType(Interface):
    monitoring_programme_types = List(
        title=u"Monitoring programme Type",
        value_type=Choice(
            vocabulary="wise_search_monitoring_programme_vb_factory"),
        required=False
    )


class IA1314MemberStates(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_a1314_member_states"),
        required=False,
    )


class IA1314UniqueCodes(Interface):
    unique_codes = List(
        title=u"Unique Codes",
        required=False,
        value_type=Choice(vocabulary="wise_search_a1314_unique_codes")
    )


class IA2012GesComponentsArt9(Interface):
    ges_components = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2012_ges_components_art9")
    )


class IA2012GesComponentsArt10(Interface):
    ges_components = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2012_ges_components_art10")
    )


class IStartArticle18(Interface):
    data_type = Choice(
        title=u"Data type",
        vocabulary='wise_search_a18_data_type',
        required=False
    )


class IStartArticle4(Interface):
    reporting_cycle = Choice(
        title=u"Select reporting cycle",
        vocabulary='wise_search_a4_mru_reporting_cycle_factory',
        required=False
    )


# Articles 8, 9, 10
# 2018 reporting year
class IArticleSelectA82018(Interface):
    article = Choice(title=u"Report type",
                     required=False,
                     default='',
                     vocabulary="wise_search_articles_a8_2018")


class ICountryCode(Interface):
    member_states = List(
        title=u"Country",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_country")
    )


class ICountryCode2018Art9(Interface):
    member_states = List(
        title=u"Country",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_country_art9")
    )


class IGESComponentsA9(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_ges_component_art9")
    )


class IFeatures(Interface):
    feature = List(
        title=u"Feature",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature")
    )


class IGESComponents(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_ges_component")
    )

class IGESComponentsA132022(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_ges_component_a132022")
    )


class IReportTypeArt9(Interface):
    report_type = Choice(
        title=u"Report type",
        required=False,
        default='',
        vocabulary="wise_search_report_type_a9"
    )


class IReportTypeArt10(Interface):
    report_type = Choice(
        title=u"Report type",
        required=False,
        default='',
        vocabulary="wise_search_report_type_a10"
    )


class IFeaturesA9(Interface):
    feature = List(
        title=u"Feature",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature_art9")
    )


class IFeatures81c(Interface):
    feature = List(
        title=u"Feature",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature_art81c")
    )


class IIndicatorsFeature(Interface):
    feature = List(
        title=u"Feature",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature_ind")
    )


class IIndicatorsGesComponent(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_ges_component_ind")
    )


class IMarineUnit2018(Interface):
    marine_unit_id = List(
        title=u"Marine Reporting Unit",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_marine_reporting_unit")
    )


class IMonitoringProgramme(Interface):

    marine_unit_ids = List(
        title=u"Marine Unit IDs",
        value_type=Choice(vocabulary="wise_search_art11_marine_unit_id"),
        required=False
    )


class IMonitoringSubprogramme(Interface):

    marine_unit_ids = List(
        title=u"Marine Unit IDs",
        value_type=Choice(vocabulary="wise_search_art11_marine_unit_id_ms"),
        required=False
    )


class IRegionSubregionsArt6(Interface):
    region_subregions = List(
        title=u"Region and Subregion",
        value_type=Choice(vocabulary="wise_search_region_subregions_art6"),
        required=False,
    )


class IGESComponentsA18(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a18_ges_component")
    )


class IRegionSubregionsArt112020(Interface):
    region_subregions = List(
        title=u"Region and Subregion",
        value_type=Choice(vocabulary="wise_search_region_art112020"),
        required=False,
    )


class IMemberStatesArt112020(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_country_art112020"),
        required=False,
    )


class IGESComponentArt112020(Interface):
    ges_component = List(
        title=u"Descriptor",
        value_type=Choice(vocabulary="wise_search_ges_component_a112020"),
        required=False,
    )

# Article 19
class IArticle19ReportingPeriod(Interface):
    reporting_period = Choice(title=u"Reporting period",
                              required=False,
                              vocabulary="wise_search_reporting_period_art19")


class IRegionSubregionsArt19(Interface):
    region_subregions = List(
        title=u"Region and Subregion",
        value_type=Choice(vocabulary="wise_search_region_subregions_art19"),
        required=False,
    )


class ICountryArt19(Interface):
    member_states = List(
        title=u"Country",
        value_type=Choice(vocabulary="wise_search_member_states_art19"),
        required=False,
    )
