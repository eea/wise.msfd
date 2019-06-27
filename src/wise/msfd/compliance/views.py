import json
import logging
from collections import deque

from eea.cache import cache
from plone import api
from plone.api.content import transition, get_state
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


class CommentsList(BaseComplianceView):
    """ Renders a list of comments, to be loaded with Ajax in assessment edit
    """
    template = ViewPageTemplateFile('pt/comments-list.pt')

    @property
    def current_user(self):
        user = api.user.get_current()

        return user.id

    def add_comment(self):
        form = self.request.form
        question_id = form.get('q').lower()
        thread_id = form.get('thread_id')
        transition_id = 'open_for_{}'.format(thread_id)

        text = form.get('text')

        folder = self.context[thread_id]

        if question_id in folder.contentIds():
            q_folder = folder[question_id]

            # Due to a bug, For 'EC' the wrong state was given (opened_for_tl)
            # transition to the correct state if necessary
            current_state = get_state(q_folder)
            correct_state = 'opened_for_{}'.format(thread_id)

            if current_state != 'closed' and current_state != correct_state:
                transition(obj=q_folder, transition='close')
                transition(obj=q_folder, transition=transition_id)

        else:       # initially create the question folder for comments
            q_folder = create(folder,
                              'wise.msfd.commentsfolder',
                              id=question_id,
                              title='Comments for question ' + question_id)
            transition(obj=q_folder, transition=transition_id)

        comment = create(q_folder, 'wise.msfd.comment', text=text)
        logger.info('Added comment %r in %r:, %r', q_folder, comment, text)

        return self.template()

    def del_comment(self):
        to_local_time = self.context.Plone.toLocalizedTime

        form = self.request.form

        question_id = form.get('q').lower()
        thread_id = form.get('thread_id')
        text = form.get('text')
        comm_time = form.get('comm_time')
        comm_name = form.get('comm_name')

        folder = self.context[thread_id]
        q_folder = folder[question_id]
        comments = q_folder.contentValues()

        for comment in comments:
            if comment.text != text or comment.Creator() != comm_name:
                continue
            if to_local_time(comment.created(), long_format=True) != comm_time:
                continue

            del q_folder[comment.id]

        return self.template()

    def __call__(self):
        return self.template()

    def comments(self):
        thread_id = self.request.form.get('thread_id')
        folder = self.context[thread_id]
        question_id = self.request.form.get('q', 'missing-id').lower()

        if question_id not in folder.contentIds():
            return []

        q_folder = folder[question_id]

        return q_folder.contentValues()
