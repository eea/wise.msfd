# -*- coding: utf-8 -*-

from io import BytesIO
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd.compliance.interfaces import (IDescriptorFolder,
                                             INationalDescriptorAssessment,
                                             INationalDescriptorsFolder,
                                             INationalRegionDescriptorFolder)
from wise.msfd.compliance.utils import ordered_regions_sortkey
from wise.msfd.data import get_report_filename
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from lpod.document import odf_new_document
from lpod.toc import odf_create_toc

import pdfkit

from ..nationaldescriptors.a7 import Article7
from ..nationaldescriptors.a34 import Article34
from ..nationaldescriptors.base import BaseView
from .base import BaseRegSummaryView


logger = logging.getLogger('wise.msfd')


class RegionalSummaryView(BaseRegSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Regional summary report: {}".format(
                self.country_name,
            )
        )
        # trans_edit_html = self.translate_view()()

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
            url = "{}/edit".format(self._country_folder.absolute_url())
            return self.request.response.redirect(url)

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'download' in self.request.form:
            return self.download()

        if 'download_pdf' in self.request.form:
            return self.download_pdf()

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
