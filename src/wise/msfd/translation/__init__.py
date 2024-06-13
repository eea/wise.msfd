#pylint: skip-file
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json
import logging
import os
from datetime import datetime

import chardet
import requests
from requests.auth import HTTPDigestAuth

import transaction
from BTrees.OOBTree import OOBTree
from langdetect import detect
from persistent import Persistent
from plone.api import portal

from .interfaces import ITranslationsStorage
import six

env = os.environ.get

ANNOTATION_KEY = 'translation.msfd.storage'
TRANS_USERNAME = 'ipetchesi'        # TODO: get another username?
MARINE_PASS = env('MARINE_PASS', '')
SERVICE_URL = 'https://webgate.ec.europa.eu/etranslation/si/translate'

logger = logging.getLogger('wise.msfd.translation')


def get_detected_lang(text):
    """ Detect the language of the text, return None for short texts """

    if len(text) < 50:
        return None

    try:
        detect_lang = detect(text)
    except:
        # Can't detect language if text is an url
        # it throws LangDetectException
        return None

    return detect_lang


# Detect the source language for countries which have more official languages
TRANS_LANGUAGE_MAPPING = {
    # 'DE': lambda text: 'DE'
    'BE': get_detected_lang,
    'SE': get_detected_lang,
}

# For the following countries, the translation service uses
# different country code
ALTERNATE_COUNTRY_CODES = {
    'SI': 'SL',
}


def get_mapped_language(country_code, text):
    detect_func = TRANS_LANGUAGE_MAPPING[country_code]
    detected_lang = detect_func(text)

    if not detected_lang:
        return country_code

    if detected_lang == 'en':
        return country_code

    return detected_lang.upper()


def _get_country_code(country_code, text):
    if country_code in TRANS_LANGUAGE_MAPPING:
        country_code = get_mapped_language(country_code, text)

    if country_code in ALTERNATE_COUNTRY_CODES:
        country_code = ALTERNATE_COUNTRY_CODES.get(country_code, country_code)

    return country_code


def decode_text(text):
    encoding = chardet.detect(text)['encoding']
    text_encoded = text.decode(encoding)

    # import unicodedata
    # text_encoded = unicodedata.normalize('NFKD', text_encoded)

    return text_encoded


class Translation(Persistent):
    def __init__(self, text, source=None):
        self.text = text
        self.source = source
        self.approved = False
        self.modified = datetime.now()

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


def retrieve_translation(country_code,
                         text, target_languages=None, force=False):
    """ Send a call to automatic translation service, to translate a string

    Returns a json formatted string
    """

    country_code = _get_country_code(country_code, text)

    if not text:
        return

    translation = get_translated(text, country_code)

    if translation:
        if not(force or (u'....' in translation)):
            # don't translate already translated strings, it overrides the
            # translation
            res = {
                'transId': translation,
                'externalRefId': text,
            }

            return res

    site_url = portal.get().absolute_url()

    if 'localhost' in site_url:
        logger.warning(
            "Using localhost, won't retrieve translation for: %s", text)

        return {}

    # if detected language is english skip translation
    
    if get_detected_lang(text) == 'en':
        logger.info(
            "English language detected, won't retrive translation for: %s",
            text
        )

        return

    if not target_languages:
        target_languages = ['EN']

    dest = '{}/assessment-module/@@translate-callback?source_lang={}'.format(site_url,
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

    resp = requests.post(
        SERVICE_URL,
        auth=HTTPDigestAuth('Marine_EEA_20180706', MARINE_PASS),
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    logger.info('Response from translation request: %r', resp.content)

    res = {
        "transId": resp.content,
        "externalRefId": text
    }

    return res


def get_translated(value, language, site=None):
    language = _get_country_code(language, value)

    if site is None:
        site = portal.get()

    storage = ITranslationsStorage(site)

    translated = storage.get(language, {}).get(value, None)

    if translated:
        if hasattr(translated, 'text'):
            return translated.text.lstrip('?')

        return translated.lstrip('?')


def normalize(text):
    if not isinstance(text, six.string_types):
        return text

    if isinstance(text, str):
        text = text  # .decode('utf-8')

    if not text:
        return text

    text = text.strip().replace(u'\r\n', u'\n').replace(u'\r', u'\n')

    return text


def delete_translation(text, source_lang):
    source_lang = _get_country_code(source_lang, text)

    site = portal.get()

    storage = ITranslationsStorage(site)

    if storage.get(source_lang, None):
        decoded = normalize(text)

        if text in storage[source_lang]:
            del storage[source_lang][text]

        if decoded in storage[source_lang]:
            del storage[source_lang][decoded]

            # I don't think this is needed
            storage[source_lang]._p_changed = True
            transaction.commit()


def save_translation(original, translated, source_lang, approved=False):
    source_lang = _get_country_code(source_lang, original)

    site = portal.get()
    
    storage = ITranslationsStorage(site)

    storage_lang = storage.get(source_lang, None)

    if storage_lang is None:
        storage_lang = OOBTree()
        storage[source_lang] = storage_lang
    
    translated = Translation(translated)

    if approved:
        translated.approved = True

    storage_lang[original] = translated
    logger.info('Saving to annotation: %s', translated)
