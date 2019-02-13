import logging
import time

from zope import event
from zope.security import checkPermission

from eea.cache.event import InvalidateMemCacheEvent
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF

from . import (delete_translation, get_translated,  # decode_text,
               retrieve_translation, save_translation)
from .interfaces import ITranslationContext

logger = logging.getLogger('wise.msfd.translation')


class TranslationCallback(BrowserView):
    """ This view is called by the EC translation service.

    Saves the translation in Annotations
    """

    def __call__(self):
        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))
        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        form = self.request.form

        form.pop('request-id', None)
        form.pop('target-language', None)

        language = form.pop('source_lang', None)

        if language is None:
            language = ITranslationContext(self.context).language

        original = form.pop('external-reference', '').decode('utf-8').strip()

        translated = form.pop('translation', form.keys()[0]).strip()

        # translated = decode_text(translated)
        # it seems the EC service sends translated text in latin-1.
        # Please double-check, but the decode_text that automatically detects
        # the encoding doesn't seem to do a great job

        translated = translated.decode('latin-1')

        save_translation(original, translated, language)

        return '{}'


class TranslationView(BrowserView):
    """ This is composed into BaseComplianceView to use the translate() method

    Calling the view yields the translation edit template
    """

    translation_edit_template = VPTF('./pt/translation-edit-form.pt')
    translate_tpl = VPTF('pt/translate-snip.pt')
    cell_tpl = VPTF('pt/cell.pt')

    @property
    def country_code(self):
        code = self.context.aq_parent.aq_parent.aq_parent.id.upper()

        return code

    def can_modify(self):
        return checkPermission('cmf.ModifyPortalContent', self.context)

    def translate(self, source_lang, value, is_translatable):
        # TODO: implement getting the translation from annotations
        # orig = value

        if isinstance(value, str):      # BBB: with older implementation
            value = value.decode('utf-8')      # TODO: should use decode?

        if (not value) or (not is_translatable):
            return self.cell_tpl(value=value)

        if not isinstance(value, basestring):
            return self.cell_tpl(value=value)

        translated = get_translated(value, source_lang)

        return self.translate_tpl(text=value,
                                  translation=translated,
                                  can_translate=self.can_modify())

    def __call__(self):
        return self.translation_edit_template()


class SendTranslationRequest(BrowserView):
    """ Sends translation request

    TODO: this view is not used anymore, can be deleted.
    """

    def __call__(self):

        source_lang = self.request.form.get('sourceLanguage', '')

        if not source_lang:
            source_lang = ITranslationContext(self.context).language

        logger.info("Source lang %s", source_lang)

        if 'from_annot' in self.request.form.keys():
            time.sleep(0.5)
            text = self.request.form['from_annot']

            return get_translated(text, source_lang)

        text = self.request.form.get('text-to-translate', '')
        # text = decode_text(orig)

        if not text:
            return ''

        delete_translation(text, source_lang)

        targetLanguages = self.request.form.get('targetLanguages', ['EN'])

        headers = {'Content-Type': 'application/json'}
        self.request.response.headers.update(headers)

        return retrieve_translation(source_lang, text, targetLanguages)
