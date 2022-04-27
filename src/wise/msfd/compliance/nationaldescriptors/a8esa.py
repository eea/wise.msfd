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
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow, 
                             RelaxedNode, Row)

from ..base import BaseArticle2012
from .data import REPORT_DEFS
import six

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


def xp(xpath, node):
    if not node:
        return []

    return node.xpath(xpath, namespaces=NSMAP)


class A8ESAUsesActivityItem(Item):
    def __init__(self, parent, node):

        super(A8ESAUsesActivityItem, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        attrs = [
            ('Feature', self.feature()),
            ('Description of use/activity', self.description_activity()),
            ('Proportion of area with use/activity', self.proportion_area()),
            ('Proportion of area with use/activity: confidence', 
                self.proportion_area_confidence()),
            ('NACE codes', self.nace_codes()),
            ('Trends (recent)', self.trends_recent()),
            ('Trends period (recent)', self.trends_period_recent()),
            ('Trends (future)', self.trends_future()),
            ('Trends period (future)', self.trends_period_future()),
            ('Limitations', self.limitations()),
            ('Production value: description', self.production_description()),
            ('Production value: € millions', self.production_millions()),
            ('Production value: confidence', self.production_confidence()),
            ('Production value: limitations', self.production_limitations()),
            ('Value added: description', self.value_added_description()),
            ('Value added: € millions', self.value_added_millions()),
            ('Value added: confidence', self.value_added_confidence()),
            ('Value added: limitations', self.value_added_limitations()),
            ('Employment: description', self.employment_description()),
            ('Employment (direct): *1000 FTE', self.employment_direct()),
            ('Employment: confidence', self.employment_confidence()),
            ('Employment: limitations', self.employment_limitations()),
        ]

        # Other indicators are added dinamically
        import pdb; pdb.set_trace()
        other_indicator_nodes = xp('//w:UseActivity/w:OtherIndicators', node)

        for other_indicator in other_indicator_nodes:
            other_indicator = RelaxedNode(other_indicator, NSMAP)
            attrs.append(('Other indicators: name', self.other_name(other_indicator)))
            attrs.append(('Other indicators: description', self.other_description(other_indicator)))
            attrs.append(('Other indicators: value/units', self.other_value(other_indicator)))
            attrs.append(('Other indicators: value/units confidence', self.other_value_confidence(other_indicator)))

        # for title, value in attrs:
        #     self[title] = value
        #     setattr(self, title, value)

        self.attributes = attrs

    def feature(self):
        v = self.g['w:ReportingFeature/text()']

        return v and v[0] or ''

    def description_activity(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:Description/text()']

        return v and v[0] or ''

    def proportion_area(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:SumInfo1/text()']

        return v and v[0] or ''

    def proportion_area_confidence(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse'
                   '/w:SumInfo1Confidence/text()']

        return v and v[0] or ''
    
    def nace_codes(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:SumInfo2/text()']

        return v and v[0] or ''

    def trends_recent(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:TrendsRecent/text()']

        return v and v[0] or ''
    
    def trends_period_recent(self):
        start = self.g['w:UseActivity/w:CharacteristicsUse'
                       '/w:RecentTimeStart/text()']
        end = self.g['w:UseActivity/w:CharacteristicsUse'
                     '/w:RecentTimeEnd/text()']
        start = start and start[0] or ''
        end = end and end[0] or ''
        v = "{}-{}".format(start, end)

        return v

    def trends_future(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:TrendsFuture/text()']

        return v and v[0] or ''
    
    def trends_period_future(self):
        start = self.g['w:UseActivity/w:CharacteristicsUse/w:FutureTimeStart/text()']
        end = self.g['w:UseActivity/w:CharacteristicsUse/w:FutureTimeEnd/text()']
        start = start and start[0] or ''
        end = end and end[0] or ''
        v = "{}-{}".format(start, end)

        return v
    
    def limitations(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:Limitations/text()']

        return v and v[0] or ''

    def production_description(self):
        v = self.g['w:UseActivity/w:ProductionValue/w:Description/text()']

        return v and v[0] or ''

    def production_millions(self):
        v = self.g['w:UseActivity/w:ProductionValue/w:SumInfo1/text()']

        return v and v[0] or ''

    def production_confidence(self):
        v = self.g['w:UseActivity/w:ProductionValue/w:SumInfo1Confidence/text()']

        return v and v[0] or ''

    def production_limitations(self):
        v = self.g['w:UseActivity/w:ProductionValue/w:Limitations/text()']

        return v and v[0] or ''

    def value_added_description(self):
        v = self.g['w:UseActivity/w:ValueAdded/w:Description/text()']

        return v and v[0] or ''

    def value_added_millions(self):
        v = self.g['w:UseActivity/w:ValueAdded/w:SumInfo1/text()']

        return v and v[0] or ''

    def value_added_confidence(self):
        v = self.g['w:UseActivity/w:ValueAdded/w:SumInfo1Confidence/text()']

        return v and v[0] or ''

    def value_added_limitations(self):
        v = self.g['w:UseActivity/w:ValueAdded/w:Limitations/text()']

        return v and v[0] or ''

    def employment_description(self):
        v = self.g['w:UseActivity/w:Employment/w:Description/text()']

        return v and v[0] or ''

    def employment_direct(self):
        v = self.g['w:UseActivity/w:Employment/w:SumInfo1/text()']

        return v and v[0] or ''

    def employment_confidence(self):
        v = self.g['w:UseActivity/w:Employment/w:SumInfo1Confidence/text()']

        return v and v[0] or ''

    def employment_limitations(self):
        v = self.g['w:UseActivity/w:Employment/w:Limitations/text()']

        return v and v[0] or ''

    def other_name(self, other_indicator):
        v = other_indicator['w:IndicatorName/text()']

        return v and v[0] or ''

    def other_description(self, other_indicator):
        v = other_indicator['w:Description/text()']

        return v and v[0] or ''

    def other_value(self, other_indicator):
        v = other_indicator['w:SumInfo1/text()']

        return v and v[0] or ''

    def other_value_confidence(self, other_indicator):
        v = other_indicator['w:SumInfo1Confidence/text()']

        return v and v[0] or ''


class Article8ESA(BaseArticle2012):
    # TODO not implemented, copy of Article 8
    """ Article 8.1c ESA implementation for national descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-secondary-2012.pt')
    help_text = ""

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, filename=None):

        super(Article8ESA, self).__init__(
            context, request, country_code, region_code, descriptor, article,
            muids)

        self.filename = filename

    def setup_data(self):
        filename = self.filename
        text = get_xml_report_data(filename)
        root = fromstring(text)
        node_names = ['UsesActivity']

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][self.article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        items = []

        for name in node_names:
            nodes = xp('//w:' + name, root)

            for node in nodes:
                item = A8ESAUsesActivityItem(self, node)
                items.append(item)

        self.rows = []
        self.cols = items

        if not items:
            return

        for index, (name, value) in enumerate(items[0].attributes):
            values = []
            
            for inner in items:
                attrs = inner.attributes

                values.append(attrs[index][1])

            raw_values = []
            vals = []

            for v in values:
                raw_values.append(v)
                vals.append(self.context.translate_value(
                    name, v, self.country_code))

            row = RawRow(name, vals, raw_values)
            self.rows.append(row)

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
