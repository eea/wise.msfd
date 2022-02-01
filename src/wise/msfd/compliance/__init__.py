#
from __future__ import absolute_import
import logging

from zope.interface import alsoProvides

from wise.msfd.compliance.interfaces import (IComplianceModuleFolder,
                                             IComplianceModuleMarker)

logger = logging.getLogger(__name__)


def handle_traverse(event):
    req = event.request
    parents = req.other['PARENTS']

    for obj in parents:

        if IComplianceModuleFolder.providedBy(obj):
            logger.info("Add IComplianceModuleMarker to request")
            alsoProvides(req, IComplianceModuleMarker)

            break
