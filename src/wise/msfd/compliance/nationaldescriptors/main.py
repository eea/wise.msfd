# pylint: skip-file
""" Classes and views to implement the National Descriptors compliance page
"""

from __future__ import absolute_import
from collections import namedtuple
from logging import getLogger

import re

from zope.interface import implementer

from plone.api import portal
from plone.api.content import transition
from plone.api.portal import get_tool
from Products.statusmessages.interfaces import IStatusMessage

from wise.msfd import db, sql2018
from wise.msfd.compliance.base import is_row_relevant_for_descriptor
from wise.msfd.compliance.utils import ordered_regions_sortkey
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.data import get_text_reports_2018
from wise.msfd.gescomponents import get_descriptor, get_features
from wise.msfd.compliance.nationaldescriptors.base import BaseView
from wise.msfd.compliance.interfaces import (
    ICountryDescriptorsFolder, ICountryStartReports, IMSFDReportingHistoryFolder)


logger = getLogger('wise.msfd')

RE_REGION_NORM = re.compile(r'^[A-Z]{3}\s')

CROSS_CUTTING_SECTIONS = (
    ("Socio-economic assessment", ["Ad11E", "Ad12E"]),
    ("Impact of climate change", ["Ad13F",]),
    ("Funding of the measures", ["Ad14G", "Ad15G"]),
    ("Links to other policies", ["Ad16G", "Ad17G", "Ad18G"]),
    ("Regional cooperation and transboundary impacts", ["Ad19H", "Ad20H"]),
    ("Public consultation", ["Ad21I", "Ad22I"]),
    ("Administrative processes", ["Ad23J", "Ad24J"]),
)

Assessment = namedtuple('Assessment',
                        [
                            'gescomponents',
                            'answers',
                            'assessment_summary',
                            'recommendations',
                            'phase_overall_scores',
                            'overall_score',
                            'overall_conclusion',
                            'overall_conclusion_color',
                            'progress'
                        ])

AssessmentRow = namedtuple('AssessmentRow',
                           [
                               'question',
                               'summary',
                               'conclusion',
                               'conclusion_color',
                               'score',
                               'values'
                           ])

CountryStatus = namedtuple('CountryStatus',
                           ['code', 'name', 'status', 'state_id', 'url'])


@db.use_db_session('2018')
def get_assessment_head_data_2012(article, region, country_code):

    t = sql2018.COMGeneral
    count, res = db.get_all_records(
        t,
        t.CountryCode == country_code,
        t.MSFDArticle == article,
        t.RegionSubregion.startswith(region),
        # t.RegionSubregion == region + country_code,
        t.AssessmentTopic == 'GES Descriptor'
    )

    # assert count == 1
    # Removed condition because of spain RegionSubregion
    # ABIES - NOR and ABIES - SUD

    if count:
        # report_by = res[0].ReportBy
        report_by = 'Commission'
        assessors = res[0].Assessors
        assess_date = res[0].DateAssessed
        com_report = res[0].CommissionReport

        return (report_by,
                assessors,
                assess_date,
                (com_report.split('/')[-1], com_report))

    return ['Not found'] * 3 + [('Not found', '')]


class NationalDescriptorsOverview(BaseView):
    section = 'national-descriptors'
    iface_country_folder = ICountryDescriptorsFolder

    def countries(self):
        countries = self.context.contentValues()
        res = []

        for country in countries:
            if not self.iface_country_folder.providedBy(country):
                continue

            state_id, state_label = self.process_phase(country)
            info = CountryStatus(country.id.upper(), country.Title(),
                                 state_label, state_id, country.absolute_url())

            res.append(info)

        return res


class NationalDescriptorCountryOverview(BaseView):
    section = 'national-descriptors'

    def root_url(self):
        # return the url of the assessment module
        site = portal.get()
        url = site.absolute_url()

        final_url = url + "/marine/assessment-module"

        return final_url

    @property
    def is_search(self):
        return True

    @property
    def _country_folder(self):
        site = portal.get()

        ccode = getattr(self.context, '_ccode', self.context.id)

        country_folder = site['marine']['assessment-module']['national-descriptors-assessments'][ccode]

        return country_folder

    def country_name_url(self):
        return self.country_name.lower().replace(' ', '-')

    def get_regions(self, context=None):
        if not context:
            context = self._country_folder

        regions = [
            x for x in context.contentValues()
            if x.portal_type == 'Folder'
        ]

        sorted_regions = sorted(
            regions, key=lambda i: ordered_regions_sortkey(i.id.upper())
        )

        return sorted_regions

    def send_to_tl(self):
        regions = self.get_regions()

        for region in regions:
            descriptors = self.get_descriptors(region)

            for desc in descriptors:
                assessments = self.get_articles(desc)

                for assessment in assessments:
                    state_id = self.get_wf_state_id(assessment)

                    if state_id == 'approved':
                        transition(obj=assessment, to_state='in_work')

        IStatusMessage(self.request).add(u'Sent to TL', type='info')

        url = self.context.absolute_url()

        return self.request.response.redirect(url)

    def ready_phase2(self, regions=None):
        # roles = self.get_current_user_roles(self.context)

        if not self.can_view_edit_assessment_data(self.context):
            return False

        if not regions:
            regions = self.get_regions()

        for region in regions:
            descriptors = self.get_descriptors(region)

            for desc in descriptors:
                assessments = self.get_articles(desc)

                for assessment in assessments:
                    state_id = self.get_wf_state_id(assessment)

                    if state_id != 'approved':
                        return False

        return True

    def get_descriptors(self, region):
        order = [
            'd1.1', 'd1.2', 'd1.3', 'd1.4', 'd1.5', 'd1.6', 'd2', 'd3', 'd4',
            'd5', 'd6', 'd7', 'd8', 'd9', 'd10', 'd11',
        ]

        return [region[d] for d in order]

    def descriptor_for_code(self, code):
        desc = get_descriptor(code.upper())

        return desc

    def get_secondary_articles(self, country):
        order = ['art7', 'art3', 'art4']

        return [country[a] for a in order]

    def __call__(self):

        return self.index()


class MSFDReportingHistoryMixin(object):
    def get_msfd_reporting_history(self):
        reporting_data = []
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            object_provides=IMSFDReportingHistoryFolder.__identifier__,
        )

        for brain in brains:
            obj = brain._unrestrictedGetObject()

            if not hasattr(obj, '_msfd_reporting_history_data'):
                continue

            reporting_data = obj._msfd_reporting_history_data

            break

        return reporting_data

    def get_msfd_url(self, article, country_code, report_type, task_product):
        data = self.get_msfd_reporting_history()

        res = ['']

        if country_code == 'ATL':
            country_code = 'NEA'

        for row in data:
            if article != row.MSFDArticle:
                continue

            if country_code != row.CountryCode:
                continue

            if report_type != row.ReportType:
                continue

            if task_product != row.TaskProduct:
                continue

            # res.append((row.LocationURL, row.FileName))
            res.append(row.LocationURL)

        return res[-1]


@implementer(ICountryStartReports)
class NatDescCountryOverviewReports(NationalDescriptorCountryOverview):
    """ Class declaration needed to be able to override HTML head title """

    def _is_report_2018_art8(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art8_data:
            # TODO check get_data_from_view_art8 for more edge cases
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region or row.Region == 'NotReported'):
                continue

            if row.GESComponent not in all_ids:
                continue

            if not desc_id.startswith('D1.'):
                return True

            feats = set((row.Feature, ))

            if feats.intersection(ok_features):
                return True

        return False

    def _is_report_2018_art9(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art9_data:
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region or row.Region == 'NotReported' or row.Region is None):
                continue

            if row.GESComponent not in all_ids:
                continue

            if not row.Features:
                return True

            if not desc_id.startswith('D1.'):
                return True

            feats = set(row.Features.split(','))

            if feats.intersection(ok_features):
                return True

        return False

    def _is_report_2018_art10(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        ok_features = set([f.name for f in get_features(desc_id)])

        blacklist_descriptors = ['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5',
                                 'D1.6', 'D4', 'D6']

        if descriptor.id in blacklist_descriptors:
            blacklist_descriptors.remove(descriptor.id)

        blacklist_features = []
        for _desc in blacklist_descriptors:
            blacklist_features.extend([
                f.name for f in get_features(_desc)
            ])
        blacklist_features = set(blacklist_features)

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art10_data:
            if row.CountryCode != country_code:
                continue

            if not (row.Region == region
                    or row.Region == 'NotReported'
                    or row.Region is None):
                continue

            ges_comps = getattr(row, 'GESComponents', ())
            ges_comps = set([g.strip() for g in ges_comps.split(',')])

            if not ges_comps.intersection(all_ids):
                continue

            if not desc_id.startswith('D1.'):
                return True

            row_needed = is_row_relevant_for_descriptor(
                row, desc_id, ok_features, blacklist_features,
                ges_comps
            )

            if row_needed:
                return True

        return False

    def _is_report_2018_art11(self, region, desc_id):
        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        region_names = [
            REGIONS[region].replace('&', 'and')
        ]
        region_names = [
            ':' in rname and rname.split(':')[1].strip() or rname
            for rname in region_names
        ]

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in self.art11_data:
            if row.CountryCode != country_code:
                continue

            if row.Descriptor not in all_ids:
                continue

            sub_regions = row.SubRegions or ''

            if not sub_regions:
                return True

            regions_reported = set(sub_regions.split(','))

            if regions_reported.intersection(set(region_names)):
                return True

        return False

    def _is_report_2018_art13(self, region, desc_id, data=None):
        if not data:
            data = self.art13_data

        country_code = self.country_code.upper()
        region = region.upper()
        desc_id = desc_id.upper()
        # descriptor_db = desc_id.replace('D4', 'D4/D1').replace('D6', 'D6/D1')
        descriptor = get_descriptor(desc_id)
        all_ids = list(descriptor.all_ids())
        region_names = [
            REGIONS[region].replace('&', 'and')
        ]
        region_names = [
            ':' in rname and rname.split(':')[1].strip() or rname
            for rname in region_names
        ]

        if desc_id.startswith('D1.'):
            all_ids.append('D1')

        for row in data:
            if row.CountryCode != country_code:
                continue

            desc_reported = row.GEScomponent.split(';')
            desc_reported = set([d.strip() for d in desc_reported])

            if not desc_reported.intersection(set(all_ids)):
                continue

            regions_reported = row.RegionSubregion.split(';')
            regions_reported = set([r.strip() for r in regions_reported])
            regions_reported_norm = []

            for region_rep in regions_reported:
                region_rep_norm = RE_REGION_NORM.sub('', region_rep)

                regions_reported_norm.append(region_rep_norm)

            regions_reported_norm = set(regions_reported_norm)

            if regions_reported_norm.intersection(set(region_names)):
                return True

        return False

    def _is_report_2018_art14(self, region, desc_id):
        return self._is_report_2018_art13(region, desc_id, self.art14_data)

    def is_report_available_2018(self, region, descriptor, article):
        method_name = '_is_report_2018_' + article

        available = True

        if hasattr(self, method_name):
            check_method = getattr(self, method_name)
            available = check_method(region, descriptor)

        # print("Report for %s %s %s is %s"
        #         % (region, descriptor, article, available))

        return available

    def text_reports(self):
        reports = get_text_reports_2018(self.country_code)
        res = []

        for row in reports:
            file_url = row[0]
            report_date = row[1]
            report_date = report_date.date().isoformat()
            file_url_split = file_url.split('/')
            file_name = file_url_split[-1]
            res.append((file_name, file_url, report_date))

        return res

         # return sorted(res, key=lambda i: i[0])

    def __call__(self):
        self.art8_data = db.get_all_data_from_view_Art8(self.country_code)
        self.art9_data = db.get_all_data_from_view_Art9(self.country_code)
        self.art10_data = db.get_all_data_from_view_Art10(self.country_code)
        self.art11_data = db.get_all_data_from_view_art11(self.country_code)
        self.art13_data = db.get_all_data_from_view_art13(self.country_code)
        self.art14_data = db.get_all_data_from_view_art14(self.country_code)

        return self.index()


class NationalDescriptorRegionView(BaseView):
    section = 'national-descriptors'
