# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
import logging
from datetime import datetime
from io import BytesIO


import xlsxwriter
from six import text_type
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as Template
from wise.msfd import db, sql2018
from wise.msfd.compliance.base import is_row_relevant_for_descriptor
from wise.msfd.compliance.nationaldescriptors.data import get_report_definition
from wise.msfd.gescomponents import get_all_descriptors, get_descriptor, get_features

from ..base import BaseView
from ..utils import Proxy2018, consolidate_singlevalue_to_list
from .utils import ORDER_COLS_ART11

logger = logging.getLogger("wise.msfd")


class ExportMSReportData(BaseView):
    """"""

    template = Template("../pt/reports-per-descriptor.pt")
    name = "reports-per-descriptor"

    @property
    def descriptors(self):
        descriptors = get_all_descriptors()
        descriptors = [d for d in descriptors if d[0] != "D1"]

        return descriptors

    @property
    def articles(self):
        return ["Art9", "Art8", "Art10"]

    @property
    def article(self):
        article = self.request.form["art"]

        return article

    @property
    def country_code(self):
        return "Not available"

    @property
    def blacklist_fields(self):
        blacklist = ("IdReportedInformation",)

        return blacklist

    def get_report_definition(self):
        year = "2018"

        if self.article in ("Art11",):
            year = "2020"

        rep_def = get_report_definition(year, self.article).get_fields()

        filtered_fields = [f for f in rep_def if f.section != "empty"]

        return filtered_fields

    def data_to_xls(self, labels, data):
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {"constant_memory": True})
        sheetname = "Data"
        worksheet = workbook.add_worksheet(sheetname)

        for i, label in enumerate(labels):
            _label = label.replace("P_", "")
            worksheet.write(0, i, _label)

        x = 0

        for row in data:
            x += 1

            for iv, fieldname in enumerate(labels):
                value = getattr(row, fieldname) or ""
                worksheet.write(x, iv, text_type(value))

        workbook.close()
        out.seek(0)

        return out

    @db.use_db_session("2018")
    def get_art11_data(self, _descriptor):
        t = sql2018.t_V_ART11_Strategies_Programmes_2020

        conditions = []

        descriptor = get_descriptor(_descriptor)
        all_ids = list(descriptor.all_ids())

        if _descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions.append(t.c.Descriptor.in_(all_ids))

        count, q = db.get_all_records_ordered(t, ORDER_COLS_ART11, *conditions)

        data = [x for x in q]
        fields = get_report_definition("2020", self.article).get_fields()
        field_names = [x.name for x in fields if x.title]
        labels_ordered = ["SubRegions", "CountryCode"] + field_names

        return labels_ordered, data

        data = [Proxy2018(row, self) for row in data]
        data_by_mru = consolidate_singlevalue_to_list(
            data, "Element", ORDER_COLS_ART11)

        if data_by_mru:
            data_by_mru = {"": data_by_mru}
        else:
            data_by_mru = {}

        return data_by_mru

    @db.use_db_session("2018")
    def get_art8_data(self, _descriptor):
        sess = db.session()
        t = sql2018.t_V_ART8_GES_2018
        descr_class = get_descriptor(_descriptor)
        all_ids = list(descr_class.all_ids())

        if _descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions = [t.c.GESComponent.in_(all_ids), t.c.Element.isnot(None)]

        orderby = [getattr(t.c, x)
                   for x in ("Region", "CountryCode", "GESComponent")]

        # groupby IndicatorCode
        q = sess.query(t).filter(*conditions).order_by(*orderby).distinct()

        # For the following countries filter data by features
        # for other countries return all data
        country_filters = ("BE",)
        ok_features = set([f.name for f in get_features(_descriptor)])
        data = []

        for row in q:
            if not _descriptor.startswith("D1."):
                data.append(row)
                continue

            if row.CountryCode not in country_filters:
                data.append(row)
                continue

            feats = set((row.Feature,))

            if feats.intersection(ok_features):
                data.append(row)

        fields = get_report_definition("2018", self.article).get_fields()
        field_names = [x.name for x in fields if x.title and not x.drop]
        labels_ordered = ["Region", "CountryCode"] + field_names

        return labels_ordered, data

    @db.use_db_session("2018")
    def get_art9_data(self, _descriptor):
        t = sql2018.t_V_ART9_GES_2018
        descriptor = get_descriptor(_descriptor)
        all_ids = list(descriptor.all_ids())

        if _descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions = [t.c.GESComponent.in_(all_ids)]

        count, q = db.get_all_records_ordered(
            t,
            (
                "Region",
                "CountryCode",
                "GESComponent",
            ),
            *conditions
        )

        ok_features = set([f.name for f in get_features(_descriptor)])
        data = []

        # There are cases when justification for delay is reported
        # for a ges component. In these cases region, mru, features and
        # other fields are empty. Justification for delay should be showed
        # for all regions, mrus
        for row in q:
            if not row.Features:
                data.append(row)
                continue

            if not _descriptor.startswith("D1."):
                data.append(row)
                continue

            feats = set(row.Features.split(","))

            if feats.intersection(ok_features):
                data.append(row)

        fields = get_report_definition("2018", self.article).get_fields()
        field_names = [x.name for x in fields if x.title]
        labels_ordered = ["Region", "CountryCode"] + field_names

        return labels_ordered, data

    @db.use_db_session("2018")
    def get_art10_data(self, _descriptor):
        t = sql2018.t_V_ART10_Targets_2018
        descriptor = get_descriptor(_descriptor)
        all_ids = list(descriptor.all_ids())

        if _descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions = []
        count, res = db.get_all_records_ordered(
            t, ("Region", "CountryCode", "GESComponents"), *conditions
        )

        data = []

        # GESComponents contains multiple values separated by comma
        # filter rows by splitting GESComponents
        for row in res:
            ges_comps = getattr(row, "GESComponents", ())
            ges_comps = set([g.strip() for g in ges_comps.split(",")])

            if ges_comps.intersection(all_ids):
                data.append(row)

        fields = get_report_definition("2018", self.article).get_fields()
        field_names = [x.name for x in fields if x.title]
        labels_ordered = ["Region", "CountryCode"] + field_names

        if not _descriptor.startswith("D1."):
            return labels_ordered, data

        # DISABLE filtering by features for D1.x
        # return out

        # conditions = []
        # params = get_parameters(self.descriptor)
        # p_codes = [p.name for p in params]
        # conditions.append(t.c.Parameter.in_(p_codes))

        # Filtering results based on FeaturesSmart and other conditions
        # I don't think this code should be kept. Probably the edge case should
        # be documented. It makes it fragile and dependent on correct
        # definitions in FeaturesSmart. I think it's trying to avoid showing
        # too many results when the GESComponent has been incorectly reported
        # on the <Target> records.
        ok_features = set([f.name for f in get_features(_descriptor)])
        data_filtered = []

        blacklist_descriptors = [
            "D1.1",
            "D1.2",
            "D1.3",
            "D1.4",
            "D1.5",
            "D1.6",
            "D4",
            "D6",
        ]
        blacklist_descriptors.remove(_descriptor)
        blacklist_features = []

        for _desc in blacklist_descriptors:
            blacklist_features.extend([f.name for f in get_features(_desc)])

        blacklist_features = set(blacklist_features)

        for row in data:
            # Because some Features are missing from FeaturesSmart
            # we consider 'D1' descriptor valid for all 'D1.x'
            # and we keep the data if 'D1' is present in the GESComponents
            # countries_filter = for these countries DO NOT filter by features
            ges_comps = getattr(row, "GESComponents", ())
            ges_comps = set([g.strip() for g in ges_comps.split(",")])

            if "D1" in ges_comps:
                data_filtered.append(row)
                continue

            row_needed = is_row_relevant_for_descriptor(
                row, _descriptor, ok_features, blacklist_features, ges_comps
            )

            if row_needed:
                data_filtered.append(row)

        return labels_ordered, data_filtered

    def download(self, article, descriptor):
        articles_map = {
            "Art11": self.get_art11_data,
            "Art8": self.get_art8_data,
            "Art9": self.get_art9_data,
            "Art10": self.get_art10_data,
        }

        labels, xlsdata = articles_map[article](descriptor)

        xlsio = self.data_to_xls(labels, xlsdata)
        sh = self.request.response.setHeader

        sh(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet",
        )
        fname = "-".join(
            ["Data-per-descriptor", article,
                descriptor, str(datetime.now().date())]
        )
        sh("Content-Disposition", "attachment; filename=%s.xlsx" % fname)

        return xlsio.read()

    def __call__(self):
        if "art" in self.request.form:
            article = self.request.form["art"]
            descriptor = self.request.form["desc"]

            return self.download(article, descriptor)

        return self.template()
