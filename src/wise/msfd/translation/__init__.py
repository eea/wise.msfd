# -*- coding: utf-8 -*-

import json
import logging
import os

import chardet
import requests
from requests.auth import HTTPDigestAuth

import transaction
from BTrees.OOBTree import OOBTree
from plone.api import portal
from plone.api.portal import get

from .interfaces import ITranslationsStorage

# from zope.annotation.interfaces import IAnnotations


env = os.environ.get

ANNOTATION_KEY = 'translation.msfd.storage'
TRANS_USERNAME = 'ipetchesi'        # TODO: get another username?
MARINE_PASS = env('MARINE_PASS', '')
SERVICE_URL = 'https://webgate.ec.europa.eu/etranslation/si/translate'

logger = logging.getLogger('wise.msfd.translation')


def decode_text(text):
    encoding = chardet.detect(text)['encoding']
    text_encoded = text.decode(encoding)

    # import unicodedata
    # text_encoded = unicodedata.normalize('NFKD', text_encoded)

    return text_encoded


def retrieve_translation(country_code, text, target_languages=None):
    """ Send a call to automatic translation service, to translate a string
    """

    if not text:
        return

    translation = get_translated(text, country_code)

    if translation and (u'....' not in translation):
        # don't translate already translated strings, it overrides the
        # translation
        res = {
            'transId': translation,
            'externalRefId': text,
        }

        return json.dumps(res)

    site_url = portal.getSite().absolute_url()

    if 'localhost' in site_url:
        logger.warning("Using localhost, won't retrieve translation for: %s",
                       text
                       )

        return

    if not target_languages:
        target_languages = ['EN']

    dest = '{}/@@translate-callback?source_lang={}'.format(site_url,
                                                           country_code)

    logger.info('Translate callback URL: %s', dest)

    data = {
        'priority': 5,
        'callerInformation': {
            'application': 'Marine_EEA_20180706',
            'username': TRANS_USERNAME,
        },
        'domain': 'SPD',
        'externalReference': text,          # externalReference,
        'textToTranslate': text,
        'sourceLanguage': country_code,
        'targetLanguages': target_languages,
        'destinations': {
            'httpDestinations':
            [dest],
        }
    }

    dataj = json.dumps(data)
    headers = {'Content-Type': 'application/json'}

    resp = requests.post(SERVICE_URL,
                         auth=HTTPDigestAuth('Marine_EEA_20180706',
                                             MARINE_PASS),
                         data=dataj,
                         headers=headers)

    res = {
        "transId": resp.content,
        "externalRefId": text
    }

    # res = {'translation': 'Translation in progress!'}

    logger.info('Response from translation request:', res)

    return json.dumps(res)


def get_translated(value, language, site=None):
    if site is None:
        site = get()

    storage = ITranslationsStorage(site)

    translated = storage.get(language, {}).get(value, None)

    if translated:
        return translated.lstrip('?')


def delete_translation(self, text, source_lang):
    site = portal.getSite()

    storage = ITranslationsStorage(site)

    if (storage.get(source_lang, None)):
        decoded = text.decode('utf-8')      # TODO: is decode() needed?

        if decoded in storage[source_lang]:
            del storage[source_lang]

        transaction.commit()


def save_translation(original, translated, source_lang):
    site = portal.getSite()

    storage = ITranslationsStorage(site)

    storage_lang = storage.get(source_lang, None)

    if storage_lang is None:
        storage_lang = OOBTree()
        storage[source_lang] = storage_lang

    storage_lang[original] = translated
    logger.info('Saving to annotation: %s', translated)
