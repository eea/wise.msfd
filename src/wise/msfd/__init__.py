# from .patch import install
# install()

""" Main product initializer
"""

from Acquisition import aq_parent
from plone.restapi.deserializer import utils
from plone.uuid.interfaces import IUUID, IUUIDAware
from zope.component import getMultiAdapter
from zope.i18nmessageid.message import MessageFactory


EEAMessageFactory = MessageFactory('eea')


def initialize(context):
    """Initializer called when used as a Zope 2 product.
    """


def path2uid(context, link):
    """ Remove /marine/ from the path if it is present

        unrestrictedTraverse requires a string on py3. see:
        https://github.com/zopefoundation/Zope/issues/674
    """
    if not link:
        return ""

    if link.startswith('/marine/'):
        link = link.replace('/marine/', '/')

    portal = getMultiAdapter(
        (context, context.REQUEST), name="plone_portal_state"
    ).portal()
    portal_url = portal.portal_url()
    portal_path = "/".join(portal.getPhysicalPath())
    path = link
    context_url = context.absolute_url()
    relative_up = len(context_url.split("/")) - len(portal_url.split("/"))
    if path.startswith(portal_url):
        path = path[len(portal_url) + 1:]
    if not path.startswith(portal_path):
        path = "{portal_path}/{path}".format(
            portal_path=portal_path, path=path.lstrip("/")
        )

    # handle edge-case when we have non traversable path like /@@download/file
    if "/@@" in path:
        path, suffix = path.split("/@@", 1)
        suffix = "/@@" + suffix
    else:
        suffix = ""
    obj = portal.unrestrictedTraverse(path, None)

    if obj is None or obj == portal:
        return link

    segments = path.split("/")
    while not IUUIDAware.providedBy(obj):
        obj = aq_parent(obj)
        if obj is None:
            break
        suffix = "/" + segments.pop() + suffix
    # check if obj is wrong because of acquisition
    if not obj or "/".join(obj.getPhysicalPath()) != "/".join(segments):
        return link
    href = relative_up * "../" + "resolveuid/" + IUUID(obj)
    if suffix:
        href += suffix
    return href


utils.path2uid = path2uid
