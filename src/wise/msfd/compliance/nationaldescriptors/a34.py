import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.data import get_xml_report_data
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow,
                             RelaxedNode, Row, natural_sort_key, to_html)

from ..base import BaseArticle2012
from .data import REPORT_DEFS

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


def xp(xpath, node):
    return node.xpath(xpath, namespaces=NSMAP)


class A34Item(Item):
    def __init__(self, parent, node, description):

        super(A34Item, self).__init__([])

        self.parent = parent
        self.node = node
        self.description = description
        self.g = RelaxedNode(node, NSMAP)

        # self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text

        attrs = [
            ('Member state description', self.member_state_descr),
            ('Region / subregion description', self.region_subregion),
            ('Subdivisions', self.subdivisions),
            ('Marine reporting units description', self.assessment_areas),
            ('Region or subregion', self.region_or_subregion),
            ('Member state', self.member_state),
            ('Area type', self.area_type),
            ('MRU ID', self.mru_id),
            ('Marine reporting unit', self.marine_reporting_unit),
        ]

        for title, getter in attrs:
            self[title] = getter()

    def member_state_descr(self):
        text = xp('w:MemberState/text()', self.description)

        return text and text[0] or ''

    def region_subregion(self):
        text = xp('w:RegionSubregion/text()', self.description)

        return text and text[0] or ''

    def subdivisions(self):
        text = xp('w:Subdivisions/text()', self.description)

        return text and text[0] or ''

    def assessment_areas(self):
        text = xp('w:AssessmentAreas/text()', self.description)

        return text and text[0] or ''

    def region_or_subregion(self):
        v = self.g['w:RegionSubRegions/text()']

        return v and v[0] or ''

    def member_state(self):
        v = self.g['w:MemberState/text()']

        return v and v[0] or ''

    def area_type(self):
        v = self.g['w:AreaType/text()']

        return v and v[0] or ''

    def mru_id(self):
        v = self.g['w:MarineUnitID/text()']

        return v and v[0] or ''

    def marine_reporting_unit(self):
        v = self.g['w:MarineUnits_ReportingAreas/text()']

        return v and v[0] or ''


class Article34(BaseArticle2012):
    """ Article 3 & 4 implementation

    klass(self, self.request, self.country_code, self.country_region_code,
            self.descriptor, self.article, self.muids)
    """

    template = Template('pt/report-data-secondary.pt')
    help_text = ""

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, filename):

        super(Article34, self).__init__(context, request, country_code,
                                        region_code, descriptor, article,
                                        muids)

        self.filename = filename

    def setup_data(self):
        filename = self.filename
        text = get_xml_report_data(filename)
        root = fromstring(text)

        # basic algorthim to detect what type of report it is
        article = self.article

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        cols = []
        # TODO get nodes from XML
        nodes = xp('//w:GeographicalBoundariesID', root)
        description = xp('//w:Description', root)[0]

        for node in nodes:
            item = A34Item(self, node, description)
            cols.append(item)

        self.rows = []

        sorted_cols = sorted(
            cols, key=lambda _r: (
                _r['Region or subregion'], _r['Area type'], _r['MRU ID']
            )
        )

        for col in sorted_cols:
            for name in col.keys():
                values = []

                for inner in sorted_cols:
                    values.append(inner[name])

                raw_values = []
                vals = []
                for v in values:
                    raw_values.append(v)
                    vals.append(self.context.translate_value(
                        name, v, self.country_code))

                # values = [self.context.translate_value(name, value=v)
                #           for v in values]

                row = RawRow(name, vals, raw_values)
                self.rows.append(row)

            break       # only need the "first" row

        self.cols = sorted_cols

    def __call__(self):
        self.setup_data()

        return self.template()

    def auto_translate(self):
        self.setup_data()
        translatables = self.context.TRANSLATABLES
        seen = set()

        for row in self.rows:
            if not row:
                continue
            if row.title not in translatables:
                continue

            for value in row.raw_values:
                if not isinstance(value, basestring):
                    continue
                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        return ''
