# pylint: skip-file
from __future__ import absolute_import
from plone.api import content, portal
from plone.app.contenttypes.utils import replace_link_variables_by_paths
from plone.app.layout.viewlets import ViewletBase
from plone.namedfile.file import NamedBlobImage
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class SlidesViewlet(ViewletBase):

    render = ViewPageTemplateFile("pt/slideshow.pt")

    def images(self):
        site = portal.get()
        base = '/'.join(site.getPhysicalPath())

        path = {'query': base + '/homepage-slide-images', 'depth': 1}
        results = content.find(
            path=path, portal_type='Image', sort_on='getObjPositionInParent')

        return results


class FrontpageKeyMessagesViewlet(ViewletBase):
    """ BrowserView for frontpage key messages
    """

    def get_url(self, obj):
        url = replace_link_variables_by_paths(obj, obj.remoteUrl)
        return url

    def tabs(self):
        site = portal.get()
        base = '/'.join(site.getPhysicalPath())

        path = {'query': base + '/key-messages', 'depth': 1}
        sections = content.find(
            path=path,
            portal_type='Folder',
            state='published',
            sort_on='created',
            sort_order='ascending'
        )

        klass = ['light-blue-color', 'cyan-color', 'blue-color']
        klass_iterator = 0

        tabs = []

        for section in sections:
            obj = section.getObject()
            cards = []
            folder_contents = obj.getFolderContents(
                contentFilter={
                    'portal_type': 'key_message_card',
                    'state': 'published',
                })

            for card in folder_contents:
                card = card.getObject()
                image = self.image(card)
                cards.append({
                    'id': card.id,
                    'name': card.title,
                    'description': card.text,
                    'url': self.get_url(card),
                    'image': image,
                })

            tab = {
                'id': obj.id,
                'name': obj.title,
                'description': obj.description,
                'url': obj.absolute_url(),
                'color': '',
                'cards': cards,
            }

            try:
                tab['color'] = klass[klass_iterator]
                klass_iterator += 1
            except IndexError:
                pass

            tabs.append(tab)

        return tabs

    def image(self, obj):
        image = getattr(obj, 'image', None)

        if image is None:
            return None

        if not isinstance(image, NamedBlobImage):
            return None

        url = '{0}/@@images/image/large'.format(obj.absolute_url())
        return url


class FrontpageReportsViewlet(ViewletBase):
    """ BrowserView for frontpage reports viewlet
    """

    def reports(self):
        results = content.find(
            portal_type='external_report', state='published',
            sort_on="EffectiveDate", sort_order="descending"
        )[:3]

        return [b.getObject() for b in results]


class LeadImage(ViewletBase):
    def lead_image(self):
        """Return lead image information
        """
        image = getattr(self.context, 'image', None)

        if image is None:
            return None

        if not isinstance(image, NamedBlobImage):
            return None

        url = '{0}/@@download/image/{1}'.format(
            self.context.absolute_url(), image.filename)
        caption = getattr(self.context, 'image_caption', None)

        return dict(url=url, caption=caption)


# from AccessControl import Unauthorized
# from plone import api
# from plone.app.layout.viewlets.common import GlobalSectionsViewlet
# from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
# from tlspu.cookiepolicy.browser.viewlets import CookiePolicyViewlet
#
#
# class CookiesViewlet(CookiePolicyViewlet):
#     render = ViewPageTemplateFile("pt/cookiepolicy.pt")
#
#     def update(self):
#         return super(CookiesViewlet, self).render()
#
#
# class NavigationViewlet(GlobalSectionsViewlet):
#     """ Navigation menu viewlet override
#     """
#     index = ViewPageTemplateFile('pt/sections.pt')
#
#     def tabs(self):
#         root = api.portal.get_navigation_root(context=self.context)
#         contentish = ['Folder', 'Collection', 'Topic']
#         # tabs = [{
#         #     'url': root.absolute_url(),
#         #     'id': root.id,
#         #     'name': 'Home',
#         #     'image': '',
#         #     'subtabs': []}]
#         tabs = []
#
#         brains = root.getFolderContents(
#             contentFilter={
#                 'portal_type': contentish
#
#             })
#
#         brains = [b for b in brains if b.exclude_from_nav is False]
#
#         for brain in brains:
#             obj = brain.getObject()
#             children = []
#
#             types = ['collective.cover.content', 'Document',
#                      'News Item', 'Event', 'Folder']
#             folder_contents = obj.getFolderContents(
#                 contentFilter={
#                     'portal_type': types
#                 })
#
#             for child in folder_contents:
#                 if child.exclude_from_nav:
#                     continue
#                 try:
#                     child = child.getObject()
#                 except Unauthorized:
#                     continue
#                 children.append({
#                     'url': child.absolute_url(),
#                     'description': '',
#                     'name': child.title,
#                     'id': child.id})
#
#             image = self.get_image(obj)
#             tab = {
#                 'url': obj.absolute_url(),
#                 'description': '',
#                 'name': obj.title,
#                 'id': obj.id,
#                 'image': image,
#                 'subtabs': children
#             }
#             tabs.append(tab)
#
#         return tabs
#
#     def get_image(self, obj):
#         if not hasattr(obj, 'image') or obj.image is None:
#             return ''
#
#         scales = obj.restrictedTraverse('@@images')
#         image = scales.scale('image', scale='menu-icon')
#
#         return image and image.absolute_url() or ''
