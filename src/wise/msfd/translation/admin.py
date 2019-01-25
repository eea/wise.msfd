from Products.Five.browser import BrowserView

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
        import pdb; pdb.set_trace()
        pass

    # def edit_translation(self, original, translation, language):
