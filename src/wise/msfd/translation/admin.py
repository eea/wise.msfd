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

        save_translation(original, translated, language, approved=True)

        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))

        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        response = self.request.response
        response.addHeader('Content-Type', 'application/json')

        return json.dumps({'text': translated})


    def add_translation(self):

        form = self.request.form

        language = form.get('language')
        original = form.get('original')  # .decode('utf-8')
        original = normalize(original)
        translated = form.get('translated').decode('utf-8')

        save_translation(original, translated, language, approved=True)

        url = './@@translations-overview?language=' + language

        return self.request.response.redirect(url)

    def approve_translations(self):
        form = self.request.form

        language = form.get('language')
        approved = form.get('approved')  # .decode('utf-8')

        url = './@@translations-overview?language=' + language

        if not approved:
            return self.request.response.redirect(url)

        if isinstance(approved, str):
            approved = [approved]

        storage = ITranslationsStorage(self.context)
        selected_lang = self.request.form.get('language')

        langstore = storage.get(selected_lang, {})

        for label in approved:
            translation = langstore[label]

            if translation.text.startswith('?'):
                translation.text = translation.text[1:]

            translation.approved = True
            translation.modified = datetime.now()

        return self.request.response.redirect(url)

