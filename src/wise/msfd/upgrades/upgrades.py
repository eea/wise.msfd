"""upgrades"""
from Products.CMFCore.utils import getToolByName
from Products.ZCatalog.Catalog import CatalogError
from logging import getLogger


indexes = [
    'nis_species_name_accepted',
    'nis_scientificname_accepted',
    'nis_subregion',
    'nis_region',
    'nis_group'
]


def add_nis_metadata(context):
    """Add NIS metadata and indexes"""

    catalog = getToolByName(context, 'portal_catalog')

    for index_name in indexes:
        # Add index if it doesn't exist
        if index_name not in catalog.indexes():
            catalog.addIndex(index_name, 'FieldIndex')

        # Add metadata column if it doesn't exist
        if index_name not in catalog.schema():
            catalog.addColumn(index_name)
