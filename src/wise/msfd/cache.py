# pylint: skip-file
"""cache.py"""
from __future__ import absolute_import
from __future__ import print_function
import logging

from zope.tales.expressions import StringExpr

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PageTemplates.Expressions import createTrustedZopeEngine

logger = logging.getLogger(__name__)

_cache = {}


class CacheExpr(StringExpr):
    """CacheExpr"""
    def __call__(self, econtext):
        vvals = []

        for var in self._vars:
            v = var(econtext)
            vvals.append(v)

        # return self._expr % tuple(vvals)
        print(self._expr, vvals)

        return None

    def __str__(self):
        return 'cache expression (%s)' % repr(self._s)

    def __repr__(self):
        return '<CacheExpr %s>' % repr(self._s)


_engine = createTrustedZopeEngine()
_engine.registerType('cache', CacheExpr)


def getEngine():
    """getEngine"""
    return _engine


class CacheViewPageTemplateFile(ViewPageTemplateFile):
    """CacheViewPageTemplateFile"""
    def pt_getEngine(self):
        return getEngine()
