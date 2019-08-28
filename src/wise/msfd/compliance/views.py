import json
import logging
import time
from collections import deque

from eea.cache import cache
from plone import api
from plone.api.content import get_state, transition
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

        folder = self.context

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

    def _del_comments_from_q_folder(self, form, q_folder, comments):
        to_local_time = self.context.Plone.toLocalizedTime
        text = form.get('text')
        comm_time = form.get('comm_time')
        comm_name = form.get('comm_name')

        for comment in comments:
            if comment.text != text or comment.Creator() != comm_name:
                continue

            if to_local_time(comment.created(), long_format=True) != comm_time:
                continue

            del q_folder[comment.id]

    def del_comment(self):
        form = self.request.form

        question_id = form.get('q').lower()

        # old comments
        for thread_id in ('ec', 'tl'):
            folder = self.context.get(thread_id, {})
            q_folder = folder.get(question_id, {})
            if q_folder:
                old_comments = q_folder.contentValues()
                self._del_comments_from_q_folder(form, q_folder, old_comments)

        # new comments
        folder = self.context
        q_folder = folder[question_id]
        new_comments = q_folder.contentValues()
        self._del_comments_from_q_folder(form, q_folder, new_comments)

        return self.template()

    def __call__(self):
        return self.template()

    def comments(self):
        """ Return all comments

        Comments are no longer stored in ec/tl folders, instead on national
        descriptor assessment folder (../fi/bal/d5/art9)
        """

        folder = self.context
        question_id = self.request.form.get('q', 'missing-id').lower()
        old_comments = self.old_comments(question_id)

        if question_id not in folder.contentIds():
            return old_comments

        q_folder = folder[question_id]
        comments = q_folder.contentValues()
        all_comments = old_comments + comments

        sorted_all_comments = sorted(all_comments, key=lambda c: c.created())

        return sorted_all_comments

    def old_comments(self, question_id):
        """ Return comments from the old comment folders: ec and tl
        """

        thread_ids = ['ec', 'tl']
        all_comments = []

        for thread_id in thread_ids:
            folder = self.context.get(thread_id, None)

            if not folder:
                continue

            if question_id not in folder.contentIds():
                continue

            q_folder = folder[question_id]

            all_comments.extend(q_folder.contentValues())

        return all_comments


class TabsView(BaseComplianceView):
    """ A view to render the compliance navigation tabs
    """

    name = '/help'
