from collections import defaultdict

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql

from ..base import BaseArticle2012
from ..a8_utils import DESC_DATA_MAPPING, DB_MAPPER_CLASSES, DESCR_TOPIC_UTILS


class Article8(BaseArticle2012):
    template = Template('pt/report-data-a8.pt')

    def get_suminfo2_data(self, marine_unit_id, descriptor):
        """ Get all data from table _SumInfo2ImpactedElement
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: {u'ImpactPressureSeabedHabitats': [u'ShallRock', u'ShallSand'],
            u'ImpactPressureWaterColumn': [u'NutrientLevels', u'Transparency']}
        """

        results = defaultdict(list)
        tables = DESC_DATA_MAPPING[descriptor]

        for table in tables:
            tbl_name = '{}SumInfo2ImpactedElement'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )

            for row in res:
                topic = row.ImpactType
                sum_info2 = row.SumInfo2
                results[topic].append(sum_info2)

        return results

    def get_metadata_data(self, marine_unit_id, descriptor):
        """ Get all data from table _Metadata
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: list [u'1973 - 2008', ...]
        """

        results = []

        tables = DESC_DATA_MAPPING[descriptor]

        for table in tables:
            tbl_name = 't_{}Metadata'.format(table)
            mc_assessment = getattr(sql, tbl_name, None)

            if mc_assessment is None:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.c.MarineUnitID == marine_unit_id
            )

            for row in res:
                start = row[2]
                end = row[3]

                if row[1].startswith('Assessment') and start and end:
                    val = ' - '.join((start, end))
                    results.extend([val])

                    break

        return results

    def get_activity_descr_data(self, marine_unit_id, descriptor):
        """ Get all data from table _ActivityDescription
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}ActivityDescription'.format(table.replace("_", ""))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_activity_data(self, descriptor):
        """ Get all data from table _Activity for specific descriptor
        :param descriptor: 'D5'
        :return: list [u'AgricultForestry; Urban']
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}Activity'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            d = self.activ_descr_data
            col = '{}_ActivityDescription_ID'.format(table)
            # _id_act_descr = getattr(d[0], col, 0) if d else 0
            _id_act_descr = [getattr(x, col, 0) for x in d]

            col_ad = '{}_ActivityDescription'.format(table)
            count, res = db.get_all_records(
                mc_assessment,
                getattr(mc_assessment, col_ad).in_(_id_act_descr)
            )
            res = [x.Activity for x in res if x.Activity != 'NotReported']
            results.extend(res)

        results = '; '.join(results)

        return results

    def get_assesment_ind_data(self, marine_unit_id, descriptor):
        """ Get all data from table _AssesmentIndicator
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}AssesmentIndicator'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_assesment_data(self, marine_unit_id, descriptor):
        """ Get all data from table _Assesment
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            tbl_name = '{}Assesment'.format(table.replace('_', ''))
            mc_assessment = getattr(sql, tbl_name, None)

            if not mc_assessment:
                continue

            count, res = db.get_all_records(
                mc_assessment,
                mc_assessment.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_base_data(self, marine_unit_id, descriptor):
        """ Get all data from base table
            for specific Marine Units and descriptor
        :param marine_unit_id: ['LV-001', 'LV-002']
        :param descriptor: 'D5'
        :return: table results
        """

        tables = DESC_DATA_MAPPING[descriptor]
        results = []

        for table in tables:
            mapper_class = DB_MAPPER_CLASSES.get(table, None)

            if not mapper_class:
                continue

            count, res = db.get_all_records(
                mapper_class,
                mapper_class.MarineUnitID == marine_unit_id
            )
            results.extend(res)

        return results

    def get_topic_assessment(self, marine_unit_id):
        """ Get dict with topics(analisys/features) and the GESComponents
        :param marine_unit_id: 'LV-001'
        :return: {'LevelPressureOLoad': ['5.1.1'],
            u'ImpactPressureWaterColumn': [u'5.2.1', u'5.2.1', u'5.2.2'],
            ...}
        """
        self.descriptor = self.descriptor.split('.')[0]

        self.base_data = self.get_base_data(marine_unit_id,
                                            self.descriptor)

        self.asses_data = self.get_assesment_data(marine_unit_id,
                                                  self.descriptor)

        self.asses_ind_data = self.get_assesment_ind_data(
            marine_unit_id, self.descriptor)

        self.activ_descr_data = self.get_activity_descr_data(
            marine_unit_id, self.descriptor)

        self.activ_data = self.get_activity_data(self.descriptor)

        self.metadata_data = self.get_metadata_data(marine_unit_id,
                                                    self.descriptor)

        self.suminfo2_data = self.get_suminfo2_data(marine_unit_id,
                                                    self.descriptor)

        topic_assesment = defaultdict(list)

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )
        topic_ind = DESCR_TOPIC_UTILS['topic_indicators'].get(self.descriptor,
                                                              {})

        for row in self.base_data:
            base_topic = getattr(row, 'Topic', None)
            asses_topic = topic_atn.get(base_topic, 'NOT FOUND')

            # if not asses_topic:
            #     continue
            topic_assesment[base_topic] = []

            indicators = [
                x.GESIndicators

                for x in self.asses_ind_data

                if x.Topic == asses_topic
            ]

            if not indicators:
                indic = topic_ind.get(base_topic, 'INDICATOR EMPTY')
                indicators = (indic, )

            topic_assesment[base_topic].extend(indicators)

        self.topic_assesment = topic_assesment

        # import pdb; pdb.set_trace()

        return topic_assesment

    def get_col_span_indicator(self, indicator):
        """ Get colspan based on the count of indicators
        :param indicator: '5.2.1'
        :return: integer
        """

        colspan = 0
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])
        topics_needed = self.topic_assesment.keys()

        if topic_groups:
            topics_needed = topic_groups[0]

        for topic, indics in self.topic_assesment.items():
            count = indics.count(indicator)

            if topic in topics_needed:
                colspan += count

        if not colspan:
            colspan = 1

        return colspan

    def print_feature(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        results = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])
        topics_needed = self.topic_assesment.keys()

        if topic_groups:
            topics_needed = topic_groups[topic_group_index]

        for row in self.base_data:
            topic = row.Topic

            if topic in topics_needed:
                nr = self.topic_assesment[topic].count(indicator)

                for i in range(nr):
                    results.append(getattr(row, col_name))

        if not results:
            return ['']

        return results

    def print_asses_ind(self, indicator, col_name, topic_group_index):
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
             and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )
        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = topic_atn.get(topic)

            res = []

            for row_asess in self.asses_ind_data:
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
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
             and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data:
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
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        topic_atn = DESCR_TOPIC_UTILS['topic_assessment_to_nutrients'].get(
            self.descriptor, {}
        )
        for row in self.base_data:
            topic = row.Topic

            if topic not in topics_needed:
                continue

            asses_topic = topic_atn.get(topic)

            print_val = [
                getattr(row, col_name)

                for row in self.asses_data

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
        """ Get data to be printed in template
        """

        topics_needed = []
        topic_groups = DESCR_TOPIC_UTILS['topic_groups'].get(
            self.descriptor, [])

        for topic, indics in self.topic_assesment.items():
            if indicator in indics \
                    and topic in topic_groups[topic_group_index]:
                topics_needed.append(topic)

        results = []

        for row in self.base_data:
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
