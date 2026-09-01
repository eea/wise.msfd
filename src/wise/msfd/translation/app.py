#pylint: skip-file
from __future__ import absolute_import
from zope.annotation.factory import factory
from zope.component import adapter
from zope.interface import implementer

from BTrees.OOBTree import OOBTree
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

from . import ANNOTATION_KEY, REQUESTS_ANNOTATION_KEY
from .interfaces import (ITranslationsStorage,
                         ITranslationRequestsStorage)


@implementer(ITranslationsStorage)
@adapter(IPloneSiteRoot)
class TranslationsStorage(OOBTree):
    pass


annotfactory = factory(TranslationsStorage, key=ANNOTATION_KEY)


@implementer(ITranslationRequestsStorage)
@adapter(IPloneSiteRoot)
class TranslationRequestsStorage(OOBTree):
    pass


requestsannotfactory = factory(
    TranslationRequestsStorage,
    key=REQUESTS_ANNOTATION_KEY,
)
