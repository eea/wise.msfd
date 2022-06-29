
from __future__ import absolute_import
from collections import namedtuple

import logging

from lxml.etree import fromstring, XMLSyntaxError

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.data import get_report_filename, get_xml_report_data
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemListFiltered, 
                             RelaxedNodeEmpty, SingeHeaderRow)

from ..base import BaseArticle2012
import six

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


SUBEMPTY = fromstring('<SubProgramme/>')
FIELD = namedtuple("Field", ["group_name", "name", "title",
                             "article", "section", "setlevel"])


def xp(xpath, node):
    return node.xpath(xpath, namespaces=NSMAP)


class A13Item(Item):
    def __init__(self, context, measure_node, mru):

        super(A13Item, self).__init__([])
        
        self.mru_name = mru and mru[0].text or ''
        self.context = context
        self.mnode = measure_node
        self.mrelax = RelaxedNodeEmpty(measure_node, NSMAP)

        attrs = [
            ('MarineUnitID', self.mru),
            ('Features', self.default),
            ('KTM', self.ktm),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

    def default(self):
        return ''

    def mru(self):
        return self.mru_name

    def ktm(self):
        return self.mrelax['KTM/text()'][0]

    def programme_id(self):
        return self.mpr['ReferenceExistingProgramme/ProgrammeID/text()'][0]

    def q4e_prog(self):
        return self.mpr['MonitoringProgramme/Q4e_ProgrammeID/text()'][0]

    def q4f_prog(self):
        v = self.mpr['MonitoringProgramme/Q4f_ProgrammeDescription/text()'][0]

        return v

    def q5e_natural(self):
        v = self.mpr['MonitoringProgramme/Q5e_NaturalVariablity/text()'][0]
        other = self.mpr['.//Q5e_NaturalVariablity/Q5e_Other/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q5c_habitats(self):
        v = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                     '/Habitats/text()']
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts/Habitats' \
                         '/Q5c_HabitatsOther/text()']

        return ItemListFiltered(v + other)


class Article13(BaseArticle2012):
    """ Article 13 implementation for 2016 year

    klass(self, self.request, country_code, region_code,
          descriptor, article,  muids)

        1. Get the report filename with a sparql query
        2. With the filename get the report url from CDR
        3. Get the data from the xml file
    """

    # template = Template('pt/report-data-secondary.pt')
    template = Template('pt/report-data-art13.pt')
    help_text = ""
    available_regions = []
    translatable_extra_data = []
    is_regional = False

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, filenames=None):

        super(Article13, self).__init__(context, request, country_code,
                                        region_code, descriptor, article,
                                        muids)
        self._filename = filenames

    @property
    def sort_order(self):
        order = ('MarineUnitID',)

        return order

    def get_report_filename(self):
        if self._filename:
            return self._filename

        filename = get_report_filename(
            '2016',
            self.country_code,
            self.region_code,
            self.article,
            self.descriptor,
        )

        return filename

    def get_report_file_root(self, filename=None):
        if not filename:
            filename = self.get_report_filename()

        text = get_xml_report_data(filename)

        root = fromstring(text)

        return root

    def _make_item(self, measure_node, mru):
        item = A13Item(self, measure_node, mru)

        return item

    def auto_translate(self):
        try:
            self.setup_data()
        except AssertionError:
            return

        translatables = self.context.TRANSLATABLES
        seen = set()

        for row in self.rows:
            if not row:
                continue

            if row.field.name not in translatables:
                continue

            for value in row.raw_values:
                if not isinstance(value, six.string_types):
                    continue

                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        return ''

    def items_to_rows(self, items):
        rep_fields = self.context.get_report_definition()
        self.rows = []

        for field in rep_fields:
            field_name = field.name
            values = []

            for inner in items:
                values.append(inner.get(field_name, ''))

            raw_values = []
            vals = []

            for v in values:
                raw_values.append(v)

                vals.append(self.context.translate_value(
                    field_name, v, self.country_code))

            row = SingeHeaderRow(
                self.context, self.request, field, vals, raw_values)
            self.rows.append(row)

    def setup_data(self):
        descriptor_class = get_descriptor(self.descriptor)
        all_ids = descriptor_class.all_ids()
        self.descriptor_label = descriptor_class.title

        if self.descriptor.startswith('D1.'):
            all_ids.add('D1')

        fileurl = self._filename

        try:
            root = self.get_report_file_root(fileurl)
        except XMLSyntaxError:
            pass

        nodes = xp('//Measures', root)
        mru = xp('//MarineUnitID', root)
        items = []

        for node in nodes:
            # filter empty nodes
            if not node.getchildren():
                continue

            # filter mp node by ges criteria
            ges_crit = xp('.//RelevantGESDescriptors', node)
            if ges_crit:
                ges_crit_text = ges_crit[0].text
                ges_crit = (
                        ges_crit_text
                        and set(ges_crit_text.split(' '))
                        or set()
                )

            if not all_ids.intersection(ges_crit):
                continue

            item = self._make_item(node, mru)
            items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        self.cols = items
        self.items_to_rows(items)

    def __call__(self):
        self.setup_data()

        return self.template(data=self.rows)
