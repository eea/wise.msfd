# pylint: skip-file
"""cache.py"""
from __future__ import absolute_import
from __future__ import print_function
from plone.restapi.cache import paths
from plone.cachepurging.purger import logger as purgeLogger
from plone.memoize import volatile
from plone.memoize import ram
from plone.uuid.interfaces import IUUID
import logging
import threading
import time
from functools import wraps

from zope.component import queryAdapter
from zope.tales.expressions import StringExpr

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PageTemplates.Expressions import createTrustedZopeEngine

logger = logging.getLogger(__name__)
purgeLogger.setLevel(logging.DEBUG)


# ``eea.cache`` combined plone.memoize with a memcached backend and added
# dependency invalidation and per-entry lifetimes.  Keep those two small
# pieces of behaviour here while using Plone's maintained memoize API.  The
# cache itself is provided by ``plone.memoize.ram`` (or by the cache chooser
# configured by the application).
_dependency_versions = {}
_dependency_lock = threading.RLock()
_cache_marker = object()


def invalidate_dependencies(dependencies):
    """Invalidate memoized values associated with *dependencies*.

    Dependency invalidation is deliberately process-local, like Plone's RAM
    cache.  Applications using several Zope workers should also use a shared
    cache chooser or include a data/version date in their cache keys.
    """
    with _dependency_lock:
        for dependency in dependencies or ():
            _dependency_versions[dependency] = (
                _dependency_versions.get(dependency, 0) + 1
            )


def _dependency_version(dependency):
    with _dependency_lock:
        return _dependency_versions.get(dependency, 0)


def _context_for(args):
    if not args:
        return None
    return getattr(args[0], 'context', args[0])


def _object_uid(args):
    context = _context_for(args)
    if context is None:
        return None
    try:
        return queryAdapter(context, IUUID)
    except Exception:
        return None


def invalidate_object_cache(obj, event=None):
    """Invalidate cache entries tied to a modified Plone object."""
    uid = _object_uid((obj,))
    if uid:
        invalidate_dependencies((uid,))


def cache(get_key, dependencies=None, lifetime=None, auto_invalidate=True,
          cache_empty=False):
    """Memoize a function using Plone's standard RAM cache.

    This is a small compatibility layer for the old decorator call shape. It
    intentionally supports the options used by this package, without taking a
    dependency on the unmaintained ``eea.cache`` package:

    * ``dependencies`` are invalidated through :func:`invalidate_dependencies`;
    * ``lifetime`` creates a time bucket in the key; and
    * empty values are not cached unless ``cache_empty`` is true.

    ``plone.memoize.ram`` owns the actual storage and therefore retains its
    normal cache configuration and cache chooser behaviour.
    """
    dependencies = tuple(dependencies or ())

    def decorator(fun):
        @wraps(fun)
        def replacement(*args, **kwargs):
            try:
                base_key = get_key(fun, *args, **kwargs)
            except volatile.DontCache:
                return fun(*args, **kwargs)

            active_dependencies = list(dependencies)
            if auto_invalidate:
                uid = _object_uid(args)
                if uid and uid not in active_dependencies:
                    active_dependencies.append(uid)

            dependency_key = tuple(
                (dependency, _dependency_version(dependency))
                for dependency in active_dependencies
            )
            lifetime_key = None
            if lifetime:
                lifetime_key = int(time.time() // lifetime)

            key = repr((base_key, dependency_key, lifetime_key))
            cache_store = ram.store_in_cache(fun, *args, **kwargs)
            cached_value = cache_store.get(key, _cache_marker)
            if cached_value is _cache_marker:
                cached_value = fun(*args, **kwargs)
                if not cached_value and not cache_empty:
                    return cached_value
                cache_store[key] = cached_value

            return cached_value

        return replacement
    return decorator


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


def install_patches():
    paths.CONTEXT_ENDPOINTS = [
        "?expand=subsite,siblings",
        "/?expand=subsite,siblings",
    ]

    logger.info("plone.restapi cache purging paths were setup")
