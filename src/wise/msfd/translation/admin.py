from Products.Five.browser import BrowserView

from . import save_translation
from .interfaces import ITranslationsStorage


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

        original = form.get('original').decode('utf-8')
        translated = form.get('tr-new').decode('utf-8')

        save_translation(original, translated, language)
        url = '{}/@@translations-overview?language={}'.format(
            self.context.absolute_url(),
            language
        )

        return self.request.response.redirect(url)
