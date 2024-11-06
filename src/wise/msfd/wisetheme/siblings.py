# pylint: skip-file
from plone import api
from plone.restapi.interfaces import IExpandableElement, ISerializeToJson
from plone.restapi.services import Service
from zope.component import adapter, getMultiAdapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class Siblings(object):
    """siblings object"""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {
            "siblings": {
                "@id": "{}/@siblings".format(self.context.absolute_url())}
        }

        if ("fullobjects" not in self.request.form) and not expand:
            return result

        portal = api.portal.get()

        if self.context is portal:
            return result

        if "expand" in self.request.form:
            del self.request.form["expand"]
        self.request.form["include_items"] = True
        self.request.form["b_size"] = 1000

        parent = self.context.aq_parent  # .aq_parent.aq_inner

        serializer = getMultiAdapter((parent, self.request), ISerializeToJson)
        serialized = serializer()
        result["siblings"]["items"] = serialized["items"]

        return result


class SiblingsGet(Service):
    """siblings - get"""

    def reply(self):
        """reply"""
        siblings = Siblings(self.context, self.request)

        return siblings(expand=True)["siblings"]
