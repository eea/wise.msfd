# pylint: skip-file
"""``@msfd-explorer`` plone.restapi service.

Single read-only endpoint serving both the filter definitions and the result
data of the MSFD data explorer::

    GET /++api++/<site>/@msfd-explorer?article=4&cycle=2024&view=filters
    GET /++api++/<site>/@msfd-explorer?article=4&cycle=2024&view=data&page=0

Filter selections are passed as repeated (or comma separated) query params,
named after the facet they belong to, e.g.::

...&view=filters&region_subregions=ANS&region_subregions=BAL&member_states=DE

``view=data`` responses carry a ``pagination`` object with ``page``,
``pageSize``, ``pageCount``, ``total`` and ``truncated``. ``truncated`` is only
true for ``all=1`` bulk exports that hit the ``MAX_ALL_ROWS`` cap, and tells
the client that ``rows`` is a partial result set.
"""
from __future__ import absolute_import

import logging

from plone.restapi.services import Service

from wise.msfd.explorer.providers.base import ExplorerError
from wise.msfd.explorer.providers.registry import get_provider_class

logger = logging.getLogger('wise.msfd')

RESERVED_PARAMS = (
    'article', 'cycle', 'view', 'page', 'pageSize', 'sort', 'dir', 'all',
)

VIEWS = ('filters', 'data', 'summary')


class MsfdExplorerGet(Service):
    """MSFD data explorer GET service."""

    def _param(self, name, default=None):
        value = self.request.form.get(name, default)

        if isinstance(value, (list, tuple)):
            return value[-1] if value else default

        return value

    def _param_list(self, name):
        value = self.request.form.get(name)

        if value is None:
            return []

        if not isinstance(value, (list, tuple)):
            value = [value]

        out = []

        for item in value:
            for part in str(item).split(','):
                part = part.strip()

                if part:
                    out.append(part)

        return out

    def _selections(self):
        selections = {}

        for name in self.request.form.keys():
            if name in RESERVED_PARAMS:
                continue

            values = self._param_list(name)

            if values:
                selections[name] = values

        return selections

    def reply(self):
        article = self._param('article')
        cycle = self._param('cycle')
        view = (self._param('view') or 'filters').lower()
        page = self._param('page') or 0
        page_size = self._param('pageSize') or 25
        sort = self._param('sort')
        direction = self._param('dir') or 'asc'
        all_rows = self._param('all') in ('1', 'true', 'True', 'yes')

        if view not in VIEWS:
            view = 'filters'

        if not article or not cycle:
            self.request.response.setStatus(400)

            return {
                'error': 'Both "article" and "cycle" parameters are required.',
            }

        provider_class = get_provider_class(article, cycle)

        if provider_class is None:
            self.request.response.setStatus(404)

            return {
                'error': 'No explorer provider for article=%s cycle=%s.' % (
                    article, cycle
                ),
            }

        provider = provider_class(
            selections=self._selections(),
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
            all_rows=all_rows,
        )

        try:
            if view == 'summary':
                # The summary is an independent, lighter request: it does not
                # need the (six query) facet option lists, so skip building
                # them and only return the aggregates.
                filters = None
                data = {'summary': provider.build_summary()}
            else:
                filters = provider.build_filters()

                if view == 'data':
                    data = provider.build_data()
                else:
                    data = {
                        'columns': provider.build_columns(),
                        'rows': None,
                        'pagination': None,
                        'meta': None,
                    }
        except ExplorerError:
            logger.warning(
                'MSFD explorer: database unavailable for article=%s cycle=%s',
                article, cycle
            )
            self.request.response.setStatus(503)

            return {
                'error': 'The MSFD database is not available, '
                         'please try again later.',
            }

        payload = {
            'article': provider.article,
            'cycle': provider.cycle,
            'cycleLabel': provider.cycle_label,
            'recordTitle': provider.record_title,
            'view': view,
            'filters': filters,
        }
        payload.update(data)

        return payload
