from __future__ import absolute_import
from zope.interface import Interface


class INationaldescriptorArticleView(Interface):
    """ Page to view an article (Articles 8, 9, 10) overview page
    """


class INationaldescriptorSecondaryArticleView(Interface):
    """ Page to view a "secondary" article (Articles 3-4, 7, 8ESA)
        overview page
    """


class INationaldescriptorArticleViewCrossCutting(Interface):
    """ Page to view a Cross Cutting assessment overview page
    """
