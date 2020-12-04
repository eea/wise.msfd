# -*- coding: utf-8 -*-

from io import BytesIO

from zope.annotation.factory import factory
from zope.component import adapter
from zope.interface import implementer, alsoProvides

from BTrees.OOBTree import OOBTree
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from persistent import Persistent
from plone.api import portal
from plone.protect.interfaces import IDisableCSRFProtection
from StringIO import StringIO

from wise.msfd.compliance.vocabulary import (
    REGIONAL_DESCRIPTORS_REGIONS,
    REGIONS, get_all_countries, ReportingHistoryENVRow,
    get_msfd_reporting_history_from_file
)
from wise.msfd.gescomponents import (GES_DESCRIPTORS, get_all_descriptors,
                                     get_descriptor)

import xlsxwriter

from .base import BaseComplianceView
from .interfaces import IRecommendationStorage
# from itertools import chain

ANNOTATION_KEY = 'wise.msfd.recommendations'
STORAGE_KEY = 'recommendations'
TOPICS_STORAGE_KEY = '__topics__'


class StartComplianceView(BaseComplianceView):
    name = 'comp-start'


class DescriptorsView(BaseComplianceView):
    name = 'comp-start'

    @property
    def descriptors(self):
        return GES_DESCRIPTORS


@implementer(IRecommendationStorage)
@adapter(IPloneSiteRoot)
class RecommendationStorage(OOBTree):
    pass


annotfactory_rec = factory(RecommendationStorage, key=ANNOTATION_KEY)


class Recommendation(Persistent):
    def __init__(self, code, topic, text, ms_region, descriptors):
        self.code = code
        self.topic = topic
        self.text = text

        if not hasattr(ms_region,  '__iter__'):
            ms_region = [ms_region]

        self.ms_region = ms_region

        if not hasattr(descriptors, '__iter__'):
            descriptors = [descriptors]

        self.descriptors = descriptors

    def data_to_list(self):
        return [
            self.code,
            self.topic,
            self.text,
            ', '.join(self.ms_region),
            ', '.join(self.descriptors)
        ]


class RecommendationsTable:
    template = PageTemplateFile('pt/recommendations-table.pt')

    def __init__(self, recommendations, show_edit_buttons):
        self.recommendations = recommendations
        self.show_edit_buttons = show_edit_buttons

    def __call__(self):
        return self.template(recommendations=self.recommendations,
                             show_edit_buttons=self.show_edit_buttons)


class RecommendationsView(BaseComplianceView):
    name = 'recommendation'
    section = 'compliance-admin'

    __topics = (
'Allocation of species to species groups',
'Assess progress with targets',
'Assessment methodology',
'Assessment scales/areas',
'Coherence of extent to which GES is achieved',
'Coherent assessment methodology',
'Coherent qualitative GES description',
'Coherent quantitative GES determination',
'Coherent set of elements',
'Coherent use of primary criteria',
'Coherent use of secondary criteria',
'Extent to which GES is achieved',
'Features and elements assessed',
'Good status based on low risk',
'Guidance on good status based on low risk',
'Guidance on quantitative GES determination',
'Integrated MSFD and Birds Directive assessments',
'Key pressures in (sub)region',
'Key pressures preventing GES',
'Link target to direct measures',
'Lists of parameters and units for reporting',
'Measurable joint targets',
'Measurable targets',
'(Sub)regional targets',
'Qualitative GES description',
'Quantify gap to GES',
'Quantitative GES determination',
'Targets for key pressures',
'Use of primary criteria',
'Use of secondary criteria',
    )

    @property
    def topics(self):
        site = portal.get()
        storage = IRecommendationStorage(site)
        topics = storage.get(TOPICS_STORAGE_KEY, [])

        return topics

    def descriptors(self):
        descriptors = get_all_descriptors()
        descriptors.pop(0)  # remove D1 general descriptor

        res = []

        for desc in descriptors:
            desc_obj = get_descriptor(desc[0])

            res.append((desc_obj.template_vars['title'], desc_obj.title))

        return res

    def regions(self):
        return [(code, name) for code, name in REGIONS.items()]

    def countries(self):
        # countries = get_all_countries()

        res = []

        for r_code, r_name in self.regions():
            countries = [
                r.countries
                for r in REGIONAL_DESCRIPTORS_REGIONS
                if r.code == r_code
            ]

            sorted_countries = countries[0]

            for c_code in sorted_countries:
                res.append(
                    "{} - {}".format(r_code, c_code)
                )

        # res_sorted = sorted(res, key=lambda i: i[0])

        return res

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, None)

        if not storage_recom:
            storage_recom = OOBTree()
            storage[STORAGE_KEY] = storage_recom

        if 'add-recommendation' in self.request.form:
            form_data = self.request.form

            code = form_data.get('rec_code', '')
            topic = form_data.get('topic', '')
            text = form_data.get('rec_text', '')
            ms_region = form_data.get('ms_or_region', [])
            descriptors = form_data.get('descriptors', [])

            recom = Recommendation(code, topic, text, ms_region, descriptors)
            storage_recom[code] = recom

        if 'edit-topics' in self.request.form:
            topics = self.request.form.get('topics', '')
            topics = topics.split('\r\n')
            storage[TOPICS_STORAGE_KEY] = topics

        recommendations = []

        if len(storage_recom.items()):
            for code, recommendation in storage_recom.items():
                recommendations.append(recommendation.data_to_list())

        sorted_rec = sorted(recommendations, key=lambda i: i[0])

        show_edit_buttons = self.can_view_assessment_data()

        self.recommendations_table = RecommendationsTable(
            recommendations=sorted_rec, show_edit_buttons=show_edit_buttons
        )

        return self.index()


class ViewComplianceModule(BaseComplianceView):
    # name = 'comp-start2'

    @property
    def national_descriptors(self):
        pass

    @property
    def regional_descriptors(self):
        pass

    # def get_folder_by_id(self, id):
    #     folders = [
    #         x.contentValues()
    #
    #         for x in self.context.contentValues()
    #
    #         if x.portal_type == 'Folder'
    #         and x.id == id
    #     ]
    #     folders = [f for f in chain(*folders)]
    #
    #     return folders
    #
    # @property
    # def regional_descriptors_folders(self):
    #     id = 'regional-descriptors-assessments'
    #     folders = self.get_folder_by_id(id)
    #
    #     return folders
    #
    # @property
    # def national_descriptors_folders(self):
    #     id = 'national-descriptors-assessments'
    #     folders = self.get_folder_by_id(id)
    #
    #     return folders


class MSFDReportingHistoryView(BaseComplianceView):
    name = 'msfd-reporting-history'
    section = 'compliance-admin'

    column_widths = {
        'DateDue': '100px',
        'DateReceived': '100px',
        'MSFDArticle(year)': '200px',
        'ReportType': '250px',
    }

    @property
    def _msfd_rep_history_data(self):
        """ all data including the headers """

        return self.context._msfd_reporting_history_data

    @property
    def msfd_rep_history_headers(self):
        return self._msfd_rep_history_data[0]

    @property
    def msfd_rep_history_data(self):
        """ only the data, without headers """

        return self._msfd_rep_history_data[1:]

    @property
    def msfd_file(self):
        return self.context.msfd_reporting_history_xml

    def setup_msfd_data(self):
        file_obj = StringIO(self.msfd_file.data)
        data = get_msfd_reporting_history_from_file(file_obj)

        self.context._msfd_reporting_history_filename = self.msfd_file.filename
        self.context._msfd_reporting_history_data = data
        self._p_changed = True

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = 'ENV'
        worksheet = workbook.add_worksheet(unicode(wtitle)[:30])

        row_index = 0

        for row in data:
            for i, value in enumerate(row):
                worksheet.write(row_index, i, unicode(value or ''))

            row_index += 1

        workbook.close()
        out.seek(0)

        return out

    def download(self):
        xlsdata = self._msfd_rep_history_data

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["MSFDReportingHistory",
                          'date_here'])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def __call__(self):
        form_data = self.request.form

        if 'download-excel' in form_data:
            return self.download()

        if self.msfd_file:
            old_filename = getattr(self.context,
                                   '_msfd_reporting_history_filename', u'')
            new_filename = self.msfd_file.filename

            if new_filename != old_filename:
                self.setup_msfd_data()

        if 'add-msfd-data' in form_data:
            index = int(form_data.get('Row'))

            _data = [
                form_data.get(f)
                for f in self.msfd_rep_history_headers
            ]
            new_data = ReportingHistoryENVRow(*_data)

            if index == len(self._msfd_rep_history_data):
                self._msfd_rep_history_data.append(new_data)
            else:
                self._msfd_rep_history_data[index] = new_data

            self._p_changed = True

        return self.index()
