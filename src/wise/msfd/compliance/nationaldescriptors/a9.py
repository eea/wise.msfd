#!/home/tibi/tools/bin/python

# import sys
from collections import defaultdict

import requests
from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.utils import Row

from ..base import BaseArticle2012
from .utils import get_descriptors

NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class Article9(BaseArticle2012):
    """ Article 9 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a9.pt')

    def __call__(self):
        filename = self.context.get_report_filename()
        url = self.context.get_report_file_url(filename)
        req = requests.get(url)
        text = req.content
        root = fromstring(text)

        self.descriptor_label = dict(get_descriptors())[self.descriptor]

        def x(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        def filter_descriptors(nodes, descriptor):
            res = []
            m = descriptor.replace('D', '')

            for d in nodes:
                rf = x('w:ReportingFeature/text()', d)[0]

                if rf == descriptor or rf.startswith(m):
                    res.append(d)

            return res

        descriptors = filter_descriptors(x('//w:Descriptors'), self.descriptor)

        def get_marine_unit_ids():
            return set(x('//w:Descriptors/w:MarineUnitID/text()'))

        def get_ges_components():
            res = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]
                res.append(rf)

            return res

        def get_ges_descriptions():
            res = []

            for d in descriptors:
                v = x('//w:DescriptionGES/text()', d)[0]
                res.append(v)

            return res

        def get_features_reported(ges_components):
            return []

        def map_threshold_values(ges_components):
            rfs = defaultdict(dict)

            for d in descriptors:
                muid = x('w:MarineUnitID/text()', d)[0]
                rf = x('w:ReportingFeature/text()', d)[0]

                if rf not in ges_components:
                    continue

                tv = x('w:ThresholdValue/text()', d)

                if not tv:
                    continue

                tv = tv[0]

                rfs[rf][muid] = tv

            return rfs

        def get_threshold_values(ges_components, threshold_values_map):
            res = []

            for gc in ges_components:
                values = threshold_values_map[gc]
                row = '\n'.join(['{} = {}'.format(m, v)
                                 for m, v in values.items()])
                res.append(row)

            return res

        def get_threshold_value_units(ges_components):
            res = []
            seen = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]

                if (rf not in ges_components) or (rf in seen):
                    continue

                tvu = x('w:ThresholdValueUnit/text()', d)

                if not tvu:
                    continue

                seen.append(rf)
                tvu = tvu[0]
                res.append(tvu)

            return res

        def get_reference_point_type(ges_components):
            res = []
            seen = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]

                if (rf not in ges_components) or (rf in seen):
                    continue

                tvu = x('w:ReferencePointType/text()', d)

                if not tvu:
                    continue

                seen.append(rf)
                tvu = tvu[0]
                res.append(tvu)

            return res

        def get_proportion(ges_components):
            res = []
            seen = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]

                if (rf not in ges_components) or (rf in seen):
                    continue

                tvu = x('w:Proportion/text()', d)

                if not tvu:
                    continue

                seen.append(rf)
                tvu = tvu[0]
                res.append(tvu)

            return res

        def get_assessment_method(ges_components):
            res = []
            seen = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]

                if (rf not in ges_components) or (rf in seen):
                    continue

                tvu = x('w:AssessmentMethod/text()', d)

                if not tvu:
                    continue

                seen.append(rf)
                tvu = tvu[0]
                res.append(tvu)

            return res

        def get_development_status(ges_components):
            res = []
            seen = []

            for d in descriptors:
                rf = x('w:ReportingFeature/text()', d)[0]

                if (rf not in ges_components) or (rf in seen):
                    continue

                tvu = x('w:DevelopmentStatus/text()', d)

                if not tvu:
                    continue

                seen.append(rf)
                tvu = tvu[0]
                res.append(tvu)

            return res

        self.rows = []
        self.rows.append(Row('Reporting area(s) [MarineUnitID]',
                             [', '.join(sorted(get_marine_unit_ids()))]))

        self.rows.append(Row('GES component [Reporting feature]',
                             get_ges_components()))

        self.rows.append(Row('GES description [DescriptionGES]',
                             get_ges_descriptions()))

        ges_components = get_ges_components()

        threshold_values = map_threshold_values(ges_components)

        self.rows.append(
            Row('Threshold value(s)',
                get_threshold_values(ges_components, threshold_values)))

        self.rows.append(
            Row('Threshold value unit',
                get_threshold_value_units(ges_components)))

        self.rows.append(
            Row('Reference point type',
                get_reference_point_type(ges_components)))

        # TODO: do the baseline according to xls

        self.rows.append(Row('Proportion', get_proportion(ges_components)))

        self.rows.append(Row('Assessment method',
                             get_assessment_method(ges_components)))

        self.rows.append(Row('Development status',
                             get_development_status(ges_components)))

        return self.template()
