""" Indicators """
from zope.interface import alsoProvides
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from DateTime import DateTime


class UpdateIndicatorLastUpdate(BrowserView):
    """UpdateIndicatorLastUpdate"""
    def update_indicators(self):
        """update_indicators"""
        updated_items = []

        # Access the portal catalog
        catalog = self.context.portal_catalog

        # Search for all items of type "indicator"
        indicators = catalog(portal_type="indicator")

        # Process each indicator
        for brain in indicators:
            obj = brain.getObject()
            current_value = getattr(obj, 'indicator_last_update', None)

            if current_value:
                if isinstance(current_value, str):
                    date_only = current_value.split(" ")[0]
                elif isinstance(current_value, DateTime):
                    # If it's a DateTime object, convert to YYYY-MM-DD format
                    date_only = current_value.strftime('%Y-%m-%d')
                else:
                    date_only = current_value

                # import pdb; pdb.set_trace()
                # Update the field
                obj.indicator_last_update = date_only
                obj.reindexObject()

                updated_items.append(obj.absolute_url())

        return updated_items

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        updated_items = self.update_indicators()

        if updated_items:
            return "Updated {}!".format(len(updated_items))

        return "No items to update."
