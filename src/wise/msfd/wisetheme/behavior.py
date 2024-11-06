# pylint: skip-file
from __future__ import absolute_import
import requests

from plone.app.dexterity.behaviors.metadata import (DCFieldProperty,
                                                    MetadataBase)
from plone.namedfile.file import NamedBlobImage
from .interfaces import (ICatalogueMetadata, IDisclaimer, IExternalLinks,
                         IReferenceLinks)


class ExternalLinks(MetadataBase):
    """External Links Behavior"""

    external_links = DCFieldProperty(IExternalLinks["external_links"])


class ReferenceLinks(MetadataBase):
    """Reference Links Behavior"""

    reference_links = DCFieldProperty(IReferenceLinks["reference_links"])


class Disclaimer(MetadataBase):
    """Disclaimer Behavior"""

    disclaimer = DCFieldProperty(IDisclaimer["disclaimer"])


class CatalogueMetadata(MetadataBase):
    """Wise metadata"""

    title = DCFieldProperty(ICatalogueMetadata["title"])
    description = DCFieldProperty(ICatalogueMetadata["description"])
    lineage = DCFieldProperty(ICatalogueMetadata["lineage"])
    original_source = DCFieldProperty(ICatalogueMetadata["original_source"])
    embed_url = DCFieldProperty(ICatalogueMetadata["embed_url"])
    webmap_url = DCFieldProperty(ICatalogueMetadata["webmap_url"])
    organisation = DCFieldProperty(ICatalogueMetadata["organisation"])
    legislative_reference = DCFieldProperty(
        ICatalogueMetadata["legislative_reference"])
    dpsir_type = DCFieldProperty(ICatalogueMetadata["dpsir_type"])
    theme = DCFieldProperty(ICatalogueMetadata["theme"])
    external_links = DCFieldProperty(ICatalogueMetadata["external_links"])
    data_source_info = DCFieldProperty(ICatalogueMetadata["data_source_info"])
    thumbnail = DCFieldProperty(ICatalogueMetadata["thumbnail"])
    sources = DCFieldProperty(ICatalogueMetadata["sources"])

    # subtheme = DCFieldProperty(ICatalogueMetadata["subtheme"])
    # publication_year = DCFieldProperty(
    #     ICatalogueMetadata["publication_year"])
    # license_copyright = DCFieldProperty(
    #    ICatalogueMetadata["license_copyright"])
    # temporal_coverage = DCFieldProperty(
    #    ICatalogueMetadata["temporal_coverage"])
    # geo_coverage = DCFieldProperty(ICatalogueMetadata["geo_coverage"])


def set_thumbnail(context, event):
    """ Set the thumbnail image if it was not completed and the
        original_source is www.eea.europa.eu
    """

    if not context.original_source:
        return context

    if 'www.eea.europa.eu' not in context.original_source:
        return context

    if context.thumbnail:
        return context

    image_url = context.original_source + '/image_large'
    filename = u'image_large.png'
    response = requests.get(image_url)

    if not response.ok:
        return context

    context.thumbnail = NamedBlobImage(data=response.content,
                                       filename=filename)

    return context


def unset_effective_date(context, event):
    """ Unset the effective date (published date) when a page is unpublished
    """
    if not event.transition or \
       event.transition.id not in ['reject', 'retract']:
        return

    if not event.old_state:
        return

    if not event.new_state:
        return

    if event.old_state.id != 'published':
        return

    context.effective_date = None

    return context
