#pylint: skip-file
from __future__ import absolute_import
import logging
import cgi

from zope import event
from zope.security import checkPermission

from eea.cache.event import InvalidateMemCacheEvent
from langdetect.detector import LangDetectException
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF
from Products.statusmessages.interfaces import IStatusMessage

from . import (delete_translation, get_detected_lang, get_translated,
               normalize, retrieve_translation, save_translation)
from .interfaces import ITranslationContext
import six

logger = logging.getLogger('wise.msfd.translation')


class TranslationCallback(BrowserView):
    """ This view is called by the EC translation service.
    Saves the translation in Annotations
    """

    def __call__(self):
        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))
        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        qs = self.request["QUERY_STRING"]
        parsed = cgi.parse_qs(qs)
        form = {}
        for name, val in parsed.items():
            form[name] = val[0]

        logger.info("Form received: %s", form)
        form.pop('request-id', None)
        form.pop('target-language', None)

        language = form.pop('source_lang', None)

        if language is None:
            language = ITranslationContext(self.context).language

        original = form.pop('external-reference', '')
        original = normalize(original)

        translated = form.pop('translation', list(form.keys())[0]).strip()

        # translated = decode_text(translated)
        # it seems the EC service sends translated text in latin-1.
        # Please double-check, but the decode_text that automatically detects
        # the encoding doesn't seem to do a great job

        translated = translated  # .decode('latin-1')

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

    def translate(self, source_lang, value, is_translatable):
        """ Renders a translated cell based on lang and original value

        We have a special template for not-translatable values, to be
        integrated in the general format that is required by the styling
        """

        value = normalize(value)
        # if isinstance(value, str):      # BBB: with older implementation
        #     value = value.decode('utf-8')      # TODO: should use decode?

        if (not value) or (not is_translatable):
            return self.cell_tpl(value=value)

        if not isinstance(value, six.string_types):
            return self.cell_tpl(value=value)

        # if detected language is english render cell template
        lang = None
        try:
            lang = get_detected_lang(value)
        except LangDetectException:
            lang = 'en'

        if lang == 'en':
            return self.cell_tpl(value=value)

        translated = get_translated(value, source_lang)

        can_edit = checkPermission('wise.EditTranslations', self.context)

        return self.translate_tpl(text=value,
                                  translation=translated,
                                  can_translate=can_edit,
                                  source_lang=source_lang)

    def __call__(self):
        return self.translation_edit_template()


class SendTranslationRequest(BrowserView):
    """ Sends (re)translation request
    """

    def __call__(self):

        form = self.request.form
        source_lang = form.get('language', '')
        url = form.get('redirect_url')
        text = form.get('text', '')

        if not source_lang:
            source_lang = ITranslationContext(self.context).language

        logger.info("Source lang %s", source_lang)

        if not text:
            return self.request.response.redirect(url)

        text = normalize(text)

        delete_translation(text, source_lang)
        targetLanguages = self.request.form.get('targetLanguages', ['EN'])

        retrieve_translation(source_lang, text, targetLanguages, force=True)

        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))

        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        return self.request.response.redirect(url)
