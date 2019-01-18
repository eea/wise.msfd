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
    if not target_languages:
        target_languages = ['EN']

    # externalReference = self.request.form.get('externalReference', '')

    site = portal.getSite()
    marine_url = site.Plone.marine.absolute_url()

    if 'europa.eu' in marine_url:
        dest = marine_url + \
            '/translation-callback2?source_lang={}'.format(country_code)
    else:
        dest = 'http://office.pixelblaster.ro:4880/Plone/marine' + \
            '/translation-callback2?source_lang={}'.format(country_code)

    logger.info('Translate callback destination: %s', dest)

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

    result = requests.post(SERVICE_URL,
                           auth=HTTPDigestAuth('Marine_EEA_20180706',
                                               MARINE_PASS),
                           data=dataj,
                           headers=headers)

    res = {
        "transId": result.content,
        "externalRefId": text
    }

    # res = {'translation': 'Translation in progress!'}

    logger.info('Translate request sent: %s', res)

    return json.dumps(res)
