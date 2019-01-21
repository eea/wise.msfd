from zope.interface import Attribute, Interface


class ITranslationContext(Interface):
    """
    """

    language = Attribute(u"Language code")
