
from wise.msfd import sql

# descriptors mapped to DB tables, based on mappings excel doc
# TODO should we get data from all of these tables, or only from specific tables
DESC_DATA_MAPPING = {
    'D1': ('MSFD8a_Functional', 'MSFD8a_Species'),
    'D2': ('MSFD8b_NIS', ),
    'D3': ('MSFD8b_ExtractionFishShellfish',
           'MSFD8b_ExtractionSeaweedMaerlOther'),
    'D4': ('MSFD8b_Acidification', 'MSFD8a_Ecosystem', 'MSFD8a_Other',
           'MSFD8a_Physical'),
    'D5': ('MSFD8b_Nutrients', ),
    'D6': ('MSFD8a_Habitat', 'MSFD8b_PhysicalDamage', 'MSFD8b_PhysicalLoss',
           'MSFD8b_ExtractionFishShellfish',
           # TODO not sure if MSFD8b_ExtractionSeaweedMaerlOther belongs here
           'MSFD8b_ExtractionSeaweedMaerlOther'),
    'D7': ('MSFD8b_HydrologicalProcesses', ),
    'D8': ('MSFD8b_HazardousSubstances', 'MSFD8b_MicrobialPathogens',
           'MSFD8b_PollutantEvents'),
    'D9': ('MSFD8b_HazardousSubstances', ),
    'D10': ('MSFD8b_Litter', ),
    'D11': ('MSFD8b_Noise', ),
}

DB_MAPPER_CLASSES = {
    'MSFD8a_Ecosystem': sql.MSFD8aEcosystem,
    'MSFD8a_Functional': sql.MSFD8aFunctional,
    'MSFD8a_Habitat': sql.MSFD8aHabitat,
    'MSFD8a_Other': sql.MSFD8aOther,
    'MSFD8a_Physical': sql.MSFD8aPhysical,
    'MSFD8a_Species': sql.MSFD8aSpecy,
    'MSFD8b_Acidification': sql.MSFD8bAcidification,
    'MSFD8b_ExtractionFishShellfish': sql.MSFD8bExtractionFishShellfish,
    'MSFD8b_ExtractionSeaweedMaerlOther': sql.MSFD8bExtractionSeaweedMaerlOther,
    'MSFD8b_HazardousSubstances': sql.MSFD8bHazardousSubstance,
    'MSFD8b_HydrologicalProcesses': sql.MSFD8bHydrologicalProcess,
    'MSFD8b_Litter': sql.MSFD8bLitter,
    'MSFD8b_MicrobialPathogens': sql.MSFD8bMicrobialPathogen,
    'MSFD8b_NIS': sql.MSFD8bNI,
    'MSFD8b_Noise': sql.MSFD8bNoise,
    'MSFD8b_Nutrients': sql.MSFD8bNutrient,
    'MSFD8b_PhysicalDamage': sql.MSFD8bPhysicalDamage,
    'MSFD8b_PhysicalLoss': sql.MSFD8bPhysicalLos,
    'MSFD8b_PollutantEvents': sql.MSFD8bPollutantEvent,
}

# TODO for Nutrients topics list is incomplete in XLS??
# list of topics to be show in regional descriptors, if empty all topics are
# showed
TOPIC_CONDITIONS = {
    'MSFD8a_Ecosystem': (),
    'MSFD8a_Functional': (),
    'MSFD8a_Habitat': (),
    'MSFD8a_Other': (),
    'MSFD8a_Physical': (),
    'MSFD8a_Species': (),
    'MSFD8b_Acidification': (),
    'MSFD8b_ExtractionFishShellfish': (),
    'MSFD8b_ExtractionSeaweedMaerlOther': (),
    'MSFD8b_HazardousSubstances': (),
    'MSFD8b_HydrologicalProcesses': (),
    'MSFD8b_Litter': (),
    'MSFD8b_MicrobialPathogens': (),
    'MSFD8b_NIS': (),
    'MSFD8b_Noise': (),
    'MSFD8b_Nutrients': (
        'LevelPressureOverall', 'LevelPressureNConcentration',
        'LevelPressurePConcentration', 'LevelPressureOConcentration',
        'ImpactPressureWaterColumn', 'ImpactPressureSeabedHabitats'),
    'MSFD8b_PhysicalDamage': (),
    'MSFD8b_PhysicalLoss': (),
    'MSFD8b_PollutantEvents': (),
}

# because some topics are not assessed therefore we get data from
# its appropriate topic
TOPIC_ASSESSMENT = {
    'LevelPressureNConcentration': 'LevelPressureNLoad',
    'LevelPressurePConcentration': 'LevelPressurePLoad',
    'LevelPressureOConcentration': 'LevelPressureOLoad',
}

# used in national descriptors
DESCR_TOPIC_UTILS = {
    # if the Topic is not assessed, therefore the indicator is missing, get
    # the default indicator for that topic
    # TODO which one to choose if there are multiple defaults
    'topic_indicators': {
        'D5': {
            'ImpactPressureWaterColumn': ('5.2.1', '5.2.4', '5.2.2'),
            'ImpactPressureSeabedHabitats': ('5.3.2', '5.2.3', '5.3.1'),
            'LevelPressureNConcentration': '5.1.1',
            'LevelPressureNLoad': '5.1.1',
            'LevelPressureOConcentration': '5.1.1',
            'LevelPressureOLoad': '5.1.1',
            'LevelPressureOverall': '5.1.1',
            'LevelPressurePConcentration': '5.1.1',
            'LevelPressurePLoad': '5.1.1',
        },
        'D8': {
            'LevelPressureEnvironment': '8.1',
            'LevelPressureFunctionalGroups': '8.1',
            'ImpactPressureSeabedHabitats': '8.2',
            'ImpactPressureFunctionalGroup': '8.2',
        }
    },

    # The report data view table is separeted in 3 groups based on topics
    # TODO shoould we separate the topics for other descriptors too
    'topic_groups': {
        'D5': (
            ('LevelPressureNConcentration', 'LevelPressurePConcentration',
             'LevelPressureOConcentration', 'ImpactPressureWaterColumn',
             'ImpactPressureSeabedHabitats'),
            ('LevelPressureOverall', ),
            ('LevelPressureNLoad', 'LevelPressurePLoad', 'LevelPressureOLoad'),
        ),
        'D6': (
            ('asd', ),
            ('asd', ),
            ('asd', ),
        )
    },

    # Mapping of topics from base table to topics from assessment table,
    # it is needed because some topics are not assessed for example:
    # LevelPressureNConcentration, LevelPressurePConcentration, and we get
    # the data from its appropriate topic
    'topic_assessment_to_nutrients': {
        'D5': {
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
        },
        'D8': {
            'LevelPressureEnvironment': 'HazardousSubstances8_1'
        }
    }
}


class UtilsArticle8(object):
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.tables = DESC_DATA_MAPPING[descriptor]

    def get_base_mc(self, table):
        mc = DB_MAPPER_CLASSES[table]

        return mc

    def get_topic_conditions(self, table):
        topics = TOPIC_CONDITIONS.get(table, [])

        return topics

    def get_proper_topic(self, topic):
        proper = TOPIC_ASSESSMENT.get(topic, topic)

        return proper