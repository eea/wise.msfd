import json
import logging
from collections import deque

from eea.cache import cache
from plone.api.content import transition
from plone.dexterity.utils import createContentInContainer as create
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .base import BaseComplianceView

logger = logging.getLogger('wise.msfd')


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


class CommentsList(BrowserView):
    """ Renders a list of comments, to be loaded with Ajax in assessment edit
    """
    template = ViewPageTemplateFile('pt/comments-list.pt')

    def add_comment(self):
        form = self.request.form
        question_id = form.get('q').lower()
        text = form.get('text')

        tl_folder = self.context['tl']

        if question_id in tl_folder.contentIds():
            q_folder = tl_folder[question_id]
        else:       # initially create the question folder for comments
            q_folder = create(tl_folder,
                              'wise.msfd.commentsfolder',
                              id=question_id,
                              title='Comments for question ' + question_id)
            transition(obj=q_folder, transition='open_for_tl')

        comment = create(q_folder, 'wise.msfd.comment', text=text)
        logger.info('Added comment %r in %r:, %r', q_folder, comment, text)

        return self.template()

    def __call__(self):
        return self.template()

    def comments(self):
        tl_folder = self.context['tl']
        question_id = self.request.form.get('q', 'missing-id').lower()

        if question_id not in tl_folder.contentIds():
            return []

        q_folder = tl_folder[question_id]

        return q_folder.contentValues()
