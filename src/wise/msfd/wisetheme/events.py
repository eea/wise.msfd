# pylint: skip-file
""" events.py """
from __future__ import absolute_import
from wise.msfd.wisetheme.interfaces import ISlideshowCreatedEvent
from wise.msfd.wisetheme.interfaces import ISlideshowRemovedEvent
from wise.msfd.wisetheme.interfaces import ISlideshowWillBeCreatedEvent
from wise.msfd.wisetheme.interfaces import ISlideshowWillBeRemovedEvent
from zope.component.interfaces import ObjectEvent
from zope.interface import implements


class SlideshowWillBeCreatedEvent(ObjectEvent):
    """SlideshowWillBeCreatedEvent"""
    implements(ISlideshowWillBeCreatedEvent)


class SlideshowCreatedEvent(ObjectEvent):
    """SlideshowCreatedEvent"""
    implements(ISlideshowCreatedEvent)


class SlideshowWillBeRemovedEvent(ObjectEvent):
    """SlideshowWillBeRemovedEvent"""
    implements(ISlideshowWillBeRemovedEvent)


class SlideshowRemovedEvent(ObjectEvent):
    """SlideshowRemovedEvent"""
    implements(ISlideshowRemovedEvent)
