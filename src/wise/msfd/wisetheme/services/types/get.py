"""
TypesGet
"""
from plone.restapi.services.types.get import (
    check_security,
    TypesGet as BaseTypesGet
)
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

plone_site_schema = {
    "type": "object",
    "title": "Plone Site",
    "properties": {
        "title": {
            "type": "string",
            "title": "Title",
            "description": "",
            "factory": "Text line (String)",
            "behavior": "plone.dublincore"
        },
        "description": {
            "type": "string",
            "title": "Summary",
            "description": "Used in item listings and search results.",
            "widget": "textarea",
            "factory": "Text",
            "behavior": "plone.dublincore"
        },
    },
    "required": [
        "title"
    ],
    "fieldsets": [
        {
            "id": "default",
            "title": "Default",
            "fields": [
                "title",
                "description"
            ],
            "behavior": "plone"
        },
    ],
    "layouts": []
}


@implementer(IPublishTraverse)
class TypesGet(BaseTypesGet):
    """
    A custom implementation of the TypesGet service for freshwater content.
    """

    def __init__(self, context, request):
        super(TypesGet, self).__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        """
        Handles traversal of the object hierarchy.
        """
        # Treat any path segments after /@types as parameters
        self.params.append(name)
        return self

    def reply(self):
        """
        This method handles the reply logic for the 'get' service type.
        """
        if len(self.params) == 1 and self.params[0] == 'Plone Site':
            return self.reply_for_plone_site()
        return super(TypesGet, self).reply()

    def reply_for_plone_site(self):
        """
        Returns the JSON schema for the Plone site.
        """
        check_security(self.context)
        self.content_type = "application/json+schema"
        return plone_site_schema
