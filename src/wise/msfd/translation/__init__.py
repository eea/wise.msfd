#pylint: skip-file
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import os
from datetime import datetime

import chardet

import transaction
from BTrees.OOBTree import OOBTree
from langdetect import detect
from persistent import Persistent
from plone.api import portal

from .interfaces import ITranslationsStorage
import six

env = os.environ.get

ANNOTATION_KEY = 'translation.msfd.storage'
REQUESTS_ANNOTATION_KEY = 'translation.msfd.requests'
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


# ---------------------------------------------------------------------------
# eTranslation REST v2 switch.
#
# Import this only after the shared helpers above have been defined.  restv2
# imports those helpers from this package, so importing it near the top of this
# module creates a circular import during package initialisation.
# ---------------------------------------------------------------------------
from .restv2 import retrieve_translation as retrieve_translation
