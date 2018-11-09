# -*- coding: utf-8 -*-

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

ANNOTATION_KEY = 'translation.msfd.storage'


def decode_text(text):
    encoding = chardet.detect(text)['encoding']
    text_encoded = text.decode(encoding)

    return text_encoded


class TranslateBTree(OOBTree):
    pass


class SendTranslationRequest(BrowserView):
    """ Sends translation request
    """

    def get_translation_from_annot(self, text):
        if not text:
            return text

        site = portal.getSite()
        annot = IAnnotations(site, None)

        if annot.get(ANNOTATION_KEY, None):
            decoded = decode_text(text)

            translation = annot[ANNOTATION_KEY].get(decoded, '')

            return translation

        return text

    def delete_translation(self, text):
        site = portal.getSite()
        annot = IAnnotations(site, None)

        if annot.get(ANNOTATION_KEY, None):
            decoded = decode_text(text)

            translation = annot[ANNOTATION_KEY].pop(decoded, '')

            transaction.commit()

            return translation

        return text

    def __call__(self):

        # import pdb; pdb.set_trace()

        if 'from_annot' in self.request.form.keys():
            time.sleep(0.5)
            text = self.request.form['from_annot']

            return self.get_translation_from_annot(text)

        text = self.request.form.get('text-to-translate', '')

        if not text:
            return ''

        self.delete_translation(text)

        sourceLanguage = self.context.aq_parent.aq_parent.id.upper()

        if not sourceLanguage:
            sourceLanguage = self.request.form.get('sourceLanguage', '')

        targetLanguages = self.request.form.get('targetLanguages', ['EN'])
        externalReference = self.request.form.get('externalReference', '')

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
                    ['http://office.pixelblaster.ro:4880/Plone/marine/translation-callback2/'],
                'emailDestinations':
                    ['laszlo.cseh@eaudeweb.ro']
                    }
        }

        dataj = json.dumps(data)
        headers = {'Content-Type': 'application/json'}

        service_url = 'https://webgate.ec.europa.eu/etranslation/si/translate'
        result = requests.post(service_url, auth=HTTPDigestAuth(
                 'Marine_EEA_20180706', 'P7n3BLvCerm7cx3B'),
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
        if ANNOTATION_KEY not in annot.keys():
            annot[ANNOTATION_KEY] = OOBTree()

        # import pdb; pdb.set_trace()

        # transId = self.request.form.get('request-id', '')
        # targetLang = self.request.form.get('target-language', '')

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
        annot[ANNOTATION_KEY].update(trans_entry)

        # import pdb; pdb.set_trace()

        transaction.commit()
