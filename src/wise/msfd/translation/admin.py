import json
import logging

from zope import event

from eea.cache.event import InvalidateMemCacheEvent
from Products.Five.browser import BrowserView

from . import normalize, save_translation
from .interfaces import ITranslationsStorage

logger = logging.getLogger('wise.msfd.translation')


class TranslationsOverview(BrowserView):
    """ Translations overview page
    """

    def languages(self):
        return ITranslationsStorage(self.context).keys()

    def available_translations(self):
        storage = ITranslationsStorage(self.context)
        selected_lang = self.request.form.get('language')

        langstore = storage.get(selected_lang, {})

        return langstore

    def edit_translation(self):
        form = self.request.form

        language = form.get('language')
        original = form.get('original')  # .decode('utf-8')
        original = normalize(original)
        translated = form.get('tr-new').decode('utf-8')
        import pdb;pdb.set_trace()

        save_translation(original, translated, language)

        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))

        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        response = self.request.response
        response.addHeader('Content-Type', 'application/json')

        return json.dumps({'text': translated})
