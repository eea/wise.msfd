from collections import defaultdict

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.Five.browser import BrowserView
from wise.msfd import db, sql

# from .reportdata import ReportData2012


DESCRIPTORS = {}


def register_descriptor(class_):
    DESCRIPTORS[class_.id] = class_

    return class_


class Nutrients(object):
    topic_indicators = {
        'ImpactPressureWaterColumn': ('5.2.1', '5.2.4', '5.2.2'),
        'ImpactPressureSeabedHabitats': ('5.3.2', '5.2.3', '5.3.1'),
        'LevelPressureNConcentration': '5.1.1',
        'LevelPressureNLoad': '5.1.1',
        'LevelPressureOConcentration': '5.1.1',
        'LevelPressureOLoad': '5.1.1',
        'LevelPressureOverall': '5.1.1',
        'LevelPressurePConcentration': '5.1.1',
        'LevelPressurePLoad': '5.1.1',
    }

    topic_groups = (
        ('LevelPressureNConcentration', 'LevelPressurePConcentration',
         'LevelPressureOConcentration', 'ImpactPressureWaterColumn',
         'ImpactPressureSeabedHabitats'),
        ('LevelPressureOverall', ),
        ('LevelPressureNLoad', 'LevelPressurePLoad', 'LevelPressureOLoad'),
    )

    topic_assessment_to_nutrients = {
        'LevelPressureNConcentration': 'NutrientsNitrogen5_1',
        'LevelPressureNLoad': 'NutrientsNitrogen5_1',
        'LevelPressurePConcentration': 'NutrientsPhosphorus5_1',
        'LevelPressurePLoad': 'NutrientsPhosphorus5_1',
        'LevelPressureOConcentration': 'NutrientsOrganicMatter5_1',
        'LevelPressureOLoad': 'NutrientsOrganicMatter5_1',
        'LevelPressureOverall': 'NutrientsOrganicEnrichment5_1',
        'ImpactPressureWaterColumn': 'NutrientsEnrichmentWaterColumn5_2or5_3',
        'ImpactPressureSeabedHabitats':
            'NutrientsEnrichmentSeabedHabitats5_2or5_3',
    }


@register_descriptor
class Descriptor5(Nutrients):
    title = 'D5 Eutrophication'
    id = title.split()[0]

    criterias_order = (
        # descriptor code, indicator
        ('D5', 'Eutrophication'),
        ('5.1.1', 'D5C1'),
        ('5.2.1', 'D5C2'),
        ('5.2.4', 'D5C3'),
        ('5.2.2', 'D5C4'),
        ('5.3.2', 'D5C5'),
        ('5.2.3', 'D5C6'),
        ('5.3.1', 'D5C7'),
        ('GESOther', 'D5C8'),
        ('5.1.2', ''),
        ('5.2', ''),
        ('5.3', '')
    )

    article8_mapper_classes = (
        # theme name / mapper class
        ('Nutrients', sql.MSFD8bNutrient),
    )


class Article8(BrowserView):
    template = Template('pt/compliance-a8.pt')

    def get_suminfo2_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name +
                                    'SumInfo2ImpactedElement')
            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results = defaultdict(list)

            for row in res:
                topic = row.ImpactType
                sum_info2 = row.SumInfo2
                results[topic].append(sum_info2)

        return results

    def get_metadata_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            # t_MSFD8b_NutrientsMetadata
            mc_assessment = getattr(sql, 't_MSFD8b_' + theme_name + 'Metadata')
            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.c.MarineUnitID == marine_unit_id
            )

            for row in res:
                start = row[2]
                end = row[3]

                if row[1].startswith('Analysis') and start and end:
                    results.append(' - '.join((start, end)))

                    break

        return results

    def get_activity_descr_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name +
                                    'ActivityDescription')
            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.append(res)

        return results

    def get_activity_data(self, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name + 'Activity')

            d = self.activ_descr_data
            col = 'MSFD8b_Nutrients_ActivityDescription_ID'
            _id_act_descr = getattr(d[0][0], col) if d[0] else 0

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MSFD8b_Nutrients_ActivityDescription ==
                _id_act_descr
            )
            res = [x.Activity for x in res if x.Activity != 'NotReported']
            results.append('; '.join(res))

        return results

    def get_assesment_ind_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name +
                                    'AssesmentIndicator')
            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.append(res)

        return results

    def get_assesment_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            theme_name = mc[0]
            mc_assessment = getattr(sql, 'MSFD8b' + theme_name + 'Assesment')
            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.append(res)

        return results

    def get_base_data(self, marine_unit_id, descriptor_class):
        results = []

        for mc in descriptor_class.article8_mapper_classes:
            mapper_class = mc[1]
            count, res = db.get_all_records(
                mapper_class,
                mapper_class.MarineUnitID == marine_unit_id
            )
            results.append(res)

        return results

    def get_topic_assessment(self, marine_unit_id, descriptor):
        self.descriptor_class = DESCRIPTORS.get(descriptor, None)

        if not self.descriptor_class:
            return []

        self.base_data = self.get_base_data(marine_unit_id,
                                            self.descriptor_class)

        self.asses_data = self.get_assesment_data(marine_unit_id,
                                                  self.descriptor_class)

        self.asses_ind_data = self.get_assesment_ind_data(
            marine_unit_id, self.descriptor_class)

        self.activ_descr_data = self.get_activity_descr_data(
            marine_unit_id, self.descriptor_class)

        self.activ_data = self.get_activity_data(self.descriptor_class)

        self.metadata_data = self.get_metadata_data(marine_unit_id,
                                                    self.descriptor_class)

        self.suminfo2_data = self.get_suminfo2_data(marine_unit_id,
                                                    self.descriptor_class)

        topic_assesment = defaultdict(list)

        for table in self.base_data:
            for row in table:
                base_topic = getattr(row, 'Topic', None)
                asses_topic = self.descriptor_class\
                    .topic_assessment_to_nutrients.get(base_topic)

                if not asses_topic:
                    continue
                topic_assesment[base_topic] = []

                indicators = [
                    x.GESIndicators

                    for x in self.asses_ind_data[0]

                    if x.Topic == asses_topic
                ]

                if not indicators:
                    indicators = (self.descriptor_class.topic_indicators.get(
                        base_topic), )

                topic_assesment[base_topic].extend(indicators)

        self.topic_assesment = topic_assesment

        return topic_assesment

    def get_col_span_indicator(self, indicator):
        colspan = 0

        for topic, indics in self.topic_assesment.items():
            count = indics.count(indicator)

            if topic in self.descriptor_class.topic_groups[0]:
                colspan += count

        if not colspan:
            colspan = 1

        return colspan

    def print_feature(self, indicator, col_name, topic_group_index):
        results = []

        for row in self.base_data[0]:
            topic = row.Topic

            if topic in self.descriptor_class.topic_groups[topic_group_index]:
                nr = self.topic_assesment[topic].count(indicator)

                for i in range(nr):
                    results.append(getattr(row, col_name))

        if not results:
            return ['']

        return results

    def print_asses_ind(self, indicator, col_name, topic_group_index):
        topics_needed = []

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
             and topic in self.descriptor_class.topic_groups[
                 topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data[0]:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = self.descriptor_class.topic_assessment_to_nutrients\
                .get(topic)

            res = []

            for row_asess in self.asses_ind_data[0]:
                if row_asess.Topic == asses_topic and \
                 row_asess.GESIndicators == indicator:
                    res.append(getattr(row_asess, col_name))

            if not res:
                results.append('')
            else:
                results.extend(res)

        if not results:
            return ['']

        return results

    def print_base(self, indicator, col_name, topic_group_index):
        topics_needed = []

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
             and topic in self.descriptor_class.topic_groups[
                 topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data[0]:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            print_val = getattr(row, col_name)
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def print_asses(self, indicator, col_name, topic_group_index):
        topics_needed = []

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in self.descriptor_class.topic_groups[
                        topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data[0]:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = self.descriptor_class.topic_assessment_to_nutrients\
                .get(topic)

            print_val = [
                getattr(row, col_name)

                for row in self.asses_data[0]

                if row.Topic == asses_topic
            ]
            print_val = print_val[0] if print_val else ''
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def print_suminfo2(self, indicator, topic_group_index):
        topics_needed = []

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in self.descriptor_class.topic_groups[
                        topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data[0]:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            print_val = ', '.join(self.suminfo2_data[topic])
            nr_of_print = self.topic_assesment[topic].count(indicator)

            for nr in range(nr_of_print):
                results.append(print_val)

        if not results:
            return ['']

        return results

    def __call__(self):
        template = self.template
        self.content = template and template() or ""

        return self.content
