# pylint: skip-file
"""Filter groups: the titled bands the Filters panel is organised in.

Every facet declares the group it belongs to, so the frontend does not have to
guess from the facet name (``member_states`` is geographical on every cycle) or
from its widget type (a ``range`` is not always a date). The group travels in
the ``view=filters`` payload next to the facet itself::

    {
        'name': 'member_states',
        'label': 'Country',
        'type': 'checkboxes',
        'group': {'key': 'location', 'label': 'Geographical filters',
                  'order': 10},
        ...
    }

The frontend renders one band per group, sorted by ``order``, and keeps the
facets inside a band in the order the provider declared them. ``key`` is the
stable identifier used for the band icon (and anything else presentational);
an unknown key falls back to a generic icon, so adding a group here needs no
frontend change.
"""
from __future__ import absolute_import


class Group(object):
    """A titled band of facets in the Filters panel.

    ``order`` is the display order of the bands (lower comes first, 10-wide
    steps leave room for new groups between the existing ones).
    """

    __slots__ = ('key', 'label', 'order')

    def __init__(self, key, label, order=0):
        self.key = key
        self.label = label
        self.order = order

    def serialize(self):
        return {
            'key': self.key,
            'label': self.label,
            'order': self.order,
        }

    def __repr__(self):
        return '<Group {}>'.format(self.key)


def group_payload(group):
    """The wire form of a facet's group (``None`` when it has none)."""
    if group is None:
        return None

    return group.serialize()


#: where a report applies: country, region/subregion
LOCATION = Group('location', u'Geographical filters', order=10)
#: what was reported: GES descriptor, component/criteria, feature, update type
ASSESSMENT = Group('assessment', u'Assessment filters', order=20)
#: the marine reporting unit itself: area type, area, identifier, name
UNIT = Group('unit', u'Marine reporting unit', order=30)
#: the legal instrument behind a designation
LEGISLATION = Group('legislation', u'Legislation', order=40)
#: reported dates (the determination date, ...)
TIME = Group('time', u'Date', order=50)
