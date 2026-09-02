# pylint: skip-file
# -*- coding: utf-8 -*-

"""eTranslation REST v2 integration for wise.msfd.

This module is a drop-in replacement for the v1 translation logic defined in
``__init__.py``. Only the parts that actually changed between REST v1 and v2
live here (endpoint, authentication, request/response payloads and the
callback body parsing). Storage, normalisation and language-detection helpers
are reused unchanged from the package ``__init__``.

Differences covered:
    * endpoint:  webgate.ec.europa.eu/etranslation/si/translate
                 -> language-tools.ec.europa.eu/etranslation/api/askTranslate
    * auth:      HTTP Digest  ->  Authorization: Basic base64(app:password)
    * body:      externalReference moved inside callerInformation;
                 destinations{httpDestinations[]} -> deliveries{http};
                 callbacks requesterCallback/errorCallback
                 -> notifications{success,failure}{http}.
    * response:  plain number -> {"requestId": N}
    * callbacks: form/file upload (query params + raw body) -> JSON body with
                 translatedText / result / errorCode.
"""

from __future__ import absolute_import

import base64
import hashlib
import json
import logging
import os

import requests

from plone.api import portal

from . import (get_detected_lang, get_translated, _get_country_code,
               normalize, save_translation)
from .interfaces import ITranslationRequestsStorage

env = os.environ.get

SERVICE_URL = 'https://language-tools.ec.europa.eu/etranslation/api/askTranslate'

# Basic-authentication application name + password (v2 replaces the v1
# Digest credentials). Base64(app:password) is sent in the Authorization
# header.
TRANS_APP = env('ETRANS_APP', '')
TRANS_PASS = env('ETRANS_PASS', '')

# Monitoring metadata used in callerInformation. v2 no longer sends the
# ``application`` field; only externalReference + username are used here.
TRANS_USERNAME = env('ETRANS_USERNAME', '')

# Domain of the engine to use. v2 default is GEN (v1 code used SPD).
DOMAIN = env('ETRANS_DOMAIN', '')

logger = logging.getLogger('wise.msfd.translation')


def _auth_header():
    """Return the value for the Authorization header (Basic auth)."""
    creds = '{}:{}'.format(TRANS_APP, TRANS_PASS).encode('utf-8')
    return 'Basic ' + base64.b64encode(creds).decode('ascii')


def make_external_reference(text, source_language, target_languages):
    """Create a short, deterministic reference for a translation request.

    The original text is deliberately not put in ``externalReference``. The
    reference is only an identifier; the original is stored persistently in
    the site annotation storage and resolved by ``handle_callback``.
    """
    normalized = normalize(text)
    value = '{}\0{}\0{}'.format(
        source_language,
        ','.join(target_languages),
        normalized,
    )
    digest = hashlib.sha256(value.encode('utf-8')).hexdigest()
    return 'wise-msfd:' + digest


def save_request_reference(external_reference, text, source_language,
                           target_languages):
    """Persist the data needed to resolve a v2 callback reference."""
    storage = ITranslationRequestsStorage(portal.get())
    storage[external_reference] = {
        'text': normalize(text),
        'sourceLanguage': source_language,
        'targetLanguages': list(target_languages),
    }


def get_request_reference(external_reference):
    """Return the persisted request data for a callback reference."""
    storage = ITranslationRequestsStorage(portal.get())
    return storage.get(external_reference)


def delete_request_reference(external_reference):
    """Delete a request reference after a permanent failed request."""
    storage = ITranslationRequestsStorage(portal.get())
    if external_reference in storage:
        del storage[external_reference]


def retrieve_translation(country_code, text, target_languages=None, force=False):
    """Send a call to the automatic (v2) translation service.

    Returns a json formatted string (kept for v1 compatibility).
    """

    country_code = _get_country_code(country_code, text)

    if not text:
        return

    translation = get_translated(text, country_code)

    if translation:
        if not (force or (u'....' in translation)):
            # don't translate already translated strings, it overrides the
            # translation
            return {
                'transId': translation,
                'externalRefId': text,
            }

    site_url = portal.get().absolute_url()

    if 'localhost' in site_url:
        logger.warning(
            "Using localhost, won't retrieve translation for: %s", text)

        return {}

    # if detected language is english skip translation
    if get_detected_lang(text) == 'en':
        logger.info(
            "English language detected, won't retrive translation for: %s",
            text)

        return

    if not target_languages:
        target_languages = ['EN']

    external_reference = make_external_reference(
        text,
        country_code,
        target_languages,
    )

    translate_key = os.environ.get("TRANSLATE_KEY", None)

    if not translate_key:
        logger.error("Please set the TRANSLATE_KEY environment variable!!")
        return

    if not TRANS_APP or not TRANS_PASS:
        logger.error(
            "Please set the ETRANS_APP and ETRANS_PASS environment variables!")
        return

    # v2 caps textToTranslate at 5000 characters. Chunking is intentionally
    # not implemented yet -- surfaces long values so we know they exist.
    if len(text) > 5000:
        logger.warning(
            "Text to translate is %d characters (v2 limit is 5000): %s...",
            len(text), text[:200]
        )

    # The callback URL carries the translateKey so the (public) callback
    # view can validate that the request is legit.
    dest = '{}/marine/assessment-module/@@translate-callback?source_lang={}&translateKey={}'.format(
        site_url, country_code, translate_key)

    logger.info('Translate callback URL: %s', dest)

    # Store the original before submitting the request. The callback only
    # receives the short hash-based external reference.
    save_request_reference(
        external_reference,
        text,
        country_code,
        target_languages,
    )

    data = {
        'callerInformation': {
            'externalReference': external_reference,
            'username': TRANS_USERNAME,
        },
        'textToTranslate': text,
        'sourceLanguage': country_code,
        'targetLanguages': target_languages,
        'domain': DOMAIN,
        'notifications': {
            'success': {'http': dest},
            'failure': {'http': dest},
        },
        'deliveries': {
            'http': dest,
        },
    }

    resp = requests.post(
        SERVICE_URL,
        auth=None,
        headers={
            'Content-Type': 'application/json',
            'Authorization': _auth_header(),
        },
        data=json.dumps(data)
    )

    if resp.status_code == 401:
        logger.error(
            'Translation request unauthorized (401) - check ETRANS_APP / '
            'ETRANS_PASS')
        return {}

    if resp.status_code != 200:
        logger.error(
            'Translation request failed with status %s: %r',
            resp.status_code, resp.content)
        return {}

    try:
        payload = resp.json()
    except ValueError:
        logger.error('Could not parse JSON response: %r', resp.content)
        return {}

    request_id = payload.get('requestId')

    if request_id is None and payload.get('errorCode') is not None:
        logger.error(
            'Translation request error %s: %s',
            payload.get('errorCode'), payload.get('errorMessage'))
        return {}

    logger.info('Translation request accepted, requestId=%s', request_id)

    return {
        'transId': request_id,
        'externalRefId': external_reference,
    }


def handle_callback(payload, default_language=None):
    """Process a v2 callback JSON payload.

    Dispatch on the payload shape (success / delivery / failure) and persist
    the translation through the shared ``save_translation``.

    Returns True when a translation was saved.
    """

    logger.info('Translation callback (v2): %r', payload)

    external_reference = payload.get('externalReference')

    if not external_reference:
        logger.error('v2 callback missing externalReference: %r', payload)
        return False

    request_data = get_request_reference(external_reference)

    if not request_data:
        logger.error(
            'No original text found for v2 externalReference %s',
            external_reference)
        return False

    error_code = payload.get('errorCode')

    if error_code is not None:
        logger.error(
            'Translation failed (requestId=%s): %s %s',
            payload.get('requestId'), error_code,
            payload.get('errorMessage'))
        delete_request_reference(external_reference)
        return False

    # Success notification carries translatedText; a delivery callback carries
    # result (base64 for documents, raw text for snippets).
    if 'translatedText' in payload:
        translated = payload['translatedText']
    elif 'result' in payload:
        translated = payload['result']
    else:
        logger.error('Unrecognised v2 callback payload: %r', payload)
        return False

    original = request_data.get('text')
    language = payload.get('sourceLanguage')

    if not language:
        language = request_data.get('sourceLanguage') or default_language

    if not original or not language:
        logger.error(
            'Incomplete v2 request data for externalReference %s',
            external_reference)
        return False

    save_translation(original, translated, language)

    # Keep the mapping after success so a duplicate success/delivery callback
    # can resolve the original text as well.
    return True
