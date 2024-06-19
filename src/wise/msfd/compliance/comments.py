#pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
from plone.api import portal
from plone.dexterity.browser.add import DefaultAddForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button

from .base import BaseComplianceView


class AddForm(DefaultAddForm):
    """ Add form with a custom action
    """

    @property
    def action(self):
        return self.context.absolute_url() + '/++add++wise.msfd.comment'

    @button.buttonAndHandler(u'Add comment', name='save')
    def handleAdd(self, action):
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage

            return
        obj = self.createAndAdd(data)

        if obj is not None:
            # mark only as finished if we get the new object
            self._finishedAdd = True
            IStatusMessage(self.request).addStatusMessage(u"Comment added",
                                                          "info")

    @button.buttonAndHandler(u'Cancel', name='cancel',
                             condition=lambda *a: None)
    def handleCancel(self, action):
        return


class CommentsView(object):

    def add_form(self, context):
        print(context)
        types = portal.get_tool('portal_types')
        fti = types['wise.msfd.comment']

        form = AddForm(context, self.request, fti)

        form_template = ViewPageTemplateFile('pt/inline-form.pt')

        form.template = form_template.__get__(form)

        form.status = ''

        form.nextURL = ''

        return form


class CommentView(BaseComplianceView):
    def __call__(self):
        url = self._article_assessment.absolute_url()

        return self.request.response.redirect(url)
