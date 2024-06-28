#pylint: skip-file
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import pathlib

from datetime import datetime
from io import BytesIO

from zope.annotation.factory import factory
from zope.component import adapter
from zope.interface import alsoProvides, implementer

from BTrees.OOBTree import OOBTree
# from Products.Five.browser.pagetemplatefile import PageTemplateFile
from chameleon.zpt.template import PageTemplateFile
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from persistent import Persistent
from pkg_resources import resource_filename
from plone.api import portal
from plone.protect.interfaces import IDisableCSRFProtection

from wise.msfd.compliance.vocabulary import (
    REGIONAL_DESCRIPTORS_REGIONS,
    REGIONS, ReportingHistoryENVRow,
    get_msfd_reporting_history_from_file
)
from wise.msfd.gescomponents import (GES_DESCRIPTORS, get_all_descriptors,
                                     get_descriptor)

import xlsxwriter

from .base import BaseComplianceView
from .interfaces import IRecommendationStorage
import six
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
    def __init__(self, id_rec, code, topic, text, ms_region, descriptors):
        self._id_recommendation = id_rec
        self.code = code
        self.topic = topic
        self.text = text

        if not isinstance(ms_region, (list, tuple)):
            ms_region = [ms_region]

        self.ms_region = ms_region

        if not isinstance(descriptors, (list, tuple)):
            descriptors = [descriptors]

        self.descriptors = descriptors

    def data_to_list(self):
        return [
            getattr(self, '_id_recommendation', '0'),
            self.code,
            self.topic,
            self.text,
            ', '.join(self.ms_region),
            ', '.join(self.descriptors)
        ]


class RecommendationsTable:
    template = PageTemplateFile(
        os.path.join(str(pathlib.Path(__file__).parent.resolve()),
        'pt/recommendations-table.pt'))

    def __init__(self, recommendations, show_edit_buttons):
        self.recommendations = recommendations
        self.show_edit_buttons = show_edit_buttons

    def __call__(self):
        return self.template(recommendations=self.recommendations,
                             show_edit_buttons=self.show_edit_buttons)


class RecommendationsView(BaseComplianceView):
    name = 'recommendation'
    section = 'compliance-admin'
    headers = [
        'Recommendation code', 'Topic', 'Recommendation text',
        'Applicable MS or (sub)region', 'Applicable descriptors', 'Edit'
    ]

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

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = 'Recommendations'
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])

        for i, value in enumerate(self.headers):
                worksheet.write(0, i, six.text_type(value or ''))

        row_index = 1

        for row in data:
            for i, value in enumerate(row):
                worksheet.write(row_index, i, six.text_type(value or ''))

            row_index += 1

        workbook.close()
        out.seek(0)

        return out
    def download(self, xlsdata):
        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(["COM_Art12_2018_Recommendations",
                          str(datetime.now().replace(microsecond=0))])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        site = portal.get()
        storage = IRecommendationStorage(site)
        storage_recom = storage.get(STORAGE_KEY, None)
        
        if 'migrate-recommendations' in self.request.form:
            new_recommendations = []

            for i, (_, recommendation) in enumerate(storage_recom.items()):
                id_recom = str(i + 1)
                rec_code = recommendation.code.split('/')

                if len(rec_code) == 4:
                    rec_code = "/".join((
                        rec_code[0], rec_code[1], rec_code[3].strip()
                        ))
                else:
                    rec_code = "/".join(rec_code)

                recommendation = Recommendation(
                    id_recom, 
                    rec_code, 
                    recommendation.topic, 
                    recommendation.text, 
                    recommendation.ms_region, 
                    recommendation.descriptors
                    )
                # storage_recom.pop(recommendation.code, None)    
                # storage_recom.pop(id_recom, None)
                # storage_recom.pop(int(id_recom), None)        
                
                new_recommendations.append(recommendation)

            # asd = [x for x in storage_recom.keys()]
            # asdf = [x._id_recommendation for x in new_recommendations]
            # import pdb; pdb.set_trace()

            storage_recom = OOBTree()
            storage[STORAGE_KEY] = storage_recom

            for new_rec in new_recommendations:
                id_recom = new_rec._id_recommendation
                storage_recom[id_recom] = new_rec

        if not storage_recom:
            storage_recom = OOBTree()
            storage[STORAGE_KEY] = storage_recom

        if 'add-recommendation' in self.request.form:
            form_data = self.request.form

            id_recom = form_data.get('rec_id', '')
            code = form_data.get('rec_code', '')
            topic = form_data.get('topic', '')
            text = form_data.get('rec_text', '')
            ms_region = form_data.get('ms_or_region', [])
            descriptors = form_data.get('descriptors', [])

            if not id_recom:
                max_id = max([
                    int(_rec._id_recommendation)
                    for _code, _rec in storage_recom.items()
                ])

                id_recom = str(int(max_id) + 1)
            
            recom = Recommendation(
                id_recom, code, topic, text, ms_region, descriptors)

            storage_recom[id_recom] = recom

        if 'remove-recommendation' in self.request.form:
            form_data = self.request.form
            
            id_recom = form_data.get('rec_id', '')
            storage_recom.pop(id_recom)

        if 'edit-topics' in self.request.form:
            topics = self.request.form.get('topics', '')
            topics = topics.split('\r\n')
            storage[TOPICS_STORAGE_KEY] = topics

        recommendations = []

        if len(list(storage_recom.items())):
            for code, recommendation in storage_recom.items():
                recommendations.append(recommendation.data_to_list())

        sorted_rec = sorted(recommendations, key=lambda i: i[0])

        if 'download-excel' in self.request.form:
            return self.download(sorted_rec)

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
        'MSFD Article': '120px'
    }

    blacklist_headers = ['Sort', 'CIRCABC', 'WISE', 'ARES', 'Comments']

    @property
    def _msfd_rep_history_data(self):
        """ all data including the headers """
        data = self.context._msfd_reporting_history_data
        
        return data

    def msfd_rep_history_headers(self, use_blacklist=True):
        """ Used to display the headers in the table """
        # do not show these columns
        blacklist_headers = self.blacklist_headers
        headers = (
            self._msfd_rep_history_data 
            and self._msfd_rep_history_data[0] or [])

        if use_blacklist:
            headers = [
                x for x in headers
                if x not in blacklist_headers
            ]

        return headers

    @property
    def msfd_rep_history_columns(self):
        """ Define the columns displayed in the table """
        # do not show these columns
        # blacklist_headers = self.blacklist_headers
        # fields = self._msfd_rep_history_data[1]._fields
        # columns = set(fields) - set(blacklist_headers)

        columns = ['Year', 'MSFDArticle', 'TaskProduct', 'ReportType', 
            'DateDue', 'DateReceived', 'CountryCode', 'FileName', 
            'LocationURL'] 

        return columns

    @property
    def msfd_rep_history_data(self):
        """ Used when displaying the data in the table
        Here we filter the rows, hide rows where only ARES = Yes
        """

        data = self._msfd_rep_history_data[1:]
        res = []

        for index, report_row in enumerate(data):
            if (report_row.ARES == 'Yes' and not report_row.CIRCABC 
                and not report_row.WISE):
                continue

            res.append((index, report_row))

        return res

    @property
    def msfd_file(self):
        return self.context.msfd_reporting_history_xml

    def setup_msfd_data(self):
        file_obj = BytesIO(self.msfd_file.data)
        data = get_msfd_reporting_history_from_file(file_obj)

        self.context._msfd_reporting_history_filename = self.msfd_file.filename
        self.context._msfd_reporting_history_data = data
        # save to disk
        self.save_to_localfile()

        self._p_changed = True

    def save_to_localfile(self):
        data = self._msfd_rep_history_data

        file_loc = resource_filename(
            'wise.msfd', 'data/MSFDReportingHistory_Local.xlsx'
        )
        workbook = xlsxwriter.Workbook(file_loc)
        wtitle = 'ENV'
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])
        row_index = 0

        for row in data:
            for i, value in enumerate(row):
                worksheet.write(row_index, i, six.text_type(value or ''))

            row_index += 1

        workbook.close()

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        wtitle = 'ENV'
        worksheet = workbook.add_worksheet(six.text_type(wtitle)[:30])

        row_index = 0

        for row in data:
            for i, value in enumerate(row):
                worksheet.write(row_index, i, six.text_type(value or ''))

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
                          str(datetime.now().replace(microsecond=0))])
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return xlsio.read()

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        form_data = self.request.form

        if 'force-setup' in form_data:
            self.setup_msfd_data()

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
                form_data.get(f, '')
                for f in self.msfd_rep_history_headers(False)
            ]
            new_data = ReportingHistoryENVRow(*_data)

            if index == len(self._msfd_rep_history_data):
                self._msfd_rep_history_data.append(new_data)
            else:
                self._msfd_rep_history_data[index] = new_data

            self.save_to_localfile()
            self._p_changed = True

        return self.index()
