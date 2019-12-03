from zope.interface import Attribute, Interface
from zope.schema import Choice, List  # Int, Text, TextLine

# from plone.app.textfield import RichText


class IMainForm(Interface):
    """ A marker interface to easily identify main forms
    """


class IEmbeddedForm(Interface):
    """ A form that is "embeded" in another form
    """

    def extras():
        """ Return extra-html to show after the main data
        """


class IMarineUnitIDSelect(Interface):
    marine_unit_id = Choice(
        title=u"MarineUnitID",
        # description=u"Select one or more MarineUnitIDs that you're
        # interested",
        required=True,
        vocabulary="wise_search_marine_unit_id"
    )


class IMarineUnitIDsSelect(Interface):
    marine_unit_ids = List(
        title=u"MarineUnitID",
        # description=u"Select one or more MarineUnitIDs that you're
        # interested",
        value_type=Choice(vocabulary="wise_search_marine_unit_ids"),
        required=False
    )
