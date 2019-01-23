import json
import logging
import os

import requests
from requests.auth import HTTPDigestAuth

from plone.api import portal

env = os.environ.get

# TODO: get another username?
TRANS_USERNAME = 'ipetchesi'
MARINE_PASS = env('MARINE_PASS', '')
SERVICE_URL = 'https://webgate.ec.europa.eu/etranslation/si/translate'

logger = logging.getLogger('wise.msfd.translation')


def retrieve_translation(country_code, text, target_languages=None):

    # externalReference = self.request.form.get('externalReference', '')

    site_url = portal.getSite().absolute_url()

    if 'localhost' in site_url:
        logger.warning("Using localhost, won't retrieve translation for: %s",
                       text
                       )

        return '{}'

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
