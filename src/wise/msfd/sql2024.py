# pylint: skip-file
# coding: utf-8
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Float, MetaData, String, Table, Unicode
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


t_V_ART10_Target_WM = Table(
    'V_ART10_Target_WM', metadata,
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
    Column('UpdateTypeTarget', String(29, 'Latin1_General_CI_AS')),
    Column('RelatedMeasures', Unicode),
    Column('SnapshotId', BigInteger),
    Column('ReportingDate', DateTime),
    Column('Comment', Unicode),
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
    Column('GES_Description', String(
        78, 'Latin1_General_CI_AS'), nullable=False),
    Column('ReportingCycle', String(4, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_2024 = Table(
    'V_ART8_GES_2024', metadata,
    Column('CountryCode', Unicode(2)),
    Column('ReportingDate', DateTime),
    Column('Region_Art4', Unicode),
    Column('Region_Art8', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('ComponentMRUs', Unicode),
    Column('GEScomponent', Unicode),
    Column('Feature', Unicode),
    Column('GESextentAchieved', Float(53)),
    Column('GESextentUnit', Unicode),
    Column('GESextentThreshold', Float(53)),
    Column('GESachievedDate', Unicode),
    Column('AssessmentPeriod', Unicode),
    Column('DescriptionOverallStatus', Unicode),
    Column('IntegrationRuleTypeCriteria', Unicode),
    Column('IntegrationRuleDescriptionCriteria', Unicode),
    Column('IntegrationRuleTypeParameter', Unicode),
    Column('IntegrationRuleDescriptionParameter', Unicode),
    Column('SourceAssessmentFeature', Unicode),
    Column('ReportingMethodFeature', Unicode),
    Column('TrendFeature', Unicode),
    Column('PressureCode', Unicode),
    Column('TargetCode', Unicode),
    Column('Element', Unicode),
    Column('Element2', Unicode),
    Column('ElementSource', Unicode),
    Column('DescriptionElement', Unicode),
    Column('ElementStatus', Unicode),
    Column('ElementExtent', Float(53)),
    Column('TrendElement', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('DescriptionCriteria', Unicode),
    Column('Parameter', Unicode),
    Column('ThresholdValueUpper', Float(53)),
    Column('ThresholdValueLower', Float(53)),
    Column('ThresholdQualitative', Unicode),
    Column('ThresholdValueSource', Unicode),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode),
    Column('ProportionThresholdValue', Float(53)),
    Column('ProportionThresholdValueUnit', Unicode),
    Column('ProportionValueAchieved', Float(53)),
    Column('TrendParameter', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('DescriptionParameter', Unicode),
    Column('IndicatorCode', Unicode),
    Column('ThresholdValueOperator', Unicode),
    schema='dbo'
)


t_V_ART8_GES_Country_WM = Table(
    'V_ART8_GES_Country_WM', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS'), nullable=False),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GEScomponent', Unicode),
    Column('GESAchieved', String(24, 'Latin1_General_CI_AS'), nullable=False),
    Column('MRULabel', Unicode),
    Column('MRU', Unicode),
    Column('Area', Float(53)),
    Column('Unit', String(3, 'Latin1_General_CI_AS')),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('Element/Element2', Unicode),
    Column('ElementStatus', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaLabel', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('SnapshotId', BigInteger),
    Column('Comment', Unicode),
    Column('Parameter/ParameterOther', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('ParameterDescription', Unicode),
    Column('Trend', Unicode),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    Column('ParameterLabel', Unicode),
    Column('Status', String(34, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_Country_WM_TEST = Table(
    'V_ART8_GES_Country_WM_TEST', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS')),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GEScomponent', Unicode),
    Column('GESAchieved', String(24, 'Latin1_General_CI_AS'), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('MRU', Unicode),
    Column('Area', Float(53)),
    Column('Unit', String(3, 'Latin1_General_CI_AS')),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('Element/Element2', Unicode),
    Column('ElementStatus', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaLabel', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('SnapshotId', BigInteger),
    Column('Comment', Unicode),
    Column('Parameter/ParameterOther', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('ParameterDescription', Unicode),
    Column('Trend', Unicode),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    Column('ParameterLabel', Unicode),
    Column('Status', String(34, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_CriteriaStatus_WM = Table(
    'V_ART8_GES_CriteriaStatus_WM', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS')),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GEScomponent', Unicode),
    Column('MRULabel', Unicode),
    Column('MRU', Unicode),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('Element/Element2', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaLabel', Unicode),
    Column('CriteriaStatus', Unicode),
    Column('DescriptionCriteria', Unicode),
    Column('SnapshotId', BigInteger),
    Column('Comment', Unicode),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_Element_WM = Table(
    'V_ART8_GES_Element_WM', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS')),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GESAchieved', String(24, 'Latin1_General_CI_AS'), nullable=False),
    Column('GEScomponent', Unicode),
    Column('GESextentAchieved', Float(53)),
    Column('MRULabel', Unicode),
    Column('MRU', Unicode),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('Element/Element2', Unicode),
    Column('ElementStatus', Unicode),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_OverallStatus_WM = Table(
    'V_ART8_GES_OverallStatus_WM', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS')),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GESAchieved', String(24, 'Latin1_General_CI_AS'), nullable=False),
    Column('GEScomponent', Unicode),
    Column('GESextentAchieved', Float(53)),
    Column('MRULabel', Unicode),
    Column('MRU', Unicode),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    schema='dbo'
)


t_V_ART8_GES_Parameter_WM = Table(
    'V_ART8_GES_Parameter_WM', metadata,
    Column('Code', Unicode(2)),
    Column('ComponentLabel', Unicode),
    Column('Country', String(11, 'Latin1_General_CI_AS')),
    Column('Feature2', Unicode),
    Column('Feature', Unicode),
    Column('GEScomponent', Unicode),
    Column('GESachievedDate', Unicode),
    Column('MRULabel', Unicode),
    Column('MRU', Unicode),
    Column('MarineSubregionName', String(44, 'Latin1_General_CI_AS')),
    Column('MarineSubregion', Unicode),
    Column('ReportingDate', DateTime),
    Column('Element/Element2', Unicode),
    Column('Criteria', Unicode),
    Column('CriteriaLabel', Unicode),
    Column('SnapshotId', BigInteger),
    Column('Comment', Unicode),
    Column('Parameter/ParameterOther', Unicode),
    Column('ParameterAchieved', Unicode),
    Column('ParameterDescription', Unicode),
    Column('Trend', Unicode),
    Column('ReportingCycle', String(3, 'Latin1_General_CI_AS'), nullable=False),
    Column('ParameterLabel', Unicode),
    schema='dbo'
)


t_V_Art8_GES_Feature_2024_area_WM = Table(
    'V_Art8_GES_Feature_2024_area_WM', metadata,
    Column('CountryCode', Unicode(2)),
    Column('Feature', Unicode),
    Column('GESachievedDate', Unicode),
    Column('GEScomponent', Unicode),
    Column('MarineReportingUnit', Unicode),
    Column('Region_Art4', Unicode),
    Column('area_km2', Float(53)),
    schema='dbo'
)


t_V_MRU_WM = Table(
    'V_MRU_WM', metadata,
    Column('CountryCode', String(2, 'Latin1_General_CI_AS'), nullable=False),
    Column('MarineReportingUnitId', Unicode(100), nullable=False),
    Column('SHAPE', NullType),
    schema='dbo'
)


t_V_MRU_WM_test = Table(
    'V_MRU_WM_test', metadata,
    Column('CountryCode', String(2, 'Latin1_General_CI_AS'), nullable=False),
    Column('MarineReportingUnitId', Unicode(100), nullable=False),
    Column('SHAPE', NullType),
    schema='dbo'
)


t_MarineReportingUnit_Publication = Table(
    'MarineReportingUnit_Publication', metadata,
    Column('countryCode', String(2, 'Latin1_General_CI_AS'), nullable=False),
    Column('MarineReportingUnitId', Unicode(100), nullable=False),
    Column('MarineReportingUnitIdOld', Unicode(100)),
    Column('MarineReportingUnitName', Unicode(255)),
    Column('RegionSubRegion', Unicode(3), nullable=False),
    Column('inspireIdLocalId', Unicode(100)),
    Column('inspireIdNamespace', Unicode(255)),
    Column('inspireIdVersionId', Unicode(255)),
    Column('thematicIdIdentifier', Unicode(100)),
    Column('thematicIdIdentifierScheme', Unicode(100)),
    Column('nameText', Unicode(1000)),
    Column('nameTextInternational', Unicode(255)),
    Column('nameLanguage', Unicode(100)),
    Column('designationPeriodBegin', Date),
    Column('designationPeriodEnd', Date),
    Column('beginLifespanVersion', Date),
    Column('envDomain', Unicode(100)),
    Column('zoneType', Unicode(255)),
    Column('specialisedZoneType', Unicode(255)),
    Column('legisSName', Unicode(255)),
    Column('legisName', Unicode(500)),
    Column('legisDate', Date),
    Column('legisDateT', Unicode(255)),
    Column('legisLink', Unicode(1000)),
    Column('legisLevel', Unicode(255)),
    Column('relatedZoneIdentifier', Unicode(255)),
    Column('relatedZoneIdentifierScheme', Unicode(255)),
    Column('isMarineWater', Boolean, nullable=False),
    Column('statusCode', String(255, 'Latin1_General_CI_AS'), nullable=False),
    Column('statusDate', Date),
    Column('statusRemarks', Unicode(1000)),
    Column('metadata_versionId', String(1000, 'Latin1_General_CI_AS')),
    Column('metadata_beginLifeSpanVersion', DateTime),
    Column('metadata_statements', String(collation='Latin1_General_CI_AS')),
    Column('sizeValue', Float(53)),
    Column('sizeUom', String(3, 'Latin1_General_CI_AS'), nullable=False),
    Column('snapshotId', BigInteger),
    Column('geomEPSG_3035', NullType),
    Column('geomEPSG_4258', NullType),
    schema='spatial'
)


t_MarineReportingUnit_Reference = Table(
    'MarineReportingUnit_Reference', metadata,
    Column('countryCode', String(2, 'Latin1_General_CI_AS'), nullable=False),
    Column('MarineReportingUnitId', Unicode(100), nullable=False),
    Column('MarineReportingUnitIdOld', Unicode(100)),
    Column('MarineReportingUnitName', Unicode(255)),
    Column('RegionSubRegion', Unicode(3), nullable=False),
    Column('inspireIdLocalId', Unicode(100)),
    Column('inspireIdNamespace', Unicode(255)),
    Column('inspireIdVersionId', Unicode(255)),
    Column('thematicIdIdentifier', Unicode(100)),
    Column('thematicIdIdentifierScheme', Unicode(100)),
    Column('nameText', Unicode(1000)),
    Column('nameTextInternational', Unicode(255)),
    Column('nameLanguage', Unicode(100)),
    Column('designationPeriodBegin', Date),
    Column('designationPeriodEnd', Date),
    Column('beginLifespanVersion', Date),
    Column('envDomain', Unicode(100)),
    Column('zoneType', Unicode(255)),
    Column('specialisedZoneType', Unicode(255)),
    Column('legisSName', Unicode(255)),
    Column('legisName', Unicode(500)),
    Column('legisDate', Date),
    Column('legisDateT', Unicode(255)),
    Column('legisLink', Unicode(1000)),
    Column('legisLevel', Unicode(255)),
    Column('relatedZoneIdentifier', Unicode(255)),
    Column('relatedZoneIdentifierScheme', Unicode(255)),
    Column('isMarineWater', Boolean, nullable=False),
    Column('statusCode', String(255, 'Latin1_General_CI_AS'), nullable=False),
    Column('statusDate', Date),
    Column('statusRemarks', Unicode(1000)),
    Column('metadata_versionId', String(1000, 'Latin1_General_CI_AS')),
    Column('metadata_beginLifeSpanVersion', DateTime),
    Column('metadata_statements', String(collation='Latin1_General_CI_AS')),
    Column('sizeValue', Float(53)),
    Column('sizeUom', String(3, 'Latin1_General_CI_AS'), nullable=False),
    Column('snapshotId', BigInteger),
    Column('geomEPSG_3035', NullType),
    Column('geomEPSG_4258', NullType),
    schema='spatial'
)
