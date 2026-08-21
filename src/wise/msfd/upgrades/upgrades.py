"""upgrades"""
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryAdapter


# These packages were removed from the Python environment without being
# uninstalled.  Their GenericSetup profile-version markers make Plone show
# them as missing on @@plone-upgrade, but do not represent usable add-ons.
LEGACY_MISSING_PACKAGES = {
    'collective.z3cform.datagridfield',
    'eea.privacyscreen',
    'webcouturier.dropdownmenu',
    'wise.theme'
}


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


def migrate_nis_country_to_choice(context):
    """Migrate nis_country from List to Choice (single value)."""
    catalog = getToolByName(context, 'portal_catalog')

    brains = catalog.unrestrictedSearchResults(
        portal_type='non_indigenous_species'
    )
    for brain in brains:
        obj = brain.getObject()
        value = getattr(obj, 'nis_country', None)
        if isinstance(value, (list, tuple)):
            obj.nis_country = value[0] if value else None
            obj.reindexObject(idxs=['nis_country'])


def remove_legacy_missing_package_markers(context):
    """Remove profile-version markers for add-ons no longer installed.

    This deliberately removes GenericSetup bookkeeping only.  It does not
    attempt to emulate the packages' uninstall profiles or remove data they
    may have left in the site.  The private mapping is used for enumeration
    because GenericSetup exposes no public iterator for these markers; each
    deletion goes through its public API.
    """
    setup = getToolByName(context, 'portal_setup')
    profile_versions = getattr(setup, '_profile_upgrade_versions', {})
    profile_ids = list(profile_versions.keys())
    matches = [
        profile_id for profile_id in profile_ids
        if profile_id.split(':', 1)[0] in LEGACY_MISSING_PACKAGES
    ]

    for profile_id in matches:
        setup.unsetLastVersionForProfile(profile_id)


def restrict_nis_task_page_types(context):
    """Restrict addable types on /sandbox/non-indigenous-species-task-286283
    to non_indigenous_species only.

    Dexterity containers don't expose the Archetypes setLocallyAllowedTypes
    method directly; use the ISelectableConstrainTypes adapter instead. If the
    container's FTI has no constrain-types behavior, the adapter is absent and
    we skip gracefully (restriction can then be set via the Plone UI).
    """
    obj = api.content.get(path='/sandbox/non-indigenous-species-task-286283')
    if obj is None:
        return
    constrain = queryAdapter(obj, ISelectableConstrainTypes)
    if constrain is None:
        return
    constrain.setConstrainTypesMode(1)
    constrain.setLocallyAllowedTypes(['non_indigenous_species'])
    constrain.setImmediatelyAddableTypes(['non_indigenous_species'])
    obj.reindexObject()
