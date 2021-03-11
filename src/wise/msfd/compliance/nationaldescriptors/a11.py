
from collections import namedtuple

import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd.data import get_report_filename, get_xml_report_data
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemListFiltered, Node, RawRow,
                             RelaxedNode, RelaxedNodeEmpty, Row,
                             national_compoundrow, natural_sort_key, to_html)

from ..base import BaseArticle2012

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


SUBEMPTY = fromstring('<SubProgramme/>')
FIELD = namedtuple("Field", ["group_name", "name", "title"])


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
            ('Q7b_DescriptionActivities', self.q7b_description),
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
            ('Species_distribution', self.q9b_spec_distr),
            ('Species_population_size', self.q9b_spec_popsize),
            ('Species_population_characteristics', self.q9b_spec_popchar),
            ('Species_impacts', self.q9b_spec_impact),
            ('Habitat_distribution', self.q9b_hab_distr),
            ('Habitat_extent', self.q9b_hab_extent),
            ('Habitat_condition_physical', self.q9b_hab_cond_phys),
            ('Habitat_condition_biological', self.q9b_hab_cond_bio),
            ('Habitat_impacts', self.q9b_hab_impact),
            ('Pressure_input', self.q9b_pres_input),
            ('Pressure_output', self.q9b_pres_output),
            ('Activity', self.q9b_activity),
            ('Other', self.q9b_other),
            ('Q4i_SpatialScope', self.q4i_spatial),
            ('Q4j_DescriptionSpatialScope', self.q4j_description),
            ('MarineUnitID2', self.mru_mp),
            ('Q4h_StartDate', self.q4h_start_end),
            ('Q9h_TemporalResolutionSampling', self.q9h_temporal),
            ('Q9c_MonitoringMethod', self.q9c_monitoring),
            ('Q9d_DescriptionMethod', self.q9c_description),
            ('Q9e_QualityAssurance', self.q9e_quality),
            ('Q9f_QualityControl', self.q9f_quality_control),
            ('Q9g_Proportion', self.q9g_proportion),
            ('Q9g_NoSamples', self.q9g_samples),
            ('Q9i_DescriptionSampleRepresentivity', self.q9i_description),
            ('Q10a_AggregationData', self.q10a_aggregation),
            ('Q10b_DescriptionDataAggregation', self.q10b_description),
            ('Q10c_DataType', self.q10c_datatype),
            ('Q10c_DataAccessMechanism', self.q10c_data_access),
            ('Q10c_DataAccessRights', self.q10c_data_rights),
            ('Q10c_INSPIREStandard', self.q10c_inspire),
            ('Q10c_DataAvailable', self.q10c_data_available),
            ('Q10c_DataAFrequency', self.q10c_data_freq),
            ('Q10d_DescriptionDataAccess', self.q10d_description),
            ('', self.default)
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
        v = self.mpr['ReferenceExistingProgramme//MarineUnitID/text()']

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
        v = self.mpr['.//Q6a_EnvironmentalTarget/text()'][0]

        # return ItemListFiltered(v)
        return v

    def q6a_indic(self):
        v = self.mpr['.//Q6a_AssociatedIndicator/text()'][0]

        # return ItemListFiltered(v)
        return v

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

    def q7b_description(self):
        v = self.mpr['.//Q7b_DescriptionActivities/text()'][0]

        return v

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
        v = self.mpr['.//Q8a_LinksExistingMonitoringProgrammes/text()'][0]
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
                     '/Habitats/text()']
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts/Habitats' \
                         '/Q5c_HabitatsOther/text()']

        return ItemListFiltered(v + other)

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

    def q5c_pressures(self):
        v = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                     '/Pressures/text()'][0]
        other = self.mpr['.//Q5c_RelevantFeaturesPressuresImpacts' \
                         '/Pressures/Q5c_PressureOther/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q9a_element(self):
        v = self.subr['.//Q9a_ElementMonitored/text()']

        return ItemListFiltered(v)

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

    def q9b_spec_distr(self):
        v = self.subr['.//Species_distribution/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_spec_popsize(self):
        v = self.subr['.//Species_population_size/MeasurementParameter' \
                      '/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_spec_popchar(self):
        v = self.subr['.//Species_population_characteristics' \
                      '/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_spec_impact(self):
        v = self.subr['.//Species_impacts/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_hab_distr(self):
        v = self.subr['.//Habitat_distribution/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_hab_extent(self):
        v = self.subr['.//Habitat_extent/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_hab_cond_phys(self):
        v = self.subr['.//Habitat_condition_physical-chemical' \
                      '/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_hab_cond_bio(self):
        v = self.subr['.//Habitat_condition_biological' \
                      '/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_hab_impact(self):
        v = self.subr['.//Habitat_impacts/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_pres_input(self):
        v = self.subr['.//Pressure_input/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_pres_output(self):
        v = self.subr['.//Pressure_output/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_activity(self):
        v = self.subr['.//Activity/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q9b_other(self):
        v = self.subr['.//Other/MeasurementParameter/text()'][0]

        return ItemListFiltered(v.split(' '))

    def q4i_spatial(self):
        v = self.subr['.//Q4i_SpatialScope/text()'][0]

        return v

    def q4j_description(self):
        v = self.subr['.//Q4j_DescriptionSpatialScope/text()'][0]

        return v

    def mru_mp(self):
        v = self.mpr['.//MonitoringProgramme//MarineUnitID/text()']

        return ItemListFiltered(v)

    def q4h_start_end(self):
        start = self.subr['.//Q4h_StartDate/text()'][0]
        end = self.subr['.//Q4h_EndDate/text()'][0]

        return u"{}-{}".format(start, end)

    def q9h_temporal(self):
        v = self.subr['.//Q9h_TemporalResolutionSampling/text()'][0]
        other = self.subr['.//Q9h_TemporalResolutionSampling/Q9h_Other/text()']

        return ItemListFiltered(v.split(', ') + other)

    def q9c_monitoring(self):
        v = self.subr['.//Q9c_MonitoringMethod/text()'][0]

        return v

    def q9c_description(self):
        v = self.subr['.//Q9d_DescriptionMethod/text()'][0]

        return v

    def q9e_quality(self):
        v = self.subr['.//Q9e_QualityAssurance/text()'][0]
        other = self.subr['.//Q9e_QualityAssurance/Q9e_Other/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q9f_quality_control(self):
        v = self.subr['.//Q9f_QualityControl/text()'][0]

        return v

    def q9g_proportion(self):
        v = self.subr['.//Q9g_Proportion/text()'][0]

        return v

    def q9g_samples(self):
        v = self.subr['.//Q9g_NoSamples/text()'][0]

        return v

    def q9i_description(self):
        v = self.subr['.//Q9i_DescriptionSampleRepresentivity/text()'][0]

        return v

    def q10a_aggregation(self):
        v = self.subr['.//Q10a_AggregationData/text()'][0]
        other = self.subr['.//Q10a_AggregationData/Q10a_Other/text()']

        return ItemListFiltered(v.split(' ') + other)

    def q10b_description(self):
        v = self.subr['.//Q10b_DescriptionDataAggregation/text()'][0]

        return v

    def q10c_datatype(self):
        v = self.subr['.//Q10c_DataType/text()'][0]

        return v

    def q10c_data_access(self):
        v = self.subr['.//Q10c_DataAccessMechanism/text()'][0]

        return v

    def q10c_data_rights(self):
        v = self.subr['.//Q10c_DataAccessRights/text()'][0]

        return v

    def q10c_inspire(self):
        v = self.subr['.//Q10c_INSPIREStandard/text()'][0]

        return v

    def q10c_data_available(self):
        v = self.subr['.//Q10c_DataAvailable/text()'][0]

        return v

    def q10c_data_freq(self):
        v = self.subr['.//Q10c_DataAFrequency/text()'][0]

        return v

    def q10d_description(self):
        v = self.subr['.//Q10d_DescriptionDataAccess/text()'][0]

        return v


class Article11(BaseArticle2012):
    """ Article 11 implementation for 2014 year

    klass(self, self.request, country_code, region_code,
          descriptor, article,  muids)

        1. Get the report filename with a sparql query
        2. With the filename get the report url from CDR
        3. Get the data from the xml file
    """

    # template = Template('pt/report-data-secondary.pt')
    template = Template('pt/report-data-art11.pt')
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
                subprog_id = subprog_id[0].replace('.xml', '').strip()
                subp_name = xp('./SubMonitoringProgrammeName/text()', sub_prog)

                sub_prog_node = [
                    x
                    for x in sub_prog_nodes
                    if xp('./Q4g_SubProgrammeID', x)[0].text == subprog_id
                ]
                sub_prog_node = (len(sub_prog_node) and sub_prog_node[0]
                                 or SUBEMPTY)

                item = self._make_item(mp, sub_prog_node, subp_name[0])
                items.append(item)

        self.rows = []

        items = sorted(items,
                       key=lambda i: [getattr(i, o) for o in self.sort_order])

        # ikeys = items[0].keys()
        rep_fields = self.context.get_report_definition()

        for field in rep_fields:
            field_name = field.name
            values = []

            for inner in items:
                values.append(inner[field_name])

            raw_values = []
            vals = []

            for v in values:
                raw_values.append(v)

                vals.append(self.context.translate_value(
                    field_name, v, self.country_code))

            row = national_compoundrow(self.context, field, vals,
                                       raw_values)
            self.rows.append(row)

        self.cols = items

    def __call__(self):
        self.setup_data()

        return self.template(data=self.rows)


class A11OverviewItem(Item):
    def __init__(self, parent, node):

        super(A11OverviewItem, self).__init__([])

        self.parent = parent
        self.node = node
        self.r = RelaxedNodeEmpty(node, NSMAP)

        attrs = [
            ('Q4a_ResponsibleCompetentAuthority', self.q4a_responsible_ca),
            ('Q4b_ResponsibleOrganisations', self.q4b_responsible_org),
            ('Q4c_RelationshipToCA', self.q4c_relationship),
            ('Q2a_PublicConsultationDates', self.q2a_public_dates),
            ('Q2b_PublicConsultationDescription', self.q2b_public_description),
            ('Q3a_RegionalCooperation', self.q3a_regional_coop),
            ('Q1a_Overall_adequacy', self.q1a_overall_adequacy),
            ('Q1b_GapsGES', self.q1b_gaps_ges),
            ('Q1c_GapsTargets', self.q1c_gaps_targets),
            ('Habitats', self.habitats),
            ('SpeciesFunctionalGroups', self.species),
            ('PhysicalChemicalFeatures', self.physical),
            ('Pressures', self.pressures),
            ('Activities', self.activities),
            ('Q1e_Gaps_Plans', self.q1e_gaps),
            ('Q3b_TransboundaryImpactsFeatures', self.q3b_trans),
            ('Q3c_EnvironmentalChanges', self.q3c_env),
            ('Q3d_SourceContaminantsSeafood', self.q3d_source),
            ('Q3e_AccessAndUseRights', self.q3e_access),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

    def default(self):
        return ''

    def q4a_responsible_ca(self):
        return self.r['Q4a_ResponsibleCompetentAuthority/text()'][0]

    def q4b_responsible_org(self):
        v = self.r['Q4b_ResponsibleOrganisations' \
                      '/Q4b_ResponsibleOrganisation/text()']

        return ItemListFiltered(v)

    def q4c_relationship(self):
        return self.r['Q4c_RelationshipToCA/text()'][0]

    def q2a_public_dates(self):
        nodes = self.r['Q2a_PublicConsultationDates']
        v = []

        for node in nodes:
            start = node.xpath('StartDate/text()')[0]
            end = node.xpath('EndDate/text()')[0]

            v.append('{} / {}'.format(start, end))

        return ItemListFiltered(v)

    def q2b_public_description(self):
        v = self.r['Q2b_PublicConsultationDescription/text()']

        return ItemListFiltered(v)

    def q3a_regional_coop(self):
        v = self.r['Q3a_RegionalCooperation/text()'][0]

        return v

    def q1a_overall_adequacy(self):
        v = self.r['Q1a_Overall_adequacy/text()'][0]

        return v

    def _rows_from_children_nodes(self, nodes):
        res = []

        for node in nodes.getchildren():
            name = node.tag
            value = node.xpath('AddressedByProgramme/text()')[0]
            other = node.xpath('DescriptionOther/text()')

            if other:
                v = [value] + other
                res.append((name, ItemListFiltered(v)))
                continue

            res.append((name, value))

        return res

    def q1b_gaps_ges(self):
        nodes = self.r['Q1b_GapsGES'][0]

        return self._rows_from_children_nodes(nodes)

    def q1c_gaps_targets(self):
        nodes = self.r['Q1c_GapsTargets']
        res = []

        for gap_node in nodes:
            for node in gap_node.getchildren():
                name = node.tag
                value = node.text

                res.append((name, value))

        return res

    def habitats(self):
        nodes = self.r['Q1d_CoverageTargets/Habitats'][0]

        return self._rows_from_children_nodes(nodes)

    def species(self):
        nodes = self.r['Q1d_CoverageTargets/Species_FunctionalGroup'][0]

        return self._rows_from_children_nodes(nodes)

    def physical(self):
        nodes = self.r['Q1d_CoverageTargets/PhysicalChemicalFeatures'][0]

        return self._rows_from_children_nodes(nodes)

    def pressures(self):
        nodes = self.r['Q1d_CoverageTargets/Pressures'][0]

        return self._rows_from_children_nodes(nodes)

    def activities(self):
        nodes = self.r['Q1d_CoverageTargets/Activities'][0]

        return self._rows_from_children_nodes(nodes)

    def q1e_gaps(self):
        v = self.r['Q1e_Gaps_Plans/text()'][0]

        return v

    def q3b_trans(self):
        v = self.r['Q3b_TransboundaryImpactsFeatures/text()'][0]

        return v

    def q3c_env(self):
        v = self.r['Q3c_EnvironmentalChanges/text()'][0]

        return v

    def q3d_source(self):
        v = self.r['Q3d_SourceContaminantsSeafood/text()'][0]

        return v

    def q3e_access(self):
        v = self.r['Q3e_AccessAndUseRights/text()'][0]

        return v


class Article11Overview(Article11):

    def setup_data(self):
        fileurls = self._filename

        for fileurl in fileurls:
            root = self.get_report_file_root(fileurl)

            if root.tag == 'MON':
                node = xp('//GeneralDescription', root)
                break

        item = self._make_item(node[0])
        rep_fields = self.context.get_report_definition()
        self.rows = []

        for field in rep_fields:
            field_name = field.name
            value = item[field_name]

            if field.group_name == 'child_nodes':
                for val in value:
                    title = val[0]
                    _val = val[1]

                    transl = self.context.translate_value(
                                field_name, _val, self.country_code)
                    
                    _field = FIELD(field.title, title, title)

                    row = national_compoundrow(self.context, _field, [transl],
                                               [_val])

                    self.rows.append(row)

                continue

            transl = self.context.translate_value(
                field_name, value, self.country_code)

            row = national_compoundrow(self.context, field, [transl],
                                       [value])
            self.rows.append(row)

        self.cols = [item]

    def _make_item(self, node):
        return A11OverviewItem(self, node)


class Article11Compare(Article11):
    template = Template('pt/report-data-compare.pt')
    is_side_by_side = True

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, data_2020, filenames=None):

        super(Article11Compare, self).__init__(
            context, request, country_code, region_code, descriptor,
            article, muids, filenames)

        self.data_2020 = data_2020

    def __call__(self):
        self.setup_data()

        return self.template(data=self.rows, data_2020=self.data_2020)
