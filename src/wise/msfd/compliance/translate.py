# -*- coding: utf-8 -*-

import os
import json
import requests
import time
from Products.Five.browser import BrowserView
from plone.api import portal
from requests.auth import HTTPDigestAuth
from zope.annotation.interfaces import IAnnotations
from BTrees.OOBTree import OOBTree
import chardet
import transaction

env = os.environ.get

ANNOTATION_KEY = 'translation.msfd.storage'
MARINE_PASS = env('MARINE_PASS', '')


def decode_text(text):
    encoding = chardet.detect(text)['encoding']
    text_encoded = text.decode(encoding)

    return text_encoded


class TranslateBTree(OOBTree):
    pass


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

        # import pdb; pdb.set_trace()

        sourceLanguage = self.context.aq_parent.aq_parent.id.upper()

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

        abs_url = self.context.absolute_url()

        dest = abs_url + \
            '/translation-callback2?source_lang={}'.format(sourceLanguage)

        data = {
            'priority': 5,
            'callerInformation': {
                'application': 'Marine_EEA_20180706',
                'username': 'ipetchesi',
            },
            'domain': 'SPD',
            'externalReference': externalReference,
            'textToTranslate': text,
            'sourceLanguage': sourceLanguage,
            'targetLanguages': targetLanguages,
            'destinations': {
                'httpDestinations':
                    [dest],
                'emailDestinations':
                    ['']
                    }
        }

        dataj = json.dumps(data)
        headers = {'Content-Type': 'application/json'}

        service_url = 'https://webgate.ec.europa.eu/etranslation/si/translate'
        result = requests.post(service_url, auth=HTTPDigestAuth(
                 'Marine_EEA_20180706', MARINE_PASS),
                 data=dataj, headers=headers)

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
            language = self.context.aq_parent.aq_parent.id.upper()

        if (ANNOTATION_KEY not in annot.keys() or
                language not in annot[ANNOTATION_KEY].keys()):
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
