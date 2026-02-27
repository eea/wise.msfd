# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
import logging
import xlsxwriter

from zope.interface import implementer
from zope.schema import Choice
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from eea.cache import cache
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as Template
from Products.statusmessages.interfaces import IStatusMessage

from sqlalchemy import or_
from collections import defaultdict
from datetime import datetime
from itertools import chain
from io import BytesIO
from six import text_type

from wise.msfd import db, sql2018
from wise.msfd.compliance.base import is_row_relevant_for_descriptor
from wise.msfd.compliance.interfaces import (
    IReportDataView,
)
from wise.msfd.compliance.nationaldescriptors.data import get_report_definition
from wise.msfd.compliance.utils import (
    group_by_mru,
    has_cost_uses_data,
    insert_missing_criterions,
)
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.gescomponents import get_descriptor, get_features
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import items_to_rows, natural_sort_key, timeit

from ..base import BaseView
from ..proxy import Proxy2018
from ..utils import consolidate_singlevalue_to_list
from .utils import get_reportdata_key, ORDER_COLS_ART11, RE_REGION_NORM

logger = logging.getLogger("wise.msfd")


class SnapshotSelectForm(Form):
    template = Template("../../pt/inline-form.pt")
    _updated = False

    @property
    def fields(self):
        snaps = getattr(self.context.context, "snapshots", [])

        if snaps:
            default = snaps[-1][0]
        else:
            default = None

        dates = [SimpleTerm(x[0], x[0].isoformat(), x[0]) for x in snaps]

        field = Choice(
            title="Date of harvest",
            __name__="sd",
            vocabulary=SimpleVocabulary(dates),
            required=False,
            default=default,
        )

        return Fields(field)

    def update(self):
        if not self._updated:
            Form.update(self)
            self._updated = True

    @buttonAndHandler("View snapshot", name="view")
    def apply(self, action):
        return

    # TODO: make a condition for this button
    @buttonAndHandler("Harvest new data", name="harvest")
    def harvest(self, action):
        data = self.context.get_data_from_db()

        self.context.context.snapshots.append((datetime.now(), data))

        self.request.response.redirect("./@@view-report-data-2018")


@implementer(IReportDataView)
class ReportData2018(BaseView):
    report_year = "2018"  # used by cache key
    year = "2018"  # used in report definition and translation
    report_due = "2018-10-15"
    section = "national-descriptors"
    is_side_by_side = False

    help_texts = {
        "Art8": """
The data is retrieved from the MSFD2018_production.V_ART8_GES_2018 database
view, filtered by country code and ges component ids. If the current Descriptor
starts with 'D1.', we also append the 'D1' descriptor to the GES Component ids.

We use this table for the list of GES Components and the descriptor that they
belong to:

https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv
""",
        "Art9": """
The data is retrieved from the MSFD2018_production.V_ART9_GES_2018 database
view, filtered by country code and ges component ids. If the current Descriptor
starts with 'D1.', we also append the 'D1' descriptor to the GES Component ids.

We use this table for the list of GES Components and the descriptor that they
belong to:

https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv
""",
        "Art10": """
The data is retrieved from the MSFD2018_production.V_ART10_Targets_2018
database view. Because the GESComponent column is not reliable (the Netherlands
reported using the 1.1.3 GESComponent for all their records), we filter the
data using the Parameters and Features available for the current descriptor.

We use this file for the Descriptor to Parameters and Features association
table:

https://svn.eionet.europa.eu/repositories/Reportnet/Dataflows/MarineDirective/MSFD2018/Webforms/msfd2018-codelists.json
""",
        "Art3": "To be completed...",
        "Art4": "To be completed...",
        "Art7": "To be completed...",
        "Art11": """
The data is retrieved from the MSFD2018_production.V_ART11_Strategies database view.
""",
        "Art8esa": """
The data is retrieved from the MSFD2018_production.V_ART8_ESA_2018 database view.
""",
        "Art13": "To be completed...",
        "Art14": "To be completed...",
    }

    @property
    def help_text(self):
        return self.help_texts.get(self.article, "")

    Art8 = Template("../pt/report-data-multiple-muid.pt")
    Art8_2024 = Template("../pt/report-data-multiple-muid.pt")
    Art9 = Template("../pt/report-data-multiple-muid.pt")
    Art9_2024 = Template("../pt/report-data-multiple-muid.pt")
    Art10 = Template("../pt/report-data-multiple-muid.pt")
    Art10_2024 = Template("../pt/report-data-multiple-muid.pt")
    Art11 = Template("../pt/report-data-multiple-muid.pt")
    Art13 = Template("../pt/report-data-multiple-muid.pt")
    Art14 = Template("../pt/report-data-multiple-muid.pt")

    subform = None  # used for the snapshot selection form

    @property
    def all_descriptor_ids(self):
        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        all_ids = set(all_ids)

        return all_ids

    def _get_order_cols_Art8(self, descr):
        descr = descr.split(".")[0]
        criteria_priority = (
            "MarineReportingUnit",
            "GESComponent",
            "Criteria",
            "Feature",
            "Element",
            "Element2",
            "Element2Code",
            "IntegrationRuleTypeParameter",
        )

        default = (
            "MarineReportingUnit",
            "GESComponent",
            "Feature",
            "Element",
            "Element2",
            "Element2Code",
            "Criteria",
            "IntegrationRuleTypeParameter",
        )

        order_by = {
            "D2": criteria_priority,
            "D4": criteria_priority,
            "D5": (
                "MarineReportingUnit",
                "GESComponent",
                "Feature",
                "Criteria",
                "Element",
                "Element2",
                "Element2Code",
                "IntegrationRuleTypeParameter",
            ),
            "D6": default,
            "D7": criteria_priority,
            "D8": criteria_priority,
            "D11": criteria_priority,
            "default": default,
        }

        return order_by.get(descr, order_by["default"])

    def _get_order_cols_Art10(self):
        order = ("TargetCode", "Features", "Element", "Parameter")

        return order

    def get_data_from_view_Art8(self):
        sess = db.session()
        t = sql2018.t_V_ART8_GES_2018

        descr_class = get_descriptor(self.descriptor)
        all_ids = list(descr_class.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        # muids = [x.id for x in self.muids]
        conditions = [
            t.c.CountryCode == self.country_code,
            # t.c.Region == self.country_region_code,
            # t.c.MarineReportingUnit.in_(muids),     #
            t.c.GESComponent.in_(all_ids),
        ]

        # Handle the case of Romania that submitted duplicate data,
        # where Element is empty, but Criteria has data
        if self.country_code != "RO":
            conditions.append(
                or_(t.c.Element.isnot(None), t.c.Criteria.isnot(None)))
        else:
            conditions.append(t.c.Element.isnot(None))

        if self.country_code != "DK":
            conditions.insert(1, t.c.Region == self.country_region_code)
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(
                1,
                or_(
                    t.c.Region == "NotReported", t.c.Region == self.country_region_code
                ),
            )

        orderby = [getattr(t.c, x)
                   for x in self._get_order_cols_Art8(self.descriptor)]

        # groupby IndicatorCode
        q = sess.query(t).filter(*conditions).order_by(*orderby).distinct()

        # For the following countries filter data by features
        # for other countries return all data
        country_filters = ("BE",)

        if self.country_code not in country_filters:
            return q

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        for row in q:
            if not self.descriptor.startswith("D1."):
                out.append(row)
                continue

            feats = set((row.Feature,))

            if feats.intersection(ok_features):
                out.append(row)

        return out

    def get_data_from_view_Art10(self):
        t = sql2018.t_V_ART10_Targets_2018

        conditions = [t.c.CountryCode == self.country_code]

        if self.country_code != "DK":
            conditions.insert(1, t.c.Region == self.country_region_code)
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(
                1,
                or_(
                    t.c.Region == "NotReported", t.c.Region == self.country_region_code
                ),
            )

        count, res = db.get_all_records_ordered(
            t, self._get_order_cols_Art10(), *conditions
        )

        out = []

        # GESComponents contains multiple values separated by comma
        # filter rows by splitting GESComponents
        for row in res:
            ges_comps = getattr(row, "GESComponents", ())
            ges_comps = set([g.strip() for g in ges_comps.split(",")])

            if ges_comps.intersection(self.all_descriptor_ids):
                out.append(row)

        if not self.descriptor.startswith("D1."):
            return out

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
        ok_features = set([f.name for f in get_features(self.descriptor)])
        out_filtered = []

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
        blacklist_descriptors.remove(self.descriptor)
        blacklist_features = []

        for _desc in blacklist_descriptors:
            blacklist_features.extend([f.name for f in get_features(_desc)])

        blacklist_features = set(blacklist_features)

        for row in out:
            # Because some Features are missing from FeaturesSmart
            # we consider 'D1' descriptor valid for all 'D1.x'
            # and we keep the data if 'D1' is present in the GESComponents
            # countries_filter = for these countries DO NOT filter by features
            ges_comps = getattr(row, "GESComponents", ())
            ges_comps = set([g.strip() for g in ges_comps.split(",")])
            countries_nofilter = []  # ('RO', 'DK', 'CY', 'MT')

            if "D1" in ges_comps and self.country_code in countries_nofilter:
                out_filtered.append(row)
                continue

            row_needed = is_row_relevant_for_descriptor(
                row, self.descriptor, ok_features, blacklist_features, ges_comps
            )

            if row_needed:
                out_filtered.append(row)

        return out_filtered

    def get_data_from_view_Art9(self):

        t = sql2018.t_V_ART9_GES_2018

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions = [
            t.c.CountryCode == self.country_code,
            t.c.GESComponent.in_(all_ids),
        ]

        if self.country_code != "DK":
            conditions.insert(
                1, or_(t.c.Region == self.country_region_code,
                       t.c.Region.is_(None))
            )
        else:
            # Handle the case of Denmark that have submitted a lot of
            # information under the DK-TOTAL MRU, which doesn't have a region
            # attached.
            conditions.insert(
                1,
                or_(
                    t.c.Region == "NotReported",
                    t.c.Region == self.country_region_code,
                    t.c.Region.is_(None),
                ),
            )

        count, q = db.get_all_records_ordered(
            t, ("GESComponent",), *conditions)

        ok_features = set([f.name for f in get_features(self.descriptor)])
        out = []

        # There are cases when justification for delay is reported
        # for a ges component. In these cases region, mru, features and
        # other fields are empty. Justification for delay should be showed
        # for all regions, mrus
        for row in q:
            if not row.Features:
                out.append(row)
                continue

            if not self.descriptor.startswith("D1."):
                out.append(row)
                continue

            feats = set(row.Features.split(","))

            if feats.intersection(ok_features):
                out.append(row)

        return out

    def get_data_from_view_Art11(self):
        t = sql2018.t_V_ART11_Strategies_Programmes_2020

        conditions = [t.c.CountryCode.in_(self.country_code.split(","))]

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        conditions.append(t.c.Descriptor.in_(all_ids))

        count, q = db.get_all_records_ordered(t, ORDER_COLS_ART11, *conditions)

        if hasattr(self._countryregion_folder, "_subregions"):
            regions = self._countryregion_folder._subregions
        else:
            regions = [self.country_region_code]

        # filter data by regions
        region_names = [REGIONS[code].replace("&", "and") for code in regions]
        region_names = [
            ":" in rname and rname.split(":")[1].strip() or rname
            for rname in region_names
        ]

        res = []

        for row in q:
            regions_reported = set(row.SubRegions.split(","))

            if regions_reported.intersection(set(region_names)):
                res.append(row)

        return res

    def get_data_from_view_Art13(self):
        t = sql2018.t_V_ART13_Measures_2022

        conditions = [
            t.c.CountryCode == self.country_code,
        ]

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        count, q = db.get_all_records_ordered(t, ("MeasureCode",), *conditions)

        if hasattr(self._countryregion_folder, "_subregions"):
            regions = self._countryregion_folder._subregions
        else:
            regions = [self.country_region_code]

        # filter data by regions and descriptor
        region_names = [REGIONS[code].replace("&", "and") for code in regions]
        region_names = [
            ":" in rname and rname.split(":")[1].strip() or rname
            for rname in region_names
        ]

        res = []

        for row in q:
            regions_reported = row.RegionSubregion.split(";")
            regions_reported = set([r.strip() for r in regions_reported])
            regions_reported_norm = []

            for region_rep in regions_reported:
                region_rep_norm = RE_REGION_NORM.sub("", region_rep)

                regions_reported_norm.append(region_rep_norm)

            regions_reported_norm = set(regions_reported_norm)

            if not regions_reported_norm.intersection(set(region_names)):
                continue

            desc_reported = row.GEScomponent.split(";")
            # sometimes GEScomponents are separated by comma too
            # also split by comma
            desc_reported = [d.split(",") for d in desc_reported]
            desc_reported = chain.from_iterable(desc_reported)
            desc_reported = set([d.strip() for d in desc_reported])

            if not desc_reported.intersection(set(all_ids)):
                continue

            res.append(row)

        return res

    def get_data_from_view_Art14(self):
        t = sql2018.t_V_ART14_Exceptions_2022

        conditions = [
            t.c.CountryCode == self.country_code,
        ]

        descriptor = get_descriptor(self.descriptor)
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith("D1."):
            all_ids.append("D1")

        count, q = db.get_all_records(
            t, *conditions, order_by="Exception_code")

        if hasattr(self._countryregion_folder, "_subregions"):
            regions = self._countryregion_folder._subregions
        else:
            regions = [self.country_region_code]

        # filter data by regions and descriptor
        region_names = [REGIONS[code].replace("&", "and") for code in regions]
        region_names = [
            ":" in rname and rname.split(":")[1].strip() or rname
            for rname in region_names
        ]

        res = []

        for row in q:
            regions_reported = set(row.RegionSubregion.split(";"))
            regions_reported = set([r.strip() for r in regions_reported])
            regions_reported_norm = []

            for region_rep in regions_reported:
                region_rep_norm = RE_REGION_NORM.sub("", region_rep)

                regions_reported_norm.append(region_rep_norm)

            regions_reported_norm = set(regions_reported_norm)

            if not regions_reported_norm.intersection(set(region_names)):
                continue

            desc_reported = set(row.GEScomponent.split(";"))
            desc_reported = set([d.strip() for d in desc_reported])

            if not desc_reported.intersection(set(all_ids)):
                continue

            res.append(row)

        return res

    def get_data_from_view(self, article):
        art = article.replace("-", "_")
        data = getattr(self, "get_data_from_view_" + art)()

        return data

    def get_report_definition(self):
        rep_def = get_report_definition(self.year, self.article).get_fields()

        if self.is_side_by_side:
            return rep_def

        # filtered_rep_def = [f for f in rep_def if f.section != 'empty']
        filtered_rep_def = [f for f in rep_def if f.title]

        return filtered_rep_def

    def get_report_translatable_fields(self):
        rep_def = get_report_definition(
            self.year, self.article
        ).get_translatable_fields()

        return rep_def

    @db.use_db_session("2018")
    @timeit
    def get_data_from_db(self):
        data = self.get_data_from_view(self.article)
        data = [Proxy2018(row, self) for row in data]

        if self.request.form.get("split-mru") and (len(data) > 2000):
            if self.muids:
                if getattr(self, "focus_muid", None) is None:
                    self.focus_muid = self.muids[0].name

                self.focus_muids = self._get_muids_from_data(data)

        if self.article in ("Art8", "Art8-2024"):
            order = self._get_order_cols_Art8(self.descriptor)
            data = consolidate_singlevalue_to_list(
                data,
                "IndicatorCode",
                order,
            )

            data_by_mru = group_by_mru(data)

        if self.article == "Art8esa":
            order = ("MarineReportingUnit",)
            data_by_mru = consolidate_singlevalue_to_list(
                data,
                "MarineReportingUnit",
                order,
            )

            if data_by_mru:
                data_by_region = defaultdict(list)

                # group data by region, also filter items without
                # CostDegradation or UsesActivities data
                for item in data_by_mru:
                    is_needed = has_cost_uses_data(item)

                    if not is_needed:
                        continue

                    region = item.Region
                    region_name = REGIONS[region]
                    data_by_region[region_name].append(item)

                data_by_mru = data_by_region
            else:
                data_by_mru = {}

        if self.article in ("Art10", "Art10-2024"):
            # data_by_mru = group_by_mru(data)
            order = self._get_order_cols_Art10()
            data_by_mru = consolidate_singlevalue_to_list(
                data, "MarineReportingUnit", order
            )
            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                data_by_mru = {}

        if self.article in ("Art9", "Art9-2024"):
            data_by_mru = consolidate_singlevalue_to_list(
                data, "MarineReportingUnit")
            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                data_by_mru = {}
            insert_missing_criterions(data_by_mru, self.descriptor_obj)

        if self.article == "Art11":
            order = ORDER_COLS_ART11
            data_by_mru = consolidate_singlevalue_to_list(
                data, "Element", order)

            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                if not self.is_side_by_side:
                    return []

                data_by_mru = {"": []}

        if self.article in ("Art13", "Art14"):
            # data_by_mru = consolidate_singlevalue_to_list(
            #     data, 'MarineReportingUnit'
            # )
            data_by_mru = data

            if data_by_mru:
                data_by_mru = {"": data_by_mru}
            else:
                data_by_mru = {}

        res = []
        fields = self.get_report_definition()

        # if view is article 11 compare
        return_empty = self.is_side_by_side and self.article in ("Art11",)

        for mru, rows in data_by_mru.items():
            _rows = items_to_rows(rows, fields, return_empty)

            res.append((mru, _rows))

        # resort the results by marine reporting unit
        res_sorted = sorted(
            res, key=lambda r: natural_sort_key(r[0].__repr__()))

        return res_sorted

    def get_snapshots(self):
        """Returns all snapshots, in the chronological order they were created"""
        # TODO: fix this. I'm hardcoding it now to always use generated data
        db_data = self.get_data_from_db()
        snapshot = (datetime.now(), db_data)

        return [snapshot]

        # snapshots = getattr(self.context, 'snapshots', None)
        #
        # if snapshots is None:
        #     self.context.snapshots = PersistentList()
        #
        #     db_data = self.get_data_from_db()
        #     snapshot = (datetime.now(), db_data)
        #
        #     self.context.snapshots.append(snapshot)
        #     self.context.snapshots._p_changed = True
        #
        #     self.context._p_changed = True
        #
        #     return self.context.snapshots
        #
        # return snapshots

    def get_report_data(self):
        """Returns the data to display in the template

        Returns a list of "rows (tuples of label: data)"
        """

        snapshots = self.get_snapshots()
        self.subform.update()
        fd, errors = self.subform.extractData()
        date_selected = fd["sd"]

        data = snapshots[-1][1]

        if hasattr(self, "focus_muid"):
            # filter the data based on selected muid
            # this is used to optmize display of really long data
            data = [t for t in data if t[0].name == self.focus_muid]

        if date_selected:
            filtered = [x for x in snapshots if x[0] == date_selected]

            if filtered:
                date, data = filtered[0]
            else:
                raise ValueError("Snapshot doesn't exist at this date")

        return data

    def _get_muids_from_data(self, data):
        muids = set()
        for row in data:
            o = getattr(row, "__o")
            muid = o.MarineReportingUnit
            muids.add(muid)

        return list(sorted(muids))

    @db.use_db_session("2018")
    @timeit
    def get_report_metadata(self):
        """Returns metadata about the reported information"""
        t = sql2018.ReportedInformation
        schemas = {
            "Art8": "ART8_GES",
            "Art8-2024": "ART8_GES",
            "Art8esa": "ART8_ESA",
            "Art9": "ART9_GES",
            "Art9-2024": "ART9_GES",
            "Art10": "ART10_Targets",
            "Art10-2024": "ART10_Targets",
            "Art11": "ART11_Programmes",
            "Art13": "ART13_Measures",
            "Art14": "ART14_Exceptions",
        }
        count, item = db.get_item_by_conditions(
            t,
            "ReportingDate",
            t.CountryCode == self.country_code,
            t.Schema == schemas[self.article],
            reverse=True,
        )
        return item

    @property
    def report_header_title(self):
        title = "Member State report / {} / {} / {} / {} / {}".format(
            self.article,
            self.report_year,
            self.descriptor_title,
            self.country_name,
            self.country_region_name,
        )

        return title

    def get_report_header(self):
        report = self.get_report_metadata()

        link = report_by = report_date = None
        if report:
            link = report.ReportedFileLink
            link = (link.rsplit("/", 1)[1], link)
            report_by = report.ContactOrganisation
            report_date = report.ReportingDate

        report_header = self.report_header_template(
            title=self.report_header_title,
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by=report_by,
            source_file=link,
            report_due=self.report_due,
            report_date=report_date,
            help_text=self.help_text,
            multiple_source_files=False,
        )

        return report_header

    @cache(get_reportdata_key, dependencies=["translation"])
    def render_reportdata(self):
        logger.info(
            "Quering database for 2018 report data: %s %s %s %s",
            self.country_code,
            self.country_region_code,
            self.article,
            self.descriptor,
        )

        data = self.get_report_data()
        report_header = self.get_report_header()
        template = self.get_template(self.article)

        return template(data=data, report_header=report_header)

    def data_to_xls(self, data):
        # Create a workbook and add a worksheet.
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out, {"in_memory": True})

        inverse_fields = ("MarineReportingUnit",)

        for index, (wtitle, wdata) in enumerate(data):
            _wtitle = "{}_{}".format(index + 1, text_type(wtitle)[:28])
            _wtitle = _wtitle.replace(":", "-")

            worksheet = workbook.add_worksheet(_wtitle)

            for i, (row_label, row_values) in enumerate(wdata):
                worksheet.write(i, 0, row_label.title)
                label_name = row_label.name

                for j, v in enumerate(row_values):
                    try:
                        if hasattr(v, "rows") and v.rows:
                            values = []

                            for item in v.rows:
                                item_title = item

                                if hasattr(item, "name"):
                                    item_title = item.name

                                if label_name in inverse_fields:
                                    item_title = item.title

                                trnsl = get_translated(
                                    item_title, self.country_code)
                                trnsl = trnsl or item_title
                                values.append(trnsl)

                            transl = ", ".join(values)
                        else:
                            if hasattr(v, "name") and v.name:
                                val = v.name

                                if label_name in inverse_fields:
                                    val = v.title

                                v = val

                            v = v and text_type(v) or ""
                            transl = get_translated(v, self.country_code) or v

                        worksheet.write(i, j + 1, transl or "")
                    except:
                        import pdb

                        pdb.set_trace()

        workbook.close()
        out.seek(0)

        return out

    def download(self):
        xlsdata = self.get_report_data()

        xlsio = self.data_to_xls(xlsdata)
        sh = self.request.response.setHeader

        sh(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet",
        )
        fname = "-".join(
            [self.country_code, self.country_region_code,
                self.article, self.descriptor]
        )
        sh("Content-Disposition", "attachment; filename=%s.xlsx" % fname)

        return xlsio.read()

    @property
    def translate_redirect_url(self):
        url = self.context.absolute_url() + "/@@view-report-data-{}".format(
            self.report_year
        )

        return url

    def auto_translate(self, data=None):
        if not data:
            data = self.get_report_data()

        # report_def = REPORT_DEFS[self.year][self.article]
        # translatables = report_def.get_translatable_fields()
        translatables = self.TRANSLATABLES
        seen = set()

        for table in data:
            muid, table_data = table

            for row in table_data:
                field, cells = row
                if field.name in translatables:
                    for value in cells:
                        if value not in seen:
                            retrieve_translation(self.country_code, value)
                            seen.add(value)

        messages = IStatusMessage(self.request)
        messages.add(
            "Auto-translation initiated, please refresh " "in a couple of minutes",
            type="info",
        )

        return self.request.response.redirect(self.translate_redirect_url)

    def get_template(self, article):
        template = getattr(self, article.replace("-", "_"), None)

        return template

    @timeit
    def __call__(self):
        # allow focusing on a single muid if the data is too big
        if "focus_muid" in self.request.form:
            self.focus_muid = self.request.form["focus_muid"].strip()
        # self.focus_muid = 'BAL-AS-EE-ICES_SD_29'

        self.content = ""
        template = self.get_template(self.article)

        if not template:
            return self.index()

        self.subform = self.get_form()

        if "download" in self.request.form:  # and report_data
            return self.download()

        if "translate" in self.request.form and self.can_view_assessment_data:
            return self.auto_translate()

        trans_edit_html = self.translate_view()()

        print("will render report")
        report_html = self.render_reportdata()
        self.report_html = report_html + trans_edit_html

        @timeit
        def render_html():
            return self.index()

        return render_html()

    def get_form(self):

        if not self.subform:
            form = SnapshotSelectForm(self, self.request)
            self.subform = form

        return self.subform
