import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.data import get_report_filename, get_xml_report_data
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemListFiltered, Node, RawRow,
                             RelaxedNode, RelaxedNodeEmpty, Row,
                             natural_sort_key, to_html)

from ..base import BaseArticle2012
from .data import REPORT_DEFS

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


SUBEMPTY = fromstring('<SubProgramme/>')


def xp(xpath, node):
    return node.xpath(xpath, namespaces=NSMAP)


class A11Item(Item):
    def __init__(self, parent, mp_node, subprog_node, subprog_name):

        super(A11Item, self).__init__([])

        self.mp_name = mp_node.tag
        self.subprog_node = subprog_node
        self.subprog_name = subprog_name
        self.parent = parent
        self.mp_node = mp_node
        self.mpr = RelaxedNodeEmpty(mp_node, NSMAP)
        self.subr = RelaxedNodeEmpty(subprog_node, NSMAP)

        attrs = [
            ('MonitoringProgrammeName', self.node_name),
            ('ProgrammeID', self.programme_id),
            ('MarineUnitID', self.mru),
            ('Q4e_ProgrammeID', self.q4e_prog),
            ('Q4f_ProgrammeDescription', self.q4f_prog),
            ('Q5e_NaturalVariablity', self.q5e_natural),
            ('Q5d_AdequateData', self.q5d_adequate),
            ('Q5d_EstablishedMethods', self.q5d_establish),
            ('Q5d_AdequateUnderstandingGES', self.q5d_understanding),
            ('Q5d_AdequateCapacity', self.q5d_capacity),
            ('Q5f_DescriptionGES', self.q5f_description),
            ('Q5g_GapFillingDateGES', self.q5g_gap),
            ('Q5h_PlansGES', self.q5h_plans),
            ('Q6a_EnvironmentalTarget', self.q6a_env),
            ('Q6a_AssociatedIndicator', self.q6a_indic),
            ('Q6b_AdequateData', self.q6b_adequate),
            ('Q6b_EstablishedMethods', self.q6b_method),
            ('Q6b_AdequateCapacity', self.q6b_capacity),
            ('Q6c_Target', self.q6c_target),
            ('Q6d_DescriptionTargets', self.q6d_description),
            ('Q6e_GapFillingDateTargets', self.q6e_gapfill),
            ('Q6f_PlansTargets', self.q6f_plans),
            ('Q7a_RelevantActivities', self.q7a_activities),
            ('Q7c_RelevantMeasures', self.q7c_measures),
            ('Q7e_AdequateData', self.q7e_adequate),
            ('Q7e_EstablishedMethods', self.q7e_methods),
            ('Q7e_AdequateUnderstandingGES', self.q7e_understanding_ges),
            ('Q7e_AdequateCapacity', self.q7e_capacity),
            ('Q7e_AddressesActivitiesPressures', self.q7e_activ_press),
            ('Q7e_AddressesEffectiveness', self.q7e_effectiveness),
            ('Q7d_DescriptionMeasures', self.q7d_description),
            ('Q7f_GapFillingDateActivitiesMeasures', self.q7f_gapfilling),
            ('Q8a_LinksExistingMonitoringProgrammes', self.q8a_links),
            ('SubMonitoringProgrammeID', self.subprog_id),
            ('SubMonitoringProgrammeName', self.subprogramme_name),
            ('Q4g_SubProgrammeID', self.subprog_id),
            ('SubMonitoringProgrammeName2', self.subprogramme_name),
            ('Q4k_Purpose', self.q4k_purpose),
            ('Q4l_LinksProgrammesDirectivesConventions', self.q4k_links),
            ('Habitats', self.q5c_habitats),
            ('SpeciesList', self.q5c_species),
            ('PhysicalChemicalFeatures', self.q5c_physical),
            ('Pressures', self.q5c_pressures),
            ('Q9a_ElementMonitored', self.q9a_element),
            ('Q5a_RelevantGESCriteria', self.q5a_gescrit),
            ('Q5b_RelevantGESIndicators', self.q5a_gesindicator),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

    def default(self):
        return ''

    def node_name(self):
        return self.mp_name

    def programme_id(self):
        return self.mpr['ReferenceExistingProgramme/ProgrammeID/text()'][0]

    def mru(self):
        v = self.mpr['ReferenceExistingProgramme/MarineUnitID/text()']

        return ItemListFiltered(v)

    def q4e_prog(self):
        return self.mpr['MonitoringProgramme/Q4e_ProgrammeID/text()'][0]

    def q4f_prog(self):
        v = self.mpr['MonitoringProgramme/Q4f_ProgrammeDescription/text()'][0]

        return v

    def q5e_natural(self):
        v = self.mpr['MonitoringProgramme/Q5e_NaturalVariablity/text()'][0]
        other = self.mpr['.//Q5e_NaturalVariablity/Q5e_Other/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q5d_adequate(self):
        v = self.mpr['.//Q5d_AdequateData/text()'][0]

        return v

    def q5d_establish(self):
        v = self.mpr['.//Q5d_EstablishedMethods/text()'][0]

        return v

    def q5d_understanding(self):
        v = self.mpr['.//Q5d_AdequateUnderstandingGES/text()'][0]

        return v

    def q5d_capacity(self):
        v = self.mpr['.//Q5d_AdequateCapacity/text()'][0]

        return v

    def q5f_description(self):
        v = self.mpr['.//Q5f_DescriptionGES/text()'][0]

        return v

    def q5g_gap(self):
        v = self.mpr['.//Q5g_GapFillingDateGES/text()'][0]

        return v

    def q5h_plans(self):
        v = self.mpr['.//Q5h_PlansGES/text()'][0]

        return v

    def q6a_env(self):
        v = self.mpr['.//Q6a_EnvironmentalTarget/text()'][0].split(' ')

        return ItemListFiltered(v)

    def q6a_indic(self):
        v = self.mpr['.//Q6a_AssociatedIndicator/text()'][0].split(' ')

        return ItemListFiltered(v)

    def q6b_adequate(self):
        v = self.mpr['.//Q6b_SuitableData/text()'][0]

        return v

    def q6b_method(self):
        v = self.mpr['.//Q6b_EstablishedMethods/text()'][0]

        return v

    def q6b_capacity(self):
        v = self.mpr['.//Q6b_AdequateCapacity/text()'][0]

        return v

    def q6c_target(self):
        v = self.mpr['.//Q6c_Target/text()'][0]

        return v

    def q6d_description(self):
        v = self.mpr['.//Q6d_DescriptionTargets/text()'][0]

        return v

    def q6e_gapfill(self):
        v = self.mpr['.//Q6e_GapFillingDateTargets/text()'][0]

        return v

    def q6f_plans(self):
        v = self.mpr['.//Q6f_PlansTargets/text()'][0]

        return v

    def q7a_activities(self):
        v = self.mpr['.//Q7a_RelevantActivities/text()'][0]
        other = self.mpr['.//Q7a_UsesActivitiesOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q7c_measures(self):
        v = self.mpr['.//Q7c_RelevantMeasure/text()']

        return ItemListFiltered(v)

    def q7e_adequate(self):
        v = self.mpr['.//Q7e_AdequateData/text()'][0]

        return v

    def q7e_methods(self):
        v = self.mpr['.//Q7e_EstablishedMethods/text()'][0]

        return v

    def q7e_understanding_ges(self):
        v = self.mpr['.//Q7e_AdequateUnderstandingGES/text()'][0]

        return v

    def q7e_capacity(self):
        v = self.mpr['.//Q7e_AdequateCapacity/text()'][0]

        return v

    def q7e_activ_press(self):
        v = self.mpr['.//Q7e_AddressesActivitiesPressures/text()'][0]

        return v

    def q7e_effectiveness(self):
        v = self.mpr['.//Q7e_AddressesEffectiveness/text()'][0]

        return v

    def q7d_description(self):
        v = self.mpr['.//Q7d_DescriptionMeasures/text()'][0]

        return v

    def q7f_gapfilling(self):
        v = self.mpr['.//Q7f_GapFillingDateActivitiesMeasures/text()'][0]

        return v

    def q8a_links(self):
        v = self.mpr['.//Q7f_GapFillingDateActivitiesMeasures/text()'][0]
        other = self.mpr['.//Q8a_Other/text()']

        return ItemListFiltered(v.split(' ') + other)

    def subprogramme_name(self):
        return self.subprog_name

    def subprog_id(self):
        return self.subr['Q4g_SubProgrammeID/text()'][0]

    def q4k_purpose(self):
        v = self.subr['.//Q4k_Purpose/text()'][0]

        return v

    def q4k_links(self):
        v = self.subr['.//Q4l_LinksProgrammesDirectivesConventions/text()'][0]

        return v

    def q5c_habitats(self):
        v = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                     '/Habitats/text()'][0]
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts/Habitats' \
                         '/Q5c_HabitatsOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q5c_species(self):
        v = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                     '/SpeciesList/text()'][0]
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts/SpeciesList'\
                         '/Q5c_SpeciesOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q5c_physical(self):
        v = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                     '/PhysicalChemicalFeatures/text()'][0]
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                         '/PhysicalChemicalFeatures' \
                         '/Q5c_PhysicalChemicalOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q9a_element(self):
        v = self.subr['.//Q9a_ElementMonitored/text()'][0]

        return v

    def q5a_gescrit(self):
        v = self.mpr['.//Q5a_RelevantGESCriteria/text()'][0]
        other = self.mpr['.//Q5a_RelevantGESCriteria' \
                         '/Q5a_DescriptionOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q5a_gesindicator(self):
        v = self.mpr['.//Q5b_RelevantGESIndicators/text()'][0]
        other = self.mpr['.//Q5b_RelevantGESIndicators' \
                         '/Q5b_DescriptionOther/text()']

        return ItemListFiltered(v.split(' ') + other)


class Article11(BaseArticle2012):
    """ Article 7 implementation for 2012 year

    klass(self, self.request, country_code, region_code,
          descriptor, article,  muids)

        1. Get the report filename with a sparql query
        2. With the filename get the report url from CDR
        3. Get the data from the xml file
    """

    template = Template('pt/report-data-secondary.pt')
    help_text = ""
    available_regions = []
    translatable_extra_data = []

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, filenames=None):

        super(Article11, self).__init__(context, request, country_code,
                                        region_code, descriptor, article,
                                        muids)

        self._filename = filenames

    @property
    def sort_order(self):
        order = ('MonitoringProgrammeName', 'Q4g_SubProgrammeID')

        return order

    def get_report_filename(self):
        if self._filename:
            return self._filename

        filename = get_report_filename(
            '2014',
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

    def _make_item(self, mp_node, subprog_node, subprog_name):
        item = A11Item(self, mp_node, subprog_node, subprog_name)

        return item

    def setup_data(self):
        descriptor_class = get_descriptor(self.descriptor)
        all_ids = descriptor_class.all_ids()
        self.descriptor_label = descriptor_class.title

        if self.descriptor.startswith('D1.'):
            all_ids.add('D1')

        fileurls = self._filename
        _mp_nodes = []
        _sub_prog_nodes = []

        # separate Monitoring Programmes from Sub Programmes
        for fileurl in fileurls:
            root = self.get_report_file_root(fileurl)

            if root.tag == 'MON':
                nodes = xp('//MonitoringProgrammes/*', root)
                _mp_nodes.extend(nodes)

            if root.tag == 'MONSub':
                nodes = xp('//SubProgrammes/*', root)
                _sub_prog_nodes.extend(nodes)

        # filter duplicate MP nodes, only keep the latest
        mp_seen = []
        mp_nodes = []

        for mp_node in _mp_nodes:
            if mp_node.tag in mp_seen:
                continue

            mp_nodes.append(mp_node)

        # filter duplicate SubProg nodes, only keep the latest
        sub_prog_seen = []
        sub_prog_nodes = []

        for sub_node in _sub_prog_nodes:
            subprog_id = xp('./Q4g_SubProgrammeID/text()', sub_node)

            if subprog_id in sub_prog_seen:
                continue

            sub_prog_nodes.append(sub_node)

        items = []
        for mp in mp_nodes:
            # filter empty nodes
            if not mp.getchildren():
                continue

            # filter mp node by ges criteria
            ges_crit = xp('.//Q5a_RelevantGESCriteria', mp)
            if ges_crit:
                ges_crit_text = ges_crit[0].text
                ges_crit = (
                        ges_crit_text
                        and set(ges_crit_text.split(' '))
                        or set()
                )

            if not all_ids.intersection(ges_crit):
                continue

            subprogrammes = xp('.//ReferenceSubProgramme', mp)

            for sub_prog in subprogrammes:
                subprog_id = xp('./SubMonitoringProgrammeID/text()', sub_prog)
                subprog_id = subprog_id[0].replace('.xml', '')
                subp_name = xp('./SubMonitoringProgrammeName/text()', sub_prog)

                sub_prog_node = [
                    x
                    for x in sub_prog_nodes
                    if xp('./Q4g_SubProgrammeID', x)[0].text == subprog_id
                ]
                sub_prog_node = sub_prog_node and sub_prog_node[0] or SUBEMPTY

                item = self._make_item(mp, sub_prog_node, subp_name)
                items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        for item in items:
            for name in item.keys():
                values = []

                for inner in items:
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

        self.cols = items

    def __call__(self):
        self.setup_data()

        return self.template()

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

            if row.title not in translatables:
                continue

            for value in row.raw_values:
                if not isinstance(value, basestring):
                    continue

                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        return ''
