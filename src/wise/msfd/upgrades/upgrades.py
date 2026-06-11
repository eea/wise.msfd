"""upgrades"""
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

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
    'nis_year',
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


def add_banner_settings(context):
    """add_banner_settings"""

    registry = getUtility(IRegistry)
    prefix = 'wise.msfd.wisetheme.interfaces.IBannerSettings'
    for key in list(registry.records.keys()):
        if key.startswith(prefix + '.'):
            del registry.records[key]
    context.runImportStepFromProfile(
        'profile-wise.msfd:to_5', 'plone.app.registry', run_dependencies=False
    )
    context.runImportStepFromProfile(
        'profile-wise.msfd:to_5', 'controlpanel', run_dependencies=False
    )


def change_country_to_fieldindex(context):
    """Change nis_country from KeywordIndex to FieldIndex and reindex."""
    catalog = getToolByName(context, 'portal_catalog')

    if 'nis_country' in catalog.indexes():
        catalog.delIndex('nis_country')

    catalog.addIndex('nis_country', 'FieldIndex')

    if 'nis_country' not in catalog.schema():
        catalog.addColumn('nis_country')

    brains = catalog.unrestrictedSearchResults(
        portal_type='non_indigenous_species'
    )
    for brain in brains:
        obj = brain.getObject()
        obj.reindexObject(idxs=['nis_country'])



def add_nis_year_metadata(context):
    """Add nis_year to catalog index and metadata."""
    catalog = getToolByName(context, 'portal_catalog')

    if 'nis_year' not in catalog.indexes():
        catalog.addIndex('nis_year', 'FieldIndex')

    if 'nis_year' not in catalog.schema():
        catalog.addColumn('nis_year')
