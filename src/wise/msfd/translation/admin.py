
from io import BytesIO

import json
import logging
from datetime import datetime

from pkg_resources import resource_filename
from plone.api import portal
from plone.protect.interfaces import IDisableCSRFProtection
from pyexcel_xlsx import get_data

from zope import event
from zope.interface import alsoProvides

from eea.cache.event import InvalidateMemCacheEvent
from Products.Five.browser import BrowserView

import xlsxwriter

from . import normalize, save_translation, retrieve_translation
from .interfaces import ITranslationsStorage

logger = logging.getLogger('wise.msfd.translation')


class TranslationsOverview(BrowserView):
    """ Translations overview page
    """

    @property
    def get_root(self):
        return portal.get()

    def languages(self):
        return ITranslationsStorage(self.get_root).keys()

    def available_translations(self, selected_lang=None):
        storage = ITranslationsStorage(self.get_root)

        if not selected_lang:
            selected_lang = self.request.form.get('language')

        langstore = storage.get(selected_lang, {})

        return langstore

    def edit_translation(self):
        form = self.request.form

        language = form.get('language')
        original = form.get('original')  # .decode('utf-8')
        original = normalize(original)
        translated = form.get('tr-new').decode('utf-8')

        save_translation(original, translated, language, approved=True)

        deps = ['translation']
        event.notify(InvalidateMemCacheEvent(raw=True, dependencies=deps))

        logger.info('Invalidate cache for dependencies: %s', ', '.join(deps))

        response = self.request.response
        response.addHeader('Content-Type', 'application/json')

        return json.dumps({'text': translated})

    def add_translation(self):

        form = self.request.form

        language = form.get('language')
        original = form.get('original')  # .decode('utf-8')
        original = normalize(original)
        translated = form.get('translated').decode('utf-8')

        save_translation(original, translated, language, approved=True)

        url = './@@translations-overview?language=' + language

        return self.request.response.redirect(url)

    def approve_translations(self):
        form = self.request.form

        language = form.get('language')
        approved = form.get('approved')  # .decode('utf-8')

        url = './@@translations-overview?language=' + language

        if not approved:
            return self.request.response.redirect(url)

        if isinstance(approved, basestring):
            approved = [approved]

        storage = ITranslationsStorage(self.get_root)
        selected_lang = self.request.form.get('language')

        langstore = storage.get(selected_lang, {})

        for label in approved:
            label = label.decode('utf-8')
            translation = langstore[label]

            if translation.text.startswith('?'):
                translation.text = translation.text[1:]

            translation.approved = True
            translation.modified = datetime.now()

        return self.request.response.redirect(url)

    def export_translations(self):
        data = []

        for language in self.languages():
            transl_data = self.available_translations(language)
            translations = [
                (language, unicode(k), unicode(v), v.approved)
                for k, v in transl_data.items()
            ]
            data.extend(translations)

        # data to xls
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = 'translations'
        worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

        row_index = 0

        for row in data:
            for i, value in enumerate(row):
                worksheet.write(row_index, i, value or '')

            row_index += 1

        workbook.close()
        out.seek(0)

        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["MSFDTranslations", ])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return out.read()

    def import_translations(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        file_loc = resource_filename(
            'wise.msfd', 'data/MSFDTranslations.xlsx'
        )

        with open(file_loc, 'rb') as file:
            sheets = get_data(file)
            transl_data = sheets['translations']

            for row in transl_data:
                try:
                    lang = row[0]
                    orig = row[1]
                    transl = row[2]
                    approved = len(row) == 4 and int(row[3]) or 0

                    save_translation(orig, transl, lang, approved=approved)
                except:
                    pass

    def __call__(self):

        if 'translate' in self.request.form:
            translations = self.available_translations()

            for orig, transl in translations.items():
                if getattr(orig, 'approved', False):
                    continue

                language = self.request.form.get('language', None)

                if not language:
                    continue

                retrieve_translation(language, orig, ['EN'], force=True)

            pass

        return self.index()
