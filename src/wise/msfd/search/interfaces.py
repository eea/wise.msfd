from zope.interface import Attribute, Interface
from zope.schema import Choice, Int, List  # , Text  # , TextLine

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


class IArticleSelect(Interface):
    article = Choice(title=u"Article",
                     required=False,
                     default='',
                     vocabulary="wise_search_articles")


class IRecordSelect(Interface):
    """ We use a pagination based record selection
    """

    page = Int(title=u'Record page', required=False, default=0)


class IRegionSubregions(Interface):
    region_subregions = List(
        title=u"Region and Subregions",
        value_type=Choice(vocabulary="wise_search_region_subregions"),
        required=False,
    )


class IMemberStates(Interface):
    member_states = List(
        title=u"Countries",
        value_type=Choice(vocabulary="wise_search_member_states"),
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


class IStartArticles1314(Interface):
    report_type = Choice(
        title=u"Report Type",
        vocabulary="wise_search_a1314_report_types",
        required=False,
    )

    # region_subregions = List(
    #     title=u"Region and Subregions",
    #     value_type=Choice(vocabulary="wise_search_region_subregions"),
    #     required=False,
    # )

    region_subregions = List(
        title=u"Region and Subregions",
        value_type=Choice(vocabulary="wise_search_a1314_regions"),
        required=False,
    )


class IStartArticle11(Interface):
    monitoring_programme_types = List(
        title=u"Monitoring programme Type",
        value_type=Choice(
            vocabulary="wise_search_monitoring_programme_vb_factory"),
        required=False
    )

    monitoring_programme_info_type = Choice(
        title=u"Information Type",
        vocabulary="wise_search_monitoring_programme_info_types",
        required=False
    )


class IA1314MemberStates(Interface):
    member_states = List(
        title=u"Countries",
        value_type=Choice(vocabulary="wise_search_a1314_member_states"),
        required=False,
    )


class IA1314UniqueCodes(Interface):
    unique_codes = List(
        title=u"Unique Codes",
        # description=u"Select one or more Unique Codes that you're
        # interested",
        required=False,
        value_type=Choice(vocabulary="wise_search_a1314_unique_codes")
    )


# Articles 8, 9, 10
# 2018 reporting year
class IArticleSelect2018(Interface):
    article = Choice(title=u"Article",
                     required=False,
                     default='',
                     vocabulary="wise_search_articles_2018")


class ICountryCode(Interface):
    member_states = List(
        title=u"Country Code",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_country")
    )


class IGESComponentsA9(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_ges_component_art9")
    )


class IFeatures(Interface):
    feature = List(
        title=u"Features",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature")
    )


class IGESComponents(Interface):
    ges_component = List(
        title=u"GES Component",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_ges_component")
    )


class IFeaturesA9(Interface):
    feature = List(
        title=u"Features",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature_art9")
    )


class IFeatures81c(Interface):
    feature = List(
        title=u"Features",
        required=False,
        value_type=Choice(vocabulary="wise_search_a2018_feature_art81c")
    )


class IIndicatorsFeature(Interface):
    feature = List(
        title=u"Features",
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
