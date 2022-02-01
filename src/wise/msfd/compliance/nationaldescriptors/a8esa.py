from __future__ import absolute_import
import logging
from collections import defaultdict

from lxml.etree import fromstring
from sqlalchemy.orm.relationships import RelationshipProperty

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql  # , sql2018
from wise.msfd.data import get_xml_report_data
from wise.msfd.gescomponents import (Criterion, MarineReportingUnit,
                                     get_criterion, get_descriptor)
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import Item, ItemLabel, ItemList, Node, RawRow, Row

from ..base import BaseArticle2012
from .data import REPORT_DEFS
import six

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


class Descriptor(Criterion):
    """ Override the default Criterion to offer a nicer title
    (doesn't duplicate code)
    """

    @property
    def title(self):
        return self._title


class Article8ESA(BaseArticle2012):
    # TODO not implemented, copy of Article 8
    """ Article 8 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a8.pt')
    help_text = ""

    def setup_data(self):

        filename = self.context.get_report_filename()
        text = get_xml_report_data(filename)
        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        # TODO: should use declared set of marine unit ids
        xml_muids = sorted(set(xp('//w:MarineUnitID/text()')))

        self.rows = [
            Row('Reporting area(s) [MarineUnitID]',
                [', '.join(set(xml_muids))]),
        ]

        report_map = defaultdict(list)
        root_tags = get_report_tags(root)

        ReportTag = None

        # basic algorthim to detect what type of report it is
        article = self.article

         # override the default translatable
        fields = REPORT_DEFS[self.context.year][article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        for name in root_tags:
            nodes = xp('//w:' + name)

            for node in nodes:
                try:
                    rep = ReportTag(node, NSMAP)
                except:
                    # There are some cases when an empty node is reported
                    # and the ReportTag class cannot be initialized because
                    # MarineUnitID element is not present in the node
                    # see ../fi/bal/d5/art8/@@view-report-data-2012
                    # search for node MicrobialPathogens
                    continue
                    import pdb
                    pdb.set_trace()

                # TODO for D7(maybe for other descriptors too)
                # find a way to match the node with the descriptor
                # because all reported criterias and indicators are GESOther

                if rep.matches_descriptor(self.descriptor):
                    report_map[rep.marine_unit_id].append(rep)

        descriptor = get_descriptor(self.descriptor)
        ges_crits = [descriptor] + list(descriptor.criterions)

        # a bit confusing code, we have multiple sets of rows, grouped in
        # report_data under the marine unit id key.
        report_data = {}

        # TODO: use reported list of muids per country,from database

        for muid in xml_muids:
            if muid not in report_map:
                logger.warning("MarineUnitID not reported: %s, %s, Article 8",
                               muid, self.descriptor)
                report_data[muid] = []

                continue

            m_reps = report_map[muid]

            if len(m_reps) > 1:
                logger.warning("Multiple report tags for this "
                               "marine unit id: %r", m_reps)

            rows = []

            for i, report in enumerate(m_reps):

                # if i > 0:       # add a splitter row, to separate reports
                #     rows.append(Row('', ''))

                cols = report.columns(ges_crits)

                for col in cols:
                    for name in col.keys():
                        values = []

                        for inner in cols:
                            values.append(inner[name])
                        translated_values = [
                            self.context.translate_value(
                                name, v, self.country_code
                            )
                            for v in values
                        ]
                        row = RawRow(name, translated_values, values)
                        rows.append(row)

                    break       # only need the "first" row, for headers

            report_data[muid] = rows

        res = {}

        muids = {m.id: m for m in self.muids}

        for mid, v in report_data.items():
            mlabel = muids.get(mid)
            if mlabel is None:
                logger.warning("Report for non-defined muids: %s", mid)
                mid = six.text_type(mid)
                mlabel = MarineReportingUnit(mid, mid)
            res[mlabel] = v

        # self.muids = sorted(res.keys())
        self.rows = res

    def __call__(self):
        self.setup_data()

        return self.template()

    def auto_translate(self):
        self.setup_data()
        translatables = self.context.TRANSLATABLES
        seen = set()

        for table in self.rows.items():
            muid, table_data = table

            for row in table_data:
                if not row:
                    continue
                if row.title not in translatables:
                    continue

                for value in row.raw_values:
                    if not isinstance(value, six.string_types):
                        continue
                    if value not in seen:
                        retrieve_translation(self.country_code, value)
                        seen.add(value)

        return ''
