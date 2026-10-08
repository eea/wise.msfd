# pylint: skip-file
"""Portable SQL aggregates used by the explorer providers.

The explorer runs against SQL Server in the live application (``mssql`` via
pymssql) and against SQLite in the test harness. A provider that packs a child
table into a single cell (the Article 9/2018 features and marine reporting
units) therefore needs one aggregate that both dialects understand.
"""
from __future__ import absolute_import

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import GenericFunction


class group_concat(GenericFunction):
    """Concatenate a column's values with a separator, per group.

    Compiles to SQLite's two argument ``group_concat(value, separator)`` and to
    SQL Server's ``string_agg(value, separator)``, so the same expression can be
    built once and executed on either database.
    """

    name = 'group_concat'
    inherit_cache = True


@compiles(group_concat, 'mssql')
def _group_concat_mssql(element, compiler, **kw):
    """SQL Server spells this aggregate ``string_agg``."""
    return 'string_agg({0})'.format(
        compiler.process(element.clauses, **kw)
    )
