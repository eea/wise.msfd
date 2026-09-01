#pylint: skip-file
from __future__ import absolute_import
from zope.interface import Attribute, Interface


class ITranslationsStorage(Interface):
    """ Provide storage (as a mapping) for translations

    Keys will be the language codes
    """


class ITranslationRequestsStorage(Interface):
    """Provide persistent external-reference to text mappings."""


class ITranslationContext(Interface):
    """
    """

    language = Attribute(u"Language code")
