import json
from collections import deque

from eea.cache import cache
from Products.Five.browser import BrowserView

from .base import BaseComplianceView


class ComplianceJSONMap(BrowserView):
    """ Build a json tree of the context
    """

    @cache(lambda *a, **kw: 'comp-json-map')
    def __call__(self):
        print "Calling"
        # node = {'name': ..., 'url': '...', 'children': []}
        initial = []

        for c in self.context.contentValues():
            initial.append((None, c))

        stack = deque(initial)
        res = []

        blacklist = ['tl', 'ec']

        while stack:
            parent, branch = stack.pop()

            node = {'u': branch.absolute_url(),
                    'i': branch.id,
                    'c': [],
                    't': branch.title_or_id()}

            if parent is None:
                res.append(node)
            else:
                parent['c'].append(node)

            if hasattr(branch.aq_self, 'contentValues'):
                for child in branch.contentValues():
                    if child.id not in blacklist:
                        stack.append((node, child))

        return json.dumps(res)


class ComplianceNavMacros(BaseComplianceView):
    """ Just a dummy class to enable testing
    """
