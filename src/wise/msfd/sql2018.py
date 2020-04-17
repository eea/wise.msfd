# coding: utf-8
from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, SmallInteger, String, Table, Unicode, UnicodeText
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql.base import BIT
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

from . import sql

Base = declarative_base()
metadata = Base.metadata


class ART10TargetsMarineUnit(Base):
    __tablename__ = 'ART10_Targets_MarineUnit'

    Id = Column(Integer, primary_key=True)
    MarineReportingUnit = Column(Unicode(50), nullable=False)
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART10TargetsProgressAssessment(Base):
    __tablename__ = 'ART10_Targets_ProgressAssessment'

    Id = Column(Integer, primary_key=True)
    Parameter = Column(Unicode(50), nullable=False)
    ParameterOther = Column(Unicode(250))
    Element = Column(Unicode(50))
    Element2 = Column(Unicode(50))
    TargetValue = Column(Float(53))
    ValueAchievedUpper = Column(Float(53))
    ValueAchievedLower = Column(Float(53))
    ValueUnit = Column(Unicode(50))
    ValueUnitOther = Column(Unicode(250))
    TargetStatus = Column(Unicode(50))
    AssessmentPeriod = Column(Unicode(9), nullable=False)
    Description = Column(Unicode(2500))
    IdTarget = Column(ForeignKey(u'ART10_Targets_Target.Id'), nullable=False)

    ART10_Targets_Target = relationship(u'ART10TargetsTarget')


class ART10TargetsProgressAssessmentIndicator(Base):
    __tablename__ = 'ART10_Targets_ProgressAssessment_Indicator'

    IndicatorCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdProgressAssessment = Column(ForeignKey(u'ART10_Targets_ProgressAssessment.Id'), primary_key=True, nullable=False)

    ART10_Targets_ProgressAssessment = relationship(u'ART10TargetsProgressAssessment')


class ART10TargetsTarget(Base):
    __tablename__ = 'ART10_Targets_Target'

    Id = Column(Integer, primary_key=True)
    TargetCode = Column(Unicode(50), nullable=False)
    Description = Column(Unicode(2500), nullable=False)
    TimeScale = Column(Unicode(6), nullable=False)
    UpdateDate = Column(Unicode(6), nullable=False)
    UpdateType = Column(Unicode(50), nullable=False)
    IdMarineUnit = Column(ForeignKey(u'ART10_Targets_MarineUnit.Id'), nullable=False)

    ART10_Targets_MarineUnit = relationship(u'ART10TargetsMarineUnit')


class ART10TargetsTargetFeature(Base):
    __tablename__ = 'ART10_Targets_Target_Feature'

    Feature = Column(Unicode(250), primary_key=True, nullable=False)
    IdTarget = Column(ForeignKey(u'ART10_Targets_Target.Id'), primary_key=True, nullable=False)

    ART10_Targets_Target = relationship(u'ART10TargetsTarget')


class ART10TargetsTargetGESComponent(Base):
    __tablename__ = 'ART10_Targets_Target_GESComponent'

    GESComponent = Column(Unicode(50), primary_key=True, nullable=False)
    IdTarget = Column(ForeignKey(u'ART10_Targets_Target.Id'), primary_key=True, nullable=False)

    ART10_Targets_Target = relationship(u'ART10TargetsTarget')


class ART10TargetsTargetMeasure(Base):
    __tablename__ = 'ART10_Targets_Target_Measure'

    Measure = Column(Unicode(250), primary_key=True, nullable=False)
    IdTarget = Column(ForeignKey(u'ART10_Targets_Target.Id'), primary_key=True, nullable=False)

    ART10_Targets_Target = relationship(u'ART10TargetsTarget')


class ART18Category1bNotWFD(Base):
    __tablename__ = 'ART18_Category1bNotWFD'

    Id = Column(Integer, primary_key=True)
    Descriptor = Column(Unicode(10))
    ImplementationProgress = Column(Unicode(30))
    MeasureWithdrawn = Column(Unicode(10))
    ReasonWithdrawal = Column(Unicode(50))
    ReasonWithdrawalOther = Column(Unicode(2500))
    ImplementationYear = Column(Unicode(4))
    Delay = Column(Integer)
    ReasonDelay = Column(Unicode(50))
    ReasonDelayOther = Column(Unicode(2500))
    OtherObstacles = Column(Unicode(10))
    TypeObstacle = Column(Unicode(50))
    TypeObstacleOther = Column(Unicode(2500))
    FurtherInformationObstacles = Column(Unicode(1000))
    ProgressDescription = Column(Unicode(2500))
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART18Category1bNotWFDMeasure(Base):
    __tablename__ = 'ART18_Category1bNotWFD_Measure'

    Id = Column(Integer, primary_key=True)
    MeasureCode = Column(Unicode(50))
    MeasureName = Column(Unicode(1000))
    Comments = Column(Unicode(2500))
    MSComments = Column(Unicode(2500))
    Disagree = Column(Unicode(10))
    Prefilling = Column(Unicode(10))
    IdCategory1bNotWFD = Column(ForeignKey(u'ART18_Category1bNotWFD.Id'), nullable=False)

    ART18_Category1bNotWFD = relationship(u'ART18Category1bNotWFD')


class ART18MeasureProgres(Base):
    __tablename__ = 'ART18_MeasureProgress'

    Id = Column(Integer, primary_key=True)
    MeasureCode = Column(Unicode(50))
    MeasureName = Column(Unicode(1000))
    Category = Column(Unicode(30))
    ImplementationProgress = Column(Unicode(30))
    MeasureWithdrawn = Column(Unicode(10))
    ReasonWithdrawal = Column(Unicode(50))
    ReasonWithdrawalOther = Column(Unicode(2500))
    ImplementationYear = Column(Unicode(4))
    Delay = Column(Integer)
    ReasonDelay = Column(Unicode(50))
    ReasonDelayOther = Column(Unicode(2500))
    OtherObstacles = Column(Unicode(10))
    TypeObstacle = Column(Unicode(50))
    TypeObstacleOther = Column(Unicode(2500))
    FurtherInformationObstacles = Column(Unicode(1000))
    ProgressDescription = Column(Unicode(2500))
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART18MeasureProgressDescriptor(Base):
    __tablename__ = 'ART18_MeasureProgress_Descriptor'

    DescriptorCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdMeasureProgress = Column(ForeignKey(u'ART18_MeasureProgress.Id'), primary_key=True, nullable=False)

    ART18_MeasureProgres = relationship(u'ART18MeasureProgres')


class ART8ESACostDegradation(Base):
    __tablename__ = 'ART8_ESA_CostDegradation'

    Id = Column(Integer, primary_key=True)
    Description = Column(Unicode(2500))
    Approach = Column(Unicode(100), nullable=False)
    Results = Column(Unicode(2500), nullable=False)
    IdFeature = Column(ForeignKey(u'ART8_ESA_Feature.Id'), nullable=False)

    ART8_ESA_Feature = relationship(u'ART8ESAFeature')


class ART8ESACostDegradationCostDegradationType(Base):
    __tablename__ = 'ART8_ESA_CostDegradation_CostDegradationType'

    CostDegradationType = Column(Unicode(50), primary_key=True, nullable=False)
    IdCostDegradation = Column(ForeignKey(u'ART8_ESA_CostDegradation.Id'), primary_key=True, nullable=False)

    ART8_ESA_CostDegradation = relationship(u'ART8ESACostDegradation')


class ART8ESACostDegradationIndicator(Base):
    __tablename__ = 'ART8_ESA_CostDegradation_Indicator'

    IndicatorCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdCostDegradation = Column(ForeignKey(u'ART8_ESA_CostDegradation.Id'), primary_key=True, nullable=False)

    ART8_ESA_CostDegradation = relationship(u'ART8ESACostDegradation')


class ART8ESAFeature(Base):
    __tablename__ = 'ART8_ESA_Feature'

    Id = Column(Integer, primary_key=True)
    Feature = Column(Unicode(250), nullable=False)
    IdMarineUnit = Column(ForeignKey(u'ART8_ESA_MarineUnit.Id'), nullable=False)

    ART8_ESA_MarineUnit = relationship(u'ART8ESAMarineUnit')


class ART8ESAFeatureGESComponent(Base):
    __tablename__ = 'ART8_ESA_Feature_GESComponent'

    GESComponent = Column(Unicode(50), primary_key=True, nullable=False)
    IdFeature = Column(ForeignKey(u'ART8_ESA_Feature.Id'), primary_key=True, nullable=False)

    ART8_ESA_Feature = relationship(u'ART8ESAFeature')


class ART8ESAFeatureNACE(Base):
    __tablename__ = 'ART8_ESA_Feature_NACE'

    NACECode = Column(Unicode(4), primary_key=True, nullable=False)
    IdFeature = Column(ForeignKey(u'ART8_ESA_Feature.Id'), primary_key=True, nullable=False)

    ART8_ESA_Feature = relationship(u'ART8ESAFeature')


class ART8ESAMarineUnit(Base):
    __tablename__ = 'ART8_ESA_MarineUnit'

    Id = Column(Integer, primary_key=True)
    MarineReportingUnit = Column(Unicode(50), nullable=False)
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART8ESAUsesActivity(Base):
    __tablename__ = 'ART8_ESA_UsesActivities'

    Id = Column(Integer, primary_key=True)
    Description = Column(Unicode(2500))
    Employment = Column(Float(53))
    ProductionValue = Column(Float(53))
    ValueAdded = Column(Float(53))
    IdFeature = Column(ForeignKey(u'ART8_ESA_Feature.Id'), nullable=False)

    ART8_ESA_Feature = relationship(u'ART8ESAFeature')


class ART8ESAUsesActivitiesEcosystemService(Base):
    __tablename__ = 'ART8_ESA_UsesActivities_EcosystemService'

    EcosystemServiceCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdUsesActivities = Column(ForeignKey(u'ART8_ESA_UsesActivities.Id'), primary_key=True, nullable=False)

    ART8_ESA_UsesActivity = relationship(u'ART8ESAUsesActivity')


class ART8ESAUsesActivitiesIndicator(Base):
    __tablename__ = 'ART8_ESA_UsesActivities_Indicator'

    IndicatorCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdUsesActivities = Column(ForeignKey(u'ART8_ESA_UsesActivities.Id'), primary_key=True, nullable=False)

    ART8_ESA_UsesActivity = relationship(u'ART8ESAUsesActivity')


class ART8ESAUsesActivitiesPressure(Base):
    __tablename__ = 'ART8_ESA_UsesActivities_Pressure'

    PressureCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdUsesActivities = Column(ForeignKey(u'ART8_ESA_UsesActivities.Id'), primary_key=True, nullable=False)

    ART8_ESA_UsesActivity = relationship(u'ART8ESAUsesActivity')


class ART8GESCriteriaStatu(Base):
    __tablename__ = 'ART8_GES_CriteriaStatus'

    Id = Column(Integer, primary_key=True)
    Criteria = Column(Unicode(50), nullable=False)
    CriteriaStatus = Column(Unicode(50), nullable=False)
    DescriptionCriteria = Column(Unicode(2500))
    IdOverallStatus = Column(ForeignKey(u'ART8_GES_OverallStatus.Id'))
    IdElementStatus = Column(ForeignKey(u'ART8_GES_ElementStatus.Id'))

    ART8_GES_ElementStatu = relationship(u'ART8GESElementStatu')
    ART8_GES_OverallStatu = relationship(u'ART8GESOverallStatu')


class ART8GESCriteriaValue(Base):
    __tablename__ = 'ART8_GES_CriteriaValues'

    Id = Column(Integer, primary_key=True)
    Parameter = Column(Unicode(50), nullable=False)
    ParameterOther = Column(Unicode(250))
    ThresholdValueUpper = Column(Float(53))
    ThresholdValueLower = Column(Float(53))
    ThresholdQualitative = Column(Unicode(250))
    ThresholdValueSource = Column(Unicode(50))
    ThresholdValueSourceOther = Column(Unicode(250))
    ValueAchievedUpper = Column(Float(53))
    ValueAchievedLower = Column(Float(53))
    ValueUnit = Column(Unicode(50))
    ValueUnitOther = Column(Unicode(250))
    ProportionThresholdValue = Column(Float(53))
    ProportionThresholdValueUnit = Column(Unicode(50))
    ProportionValueAchieved = Column(Float(53))
    Trend = Column(Unicode(50), nullable=False)
    ParameterAchieved = Column(Unicode(50), nullable=False)
    DescriptionParameter = Column(Unicode(2500))
    IdCriteriaStatus = Column(ForeignKey(u'ART8_GES_CriteriaStatus.Id'), nullable=False)

    ART8_GES_CriteriaStatu = relationship(u'ART8GESCriteriaStatu')


class ART8GESCriteriaValuesIndicator(Base):
    __tablename__ = 'ART8_GES_CriteriaValues_Indicator'

    IndicatorCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdCriteriaValues = Column(ForeignKey(u'ART8_GES_CriteriaValues.Id'), primary_key=True, nullable=False)

    ART8_GES_CriteriaValue = relationship(u'ART8GESCriteriaValue')


class ART8GESElementStatu(Base):
    __tablename__ = 'ART8_GES_ElementStatus'

    Id = Column(Integer, primary_key=True)
    Element = Column(Unicode(250))
    Element2 = Column(Unicode(250))
    ElementSource = Column(Unicode(50))
    ElementCode = Column(Unicode(50))
    Element2Code = Column(Unicode(50))
    ElementCodeSource = Column(Unicode(50))
    Element2CodeSource = Column(Unicode(50))
    DescriptionElement = Column(Unicode(2500))
    ElementStatus = Column(Unicode(50))
    IdOverallStatus = Column(ForeignKey(u'ART8_GES_OverallStatus.Id'), nullable=False)

    ART8_GES_OverallStatu = relationship(u'ART8GESOverallStatu')


class ART8GESMarineUnit(Base):
    __tablename__ = 'ART8_GES_MarineUnit'

    Id = Column(Integer, primary_key=True)
    MarineReportingUnit = Column(Unicode(50), nullable=False)
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART8GESOverallStatu(Base):
    __tablename__ = 'ART8_GES_OverallStatus'

    Id = Column(Integer, primary_key=True)
    GESComponent = Column(Unicode(50), nullable=False)
    Feature = Column(Unicode(250), nullable=False)
    GESExtentAchieved = Column(Numeric(8, 5))
    GESExtentUnit = Column(Unicode(250))
    GESExtentThreshold = Column(Numeric(8, 5))
    GESAchieved = Column(Unicode(100), nullable=False)
    AssessmentsPeriod = Column(Unicode(9), nullable=False)
    DescriptionOverallStatus = Column(Unicode(2500))
    IntegrationRuleTypeCriteria = Column(Unicode(50))
    IntegrationRuleDescriptionCriteria = Column(Unicode(1000))
    IntegrationRuleDescriptionReferenceCriteria = Column(Unicode(250))
    IntegrationRuleTypeParameter = Column(Unicode(50))
    IntegrationRuleDescriptionParameter = Column(Unicode(1000))
    IntegrationRuleDescriptionReferenceParameter = Column(Unicode(250))
    IdMarineUnit = Column(ForeignKey(u'ART8_GES_MarineUnit.Id'), nullable=False)

    ART8_GES_MarineUnit = relationship(u'ART8GESMarineUnit')


class ART8GESOverallStatusPressure(Base):
    __tablename__ = 'ART8_GES_OverallStatus_Pressure'

    PressureCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdOverallStatus = Column(ForeignKey(u'ART8_GES_OverallStatus.Id'), primary_key=True, nullable=False)

    ART8_GES_OverallStatu = relationship(u'ART8GESOverallStatu')


class ART8GESOverallStatusTarget(Base):
    __tablename__ = 'ART8_GES_OverallStatus_Target'

    TargetCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdOverallStatus = Column(ForeignKey(u'ART8_GES_OverallStatus.Id'), primary_key=True, nullable=False)

    ART8_GES_OverallStatu = relationship(u'ART8GESOverallStatu')


class ART9GESGESComponent(Base):
    __tablename__ = 'ART9_GES_GESComponent'

    Id = Column(Integer, primary_key=True)
    GESComponent = Column(Unicode(50), nullable=False)
    JustificationDelay = Column(Unicode(1000))
    JustificationNonUse = Column(Unicode(1000))
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class ART9GESGESDetermination(Base):
    __tablename__ = 'ART9_GES_GESDetermination'

    Id = Column(Integer, primary_key=True)
    GESDescription = Column(Unicode(2500), nullable=False)
    DeterminationDate = Column(Unicode(6), nullable=False)
    UpdateType = Column(Unicode(50), nullable=False)
    IdGESComponent = Column(ForeignKey(u'ART9_GES_GESComponent.Id'), nullable=False)

    ART9_GES_GESComponent = relationship(u'ART9GESGESComponent')


class ART9GESGESDeterminationFeature(Base):
    __tablename__ = 'ART9_GES_GESDetermination_Feature'

    Id = Column(Integer, primary_key=True)
    Feature = Column(Unicode(50), nullable=False)
    IdGESDetermination = Column(ForeignKey(u'ART9_GES_GESDetermination.Id'), nullable=False)

    ART9_GES_GESDetermination = relationship(u'ART9GESGESDetermination')


class ART9GESMarineUnit(Base):
    __tablename__ = 'ART9_GES_MarineUnit'

    MarineReportingUnit = Column(Unicode(50), primary_key=True, nullable=False)
    IdGESDetermination = Column(ForeignKey(u'ART9_GES_GESDetermination.Id'), primary_key=True, nullable=False)

    ART9_GES_GESDetermination = relationship(u'ART9GESGESDetermination')


class COMAssessment(Base):
    __tablename__ = 'COM_Assessments'

    Id = Column(Integer, primary_key=True)
    COM_GeneralId = Column(ForeignKey(u'COM_General.Id'), nullable=False)
    MSFDArticle = Column(Unicode(20))
    MarineUnit = Column(Unicode(50))
    Feature = Column(Unicode(200))
    GESComponent_Target = Column(Unicode(15))
    AssessmentCriteria = Column(Unicode(25))
    AssessedInformation = Column(Unicode(50))
    Evidence = Column(Unicode(150))
    Description_Summary = Column(Unicode)
    Conclusion = Column(Unicode(50))
    Score = Column(Numeric(8, 5))
    AssessmentChangeArt9 = Column(Integer)
    RecommendationsArt9 = Column(Unicode)

    COM_General = relationship(u'COMGeneral')


t_COM_Assessments_2012 = Table(
    'COM_Assessments_2012', metadata,
    Column('Country', Unicode(255)),
    Column('Descriptor', Unicode(255)),
    Column('AssessmentCriteria', Unicode(255)),
    Column('MSFDArticle', Unicode(255)),
    Column('Assessment', Unicode),
    Column('Conclusions', Unicode),
    Column('Criteria', Unicode),
    Column('OverallScore', Float(53)),
    Column('OverallAssessment', Unicode(255)),
    Column('COM_General_Id', Integer)
)


class COMAssessmentsComment(Base):
    __tablename__ = 'COM_Assessments_comments'

    Id = Column(Integer, primary_key=True)
    COM_AssessmentsId = Column(ForeignKey(u'COM_Assessments.Id'), nullable=False)
    Organisation = Column(Unicode(50))
    Comment = Column(Unicode)

    COM_Assessment = relationship(u'COMAssessment')


class COMGeneral(Base):
    __tablename__ = 'COM_General'

    Id = Column(Integer, primary_key=True)
    Reporting_historyId = Column(ForeignKey(u'Reporting_history.Id'))
    CountryCode = Column(Unicode(2))
    RegionSubregion = Column(Unicode(20))
    AssessmentTopic = Column(Unicode(200))
    MSFDArticle = Column(Unicode(20))
    DateReportDue = Column(Date)
    ReportBy = Column(Unicode(20))
    SourceFile = Column(Unicode(500))
    DateReported = Column(Date)
    DateAssessed = Column(Date)
    Assessors = Column(Unicode(500))
    CommissionReport = Column(Unicode(500))

    Reporting_history = relationship(u'ReportingHistory')


class EnvelopeFile(Base):
    __tablename__ = 'Envelope_Files'

    FileID = Column(BigInteger, primary_key=True, nullable=False)
    envelopeImportID = Column(ForeignKey(u'Envelope_Import.envelopeImportID'), primary_key=True, nullable=False)
    Name = Column(Unicode(255))
    type = Column(Unicode(50))
    schema = Column(Unicode(255))
    title = Column(Unicode(255))
    restricted = Column(Integer)
    link = Column(Unicode(500))
    uploadedDate = Column(DateTime)

    Envelope_Import = relationship(u'EnvelopeImport')


class EnvelopeImport(Base):
    __tablename__ = 'Envelope_Import'

    envelopeImportID = Column(BigInteger, primary_key=True)
    title = Column(Unicode(255))
    description = Column(UnicodeText(1073741823))
    reportingdate = Column(DateTime)
    coverage = Column(Unicode(255))
    countryCode = Column(Unicode(2))
    spatialUnit = Column(Unicode(42))
    obligation = Column(Unicode(255))
    envelopeLink = Column(Unicode(255), nullable=False)
    reportedYear = Column(Unicode(4))
    endYear = Column(Unicode(4))
    partOfYear = Column(Unicode(255))
    importDate = Column(DateTime, nullable=False)
    processed = Column(SmallInteger)
    countryName = Column(Unicode(100))
    locality = Column(Unicode(500))
    startyear = Column(Unicode(4))
    lastworkitem = Column(Unicode(50))
    penultimateworkitem = Column(Unicode(50))
    creator = Column(Unicode(255))
    feedbacks = Column(UnicodeText(1073741823))
    envelopeID = Column(Unicode(50))
    released = Column(SmallInteger)
    blockedByQA = Column(SmallInteger)
    deleted = Column(SmallInteger)


t_Envelope_Obligations = Table(
    'Envelope_Obligations', metadata,
    Column('envelopeImportID', ForeignKey(u'Envelope_Import.envelopeImportID'), primary_key=True, nullable=False),
    Column('ObligationID', ForeignKey(u'Obligation.ObligationID'), primary_key=True, nullable=False)
)


class EnvelopeSchema(Base):
    __tablename__ = 'Envelope_Schema'

    id_schema = Column(BigInteger, primary_key=True)
    name_schema = Column(Unicode(255))
    cod_schema = Column(Unicode(50))


t_FMEJobController = Table(
    'FMEJobController', metadata,
    Column('ReportNetURL', Unicode(255), nullable=False),
    Column('FMEWorkspace', Unicode(255), nullable=False),
    Column('FMEJobID', Unicode(50), nullable=False),
    Column('TimeStarted', DateTime, nullable=False),
    Column('TimeFinished', DateTime),
    Column('Result', Unicode)
)


class IMPORTERROR(Base):
    __tablename__ = 'IMPORT_ERRORS'

    importErrorID = Column(BigInteger, primary_key=True)
    envelopeImportID = Column(ForeignKey(u'Envelope_Import.envelopeImportID'))
    importID = Column(BigInteger)
    schema = Column(Unicode(10), nullable=False)
    table = Column(String(255, u'Latin1_General_CI_AS'))
    message = Column(Unicode(4000))
    raisedAt = Column(DateTime, nullable=False)

    Envelope_Import = relationship(u'EnvelopeImport')


class IndicatorsDataset(Base):
    __tablename__ = 'Indicators_Dataset'

    Id = Column(Integer, primary_key=True)
    URL = Column(Unicode(250), nullable=False)
    MD_URL = Column(Unicode(250))
    IdIndicatorAssessment = Column(ForeignKey(u'Indicators_IndicatorAssessment.Id'), nullable=False)

    Indicators_IndicatorAssessment = relationship(u'IndicatorsIndicatorAssessment')


class IndicatorsFeatureFeature(Base):
    __tablename__ = 'Indicators_Feature_Feature'

    Feature = Column(Unicode(250), primary_key=True, nullable=False)
    IdGESComponent = Column(ForeignKey(u'Indicators_Feature_GESComponent.Id'), primary_key=True, nullable=False)

    Indicators_Feature_GESComponent = relationship(u'IndicatorsFeatureGESComponent')


class IndicatorsFeatureGESComponent(Base):
    __tablename__ = 'Indicators_Feature_GESComponent'

    Id = Column(Integer, primary_key=True)
    GESComponent = Column(Unicode(50), nullable=False)
    IdIndicatorAssessment = Column(ForeignKey(u'Indicators_IndicatorAssessment.Id'), nullable=False)

    Indicators_IndicatorAssessment = relationship(u'IndicatorsIndicatorAssessment')


class IndicatorsIndicatorAssessment(Base):
    __tablename__ = 'Indicators_IndicatorAssessment'

    Id = Column(Integer, primary_key=True)
    IndicatorCode = Column(Unicode(50), nullable=False)
    IndicatorTitle = Column(Unicode(250), nullable=False)
    IndicatorSource = Column(Unicode(50), nullable=False)
    IndicatorSourceOther = Column(Unicode(50))
    UniqueReference = Column(Unicode(250), nullable=False)
    DatasetVoidReason = Column(Unicode(100))
    IdReportedInformation = Column(ForeignKey(u'ReportedInformation.Id'), nullable=False)

    ReportedInformation = relationship(u'ReportedInformation')


class IndicatorsIndicatorAssessmentTarget(Base):
    __tablename__ = 'Indicators_IndicatorAssessment_Target'

    TargetCode = Column(Unicode(50), primary_key=True, nullable=False)
    IdIndicatorAssessment = Column(ForeignKey(u'Indicators_IndicatorAssessment.Id'), primary_key=True, nullable=False)

    Indicators_IndicatorAssessment = relationship(u'IndicatorsIndicatorAssessment')


class IndicatorsMarineUnit(Base):
    __tablename__ = 'Indicators_MarineUnit'

    MarineReportingUnit = Column(Unicode(50), primary_key=True, nullable=False)
    IdIndicatorAssessment = Column(ForeignKey(u'Indicators_IndicatorAssessment.Id'), primary_key=True, nullable=False)

    Indicators_IndicatorAssessment = relationship(u'IndicatorsIndicatorAssessment')


class LAssessedInformation(Base):
    __tablename__ = 'L_AssessedInformations'

    Id = Column(Integer, primary_key=True)
    AssessedInformation = Column(Unicode(50), nullable=False)


class LAssessmentCriteria(Base):
    __tablename__ = 'L_AssessmentCriterias'

    Id = Column(Integer, primary_key=True)
    AssessmentCriteria = Column(Unicode(25), nullable=False)


class LAssessmentTopic(Base):
    __tablename__ = 'L_AssessmentTopics'

    Id = Column(Integer, primary_key=True)
    AssessmentTopic = Column(Unicode(200), nullable=False)


class LConclusion(Base):
    __tablename__ = 'L_Conclusions'

    Id = Column(Integer, primary_key=True)
    Conclusion = Column(Unicode(50), nullable=False)


class LCountry(Base):
    __tablename__ = 'L_Countries'

    Code = Column(Unicode(2), primary_key=True)
    Country = Column(Unicode(50), nullable=False)


class LDateReportDue(Base):
    __tablename__ = 'L_DateReportDues'

    Id = Column(Integer, primary_key=True)
    DateReportDue = Column(Date, nullable=False)


class LEvidence(Base):
    __tablename__ = 'L_Evidences'

    Id = Column(Integer, primary_key=True)
    Evidence = Column(Unicode(150), nullable=False)


class LFeature(Base):
    __tablename__ = 'L_Features'

    Code = Column(Unicode(50), primary_key=True)
    Feature = Column(Unicode(200))
    Subject = Column(Unicode(250))
    Theme = Column(Unicode(250))
    Sub_theme = Column('Sub-theme', Unicode(250))


class LGESComponent(Base):
    __tablename__ = 'L_GESComponents'

    Code = Column(Unicode(10), primary_key=True)
    Description = Column(Unicode(100))
    GESComponent = Column(Unicode(15))
    Old = Column(BIT, nullable=False)


class LIntegrationRule(Base):
    __tablename__ = 'L_IntegrationRules'

    Code = Column(Unicode(15), primary_key=True)
    Label = Column(Unicode(50))
    Type = Column(Unicode(50))
    Description = Column(Unicode(1000))


class LMSFDArticle(Base):
    __tablename__ = 'L_MSFDArticles'

    Id = Column(Integer, primary_key=True)
    MSFDArticle = Column(Unicode(20), nullable=False)


class LNACECode(Base):
    __tablename__ = 'L_NACECodes'

    Code = Column(Unicode(4), primary_key=True)
    Label = Column(Unicode(255))


class LParameter(Base):
    __tablename__ = 'L_Parameters'

    Code = Column(Unicode(10), primary_key=True)
    Description = Column(Unicode(150))


class LThresholdSource(Base):
    __tablename__ = 'L_ThresholdSources'

    Code = Column(Unicode(20), primary_key=True)
    Description = Column(Unicode(150))


class LUnit(Base):
    __tablename__ = 'L_Units'

    Notation = Column(Unicode(20), primary_key=True)
    Description = Column(Unicode(50))


class MRUAnalysi(Base):
    __tablename__ = 'MRU_Analysis'

    OBJECTID = Column(Integer, primary_key=True)
    MarineReportingUnitId = Column(Unicode(50), nullable=False)
    SHAPE = Column(NullType)


class MRUsPublication(Base):
    __tablename__ = 'MRUs_Publication'

    OBJECTID = Column(Integer, primary_key=True)
    localId = Column(Unicode(254))
    namespace = Column(Unicode(254))
    versionId = Column(Unicode(50))
    thematicId = Column(Unicode(50))
    nameTxtInt = Column(Unicode(254))
    nameText = Column(Unicode(254))
    nameTxtLan = Column(Unicode(254))
    desigBegin = Column(Unicode(254))
    desigEnd = Column(Unicode(254))
    themaIdSch = Column(Unicode(25))
    beginLife = Column(Unicode(10))
    envDomain = Column(Unicode(5))
    zoneType = Column(Unicode(15))
    spZoneType = Column(Unicode(25))
    legisSName = Column(Unicode(350))
    legisName = Column(Unicode(350))
    legisDate = Column(Unicode(10))
    legisDateType = Column(Unicode(15))
    legisLink = Column(Unicode(350))
    legisLevel = Column(Unicode(15))
    rZoneId = Column(Unicode(3))
    rZoneIdSch = Column(Unicode(20))
    Country = Column(Unicode(50))
    Type = Column(Unicode(50))
    Area = Column(Float(24))
    Region = Column(Unicode(20))
    GEOM = Column(NullType)


class MarineRegion(Base):
    __tablename__ = 'MarineRegion'

    OBJECTID = Column(Integer, primary_key=True)
    MarineRegionId = Column(Unicode(50), nullable=False)
    Description = Column(Unicode(255))
    Area = Column(Float(53))
    SHAPE = Column(NullType)
    localId = Column(Unicode(254))
    namespace = Column(Unicode(254))
    versionId = Column(Unicode(25))
    thematicId = Column(Unicode(42))
    nameTxtInt = Column(Unicode(254))
    nameText = Column(Unicode(254))
    nameTxtLan = Column(Unicode(254))
    desigBegin = Column(Unicode(254))
    desigEnd = Column(Unicode(254))


class MarineReportingUnit(Base):
    __tablename__ = 'MarineReportingUnit'

    OBJECTID = Column(Integer, primary_key=True)
    CountryCode = Column(Unicode(2), nullable=False)
    MarineReportingUnitId = Column(Unicode(50), nullable=False)
    Region = Column(Unicode(20))
    Description = Column(Unicode(255))
    Area = Column(Float(53))
    SHAPE = Column(NullType)
    localId = Column(Unicode(254))
    namespace = Column(Unicode(254))
    versionId = Column(Unicode(25))
    thematicId = Column(Unicode(42))
    nameTxtInt = Column(Unicode(254))
    nameText = Column(Unicode(254))
    nameTxtLan = Column(Unicode(254))
    desigBegin = Column(Unicode(254))
    desigEnd = Column(Unicode(254))
    _4geo = Column('4geo', Unicode(500))


class Obligation(Base):
    __tablename__ = 'Obligation'

    ObligationID = Column(Integer, primary_key=True)
    Title = Column(Unicode(150))
    Description = Column(Unicode(400))

    Envelope_Import = relationship(u'EnvelopeImport', secondary='Envelope_Obligations')


class ReportedInformation(Base):
    __tablename__ = 'ReportedInformation'

    Id = Column(Integer, primary_key=True)
    CountryCode = Column(Unicode(2), nullable=False)
    Schema = Column(Unicode(50), nullable=False)
    ContactMail = Column(Unicode(50), nullable=False)
    ContactName = Column(Unicode(100))
    ContactOrganisation = Column(Unicode(1000), nullable=False)
    ReportingDate = Column(Date, nullable=False)
    ReportedFileLink = Column(Unicode(350), nullable=False)
    IdReportingPeriod = Column(ForeignKey(u'ReportingPeriod.Id'), nullable=False)

    ReportingPeriod = relationship(u'ReportingPeriod')


# class ReportedInformation(Base):
#     """ Class implementation for the view named 'V_ReportedInformation'
#
#     Override the original ReportedInformation class with the 'view'
#     named V_ReportedInformation, so the view will be used instead of the
#     'ReportedInformation' table.
#     """
#
#     __tablename__ = 'V_ReportedInformation'
#
#     Id = Column(Integer, primary_key=True)
#     CountryCode = Column(Unicode(2), nullable=False)
#     Schema = Column(Unicode(50), nullable=False)
#     ContactMail = Column(Unicode(50), nullable=False)
#     ContactName = Column(Unicode(100))
#     ContactOrganisation = Column(Unicode(1000), nullable=False)
#     ReportingDate = Column(Date, nullable=False)
#     ReportedFileLink = Column(Unicode(350), nullable=False)
#     EnvelopeStatus = Column(Unicode(50))


t_V_ReportedInformation = Table(
    'V_ReportedInformation', metadata,
    Column('Id', Integer, nullable=False),
    Column('CountryCode', Unicode(2), nullable=False),
    Column('Schema', Unicode(50), nullable=False),
    Column('ContactMail', Unicode(50), nullable=False),
    Column('ContactName', Unicode(100)),
    Column('ContactOrganisation', Unicode(1000), nullable=False),
    Column('ReportingDate', Date, nullable=False),
    Column('ReportedFileLink', Unicode(350), nullable=False),
    Column('IdReportingPeriod', Integer, nullable=False),
    Column('EnvelopeStatus', Unicode(50)),
)


# class ReportedInformation(sql.Base):
#     __table__ = t_V_ReportedInformation
#
#     __mapper_args__ = {
#         'primary_key': [t_V_ReportedInformation.c.Id],
#     }


class ReportingPeriod(Base):
    __tablename__ = 'ReportingPeriod'

    Id = Column(Integer, primary_key=True)
    Year = Column(Unicode(4), nullable=False)
    Description = Column(Unicode(250), nullable=False)


class ReportingHistory(Base):
    __tablename__ = 'Reporting_history'

    Id = Column(Integer, primary_key=True)
    CountryCode = Column(Unicode(2), nullable=False)
    FileName = Column(Unicode(250), nullable=False)
    LocationURL = Column(Unicode(500), nullable=False)
    Schema = Column(Unicode(250), nullable=False)
    ReportingObligation = Column(Unicode(250))
    ReportingObligationID = Column(Integer, nullable=False)
    ReportingObligationURL = Column(Unicode(250), nullable=False)
    DateDue = Column(DateTime)
    DateReceived = Column(DateTime, nullable=False)
    DateReleased = Column(DateTime)
    ReportingDelay = Column(Integer)
    EnvelopeStatus = Column(Unicode(100))
    ReportType = Column(Unicode(50))


t_V_ART10_Targets_2018 = Table(
    'V_ART10_Targets_2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('ReportingDate', Date, nullable=False),
    Column('ReportedFileLink', Unicode(350), nullable=False),
    Column('Region', Unicode(20)),
    Column('MarineReportingUnit', Unicode(50), nullable=False),
    Column('TargetCode', Unicode(50), nullable=False),
    Column('Description', Unicode(2500), nullable=False),
    Column('TimeScale', Unicode(6), nullable=False),
    Column('UpdateDate', Unicode(6), nullable=False),
    Column('UpdateType', Unicode(50), nullable=False),
    Column('GESComponents', Unicode),
    Column('Features', Unicode),
    Column('Measures', Unicode),
    Column('Parameter', Unicode(50)),
    Column('ParameterOther', Unicode(250)),
    Column('Element', Unicode(50)),
    Column('Element2', Unicode(50)),
    Column('TargetValue', Float(53)),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode(50)),
    Column('ValueUnitOther', Unicode(250)),
    Column('TargetStatus', Unicode(50)),
    Column('AssessmentPeriod', Unicode(9)),
    Column('ProgressDescription', Unicode(2500)),
    Column('Indicators', Unicode)
)


t_V_ART8_GES_2018 = Table(
    'V_ART8_GES_2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('ReportingDate', Date, nullable=False),
    Column('ReportedFileLink', Unicode(350), nullable=False),
    Column('Region', Unicode(20)),
    Column('MarineReportingUnit', Unicode(50), nullable=False),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('Feature', Unicode(250), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('GESExtentUnit', Unicode(250)),
    Column('GESExtentThreshold', Numeric(8, 5)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('AssessmentsPeriod', Unicode(9), nullable=False),
    Column('DescriptionOverallStatus', Unicode(2500)),
    Column('IntegrationRuleTypeCriteria', Unicode(50)),
    Column('IntegrationRuleDescriptionCriteria', Unicode(1000)),
    Column('IntegrationRuleDescriptionReferenceCriteria', Unicode(250)),
    Column('IntegrationRuleTypeParameter', Unicode(50)),
    Column('IntegrationRuleDescriptionParameter', Unicode(1000)),
    Column('IntegrationRuleDescriptionReferenceParameter', Unicode(250)),
    Column('PressureCodes', Unicode),
    Column('TargetCodes', Unicode),
    Column('Element', Unicode(250)),
    Column('Element2', Unicode(250)),
    Column('ElementSource', Unicode(50)),
    Column('ElementCode', Unicode(50)),
    Column('Element2Code', Unicode(50)),
    Column('ElementCodeSource', Unicode(50)),
    Column('Element2CodeSource', Unicode(50)),
    Column('DescriptionElement', Unicode(2500)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaStatus', Unicode(50)),
    Column('DescriptionCriteria', Unicode(2500)),
    Column('Parameter', Unicode(50)),
    Column('ParameterOther', Unicode(250)),
    Column('ThresholdValueUpper', Float(53)),
    Column('ThresholdValueLower', Float(53)),
    Column('ThresholdQualitative', Unicode(250)),
    Column('ThresholdValueSource', Unicode(50)),
    Column('ThresholdValueSourceOther', Unicode(250)),
    Column('ValueAchievedUpper', Float(53)),
    Column('ValueAchievedLower', Float(53)),
    Column('ValueUnit', Unicode(50)),
    Column('ValueUnitOther', Unicode(100)),
    Column('ProportionThresholdValue', Float(53)),
    Column('ProportionThresholdValueUnit', Unicode(50)),
    Column('ProportionValueAchieved', Float(53)),
    Column('Trend', Unicode(50)),
    Column('ParameterAchieved', Unicode(50)),
    Column('DescriptionParameter', Unicode(2500)),
    Column('IndicatorCode', Unicode(50))
)


t_V_ART9_GES_2018 = Table(
    'V_ART9_GES_2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('ReportingDate', Date, nullable=False),
    Column('ReportedFileLink', Unicode(350), nullable=False),
    Column('Region', Unicode(20)),
    Column('MarineReportingUnit', Unicode(50)),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('JustificationDelay', Unicode(1000)),
    Column('JustificationNonUse', Unicode(1000)),
    Column('Features', Unicode),
    Column('GESDescription', Unicode(2500)),
    Column('DeterminationDate', Unicode(6)),
    Column('UpdateType', Unicode(50))
)


t_V_CriteriaStatus2018 = Table(
    'V_CriteriaStatus2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('Country', Unicode(50), nullable=False),
    Column('Region', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRUDescription', Unicode(255)),
    Column('MRUArea', Float(53)),
    Column('Feature', Unicode(250), nullable=False),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('Element', Unicode(250)),
    Column('Criteria', Unicode(50), nullable=False),
    Column('CriteriaStatus', Unicode(50), nullable=False)
)


t_V_D10_MarineLitter_2018 = Table(
    'V_D10_MarineLitter_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150))
)


t_V_D11_Noise_2018 = Table(
    'V_D11_Noise_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_D1_Species_2018 = Table(
    'V_D1_Species_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_D2_NIS_2018 = Table(
    'V_D2_NIS_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('Element/Element2', Unicode(503)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_D3_FishStocks_2018 = Table(
    'V_D3_FishStocks_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_D4_D1_Ecosystems_2018 = Table(
    'V_D4_D1_Ecosystems_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_D5_Eutrophication_2018 = Table(
    'V_D5_Eutrophication_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_D6_D1_Habitats_2018 = Table(
    'V_D6_D1_Habitats_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_D7_Hydrographical_2018 = Table(
    'V_D7_Hydrographical_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_D8_D9_Contaminants_2018 = Table(
    'V_D8_D9_Contaminants_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_ElementStatus2018 = Table(
    'V_ElementStatus2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('Country', Unicode(50), nullable=False),
    Column('Region', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRUDescription', Unicode(255)),
    Column('MRUArea', Float(53)),
    Column('Feature', Unicode(250), nullable=False),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('Element', Unicode(250)),
    Column('Element2', Unicode(250)),
    Column('ElementStatus', Unicode(50))
)


t_V_EnvelopeAnalytics = Table(
    'V_EnvelopeAnalytics', metadata,
    Column('EnvelopeImportID', BigInteger),
    Column('EnvelopeTitle', Unicode(255)),
    Column('EnvelopeDescription', UnicodeText(1073741823)),
    Column('EnvelopeReportingDate', DateTime),
    Column('EnvelopeLink', Unicode(255)),
    Column('EnvelopeImportDate', DateTime),
    Column('EnvelopeProcessed', SmallInteger),
    Column('EnvelopeCountryCode', Unicode(2)),
    Column('EnvelopeCountry', Unicode(100)),
    Column('EnvelopeCreator', Unicode(255)),
    Column('EnvelopeID', Unicode(50)),
    Column('EnvelopeReleased', SmallInteger),
    Column('EnvelopeBlocked', SmallInteger),
    Column('EnvelopeFileName', Unicode(255)),
    Column('EnvelopeFileTitle', Unicode(255)),
    Column('EnvelopeFileLink', Unicode(500)),
    Column('EnvelopeObligation', Unicode(150)),
    Column('EnvelopeFileID', BigInteger),
    Column('LastWorkItem', Unicode(50)),
    Column('PenultimateWorkItem', Unicode(50)),
    Column('Feedback', UnicodeText(1073741823)),
    Column('deleted', SmallInteger),
    Column('FileExtensionConcat', Unicode)
)


t_V_EnvelopeAnalyticsOtherEnvelopes = Table(
    'V_EnvelopeAnalyticsOtherEnvelopes', metadata,
    Column('EnvelopeImportID', BigInteger, nullable=False),
    Column('EnvelopeTitle', Unicode(255)),
    Column('EnvelopeDescription', UnicodeText(1073741823)),
    Column('EnvelopeReportingDate', DateTime),
    Column('EnvelopeLink', Unicode(255), nullable=False),
    Column('EnvelopeImportDate', DateTime, nullable=False),
    Column('EnvelopeProcessed', SmallInteger),
    Column('EnvelopeCountryCode', Unicode(2)),
    Column('EnvelopeCountry', Unicode(100)),
    Column('EnvelopeCreator', Unicode(255)),
    Column('EnvelopeID', Unicode(50)),
    Column('EnvelopeReleased', SmallInteger),
    Column('EnvelopeBlocked', SmallInteger),
    Column('EnvelopeFileName', Unicode(255), nullable=False),
    Column('EnvelopeFileTitle', Unicode(255), nullable=False),
    Column('EnvelopeFileLink', Unicode(500), nullable=False),
    Column('EnvelopeObligation', Unicode(150)),
    Column('EnvelopeFileID', BigInteger),
    Column('LastWorkItem', Unicode(50)),
    Column('PenultimateWorkItem', Unicode(50)),
    Column('Feedback', UnicodeText(1073741823)),
    Column('deleted', SmallInteger),
    Column('FileExtensionConcat', Unicode)
)


t_V_EnvelopeAnalytics_Thematics = Table(
    'V_EnvelopeAnalytics_Thematics', metadata,
    Column('EnvelopeCountry', Unicode(100)),
    Column('EnvelopeCountryCode', Unicode(2)),
    Column('reportingdate', DateTime),
    Column('ObligationID', Integer),
    Column('EnvelopeObligation', Unicode(150)),
    Column('LastWorkItem', Unicode(50)),
    Column('PenultimateWorkItem', Unicode(50)),
    Column('EnvelopeBlocked', SmallInteger),
    Column('deleted', SmallInteger)
)


t_V_GESComponents_Criteria = Table(
    'V_GESComponents_Criteria', metadata,
    Column('Code', Unicode(10), nullable=False),
    Column('Description', Unicode(100)),
    Column('GESComponent', Unicode(15)),
    Column('Old', BIT, nullable=False)
)


t_V_GESComponents_Descriptor = Table(
    'V_GESComponents_Descriptor', metadata,
    Column('Code', Unicode(10), nullable=False),
    Column('Description', Unicode(100)),
    Column('GESComponent', Unicode(15)),
    Column('Old', BIT, nullable=False)
)


t_V_GESComponents_Indicator = Table(
    'V_GESComponents_Indicator', metadata,
    Column('Code', Unicode(10), nullable=False),
    Column('Description', Unicode(100)),
    Column('GESComponent', Unicode(15)),
    Column('Old', BIT, nullable=False)
)


t_V_General_2018 = Table(
    'V_General_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MarineSubregion', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50)),
    Column('Parameter/ParameterOther', Unicode(303)),
    Column('ParameterLabel', Unicode(403)),
    Column('ParameterDescription', Unicode(2500)),
    Column('ParameterAchieved', Unicode(50)),
    Column('Trend', Unicode(50))
)


t_V_General_2018_2 = Table(
    'V_General_2018_2', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('OverallStatusDescription', Unicode(2500)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MarineSubregion', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Element2CodeSource', Unicode(50)),
    Column('ElementDescription', Unicode(2500)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50)),
    Column('CriteriaDescription', Unicode(2500)),
    Column('Parameter/ParameterOther', Unicode(303)),
    Column('ParameterLabel', Unicode(403)),
    Column('ParameterDescription', Unicode(2500)),
    Column('ParameterAchieved', Unicode(50)),
    Column('Trend', Unicode(50))
)


t_V_General_2018_old = Table(
    'V_General_2018_old', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_Indicators_Datasets_2018 = Table(
    'V_Indicators_Datasets_2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('IndicatorCode', Unicode(50), nullable=False),
    Column('IndicatorTitle', Unicode(250), nullable=False),
    Column('IndicatorSource', Unicode(50), nullable=False),
    Column('IndicatorSourceOther', Unicode(50)),
    Column('UniqueReference', Unicode(250), nullable=False),
    Column('MD_URL', Unicode(250)),
    Column('URL', Unicode(250), nullable=False)
)


t_V_MRU_Spatial = Table(
    'V_MRU_Spatial', metadata,
    Column('MarineReportingUnitId', Unicode(50), nullable=False),
    Column('CountryCode', Unicode(2), nullable=False),
    Column('SHAPE', NullType)
)


t_V_Obligation760 = Table(
    'V_Obligation760', metadata,
    Column('Name', Unicode(255)),
    Column('obligation', Unicode(255)),
    Column('countryCode', Unicode(2))
)


t_V_OverallStatus2018 = Table(
    'V_OverallStatus2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('Country', Unicode(50), nullable=False),
    Column('Region', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRUDescription', Unicode(255)),
    Column('MRUArea', Float(53)),
    Column('Feature', Unicode(250), nullable=False),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('GESExtentUnit', Unicode(250)),
    Column('GESExtentThreshold', Numeric(8, 5))
)


t_V_Parameters2018 = Table(
    'V_Parameters2018', metadata,
    Column('CountryCode', Unicode(2), nullable=False),
    Column('Country', Unicode(50), nullable=False),
    Column('Region', Unicode(20)),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRUDescription', Unicode(255)),
    Column('MRUArea', Float(53)),
    Column('Feature', Unicode(250), nullable=False),
    Column('GESComponent', Unicode(50), nullable=False),
    Column('Element', Unicode(250)),
    Column('Criteria', Unicode(50), nullable=False),
    Column('Parameter', Unicode(50), nullable=False),
    Column('ParameterAchieved', Unicode(50), nullable=False),
    Column('Trend', Unicode(50), nullable=False)
)


t_V_Regional_2018 = Table(
    'V_Regional_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('Subregion', Unicode(50)),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element/Element2', Unicode(503)),
    Column('ElementStatus', Unicode(50)),
    Column('ElementDescription', Unicode(2500)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50)),
    Column('Parameter/ParameterOther', Unicode(303)),
    Column('ParameterLabel', Unicode(403)),
    Column('ParameterDescription', Unicode(2500)),
    Column('ParameterAchieved', Unicode(50)),
    Column('Trend', Unicode(50))
)


t_V_Regional_D10_MarineLitter_2018 = Table(
    'V_Regional_D10_MarineLitter_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150))
)


t_V_Regional_D1_D4_Ecosystems_2018 = Table(
    'V_Regional_D1_D4_Ecosystems_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_Regional_D1_Species_2018 = Table(
    'V_Regional_D1_Species_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_Regional_D2_NIS_2018 = Table(
    'V_Regional_D2_NIS_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('GESExtentAchieved', Numeric(8, 5)),
    Column('Element', Unicode(250)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_Regional_D3_FishStocks_2018 = Table(
    'V_Regional_D3_FishStocks_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_Regional_D5_Eutrophication_2018 = Table(
    'V_Regional_D5_Eutrophication_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_Regional_D6_D1_Habitats_2018 = Table(
    'V_Regional_D6_D1_Habitats_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('CriteriaStatus', Unicode(50))
)


t_V_Regional_D8_D9_Contaminants_2018 = Table(
    'V_Regional_D8_D9_Contaminants_2018', metadata,
    Column('GESComponent', Unicode(50), nullable=False),
    Column('ComponentLabel', Unicode(100)),
    Column('Country', Unicode(50), nullable=False),
    Column('Code', Unicode(2), nullable=False),
    Column('MRU', Unicode(50), nullable=False),
    Column('MRULabel', Unicode(255)),
    Column('Subregion', Unicode(50), nullable=False),
    Column('SubregionLabel', Unicode(255)),
    Column('Feature', Unicode(200)),
    Column('GESAchieved', Unicode(100), nullable=False),
    Column('Element', Unicode(250)),
    Column('ElementStatus', Unicode(50)),
    Column('Criteria', Unicode(50)),
    Column('CriteriaLabel', Unicode(100)),
    Column('Parameter', Unicode(50)),
    Column('ParameterLabel', Unicode(150)),
    Column('Trend', Unicode(50))
)


t_V_ReportList = Table(
    'V_ReportList', metadata,
    Column('Country', Unicode(50), nullable=False),
    Column('cod_schema', Unicode(50)),
    Column('exists', Integer),
    Column('lastworkitem', Unicode(50)),
    Column('penultimateworkitem', Unicode(50)),
    Column('blockedByQa', SmallInteger),
    Column('reportingdate', DateTime),
    Column('obligation', Unicode(255))
)


t_V_Subregion_Spatial = Table(
    'V_Subregion_Spatial', metadata,
    Column('MarineRegionId', Unicode(50), nullable=False),
    Column('SHAPE', NullType)
)
