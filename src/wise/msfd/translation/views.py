# pylint: skip-file
from __future__ import absolute_import
import json
import logging
import os
from urllib.parse import parse_qs

from zope.security import checkPermission

from wise.msfd.cache import invalidate_dependencies
from langdetect.detector import LangDetectException
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF
from Products.statusmessages.interfaces import IStatusMessage

from . import (delete_translation, get_detected_lang, get_translated,
               normalize, retrieve_translation)
from .interfaces import ITranslationContext
from .restv2 import handle_callback
import six

logger = logging.getLogger('wise.msfd.translation')

# vim src/wise.msfd/src/wise/msfd/translation/views.py


class TranslationCallback(BrowserView):
    """ This view is called by the EC translation service.
    Saves the translation in Annotations
    """

    def __call__(self):
        deps = ['translation']
        invalidate_dependencies(deps)
        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        qs = self.request["QUERY_STRING"]
        parsed = parse_qs(qs)
        form = {}

        for name, val in parsed.items():
            form[name] = val[0]

        translate_key_ENV = os.environ.get("TRANSLATE_KEY", 'MISSING_ENV')
        translate_key_FORM = form.get('translateKey', 'MISSING_FORM')

        if translate_key_ENV != translate_key_FORM:
            logger.error(
                'TRANSLATE_KEY from request not equal with the key from ENV!')
            return '{}'

        return self._handle_v2()

    def _handle_v2(self):
        """Handle a v2 JSON callback body."""
        try:
            body = self.request.get('BODY', '')
            payload = json.loads(body)
        except (ValueError, TypeError):
            logger.error('Cannot parse v2 callback JSON body')
            return '{}'

        if not isinstance(payload, dict):
            logger.error('v2 callback body is not a JSON object: %r', payload)
            return '{}'

        default_language = None
        try:
            default_language = ITranslationContext(self.context).language
        except Exception:  # pylint: disable=broad-except
            pass

        handle_callback(payload, default_language=default_language)

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
        invalidate_dependencies(deps)

        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        messages = IStatusMessage(self.request)
        messages.add(u"Auto-translation initiated, please refresh "
                     u"in a couple of minutes", type=u"info")

        return self.request.response.redirect(url)
