# pylint: skip-file
""" admin.py """
# coding=utf-8
from __future__ import absolute_import
from __future__ import print_function
import logging
import transaction

from zope.interface import alsoProvides

from plone import api
from plone.api import portal

from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from wise.msfd.translation import Translation
from wise.msfd.translation.interfaces import ITranslationsStorage


from plone.base.interfaces import IPloneSiteRoot
from plone.dexterity.interfaces import IDexterityContent


logger = logging.getLogger('wise.msfd')


class MigrateTranslationStorage(BrowserView):
    """MigrateTranslationStorage"""

    def __call__(self):
        site = portal.get()
        storage = ITranslationsStorage(site)
        count = 0

        for langstore in storage.values():
            for original, translated in langstore.items():
                count = +1

                if hasattr(translated, 'text'):
                    translated = translated.text
                translated = Translation(translated, 'original')

                if not translated.text.startswith('?'):
                    translated.approved = True

                langstore[original] = translated

        return "Migrated {} strings".format(count)


class MigrateEionetGroups(BrowserView):
    """Migrate local roles from extranet- groups to local- groups"""

    def migrate_local_roles(self, obj, principal_counts, portal_groups,
                            seen_groups, dry_run=True):
        changed = False
        local_roles = obj.get_local_roles()

        for principal, roles in local_roles:
            if principal.startswith("extranet-"):
                principal_counts[principal] = principal_counts.get(
                    principal, 0) + 1

                new_principal = principal.replace("extranet-", "local-")
                existing_roles = dict(local_roles).get(new_principal, [])
                if set(roles).issubset(set(existing_roles)):
                    continue

                final_roles = list(set(roles) | set(existing_roles))
                logger.info(
                    "Migrating %s -> %s on %s",
                    principal, new_principal, obj.absolute_url(1)
                )

                if not dry_run:
                    if new_principal not in seen_groups:
                        if not portal_groups.getGroupById(new_principal):
                            portal_groups.addGroup(new_principal)
                        seen_groups.add(new_principal)
                    obj.manage_setLocalRoles(new_principal, final_roles)
                    changed = True

        return changed

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        dry_run = not self.request.get("run")
        portal = api.portal.get()
        portal_groups = getToolByName(portal, "portal_groups")

        stack = [(portal, "")]
        seen_paths = set()
        total_objects = 0
        principal_counts = {}
        seen_groups = set()

        while stack:
            obj, current_rel_path = stack.pop()
            try:
                path = obj.absolute_url(1)
            except Exception:
                path = current_rel_path

            if path in seen_paths:
                continue
            seen_paths.add(path)
            total_objects += 1

            try:
                self.migrate_local_roles(
                    obj, principal_counts, portal_groups,
                    seen_groups, dry_run=dry_run
                )
            except Exception as e:
                logger.error("Error processing %s: %s", path, e)

            if not dry_run and total_objects % 1000 == 0:
                transaction.commit()
                logger.info("Committed batch at %d objects", total_objects)

            if hasattr(obj, "objectValues"):
                try:
                    children = obj.objectValues()
                except Exception as e:
                    logger.error("Error getting children for %s: %s", path, e)
                    continue

                for child in children:
                    try:
                        child_id = child.getId()
                    except Exception:
                        continue

                    if not (
                        IDexterityContent.providedBy(child)
                        or IPloneSiteRoot.providedBy(child)
                    ):
                        continue

                    child_rel_path = (
                        "{}/{}".format(current_rel_path, child_id)
                        if current_rel_path else child_id
                    )
                    stack.append((child, child_rel_path))

        if not dry_run:
            transaction.commit()

        lines = ["Migration finished.",
                 "Total objects processed: {}".format(total_objects), ""]

        for name in sorted(principal_counts):
            lines.append("{}: {} objects".format(name, principal_counts[name]))

        lines.append("")
        lines.append(
            "Dry run - no changes committed." if dry_run else "Changes committed."
        )

        return "\n".join(lines)
