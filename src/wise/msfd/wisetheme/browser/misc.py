# pylint: skip-file
from __future__ import absolute_import
import json
import logging

import requests
from Products.Five.browser import BrowserView
from six.moves.urllib.parse import urlparse, urlunparse
from zope.component import getUtilitiesFor
from zope.schema.interfaces import IVocabularyFactory

logger = logging.getLogger("wise.theme")


class GoPDB(BrowserView):
    def __call__(self):

        import pdb

        pdb.set_trace()

        return "ok"


class VocabularyInspector(BrowserView):
    blacklist = [
        "plone.app.vocabularies.Users",
        "plone.app.multilingual.RootCatalog",
        "plone.app.vocabularies.Principals",
        "plone.app.vocabularies.Catalog",
    ]

    def vocabs(self):
        vocabs = getUtilitiesFor(IVocabularyFactory)

        vocabs = [xv for xv in vocabs if xv[0] not in self.blacklist]

        return vocabs


class ExternalResourceProxy(BrowserView):
    """A workaround for CORS issues"""

    # https://www.eea.europa.eu/api/SITE/data-and-maps/indicators/renewable-gross-final-energy-consumption-5/assessment

    def __call__(self):
        url = self.request.form.get("url")

        if "www.eea.europa.eu" in url:
            parsed = list(urlparse(url))
            parsed[2] = "/api/SITE" + parsed[2]
            url = urlunparse(parsed)
            logger.info("Requesting eea %s", url)
            req = requests.get(url, headers={"Accept": "application/json"})
            j = req.json()
            self.request.response.setHeader("Content-type", "application/json")
            return json.dumps(j)

        return ""
