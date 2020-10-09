# -*- coding: utf-8 -*-

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from wise.msfd.data import get_report_filename
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from ..nationaldescriptors.a7 import Article7
from ..nationaldescriptors.a34 import Article34
from ..nationaldescriptors.base import BaseView
from .base import BaseNatSummaryView

logger = logging.getLogger('wise.msfd')


class Article34Copy(Article34):
    """ Class to override the template """
    template = ViewPageTemplateFile('pt/report-data-secondary.pt')
    title = "Articles 3 & 4 Marine regions"


class Article7Copy(Article7):
    """ Class to override the template """
    template = ViewPageTemplateFile('pt/report-data-secondary.pt')
    title = "Article 7 Competent authorities"


class ArticleTable(BaseView):
    impl = {
        'Art3': Article34Copy,
        'Art4': Article34Copy,
        'Art7': Article7Copy,
    }

    is_translatable = True

    def __init__(self, context, request, article):
        super(ArticleTable, self).__init__(context, request)

        self._article = article
        self.klass = self.impl[article]

    year = '2012'

    @property
    def article(self):
        return self._article

    @property
    def descriptor(self):
        return 'Not linked'

    @property
    def muids(self):
        return []

    @property
    def country_region_code(self):
        return 'No region'

    def get_article_title(self, klass):
        tmpl = u"<h4>{}</h4>"
        title = klass.title

        return tmpl.format(title)

    def get_report_filename(self, art=None):
        # needed in article report data implementations, to retrieve the file

        return get_report_filename(
            self.year, self.country_code, self.country_region_code,
            art or self.article, self.descriptor
        )

    def __call__(self):
        try:
            self.view = self.klass(
                self, self.request, self.country_code,
                self.country_region_code, self.descriptor, self.article,
                self.muids
            )
            rendered_view = self.view()
        except:
            rendered_view = 'Error getting report'

        return self.get_article_title(self.klass) + rendered_view


class NationalOverviewView(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    def title(self):
        title = u"National overview: {}".format(self.country_name)

        return title

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="National summary report: {}".format(
                self.country_name,
            )
        )
        self.tables = [
            report_header,
            # ArticleTable(self, self.request, 'Art7'),
            # ArticleTable(self, self.request, 'Art3-4'),
            # trans_edit_html,
        ]

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self.absolute_url())

            return self.request.response.redirect(url)

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'translate' in self.request.form:
            for value in self._translatable_values:
                retrieve_translation(self.country_code, value)

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        @timeit
        def render_html():
            return self.index()

        return render_html()
