
from wise.msfd import sql


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

TOPIC_ASSESSMENT = {
    'LevelPressureNConcentration': 'LevelPressureNLoad',
    'LevelPressurePConcentration': 'LevelPressurePLoad',
    'LevelPressureOConcentration': 'LevelPressureOLoad',
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