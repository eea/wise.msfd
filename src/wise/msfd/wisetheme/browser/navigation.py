# pylint: skip-file
"""navigation.py"""
from __future__ import absolute_import
from zope.component import getMultiAdapter, getUtility

from Acquisition import aq_inner
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.navigation import \
    CatalogNavigationTabs as BaseCatalogNavigationTabs
from Products.CMFPlone.browser.navigation import get_id, get_view_url
from Products.CMFPlone.interfaces import INavigationSchema


class CatalogNavigationTabs(BaseCatalogNavigationTabs):
    """ We override this to add the has_default_page information
    """

    def topLevelTabs(self, actions=None, category='portal_tabs'):
        """topLevelTabs"""
        context = aq_inner(self.context)
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema,
            prefix="plone",
            check=False
        )
        mtool = getToolByName(context, 'portal_membership')
        member = mtool.getAuthenticatedMember().id
        catalog = getToolByName(context, 'portal_catalog')

        if actions is None:
            context_state = getMultiAdapter(
                (context, self.request),
                name=u'plone_context_state'
            )
            actions = context_state.actions(category)

        # Build result dict
        result = []
        # first the actions
        for actionInfo in actions:
            data = actionInfo.copy()
            data['name'] = data['title']
            self.customize_entry(data)
            result.append(data)

        # check whether we only want actions
        if not navigation_settings.generate_tabs:
            return result

        query = self._getNavQuery()

        rawresult = catalog.searchResults(query)

        def _get_url(item):
            """_get_url"""
            if item.getRemoteUrl and not member == item.Creator:
                return (get_id(item), item.getRemoteUrl)
            return get_view_url(item)

        context_path = '/'.join(context.getPhysicalPath())

        # now add the content to results
        for item in rawresult:
            if (item.exclude_from_nav and
                not context_path.startswith(item.getPath())):  # noqa: E501
                # skip excluded items if they're not in our context path
                continue
            _, item_url = _get_url(item)
            data = {
                'name': utils.pretty_title_or_id(context, item),
                'id': item.getId,
                'url': item_url,
                'description': item.Description,
                'review_state': item.review_state,

                # the only difference to the default code from Plone
                'has_default_page': item.has_default_page,
            }
            self.customize_entry(data, item)
            result.append(data)

        return result
