# pylint: skip-file
"""MSFD data explorer JSON API.

This package is intentionally separate from ``wise.msfd.search`` (the legacy
z3c.form based explorer). It exposes a single read-only ``plone.restapi``
service, ``@msfd-explorer``, which serves both the filter definitions (with
cross-facet counts) and the paged result data as plain JSON.

Nothing in ``wise.msfd.search`` is modified by this package; the legacy
explorer keeps working unchanged.
"""
