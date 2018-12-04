# -*- coding: utf-8 -*-

import json
import os
import time

import chardet
import requests
from requests.auth import HTTPDigestAuth
from zope.annotation.interfaces import IAnnotations

import transaction
from BTrees.OOBTree import OOBTree
from plone.api import portal
from plone.api.portal import get as get_portal
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as VPTF

env = os.environ.get

ANNOTATION_KEY = 'translation.msfd.storage'
MARINE_PASS = env('MARINE_PASS', '')
SERVICE_URL = 'https://webgate.ec.europa.eu/etranslation/si/translate'

# TODO: get another username?
TRANS_USERNAME = 'ipetchesi'


def decode_text(text):
    encoding = chardet.detect(text)['encoding']
    text_encoded = text.decode(encoding)

    return text_encoded


class SendTranslationRequest(BrowserView):
    """ Sends translation request
    """

    def get_translation_from_annot(self, text, source_lang):
        if not text:
            return text

        site = portal.getSite()
        annot = IAnnotations(site, None)

        if (annot.get(ANNOTATION_KEY, None) and
                annot[ANNOTATION_KEY].get(source_lang, None)):

            decoded = decode_text(text)

            translation = annot[ANNOTATION_KEY][source_lang].get(decoded, '')
            translation = translation.lstrip('?')

            return translation

        return text

    def delete_translation(self, text, source_lang):
        site = portal.getSite()
        annot = IAnnotations(site, None)

        if (annot.get(ANNOTATION_KEY, None) and
                annot[ANNOTATION_KEY].get(source_lang, None)):
            decoded = decode_text(text)

            translation = annot[ANNOTATION_KEY][source_lang].pop(decoded, '')

            transaction.commit()

            return translation

        return text

    def __call__(self):

        sourceLanguage = self.context.aq_parent.aq_parent.aq_parent.id.upper()

        if not sourceLanguage:
            sourceLanguage = self.request.form.get('sourceLanguage', '')

        if 'from_annot' in self.request.form.keys():
            time.sleep(0.5)
            text = self.request.form['from_annot']

            return self.get_translation_from_annot(text, sourceLanguage)

        text = self.request.form.get('text-to-translate', '')

        if not text:
            return ''

        self.delete_translation(text, sourceLanguage)

        targetLanguages = self.request.form.get('targetLanguages', ['EN'])
        externalReference = self.request.form.get('externalReference', '')

        site = portal.getSite()
        marine_url = site.Plone.marine.absolute_url()

        if 'europa.eu' in marine_url:
            dest = marine_url + \
                '/translation-callback2?source_lang={}'.format(sourceLanguage)
        else:
            dest = 'http://office.pixelblaster.ro:4880/Plone/marine' + \
                '/translation-callback2?source_lang={}'.format(sourceLanguage)

        data = {
            'priority': 5,
            'callerInformation': {
                'application': 'Marine_EEA_20180706',
                'username': TRANS_USERNAME,
            },
            'domain': 'SPD',
            'externalReference': externalReference,
            'textToTranslate': text,
            'sourceLanguage': sourceLanguage,
            'targetLanguages': targetLanguages,
            'destinations': {
                'httpDestinations':
                [dest],
            }
        }

        dataj = json.dumps(data)
        headers = {'Content-Type': 'application/json'}

        result = requests.post(SERVICE_URL,
                               auth=HTTPDigestAuth('Marine_EEA_20180706',
                                                   MARINE_PASS),
                               data=dataj,
                               headers=headers)

        self.request.response.headers.update(headers)
        res = {
            "transId": result.content,
            "externalRefId": externalReference
        }

        # res = {'translation': 'Translation in progress!'}

        return json.dumps(res)


class TranslationCallback(BrowserView):
    """ Saves the translation in Annotations
    """

    def __call__(self):
        self.saveToAnnotation()

        return self.request.form

    def saveToAnnotation(self):
        site = portal.getSite()
        annot = IAnnotations(site, None)

        language = self.request.form.pop('source_lang', None)

        if not language:
            language = self.context.aq_parent.aq_parent.aq_parent.id.upper()

        if ANNOTATION_KEY not in annot.keys():
            annot[ANNOTATION_KEY] = OOBTree()

        if language not in annot[ANNOTATION_KEY].keys():
            annot[ANNOTATION_KEY][language] = OOBTree()

        annot_lang = annot[ANNOTATION_KEY][language]

        originalText = self.request.form.get('external-reference')
        originalText = decode_text(originalText)

        self.request.form.pop('request-id', None)
        self.request.form.pop('target-language', None)
        self.request.form.pop('external-reference', None)

        translatedText = self.request.form.pop('translation', None)

        if not translatedText:
            translatedText = self.request.form.keys()[0]

        translatedText = decode_text(translatedText)

        trans_entry = {originalText: translatedText}
        annot_lang.update(trans_entry)

        transaction.commit()


class TranslationView(BrowserView):
    """ This is composed into BaseComplianceView to use the translate() method

    Calling the view yields the translation edit template
    """

    translation_edit_template = VPTF('./pt/translation-edit-form.pt')
    translate_snip = VPTF('pt/translate-snip.pt')

    @property
    def country_code(self):
        code = self.context.aq_parent.aq_parent.aq_parent.id.upper()

        return code

    def translate(self, source_lang, value):
        # TODO: implement getting the translation from annotations

        # 'cmf.ModifyContent'
        # context = self.context
        # from zope.security import checkPermission
        #
        # class View(BrowserView):
        #
        #     def canRequestReview(self):
        #         return checkPermission('cmf.RequestReview', self.context)

        if not value:
            return self.translate_snip(text=value, translation=u"")

        translation = u''

        site = get_portal()
        annot = IAnnotations(site, None)

        if (annot and ANNOTATION_KEY in annot and
                source_lang in annot[ANNOTATION_KEY].keys()):

            annot_lang = annot[ANNOTATION_KEY][source_lang]

            if value in annot_lang:
                translation = annot_lang.get(value, None)
                translation = translation.lstrip('?')

        return self.translate_snip(text=value, translation=translation)

    def __call__(self):
        return self.translation_edit_template()
