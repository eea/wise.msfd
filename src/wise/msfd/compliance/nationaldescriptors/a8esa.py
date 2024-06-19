#pylint: skip-file
from __future__ import absolute_import

import logging
import re
from collections import defaultdict

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.data import get_xml_report_data
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, RawRow, RelaxedNode)

from ..base import BaseArticle2012
from .data import REPORT_DEFS
import six

logger = logging.getLogger('wise.msfd')
NODE_NAME_SUB = re.compile(r'\s\(\d+\)$')

NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


def xp(xpath, node):
    if not node:
        return []

    return node.xpath(xpath, namespaces=NSMAP)


class A8ESAMetadataItem(Item):
    def __init__(self, parent, node):

        super(A8ESAMetadataItem, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        attrs = [
            ('Topic', self.topic()),
            ('Assessment date (start-end)', self.assessment_date()),
            ('Method used', self.method_used()),
            ('Sources', self.sources()),
        ]

        for title, value in attrs:
            self[title] = value
            setattr(self, title, value)

        self.attributes = attrs

    def topic(self):
        v = self.g['w:Topic/text()']

        return v and v[0] or ''

    def assessment_date(self):
        start = self.g['w:AssessmentStartDate/text()']
        end = self.g['w:AssessmentEndDate/text()']
        start = start and start[0] or ''
        end = end and end[0] or ''
        v = u"{}-{}".format(start, end)

        return v
    
    def method_used(self):
        v = self.g['w:MethodUsed/text()']

        return v and v[0] or ''

    def sources(self):
        v = self.g['w:Sources/text()']

        return v and v[0] or ''


class A8ESAThemesItem(Item):
    def __init__(self, parent, node):

        super(A8ESAThemesItem, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        attrs = [
            ('Feature', self.feature()),
            ('Characteristics: description', self.characteristics_descr()),
            ('Characteristics: limitations', self.characteristics_limit()),
            ('Cost of degradation: description', self.cod_description()),
            ('Cost of degradation: value', self.cod_value()),
            ('Cost of degradation: value confidence', self.cod_confidence()),
            ('Characteristics: information gaps', self.characteristics_info()),
            ('Pressure 1 (rank)', self.pressure_rank1()),
            ('Pressure 2 (rank)', self.pressure_rank2()),
            ('Pressure 3 (rank)', self.pressure_rank3()),
        ]

        for title, value in attrs:
            self[title] = value
            setattr(self, title, value)

        self.attributes = attrs

    def feature(self):
        v = self.g['w:ReportingFeature/text()']

        return v and v[0] or ''

    def characteristics_descr(self):
        v = self.g['w:Theme/w:CharacteristicsTheme/w:Description/text()']

        return v and v[0] or ''

    def characteristics_limit(self):
        v = self.g['w:Theme/w:CharacteristicsTheme/w:Limitations/text()']

        return v and v[0] or ''

    def cod_description(self):
        v = self.g['w:Theme/w:CostDegradationTheme/w:Description/text()']

        return v and v[0] or ''

    def cod_value(self):
        v = self.g['w:Theme/w:CostDegradationTheme/w:SumInfo1/text()']

        return v and v[0] or ''

    def cod_confidence(self):
        v = self.g['w:Theme/w:CostDegradationTheme/w:SumInfo1Confidence/text()']

        return v and v[0] or ''

    def characteristics_info(self):
        v = self.g['w:Theme/w:InfoGaps/text()']

        return v and v[0] or ''

    def assessment_date(self):
        start = self.g['w:AssessmentStartDate/text()']
        end = self.g['w:AssessmentEndDate/text()']
        start = start and start[0] or ''
        end = end and end[0] or ''
        v = u"{}-{}".format(start, end)

        return v
    
    def pressures_description(self):
        v = self.g['w:Pressures/w:Description/text()']

        return v and v[0] or ''
    
    def pressure_rank1(self):
        pressure = self.g['w:Pressures/w:Pressure1/text()']
        rank = self.g['w:Pressures/w:Rank1/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank2(self):
        pressure = self.g['w:Pressures/w:Pressure2/text()']
        rank = self.g['w:Pressures/w:Rank2/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank3(self):
        pressure = self.g['w:Pressures/w:Pressure3/text()']
        rank = self.g['w:Pressures/w:Rank3/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v



class A8ESAEcosystemServicesItem(Item):
    def __init__(self, parent, node):

        super(A8ESAEcosystemServicesItem, self).__init__([])

        self.parent = parent
        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        attrs = [
            ('Feature', self.feature()),
            ('Characteristics: description', self.characteristics_descr()),
            ('Characteristics: CICES class', self.characteristics_cices()),
            ('Characteristics: limitations', self.characteristics_limit()),
            ('Characteristics: information gaps', self.characteristics_info()),
        ]
        dependencies_nodes = xp('w:EcosystemService/w:Dependencies', node)

        for index, dependency in enumerate(dependencies_nodes):
            dependency = RelaxedNode(dependency, NSMAP)
            attrs.append(('Dependencies ({})'.format(index + 1), 
                self.dependencies(dependency)))

        attrs_extended = [
            ('Pressures: description', self.pressures_description()),
            ('Pressure 1 (rank)', self.pressure_rank1()),
            ('Pressure 2 (rank)', self.pressure_rank2()),
            ('Pressure 3 (rank)', self.pressure_rank3()),
        ]
        attrs.extend(attrs_extended)

        for title, value in attrs:
            self[title] = value
            setattr(self, title, value)

        self.attributes = attrs

    def feature(self):
        v = self.g['w:ReportingFeature/text()']

        return v and v[0] or ''
    
    def characteristics_descr(self):
        v = self.g['w:EcosystemService/w:CharacteristicsEcosystem/w:Description/text()']

        return v and v[0] or ''

    def characteristics_cices(self):
        v = self.g['w:EcosystemService/w:CharacteristicsEcosystem/w:SumInfo2/text()']

        return v and v[0] or ''

    def characteristics_limit(self):
        v = self.g['w:EcosystemService/w:CharacteristicsEcosystem/w:Limitations/text()']

        return v and v[0] or ''

    def characteristics_info(self):
        v = self.g['w:EcosystemService/w:InfoGaps/text()']

        return v and v[0] or ''

    def dependencies(self, dependency):
        dep = dependency['w:Dependency/text()']
        other = dependency['w:Other/text()']
        dep = dep and dep[0] or ''
        other = other and other[0] or ''
        v = u"-".join((dep, other))

        return v

    def pressures_description(self):
        v = self.g['w:Pressures/w:Description/text()']

        return v and v[0] or ''
    
    def pressure_rank1(self):
        pressure = self.g['w:Pressures/w:Pressure1/text()']
        rank = self.g['w:Pressures/w:Rank1/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank2(self):
        pressure = self.g['w:Pressures/w:Pressure2/text()']
        rank = self.g['w:Pressures/w:Rank2/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank3(self):
        pressure = self.g['w:Pressures/w:Pressure3/text()']
        rank = self.g['w:Pressures/w:Rank3/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

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
        other_indicator_nodes = xp('w:UseActivity/w:OtherIndicators', node)

        for index, other_indicator in enumerate(other_indicator_nodes):
            other_indicator = RelaxedNode(other_indicator, NSMAP)
            attrs.append(('Other indicators: name ({})'.format(index + 1), 
                self.other_name(other_indicator)))
            attrs.append(
                ('Other indicators: description ({})'.format(index + 1), 
                self.other_description(other_indicator)))
            attrs.append(
                ('Other indicators: value/units ({})'.format(index + 1),
                self.other_value(other_indicator)))
            attrs.append(
                ('Other indicators: value/units confidence ({})'
                    .format(index + 1),
                self.other_value_confidence(other_indicator)))

        attrs_extended = [
            ('Information gaps', self.info_gaps()),
            ('Dependencies', self.dependencies()),
            ('Pressures: description', self.pressures_description()),
            ('Pressure 1 (rank)', self.pressure_rank1()),
            ('Pressure 2 (rank)', self.pressure_rank2()),
            ('Pressure 3 (rank)', self.pressure_rank3()),
        ]

        attrs.extend(attrs_extended)

        for title, value in attrs:
            self[title] = value
            setattr(self, title, value)
       

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
        v = u"{}-{}".format(start, end)

        return v

    def trends_future(self):
        v = self.g['w:UseActivity/w:CharacteristicsUse/w:TrendsFuture/text()']

        return v and v[0] or ''
    
    def trends_period_future(self):
        start = self.g['w:UseActivity/w:CharacteristicsUse/w:FutureTimeStart/text()']
        end = self.g['w:UseActivity/w:CharacteristicsUse/w:FutureTimeEnd/text()']
        start = start and start[0] or ''
        end = end and end[0] or ''
        v = u"{}-{}".format(start, end)

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

    def info_gaps(self):
        v = self.g['w:UseActivity/w:InfoGaps/text()']

        return v and v[0] or ''

    def dependencies(self):
        v = self.g['w:UseActivity/w:Dependencies/w:Dependency/text()']

        return v and v[0] or ''

    def pressures_description(self):
        v = self.g['w:Pressures/w:Description/text()']

        return v and v[0] or ''

    def pressure_rank1(self):
        pressure = self.g['w:Pressures/w:Pressure1/text()']
        rank = self.g['w:Pressures/w:Rank1/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank2(self):
        pressure = self.g['w:Pressures/w:Pressure2/text()']
        rank = self.g['w:Pressures/w:Rank2/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v

    def pressure_rank3(self):
        pressure = self.g['w:Pressures/w:Pressure3/text()']
        rank = self.g['w:Pressures/w:Rank3/text()']
        pressure = pressure and pressure[0] or ''
        rank = rank and rank[0] or ''
        v = u"{}-{}".format(pressure, rank)

        return v


class Article8ESA(BaseArticle2012):
    # TODO not implemented, copy of Article 8
    """ Article 8.1c ESA implementation for national descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-secondary-2012.pt')
    help_text = ""

    nodes_implementation = {
        "Metadata": A8ESAMetadataItem,
        "UsesActivity": A8ESAUsesActivityItem,
        "EcosystemServices": A8ESAEcosystemServicesItem,
        "Themes": A8ESAThemesItem,
    }

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

        # override the default translatable
        fields = REPORT_DEFS[self.context.year][self.article]\
            .get_translatable_fields()
        self.context.TRANSLATABLES.extend(fields)

        items_grouped = defaultdict(list)
        node_names = self.nodes_implementation.keys()

        for node_name in node_names:
            nodes = xp('//w:' + node_name, root)

            for node in nodes:
                implementation_class = self.nodes_implementation[node_name]
                item = implementation_class(self, node)
                items_grouped[node_name].append(item)

        self.cols = items_grouped
        self.rows = []
        self.grouped_rows = []

        if not items_grouped:
            return

        for node_name in node_names:
            items = items_grouped[node_name]
            rows = []

            if not items:
                self.grouped_rows.append((node_name, rows))
                continue

            for index, (name, value) in enumerate(items[0].attributes):
                values = []
                
                for inner in items:
                    # attrs = inner.attributes

                    # values.append(attrs[index][1])
                    values.append(inner.get(name, ''))

                raw_values = []
                vals = []

                for v in values:
                    raw_values.append(v)
                    name_norm = NODE_NAME_SUB.sub('', name)
                    translated = self.context.translate_value(
                        name_norm, v, self.country_code) 

                    vals.append(translated)

                row = RawRow(name, vals, raw_values)
                
                self.rows.append(row)
                rows.append(row)

            self.grouped_rows.append((node_name, rows))

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
