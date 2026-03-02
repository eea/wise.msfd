# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
from types import SimpleNamespace
import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as Template
from wise.msfd import db, sql2024
from wise.msfd.compliance.utils import fix_gescomp_2024
from wise.msfd.gescomponents import get_descriptor, get_features

from .reportdata2018 import ReportData2018

logger = logging.getLogger("wise.msfd")


class ReportData2024(ReportData2018):
    """Implementation for Article 8, 9 and 10 report data view for year 2024"""

    report_year = "2024"  # used by cache key
    year = "2024"  # used in report definition and translation
    report_due = "2024-10-15"

    report_header_template = Template('../pt/report-data-header-2024.pt')

    def _get_order_cols_Art8(self, descr):
        descr = descr.split(".")[0]
        criteria_priority = (
            "MarineReportingUnit",
            "GEScomponent",
            "Criteria",
            "Feature",
            "Element",
            "Element2",
            # "Element2Code",
            "IntegrationRuleTypeParameter",
        )

        default = (
            "MarineReportingUnit",
            "GEScomponent",
            "Feature",
            "Element",
            "Element2",
            # "Element2Code",
            "Criteria",
            "IntegrationRuleTypeParameter",
        )

        order_by = {
            "D2": criteria_priority,
            "D4": criteria_priority,
            "D5": (
                "MarineReportingUnit",
                "GEScomponent",
                "Feature",
                "Criteria",
                "Element",
                "Element2",
                # "Element2Code",
                "IntegrationRuleTypeParameter",
            ),
            "D6": default,
            "D7": criteria_priority,
            "D8": criteria_priority,
            "D11": criteria_priority,
            "default": default,
        }

        return order_by.get(descr, order_by["default"])

    # @db.use_db_session("2018")
    def get_report_metadata(self):
        """Returns metadata about the reported information"""
        item = SimpleNamespace()
        item.ReportedFileLink = '/'
        item.ContactOrganisation = ''
        item.ReportingDate = self._reporting_date

        return item

    @db.use_db_session('2024')
    def get_data_from_view_Art8_2024(self):
        sess = db.session()
        t = sql2024.t_V_ART8_GES_2024

        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        # muids = [x.id for x in self.muids]
        conditions = [
            t.c.CountryCode == self.country_code,
            # t.c.Region == self.country_region_code,
            # t.c.MarineReportingUnit.in_(muids),     #
            # t.c.GEScomponent.in_(all_ids),
        ]

        orderby = [getattr(t.c, x)
                   for x in self._get_order_cols_Art8(self.descriptor)]

        # groupby IndicatorCode
        q = sess.query(t).filter(*conditions).order_by(*orderby).distinct()

        # ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        for row in q:
            ges_comps = getattr(row, 'GEScomponent', ())
            ges_comps = set([
                fix_gescomp_2024(g.strip())
                for g in ges_comps.split(';')
            ])

            if ges_comps.intersection(all_ids):
                out.append(row)

            # if not self.descriptor.startswith("D1."):
            #     out.append(row)
            #     continue

            # feats = set((row.Feature,))

            # if feats.intersection(ok_features):
            #     out.append(row)

        self._reporting_date = out and out[0].ReportingDate or None

        return out

    def get_data_from_view_Art10_2024(self):
        return self.get_data_from_view_Art10()

    @db.use_db_session('2024')
    def get_data_from_view_Art9_2024(self):
        t = sql2024.t_V_ART9_GES_2024

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions = [
            t.c.CountryCode == self.country_code,
            # t.c.GEScomponent.in_(all_ids),
        ]

        _, q = db.get_all_records_ordered(
            t, ("GEScomponent",), *conditions)

        # ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        # There are cases when justification for delay is reported
        # for a ges component. In these cases region, mru, features and
        # other fields are empty. Justification for delay should be showed
        # for all regions, mrus
        for row in q:
            ges_comps = getattr(row, 'GEScomponent', ())
            ges_comps = set([
                fix_gescomp_2024(g.strip())
                for g in ges_comps.split(';')
            ])

            if ges_comps.intersection(all_ids):
                out.append(row)

            # if not row.Feature:
            #     out.append(row)
            #     continue

            # if not self.descriptor.startswith("D1."):
            #     out.append(row)
            #     continue

            # feats = set(row.Feature.split(","))

            # if feats.intersection(ok_features):
            #     out.append(row)

        self._reporting_date = out and out[0].ReportingDate or None

        return out
