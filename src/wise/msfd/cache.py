# pylint: skip-file
"""cache.py"""
from __future__ import absolute_import
from __future__ import print_function
from plone.restapi.cache import paths
from plone.cachepurging.purger import logger as purgeLogger
from plone.memoize import volatile
from plone.memoize import ram
from plone.uuid.interfaces import IUUID
import hashlib
import logging
import threading
import time
from functools import wraps

import six
from BTrees.OOBTree import OOBTree
from zope.annotation.interfaces import IAnnotations
from zope.component import queryAdapter
from zope.tales.expressions import StringExpr

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PageTemplates.Expressions import createTrustedZopeEngine

logger = logging.getLogger(__name__)
purgeLogger.setLevel(logging.DEBUG)


# ``eea.cache`` (now archived) combined plone.memoize with a memcached
# backend and added dependency invalidation plus per-entry lifetimes.  We
# keep those behaviours here on top of Plone's maintained memoize API
# (``plone.memoize.ram``, or whatever cache chooser the application
# configures).
#
# Cross-worker invalidation
# -------------------------
# Plone's RAM cache is per-process, so a shared invalidation signal is
# needed for multi-worker deployments:
#
# * ``invalidate_dependencies()`` bumps a version counter stored in a
#   persistent annotation on the Plone site.  All ZEO clients share the
#   ZODB, so every worker observes the bump and recomputes its entries.
#   If no portal is reachable (tests, scripts) a process-local counter is
#   used instead.
#
# * ``auto_invalidate`` folds the context object's UID and ZODB
#   modification time (``_p_mtime``) into the cache key.  ``_p_mtime`` is
#   stored in the ZODB, so it is identical on every worker: entries are
#   recomputed on all workers as soon as the modifying transaction
#   commits, without any events or extra writes.
#
# Cache keys
# ----------
# The final key is a SHA-256 digest of a canonical tuple of typed
# components.  Even when a key function embeds request-controlled strings
# (report filenames, marine unit ids, ...) they are hashed away: they
# cannot bloat the key, target another entry, or collide with a different
# key shape.

DEPENDENCY_VERSIONS_ANNOT_KEY = 'wise.msfd.cache.dependency_versions'

_local = threading.local()
_dependency_lock = threading.RLock()
_cache_marker = object()


def _versions_store(create=False):
    """Return the shared dependency version store.

    A persistent OOBTree stored in the portal annotations, so every ZEO
    client sees the same versions.  Returns None when no portal is
    reachable.  Not cached between calls: a store created by another
    worker (or a fresh test connection) is picked up on the next lookup.
    """
    try:
        from plone.api.portal import get as get_portal
        portal = get_portal()
        annot = IAnnotations(portal, {})
        store = annot.get(DEPENDENCY_VERSIONS_ANNOT_KEY)
        if store is None and create:
            store = OOBTree()
            annot[DEPENDENCY_VERSIONS_ANNOT_KEY] = store
        return store
    except Exception:
        return None


def _local_versions():
    """Process-local fallback store (per thread)."""
    store = getattr(_local, 'local_versions', None)
    if store is None:
        store = _local.local_versions = {}
    return store


def invalidate_dependencies(dependencies):
    """Invalidate memoized values associated with *dependencies*.

    Bumps a version counter in the shared (ZODB-persistent) store, so all
    workers sharing the ZODB recompute their entries on the next lookup.
    Falls back to a process-local counter when no portal is reachable.
    """
    deps = dependencies or ()
    if not deps:
        return

    with _dependency_lock:
        local = _local_versions()
        for dependency in deps:
            local[dependency] = local.get(dependency, 0) + 1

        store = _versions_store(create=True)
        if store is not None:
            for dependency in deps:
                store[dependency] = store.get(dependency, 0) + 1


def _dependency_version(dependency):
    """Current version of *dependency* (shared store, local as fallback)."""
    store = _versions_store(create=False)
    if store is not None:
        return store.get(dependency, 0)
    return _local_versions().get(dependency, 0)


def _context_for(args):
    if not args:
        return None
    return getattr(args[0], 'context', args[0])


def _object_stamp(args):
    """Return a (uid, mtime) stamp for the cached method's context object.

    Both values live in the ZODB and are identical on every worker, so
    entries are recomputed everywhere once the object is modified and
    committed.  Returns None when the first argument is not a Plone
    content object (module-level helpers, plain values, ...).
    """
    context = _context_for(args)
    if context is None:
        return None

    try:
        uid = queryAdapter(context, IUUID)
    except Exception:
        uid = None

    if uid is None:
        return None

    try:
        mtime = context._p_mtime
    except Exception:
        mtime = None

    return (uid, mtime)


def _final_key(base_key, dependency_key, lifetime_key, object_stamp):
    """Canonical, bounded cache key.

    The tuple ``repr`` is unambiguous for the component types used here
    (strings, ints, floats, None, tuples); the SHA-256 digest then makes
    the stored key fixed-size and opaque, so user-controlled strings inside
    ``base_key`` cannot be used to grow keys or target other entries.
    """
    parts = (base_key, dependency_key, lifetime_key, object_stamp)
    data = repr(parts)

    if isinstance(data, six.text_type):
        data = data.encode('utf-8')

    return hashlib.sha256(data).hexdigest()


def cache(get_key, dependencies=None, lifetime=None, auto_invalidate=True,
          cache_empty=False):
    """Memoize a function using Plone's standard RAM cache.

    This is a small compatibility layer for the old ``eea.cache`` call
    shape, without the unmaintained dependency:

    * ``dependencies`` are invalidated through :func:`invalidate_dependencies`
      (shared across ZEO workers via a persistent version store);
    * ``lifetime`` adds a time bucket to the key (approximate TTL);
    * ``auto_invalidate`` folds the context's UID and ``_p_mtime`` into the
      key, so object edits refresh the entry on every worker at commit;
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

            dependency_key = tuple(
                (dependency, _dependency_version(dependency))
                for dependency in dependencies
            )

            lifetime_key = None
            if lifetime:
                lifetime_key = int(time.time() // lifetime)

            object_stamp = None
            if auto_invalidate:
                object_stamp = _object_stamp(args)

            key = _final_key(base_key, dependency_key, lifetime_key,
                             object_stamp)

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
