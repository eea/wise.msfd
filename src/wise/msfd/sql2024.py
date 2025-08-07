#pylint: skip-file
# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Float, MetaData, Table, Unicode
from sqlalchemy.sql.sqltypes import NullType

metadata = MetaData()


t_ART10_Targets_ProgressAssessment = Table(
    'ART10_Targets_ProgressAssessment', metadata,
    Column('CountryCode', Unicode(2)),
    Column('TargetCode', Unicode),
    Column('Element', Unicode),
    Column('Parameter', Unicode),
    Column('TargetValue', Float(53)),
    Column('TargetValueOperator', Unicode),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode),
    Column('TargetStatus', Unicode),
    Column('AssessmentPeriod', Unicode),
    Column('Description', Unicode),
    Column('RelatedIndicator', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART10_Targets_ReporterInfo = Table(
    'ART10_Targets_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART10_Targets_Target = Table(
    'ART10_Targets_Target', metadata,
    Column('CountryCode', Unicode(2)),
    Column('TargetCode', Unicode),
    Column('TargetOldCode', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('TargetPurpose', Unicode),
    Column('TargetDescription', Unicode),
    Column('Timescale', Unicode),
    Column('UpdateDate', Unicode),
    Column('UpdateTypeTarget', Unicode),
    Column('RelatedMeasures', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART1314_Supporting_documents = Table(
    'ART1314_Supporting documents', metadata,
    Column('CountryCode', Unicode(2)),
    Column('Description', Unicode),
    Column('Document', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART13_Measure = Table(
    'ART13_Measure', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MeasureCode', Unicode),
    Column('MeasureOldCode', Unicode),
    Column('MeasureName', Unicode),
    Column('MeasureDescription', Unicode),
    Column('UpdateType', Unicode),
    Column('MeasureCategory', Unicode),
    Column('PoliciesConventions', Unicode),
    Column('PolicyNational', Unicode),
    Column('ResponsibleCompetentAuthority', Unicode),
    Column('ResponsibleOrganisation', Unicode),
    Column('CoordinationLevel', Unicode),
    Column('RegionalCooperation_countries', Unicode),
    Column('CEA', Unicode),
    Column('CEAreference', Unicode),
    Column('CBA', Unicode),
    Column('CBAreference', Unicode),
    Column('Financing', Unicode),
    Column('RegionSubregion', Unicode),
    Column('SpatialScope', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('MeasurePurpose', Unicode),
    Column('Pressures', Unicode),
    Column('RelevantKTMs', Unicode),
    Column('RelevantTargets', Unicode),
    Column('RelatedIndicator', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Element', Unicode),
    Column('ImplementationStatus', Unicode),
    Column('TemporalScope', Unicode),
    Column('ImplementationDelay', BigInteger),
    Column('ImplementationReason', Unicode),
    Column('ReasonDescription', Unicode),
    Column('ProgressDescription', Unicode),
    Column('References', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART13_ReporterInfo = Table(
    'ART13_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART14_Exceptions = Table(
    'ART14_Exceptions', metadata,
    Column('CountryCode', Unicode(2)),
    Column('Exception_code', Unicode),
    Column('ExceptionOldCode', Unicode),
    Column('Exception_name', Unicode),
    Column('ExceptionType', Unicode),
    Column('ExceptionReason', Unicode),
    Column('GESachieved', Unicode),
    Column('RelevantPressures', Unicode),
    Column('RelevantTarget', Unicode),
    Column('GEScomponent', Unicode),
    Column('RelevantFeatures', Unicode),
    Column('RegionSubregion', Unicode),
    Column('Spatial_scope_geographic_zones{}', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('JustificationDescription', Unicode),
    Column('MeasuresAdHoc', Unicode),
    Column('Mitigation', Unicode),
    Column('FurtherInformation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART14_ReporterInfo = Table(
    'ART14_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART18_Measures = Table(
    'ART18_Measures', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MeasureCode', Unicode),
    Column('MeasureName', Unicode),
    Column('MeasureCategory', Unicode),
    Column('GEScomponent', Unicode),
    Column('ImplementationStatus', Unicode),
    Column('TemporalScope', Unicode),
    Column('ImplementationReason', Unicode),
    Column('ImplementationDelay', BigInteger),
    Column('ReasonDescription', Unicode),
    Column('ProgressDescription', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART18_ReporterInfo = Table(
    'ART18_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART4_GEO_Description = Table(
    'ART4_GEO_Description', metadata,
    Column('CountryCode', Unicode(2)),
    Column('Description', Unicode),
    Column('RegionSubRegions', Unicode),
    Column('Subdivisions', Unicode),
    Column('AssessmentAreas', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART4_GEO_GeographicalBoundaries = Table(
    'ART4_GEO_GeographicalBoundaries', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnitId', Unicode),
    Column('MarineReportingUnitIdOld', Unicode),
    Column('MarineReportingUnitName', Unicode),
    Column('RegionSubRegion', Unicode),
    Column('localId', Unicode),
    Column('namespace', Unicode),
    Column('versionId', Unicode),
    Column('thematicId', Unicode),
    Column('nameTxtInt', Unicode),
    Column('nameText', Unicode),
    Column('nameTxtLan', Unicode),
    Column('desigBegin', Unicode),
    Column('desigEnd', Unicode),
    Column('themaIdSch', Unicode),
    Column('beginLife', Unicode),
    Column('envDomain', Unicode),
    Column('zoneType', Unicode),
    Column('spZoneType', Unicode),
    Column('legisSName', Unicode),
    Column('legisName', Unicode),
    Column('legisDate', Unicode),
    Column('legisDateT', Unicode),
    Column('legisLink', Unicode),
    Column('legisLevel', Unicode),
    Column('rZoneId', Unicode),
    Column('rZoneIdSch', Unicode),
    Column('SnapshotId', BigInteger),
    Column('MarineReportingUnitGeometry', NullType),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART4_GEO_ReporterInfo = Table(
    'ART4_GEO_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8910_Supporting_documents = Table(
    'ART8910_Supporting documents', metadata,
    Column('CountryCode', Unicode(2)),
    Column('Description', Unicode),
    Column('Document', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_ESA_CostDegradation = Table(
    'ART8_ESA_CostDegradation', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('Feature', Unicode),
    Column('Approach', Unicode),
    Column('Description', Unicode),
    Column('CostDegradationType', Unicode),
    Column('Results', Unicode),
    Column('RelatedIndicator', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_ESA_Feature = Table(
    'ART8_ESA_Feature', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('RegionalAssessmentArea', Unicode),
    Column('Feature', Unicode),
    Column('NACEcode', Unicode),
    Column('RelatedGEScomponent', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_ESA_ReporterInfo = Table(
    'ART8_ESA_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_ESA_UsesActivities = Table(
    'ART8_ESA_UsesActivities', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('Feature', Unicode),
    Column('Description', Unicode),
    Column('Employment', Float(53)),
    Column('ProductionValue', Float(53)),
    Column('ValueAdded', Float(53)),
    Column('RelatedIndicator', Unicode),
    Column('RelatedPressures', Unicode),
    Column('RelatedEcosystemServices', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_Direct_CriteriaStatus = Table(
    'ART8_GES_Direct_CriteriaStatus', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('DescriptionCriteria', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_Direct_CriteriaStatus_CriteriaValues = Table(
    'ART8_GES_Direct_CriteriaStatus_CriteriaValues', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Criteria', Unicode),
    Column('Parameter', Unicode),
    Column('ThresholdValueUpper', Float(53)),
    Column('ThresholdValueLower', Float(53)),
    Column('ThresholdValueOperator', Unicode),
    Column('ThresholdQualitative', Unicode),
    Column('ThresholdValueSource', Unicode),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode),
    Column('ProportionThresholdValue', Float(53)),
    Column('ProportionValueAchieved', Float(53)),
    Column('ProportionThresholdValueUnit', Unicode),
    Column('TrendParameter', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('DescriptionParameter', Unicode),
    Column('RelatedIndicator', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_ElementStatus = Table(
    'ART8_GES_ElementStatus', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Element', Unicode),
    Column('ElementExtent', Float(53)),
    Column('Element2', Unicode),
    Column('ElementStatus', Unicode),
    Column('SourceElementList', Unicode),
    Column('TrendElement', Unicode),
    Column('DescriptionElement', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_ElementStatus_CriteriaStatus = Table(
    'ART8_GES_ElementStatus_CriteriaStatus', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Element', Unicode),
    Column('Element2', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('DescriptionCriteria', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_ElementStatus_CriteriaStatus_CriteriaValues = Table(
    'ART8_GES_ElementStatus_CriteriaStatus_CriteriaValues', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('Element', Unicode),
    Column('Element2', Unicode),
    Column('Criteria', Unicode),
    Column('Parameter', Unicode),
    Column('ThresholdValueUpper', Float(53)),
    Column('ThresholdValueLower', Float(53)),
    Column('ThresholdValueOperator', Unicode),
    Column('ThresholdQualitative', Unicode),
    Column('ThresholdValueSource', Unicode),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode),
    Column('ProportionThresholdValue', Float(53)),
    Column('ProportionValueAchieved', Float(53)),
    Column('ProportionThresholdValueUnit', Unicode),
    Column('TrendParameter', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('DescriptionParameter', Unicode),
    Column('RelatedIndicator', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_OverallStatus = Table(
    'ART8_GES_OverallStatus', metadata,
    Column('CountryCode', Unicode(2)),
    Column('MarineReportingUnit', Unicode),
    Column('RegionalAssessmentArea', Unicode),
    Column('ComponentMRUs', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('IntegrationRuleTypeParameter', Unicode),
    Column('IntegrationRuleDescriptionParameter', Unicode),
    Column('IntegrationRuleTypeCriteria', Unicode),
    Column('IntegrationRuleDescriptionCriteria', Unicode),
    Column('SourceAssessmentFeature', Unicode),
    Column('ReportingMethodFeature', Unicode),
    Column('AssessmentPeriod', Unicode),
    Column('GESextentThreshold', Float(53)),
    Column('GESextentAchieved', Float(53)),
    Column('GESextentUnit', Unicode),
    Column('TrendFeature', Unicode),
    Column('GESachievedDate', Unicode),
    Column('DescriptionOverallStatus', Unicode),
    Column('RelatedPressures', Unicode),
    Column('RelatedTargets', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART8_GES_ReporterInfo = Table(
    'ART8_GES_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART9_GES_GEScomponent = Table(
    'ART9_GES_GEScomponent', metadata,
    Column('CountryCode', Unicode(2)),
    Column('GESDescriptor', Unicode),
    Column('Feature', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('GEScomponent', Unicode),
    Column('GESDescription', Unicode),
    Column('DeterminationDate', Unicode),
    Column('UpdateTypeGES', Unicode),
    Column('JustificationNonUse', Unicode),
    Column('JustificationDelay', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_ART9_GES_ReporterInfo = Table(
    'ART9_GES_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_Indicators_Datasets = Table(
    'Indicators_Datasets', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('URL', Unicode),
    Column('MD_URL', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_Indicators_Feature = Table(
    'Indicators_Feature', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_Indicators_IndicatorAssessment = Table(
    'Indicators_IndicatorAssessment', metadata,
    Column('CountryCode', Unicode(2)),
    Column('IndicatorCode', Unicode),
    Column('IndicatorTitle', Unicode),
    Column('SourceAssessmentIndicator', Unicode),
    Column('ReportingMethodIndicator', Unicode),
    Column('UniqueReference', Unicode),
    Column('RelatedTargets', Unicode),
    Column('DatasetVoidReason', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('RegionalAssessmentArea', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)


t_Indicators_ReporterInfo = Table(
    'Indicators_ReporterInfo', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ContactName', Unicode),
    Column('ContactMail', Unicode),
    Column('ContactOrganisation', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
    schema='data'
)
