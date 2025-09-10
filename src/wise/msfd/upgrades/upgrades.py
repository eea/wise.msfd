"""upgrades"""
from Products.CMFCore.utils import getToolByName


indexes = [
    'nis_species_name_original',
    'nis_species_name_accepted',
    'nis_scientificname_accepted',
    'nis_subregion',
    'nis_region',
    'nis_country',
    'nis_status',
    'nis_group',
    'nis_assigned_to',
]


def add_nis_metadata(context):
    """Add NIS metadata and indexes"""

    catalog = getToolByName(context, 'portal_catalog')

    for index_name in indexes:
        # Add index if it doesn't exist
        if index_name not in catalog.indexes():
            if index_name in ('nis_country',):
                catalog.addIndex(index_name, 'KeywordIndex')
            else:
                catalog.addIndex(index_name, 'FieldIndex')

        # Add metadata column if it doesn't exist
        if index_name not in catalog.schema():
            catalog.addColumn(index_name)
