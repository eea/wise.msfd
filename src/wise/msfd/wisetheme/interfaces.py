# -*- coding: utf-8 -*-

""" Module where all interfaces, events and exceptions live."""

from __future__ import absolute_import
from plone.app.dexterity import _
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobImage
from plone.schema import JSONField
from plone.supermodel import model
from zope.interface import Interface, provider
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import Choice, Int, Text, TextLine, Tuple

import sys
import types

wisetheme_interfaces = types.ModuleType("wise.theme.interfaces")

class IWiseThemeLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

wisetheme_interfaces.IWiseThemeLayer = IWiseThemeLayer

class IHomepage(Interface):
    """Marker interface for the context object that is the homepage"""

wisetheme_interfaces.IHomepage = IHomepage

sys.modules["wise.theme.interfaces"] = wisetheme_interfaces

class ICountriesFactsheetDatabase(Interface):
    """Marker interface for the context object that is the homepage"""


class IFullWidthLayout(Interface):
    """Marker interface"""


@provider(IFormFieldProvider)
class IExternalLinks(model.Schema):
    """External links interface with RichText schema"""

    external_links = RichText(
        title=u"External Links", description=u"", required=False)


@provider(IFormFieldProvider)
class IReferenceLinks(model.Schema):
    """Reference links interface with RichText schema"""

    reference_links = RichText(
        title=u"Reference Links", description=u"", required=False
    )


@provider(IFormFieldProvider)
class IDisclaimer(model.Schema):
    """Disclaimer interface with RichText schema"""

    disclaimer = RichText(title=u"Disclaimer", description=u"", required=False)


@provider(IFormFieldProvider)
class ICatalogueMetadata(model.Schema):
    """Wise catalogue metadata

    Title   text    y
    Short description   Text    y
    Organisation name   from a list y
    Organization acronym    from the list   y
    Organization Logo   image (to be provided by Silvia)    y
    Organisation webpage    From the list   y
    Thumbnail   image   n   usefull for cards setting
    Type (DPSR) from the list   n
    Theme   from the list   n
    Subtheme    from the list   n
    keywords    text    n
    Date of Publication date (at least year)    y
    Last modified in WISE Marine    automatic from plone
    Link        y   the link can be internal or external links
        (more external, including EEA website and SDI catalogue
    """

    title = TextLine(title=_(u"label_title", default=u"Title"), required=True)

    description = Text(
        title=_(u"label_description", default=u"Description"),
        description=_(
            u"help_description",
            default=u"Used in item listings and search results."
        ),
        required=True,
    )

    lineage = Text(
        title=u"Lineage",
        required=False,
    )
    original_source = TextLine(
        title=u"Original source",
        description=u"If EEA link, can trigger automatic" +
        "fetching of EEA information",
        required=False,
    )

    legislative_reference = Tuple(
        title="Legislative reference",
        required=False,
        value_type=Choice(
            title=u"Single legislative reference",
            vocabulary="wise_legislative_vocabulary",
        ))

    embed_url = TextLine(
        title=u"Tableau URL",
        required=False,
    )

    webmap_url = TextLine(
        title=u"Embed URL",
        description=u"Webmap URL",
        required=False,
    )

    organisation = Choice(
        title=u"Organisation",
        required=True,
        vocabulary="wise_organisations_vocabulary",
        default="EEA",
    )

    dpsir_type = Choice(
        title=u"DPSIR", required=False, vocabulary="wise_dpsir_vocabulary"
    )

    directives.widget(
        "theme",
        vocabulary="wise_theme_vocabulary",
        frontendOptions={"widget": "wise_theme"},
    )

    theme = Tuple(
        title=u"Sub-Theme",
        required=False,
        default=(),
        value_type=TextLine(
            title=u"Single Theme",
        ))

    # subtheme = Choice(
    #    title=u"Subtheme", required=False,
    #    vocabulary="wise_subthemes_vocabulary"
    # )

    # Removed as we use only the "Publishing date"
    # publication_year = Int(title=u"Publication year", required=True)

    # license_copyright = TextLine(
    #    title=_(u"label_title", default=u"Rights"), required=False
    # )

    # temporal_coverage = JSONField(
    #    title=u"Temporal coverage",
    #    required=False, widget="temporal", default={}
    # )

    # geo_coverage = JSONField(
    #    title=u"Geographical coverage",
    #    required=False, widget="geolocation", default={}
    # )

    data_source_info = RichText(
        title=u"Data source information",
        description=u"Rich text, double click for toolbar.",
        required=False,
    )

    external_links = RichText(
        title=u"External links",
        description=u"Rich text, double click for toolbar.",
        required=False,
    )

    thumbnail = NamedBlobImage(
        title=u"Preview image (thumbnail)",
        required=False,
    )

    sources = RichText(title=u"Sources", description=u"", required=False)
