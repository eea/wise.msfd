from plone.api import portal
from plone.dexterity.browser.add import DefaultAddForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .base import BaseComplianceView


class AddForm(DefaultAddForm):
    """ Add form with a custom action
    """

    @property
    def action(self):
        return self.context.absolute_url() + '/++add++wise.msfd.comment'


class CommentsView(object):

    def add_form(self, context):
        print context
        types = portal.get_tool('portal_types')
        fti = types['wise.msfd.comment']

        form = AddForm(context, self.request, fti)

        form_template = ViewPageTemplateFile('pt/comment-add-form.pt')

        form.template = form_template.__get__(form)

        form.status = ''

        form.nextURL = ''

        return form


class CommentView(BaseComplianceView):
    def __call__(self):
        url = self._article_assessment.absolute_url()

        return self.request.response.redirect(url)
