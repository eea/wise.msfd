# from Products.Five.bbb import AcquisitionBBB
import logging

from zope.tales.expressions import StringExpr

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PageTemplates.Expressions import createTrustedZopeEngine

logger = logging.getLogger(__name__)

_cache = {}


class CacheExpr(StringExpr):
    def __call__(self, econtext):
        import pdb
        pdb.set_trace()
        vvals = []

        for var in self._vars:
            v = var(econtext)
            vvals.append(v)

        # return self._expr % tuple(vvals)
        print self._expr, vvals

        return None

    def __str__(self):
        return 'cache expression (%s)' % repr(self._s)

    def __repr__(self):
        return '<CacheExpr %s>' % repr(self._s)


_engine = createTrustedZopeEngine()
_engine.registerType('cache', CacheExpr)


def getEngine():
    return _engine


class CacheViewPageTemplateFile(ViewPageTemplateFile):
    def pt_getEngine(self):
        return getEngine()


class CacheTestView(BrowserView):
    index = CacheViewPageTemplateFile('pt/test-cache.pt')

    def test_meth(self):
        logger.warning("Executed test method")

        return 'test output'

    def cache_key(self):
        return 'key'

    def show_cache_content(self):
        return _cache

    def __call__(self):
        return self.index()
