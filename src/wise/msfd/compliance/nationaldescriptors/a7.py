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


class RelaxedNodeA7(RelaxedNode):
    """ If no results, return empty string instead of empty list
    """

    def __getitem__(self, name):
        val = super(RelaxedNodeA7, self).__getitem__(name)

        if not val:
            return ['']

        return val


class A7Item(Item):
    def __init__(self, parent, node):

        super(A7Item, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNodeA7(node, NSMAP)

        attrs = [
            ('CA code (EU, national)', self.ca_code),
            ('Acronym, Name (national)', self.acronym_name),
            ('Address', self.address),
            ('URL', self.url),
            ('Legal status', self.legal_status),
            ('Responsibilities', self.responsibilities),
            ('Reference', self.reference),
            ('Membership', self.membership),
            ('Regional coordination', self.regional_coord),
        ]

        for title, getter in attrs:
            self[title] = getter()

    def ca_code(self):
        v = self.g['w:MSCACode/text()']

        return v and v[0] or ''

    def acronym_name(self):
        acronym = self.g['w:Acronym/text()'][0]
        comp_auth_name = self.g['w:CompetentAuthorityName/text()'][0]
        comp_auth_name_nl = self.g['w:CompetentAuthorityNameNL/text()'][0]

        comp_auth = u"{} ({})".format(comp_auth_name, comp_auth_name_nl)
        v = acronym and "{}: {}".format(acronym, comp_auth) or comp_auth

        return v or ''

    def address(self):
        street = self.g['w:Street/text()'][0]
        city = self.g['w:City/text()'][0]
        city_nl = self.g['w:CityNL/text()'][0]
        country = self.g['w:Country/text()'][0]
        postcode = self.g['w:Postcode/text()'][0]

        v = u", ".join((street, "/".join((city, city_nl)), country, postcode))

        return v or ''

    def url(self):
        v = self.g['w:URL/text()']

        return v and v[0] or ''

    def legal_status(self):
        v = self.g['w:LegalStatus/text()']

        return v and v[0] or ''

    def responsibilities(self):
        v = self.g['w:Responsibilities/text()']

        return v and v[0] or ''

    def reference(self):
        v = self.g['w:Reference/text()']

        return v and v[0] or ''

    def membership(self):
        v = self.g['w:Membership/text()']

        return v and v[0] or ''

    def regional_coord(self):
        v = self.g['w:RegionalCoordination/text()']

        return v and v[0] or ''


class Article7(BaseArticle2012):
    # TODO not implemented, copy of Article 8
    """ Article 3 & 4 implementation

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-secondary.pt')
    help_text = ""

    def setup_data(self):
        filename = self.context.get_report_filename()
        text = get_xml_report_data(filename)
        root = fromstring(text)

        # basic algorthim to detect what type of report it is
        article = self.article

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        cols = []
        nodes = xp('//w:CompetentAuthority', root)

        for node in nodes:
            item = A7Item(self, node)
            cols.append(item)

        self.rows = []

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
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

        self.cols = cols

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
                    if not isinstance(value, basestring):
                        continue
                    if value not in seen:
                        retrieve_translation(self.country_code, value)
                        seen.add(value)

        return ''
