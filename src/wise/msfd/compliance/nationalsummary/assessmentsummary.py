# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import datetime
from io import BytesIO
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from Products.statusmessages.interfaces import IStatusMessage
from plone.api import portal
from wise.msfd.compliance.interfaces import (INationalSummaryCountryFolder,
                                             INationalSummaryEdit,
                                             IRecommendationStorage)
from wise.msfd.compliance.main import RecommendationsTable, STORAGE_KEY
from wise.msfd.compliance.vocabulary import get_regions_for_country
from wise.msfd.data import get_report_filename
from wise.msfd.gescomponents import DESCRIPTOR_TYPES
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from zope.interface import implements

from lpod.document import odf_new_document
from lpod.toc import odf_create_toc

import pdfkit

from ..nationaldescriptors.a7 import Article7
from ..nationaldescriptors.a34 import Article34
from ..nationaldescriptors.base import BaseView
from .base import BaseNatSummaryView
from .descriptor_assessments import DescriptorLevelAssessments
from .introduction import Introduction
from .odt_utils import (create_heading, create_paragraph,
                        create_table_summary, setup_document_styles)

logger = logging.getLogger('wise.msfd')


class AssessmentExportCover(BaseNatSummaryView):

    template = ViewPageTemplateFile('pt/cover.pt')

    def authors(self):
        field = 'authors'
        value = self.get_field_value(field)

        return value

    def contract(self):
        field = 'contract'
        value = self.get_field_value(field)

        return value

    def logos(self):
        field = 'logo'
        value = self.get_field_value(field)

        if '../' in value:
            return None

        if value == '-':
            return None

        return value

    def authors_logos(self):
        """ Not used anymore """
        portal_catalog = portal.get_tool('portal_catalog')
        brains = portal_catalog.searchResults(
            object_provides=INationalSummaryEdit.__identifier__
        )
        edit_page = brains[0].getObject()
        # edit_page = self.context.aq_parent['edit-summary']

        attr = 'authors_logo'
        authors_logo = getattr(edit_page, attr, '')

        if not authors_logo:
            return ''

        return authors_logo.output

    def assess_date(self):
        attr = 'date_assessed'
        if not hasattr(self._country_folder, attr):
            return '-'

        date_assessed = getattr(self._country_folder, attr)
        # date_assessed = self._format_date(date_assessed)

        return date_assessed

    def __call__(self):
        return self.template(date=self.assess_date())


class SummaryAssessment(BaseNatSummaryView):
    """ Implementation of section 2. Summary of the assessment """

    template = ViewPageTemplateFile('pt/summary-assessment.pt')
    descriptor_types = DESCRIPTOR_TYPES

    def __init__(self, context, request, overall_scores,
                 nat_desc_country_folder, year='2018'):
        super(SummaryAssessment, self).__init__(context, request)

        self.overall_scores = overall_scores
        self.nat_desc_country_folder = nat_desc_country_folder
        self.year = year

    @property
    def intro_text(self):
        text = "The table shows the overall conclusions on the adequacy, " \
               "consistency, and coherence of the information reported by " \
               "the Member State for each descriptor and article. In cases " \
               "where the Member State's marine waters lie in several " \
               "marine regions or subregions, the conclusions are presented " \
               "separately."

        return text

    @property
    def summary_of_assessment_text(self):
        output = self.get_field_value('summary_of_assessment_text')

        return output

    def get_overall_score(self, region_code, descriptor, article):
        __key = (region_code, descriptor, article, self.year)
        color = self.overall_scores[__key][1]
        conclusion = self.overall_scores[__key][0]
        # conclusion = conclusion.split(' ')
        # conclusion = " ".join(conclusion[:-1])

        return conclusion, color

    def setup_data(self):
        res = []
        region_folders = self.get_region_folders(self.nat_desc_country_folder)

        for region_folder in region_folders:
            table_rows = []
            descr_folders = self.get_descr_folders(region_folder)

            for descr_type, descriptors in self.descriptor_types:
                descr_rows = []

                for descr in descriptors:
                    descr_folder = [
                        d
                        for d in descr_folders
                        if d.id.upper() == descr
                    ][0]
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

                    descr_rows.append(row)

                table_rows.append((descr_type, descr_rows))

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


class Recommendations(BaseNatSummaryView):
    template = ViewPageTemplateFile('pt/recommendations.pt')

    def __call__(self):
        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, {})

        data_by_region = defaultdict(list)
        regions = get_regions_for_country(self.country_code)
        region_codes = set([r_code for r_code, r_name in regions])

        if not len(storage_recom.items()):
            return self.template(
                data=[(r_name, '-') for r_code, r_name in regions]
            )

        for rec_code, recommendation in storage_recom.items():
            ms_region = recommendation.ms_region

            for region_code in region_codes:
                r_code_c_code = "{} - {}".format(region_code,
                                                 self.country_code)

                if r_code_c_code in ms_region:
                    data_by_region[region_code].append(
                        recommendation.data_to_list())
                    continue

        res = []

        for region_code, region_name in regions:
            rec = data_by_region[region_code]
            sorted_rec = sorted(rec, key=lambda i: i[0])

            recomm_table = RecommendationsTable(
                recommendations=sorted_rec, show_edit_buttons=False
            )

            res.append((region_name, recomm_table()))

        return self.template(data=res)


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


class AssessmentSummaryView(BaseNatSummaryView):
    implements(INationalSummaryCountryFolder)

    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    report_header_template = ViewPageTemplateFile(
        'pt/assessment-export-header.pt'
    )
    year = "2012"

    render_header = True

    def _get_css(self):
        return [
            resource_filename('wise.msfd',
                              'static/wise/dist/css/compliance.css'),
            resource_filename('wise.msfd',
                              'static/wise/dist/css/pdf_export.css'),
        ]

    def _get_cover(self):
        absolute_url = self.context.absolute_url()
        cover_url = absolute_url + '/export-cover'

        if 'localhost' in absolute_url:
            cover_url = 'https://water.europa.eu/marine/assessment-module/' \
                        'national-summaries/lv/export-cover'
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
            'footer-font-size': '7',
            'footer-right': '[page]',
            'encoding': "UTF-8",
            'load-error-handling': 'ignore',
            # 'load-media-error-handling': 'ignore'
        }
        css = self._get_css()
        cover = self._get_cover()
        toc = self._get_toc()
        path_wkhtmltopdf = '/plone/instance/parts/wkhtmltopdf/wkhtmltopdf'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        doc = pdfkit.from_string(
            self.report_html, False, options=options,
            cover=cover,
            toc=toc,
            css=css,
            cover_first=True,
            configuration=config
        )
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/pdf')
        fname = "{}-{}-{}".format(
            self.country_name, self.get_status().title().replace(' ', ''),
            str(datetime.now().date())
        )
        sh('Content-Disposition',
           'attachment; filename=%s.pdf' % fname)

        return doc

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Commission assessment / Art12 / 2018 / {}-summary".format(
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
            descriptor_lvl_assess,
            # trans_edit_html,
        ]

        if self.render_header:
            # 5. Recommendations table
            recomm_table = Recommendations(self, self.request)

            self.tables.append(recomm_table)

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
