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
from .base import BaseNatSummaryView
from .descriptor_assessments import DescriptorLevelAssessments
from .introduction import Introduction
from .odt_utils import (create_heading, create_paragraph, create_table,
                        create_table_summary, setup_document_styles)

logger = logging.getLogger('wise.msfd')


class NationalSummaryCover(BaseNatSummaryView):

    template = ViewPageTemplateFile('pt/cover.pt')

    def assess_date(self):
        attr = 'date_assessed'
        if not hasattr(self._country_folder, attr):
            return '-'

        date_assessed = getattr(self._country_folder, attr)
        date_assessed = self._format_date(date_assessed)

        return date_assessed

    def __call__(self):
        return self.template(date=self.assess_date())


class SummaryAssessment(BaseNatSummaryView):
    """ Implementation of section 2. Summary of the assessment """

    template = ViewPageTemplateFile('pt/summary-assessment.pt')

    def __init__(self, context, request, overall_scores,
                 nat_desc_country_folder):
        super(SummaryAssessment, self).__init__(context, request)

        self.overall_scores = overall_scores
        self.nat_desc_country_folder = nat_desc_country_folder

    def get_region_folders(self, country_folder):
        region_folders = self.filter_contentvalues_by_iface(
            country_folder, INationalRegionDescriptorFolder
        )

        region_folders_sorted = sorted(
            region_folders, key=lambda i: ordered_regions_sortkey(i.id.upper())
        )

        return region_folders_sorted

    def get_descr_folders(self, region_folder):
        contents = self.filter_contentvalues_by_iface(
            region_folder, IDescriptorFolder
        )

        # D1 Biodiversity is redundant as assessments are all at finer level
        filtered_contents = [x for x in contents if x.id != 'd1']

        return filtered_contents

    def get_article_folders(self, descr_folder):
        article_folders = self.filter_contentvalues_by_iface(
            descr_folder, INationalDescriptorAssessment
        )

        article_folders = sorted(
            article_folders,
            key=lambda i: fixedorder_sortkey(i.title, self.ARTICLE_ORDER)
        )

        return article_folders

    def get_overall_score(self, region_code, descriptor, article):
        color = self.overall_scores[(region_code, descriptor, article)][1]
        conclusion = self.overall_scores[(region_code, descriptor, article)][0]
        # conclusion = conclusion.split(' ')
        # conclusion = " ".join(conclusion[:-1])

        return conclusion, color

    def setup_data(self):
        res = []
        region_folders = self.get_region_folders(self.nat_desc_country_folder)

        for region_folder in region_folders:
            table_rows = []

            for descr_folder in self.get_descr_folders(region_folder):
                # Remove brackets with text from descriptor title
                # D4 - Food webs/D1 Biodiversity - ecosystems (D4/D1)
                descriptor_title = descr_folder.title.split('(')[0]
                row = [descriptor_title]

                for article_folder in self.get_article_folders(descr_folder):
                    score = self.get_overall_score(
                        region_folder.id.upper(), descr_folder.id.upper(),
                        article_folder.title
                    )

                    row.append(score)

                table_rows.append(row)

            res.append((region_folder.title, table_rows))

        self.summary_assess_data = res

        return res

    def get_odt_data(self, document):
        res = []
        headers = ('Descriptor', 'Article 9 - GES Determination',
                   'Article 8 - Initial Assessment',
                   'Article 10 - Environmental Targets')

        t = create_heading(1, u"Summary of the assessment")
        res.append(t)

        for region_row in self.summary_assess_data:
            t = create_heading(2, region_row[0])
            res.append(t)

            table_rows = region_row[1]

            # TODO split score , it is a tuple (conclusion, color_value)
            # and somehow color the table cells
            table = create_table_summary(document, table_rows, headers=headers)
            res.append(table)

        return res

    def __call__(self):

        @timeit
        def render_summary_assessment():
            self.setup_data()
            return self.template()

        return render_summary_assessment()


class ProgressAssessment(BaseNatSummaryView):
    """ implementation of section 3. Assessment of national
    progress since 2012
    """

    template = ViewPageTemplateFile('pt/progress-assessment.pt')

    @property
    def progress_recommendations_2012(self):
        progress = self.get_field_value('progress_recommendations_2012')

        return progress

    @property
    def progress_recommendations_2018(self):
        progress = self.get_field_value('progress_recommendations_2018')

        return progress

    def get_odt_data(self, document):
        res = []

        h = create_heading(1, "Assessment of national progress since 2012")
        res.append(h)

        t = create_heading(2, "2012 recommendations to Member State")
        res.append(t)
        text = self.get_transformed_richfield_text(
            'progress_recommendations_2012'
        )
        p = create_paragraph(text)
        res.append(p)

        t = create_heading(
            2, "Progress against 2012 recommendations to Member State"
        )
        res.append(t)
        text = self.get_transformed_richfield_text(
            'progress_recommendations_2018'
        )
        p = create_paragraph(text)
        res.append(p)

        return res

    def __call__(self):

        @timeit
        def render_progress_assessment():
            return self.template()

        return render_progress_assessment()


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


class NationalSummaryView(BaseNatSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    def _get_css(self):
        return [
            resource_filename('wise.theme',
                              'static/wise/css/main.css'),
            resource_filename('wise.msfd',
                              'static/wise/dist/css/compliance.css'),
        ]

    def _get_cover(self):
        absolute_url = self.context.absolute_url()
        cover_url = absolute_url + '/nat-sum-cover'

        if 'localhost' in absolute_url:
            cover_url = cover_url.replace('localhost:5080',
                                          'office.pixelblaster.ro:4880')

        return cover_url

    def _get_toc(self):
        xsl_file = resource_filename('wise.msfd', 'data/pdf_toc.xsl'),

        toc = {"xsl-style-sheet": xsl_file}

        return toc

    def get_document(self):
        result = BytesIO()
        document = odf_new_document('text')
        setup_document_styles(document)
        body = document.get_body()

        # Create the Table Of Content
        toc = odf_create_toc()
        # Changing the default "Table Of Content" Title :
        toc.set_title("Table of Content")

        # Do not forget to add every components to the document:
        body.append(toc)

        for table in self.tables:
            if hasattr(table, 'get_odt_data'):
                odt_data = table.get_odt_data(document)

                body.extend(odt_data)

        toc.fill()

        document.save(target=result, pretty=True)

        return result.getvalue()

    def download(self):
        doc = self.get_document()
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.oasis.opendocument.text')
        fname = "{}-Draft".format(self.country_name)
        sh('Content-Disposition',
           'attachment; filename=%s.odt' % fname)

        return doc

    def download_pdf(self):
        options = {
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            # 'footer-left': "Page",
            'footer-font-size': '7',
            'footer-right': 'Page [page] of [topage]',
            'encoding': "UTF-8",
        }
        css = self._get_css()
        cover = self._get_cover()
        toc = self._get_toc()

        doc = pdfkit.from_string(
            self.report_html, False, options=options,
            cover=cover,
            toc=toc,
            css=css,
            cover_first=True
        )
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/pdf')
        fname = "{}-Draft".format(self.country_name)
        sh('Content-Disposition',
           'attachment; filename=%s.pdf' % fname)

        return doc

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="National summary report: {}".format(
                self.country_name,
            )
        )
        # trans_edit_html = self.translate_view()()

        # 4. Descriptor-level assessments
        descriptor_lvl_assess = DescriptorLevelAssessments(self, self.request)
        descriptor_lvl_assess_view = descriptor_lvl_assess()
        overall_scores = descriptor_lvl_assess.overall_scores
        nat_desc_country_folder = descriptor_lvl_assess.nat_desc_country_folder

        # 1. Introduction
        introduction = Introduction(self.context, self.request)

        # 2. Summary Assessment
        sum_assess = SummaryAssessment(self, self.request, overall_scores,
                                       nat_desc_country_folder)

        # 3. Progress Assessment
        prog_assess = ProgressAssessment(self, self.request)
        
        self.tables = [
            report_header,
            introduction,
            sum_assess,
            prog_assess,
            descriptor_lvl_assess
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

        if 'download_pdf' in self.request.form:
            self.render_header = False

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
