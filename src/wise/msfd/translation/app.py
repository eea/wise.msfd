from zope.annotation.factory import factory
from zope.component import adapter
from zope.interface import implementer

from BTrees.OOBTree import OOBTree
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

from . import ANNOTATION_KEY
from .interfaces import ITranslationsStorage


@implementer(ITranslationsStorage)
@adapter(IPloneSiteRoot)
class TranslationsStorage(OOBTree):
    pass


annotfactory = factory(TranslationsStorage, key=ANNOTATION_KEY)
