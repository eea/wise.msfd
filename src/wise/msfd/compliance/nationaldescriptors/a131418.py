#pylint: skip-file
from __future__ import absolute_import

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


def xp(xpath, node):
    return node.xpath(xpath, namespaces=NSMAP)


class A13Item(Item):
    def __init__(self, context, measure_node, mru, further_info):

        super(A13Item, self).__init__([])
        
        self.mru_name = mru and mru[0].text or ''
        self.context = context
        self.mnode = measure_node
        self.mrelax = RelaxedNodeEmpty(measure_node, NSMAP)
        self.further_info = None

        if further_info:
            self.further_info = RelaxedNodeEmpty(further_info[0], NSMAP)


        attrs = [
            ('MarineUnitID', self.mru),
            ('UniqueCode', self.unique_code),
            ('Name', self.measure_name),
            ('LinkToExistingPolicies', self.link_existing_policies),
            ('KTM', self.ktm),
            ('RelevantGESDescriptors', self.relevant_ges_descr),
            ('RelevantFeaturesFromMSFDAnnexIII', self.relevant_features),
            ('SpatialScopeGeographicZones', self.spatial_scope),
            ('Further information', self.summary_report),          
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

    def unique_code(self):
        return self.mrelax['UniqueCode/text()'][0]

    def measure_name(self):
        return self.mrelax['Name/text()'][0]

    def link_existing_policies(self):
        items = self.mrelax['LinkToExistingPolicies/text()'] 
        
        return ItemListFiltered(items)

    def relevant_ges_descr(self):
        items = self.mrelax['RelevantGESDescriptors/text()'] 
        
        return ItemListFiltered(items)

    def relevant_features(self):
        items = self.mrelax['RelevantFeaturesFromMSFDAnnexIII/text()'] 
        
        return ItemListFiltered(items)

    def spatial_scope(self):
        items = self.mrelax['SpatialScopeGeographicZones/text()'] 

        if items:
            return 'Reported'

        return ''
    
    def summary_report(self):
        items = self.further_info['*']
        template = u'<a style="cursor: help;" target="_blank" href="{}">{}</a>'
        res = []

        for node in items:
            text = node.text

            if not text:
                continue
            
            # name = "{}: {}".format(node.tag, text.split('/')[-1])
            val = template.format(text, text.split('/')[-1])

            res.append(val)

        return ItemListFiltered(res)


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
        order = ('MarineUnitID', 'UniqueCode', 'KTM')

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

        text = get_xml_report_data(filename, self.country_code)

        root = fromstring(text)

        return root

    def _make_item(self, measure_node, mru, further_info):
        item = A13Item(self, measure_node, mru, further_info)

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
            self.rows = []
            return

        nodes = xp('//Measures', root)
        mru = xp('//MarineUnitID', root)
        further_info = xp('//FurtherInformation', root)
        items = []

        for node in nodes:
            # filter empty nodes
            if not node.getchildren():
                continue

            # filter node by ges criteria
            ges_crit = xp('.//RelevantGESDescriptors/text()', node)
            ges_crit = set(ges_crit)

            if not all_ids.intersection(ges_crit):
                continue

            item = self._make_item(node, mru, further_info)
            items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        self.cols = items
        self.items_to_rows(items)

    def __call__(self):
        self.setup_data()

        has_data = False
        data = []

        for row in self.rows:
            if row.vals:
                has_data = True
                break

        if has_data:
            data = self.rows

        return self.template(data=data)


class A14Item(Item):
    def __init__(self, context, exception_node, mru, further_info):

        super(A14Item, self).__init__([])
        
        self.mru_name = mru and mru[0].text or ''
        self.context = context
        self.mnode = exception_node
        self.mrelax = RelaxedNodeEmpty(exception_node, NSMAP)
        self.further_info = None

        if further_info:
            self.further_info = RelaxedNodeEmpty(further_info[0], NSMAP)

        attrs = [
            ('MarineUnitID', self.mru),
            ('UniqueCode', self.unique_code),
            ('Name', self.measure_name),
            ('KTM', self.ktm),
            ('RelevantGESDescriptors', self.relevant_ges_descr),
            ('RelevantFeaturesFromMSFDAnnexIII', self.relevant_features),
            ('SpatialScopeGeographicZones', self.spatial_scope),
            ('SummaryReport', self.summary_report),          
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

    def unique_code(self):
        return self.mrelax['UniqueCode/text()'][0]

    def measure_name(self):
        return self.mrelax['Name/text()'][0]

    def link_existing_policies(self):
        items = self.mrelax['LinkToExistingPolicies/text()'] 
        
        return ItemListFiltered(items)

    def relevant_ges_descr(self):
        items = self.mrelax['RelevantGESDescriptors/text()'] 
        
        return ItemListFiltered(items)

    def relevant_features(self):
        items = self.mrelax['RelevantFeaturesFromMSFDAnnexIII/text()'] 
        
        return ItemListFiltered(items)

    def spatial_scope(self):
        items = self.mrelax['SpatialScopeGeographicZones/text()'] 
        
        if not items:
            return 'Not reported'

        return ItemListFiltered(items)

    def summary_report(self):
        items = self.further_info['*']
        template = u'<a style="cursor: help;" target="_blank" href="{}">{}</a>'
        res = []

        for node in items:
            text = node.text

            if not text:
                continue
            
            # name = "{}: {}".format(node.tag, text.split('/')[-1])
            val = template.format(text, text.split('/')[-1])

            res.append(val)

        return ItemListFiltered(res)


class Article14(Article13):
    """ Article 14 implementation for 2016 year

    klass(self, self.request, country_code, region_code,
          descriptor, article,  muids)

        1. Get the report filename with a sparql query
        2. With the filename get the report url from CDR
        3. Get the data from the xml file
    """

    @property
    def sort_order(self):
        order = ('MarineUnitID', 'KTM', 'UniqueCode')

        return order

    def _make_item(self, exception_node, mru, further_info):
        item = A14Item(self, exception_node, mru, further_info)

        return item

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
            self.rows = []
            return

        nodes = xp('//Exceptions', root)
        mru = xp('//MarineUnitID', root)
        further_info = xp('//FurtherInformation', root)
        items = []

        for node in nodes:
            # filter empty nodes
            if not node.getchildren():
                continue

            # filter node by ges criteria
            ges_crit = xp('.//RelevantGESDescriptors/text()', node)
            ges_crit = set(ges_crit)

            if not all_ids.intersection(ges_crit):
                continue

            item = self._make_item(node, mru, further_info)
            items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        self.cols = items
        self.items_to_rows(items)

    def __call__(self):
        self.setup_data()

        has_data = False
        data = []

        for row in self.rows:
            if row.vals:
                has_data = True
                break

        if has_data:
            data = self.rows

        return self.template(data=data)


class A18Item(Item):
    def __init__(self, context, exception_node):

        super(A18Item, self).__init__([])
        
        self.context = context
        self.mnode = exception_node
        self.mrelax = RelaxedNodeEmpty(exception_node, NSMAP)
        
        attrs = [
            ('MeasureCode', self.measure_code),
            ('MeasureName', self.measure_name),
            ('Category', self.category),
            ('ImplementationProgress', self.impl_progress),
            ('MeasureWithdrawn', self.measure_withdrawn),
            ('ReasonWithdrawal', self.reason_withdrawal),
            ('ImplementationYear', self.impl_year),
            ('Delay', self.delay),
            ('ReasonDelay', self.reson_delay),
            ('OtherObstacles', self.other_obstacles),
            ('TypeObstacle', self.type_obstacles),
            ('FurtherInformationObstacles', self.further_info_obst),
            ('ProgressDescription', self.progress_descr),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

    def default(self):
        return ''

    def measure_code(self):
        return self.mrelax['MeasureCode/text()'][0]

    def measure_name(self):
        return self.mrelax['MeasureName/text()'][0]

    def category(self):
        return self.mrelax['Category/text()'][0]
    
    def impl_progress(self):
        return self.mrelax['ImplementationProgress/text()'][0]
    
    def measure_withdrawn(self):
        return self.mrelax['MeasureWithdrawn/text()'][0]

    def reason_withdrawal(self):
        return self.mrelax['ReasonWithdrawal/text()'][0]

    def impl_year(self):
        return self.mrelax['ImplementationYear/text()'][0]

    def delay(self):
        return self.mrelax['Delay/text()'][0]

    def reson_delay(self):
        return self.mrelax['ReasonDelay/text()'][0]

    def other_obstacles(self):
        return self.mrelax['OtherObstacles/text()'][0]

    def type_obstacles(self):
        return self.mrelax['TypeObstacle/text()'][0]

    def further_info_obst(self):
        return self.mrelax['FurtherInformationObstacles/text()'][0]

    def progress_descr(self):
        return self.mrelax['ProgressDescription/text()'][0]


class Article18(Article13):
    """ Article 18 implementation for 2016 year

    klass(self, self.request, country_code, region_code,
          descriptor, article,  muids)

        1. Get the report filename with a sparql query
        2. With the filename get the report url from CDR
        3. Get the data from the xml file
    """

    @property
    def sort_order(self):
        order = ('MeasureCode', )

        return order

    def _make_item(self, exception_node):
        item = A18Item(self, exception_node)

        return item

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

        nodes = xp('//MeasureProgress', root)
        items = []

        for node in nodes:
            # filter empty nodes
            if not node.getchildren():
                continue

            # filter node by ges criteria
            ges_crit = xp('.//Descriptor/text()', node)
            ges_crit = set(ges_crit)

            if not all_ids.intersection(ges_crit):
                continue

            item = self._make_item(node)
            items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        self.cols = items
        self.items_to_rows(items)

    def __call__(self):
        self.setup_data()

        return self.template(data=self.rows)
