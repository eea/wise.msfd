# coding: utf-8
from sqlalchemy import (Column, Date, DateTime, ForeignKey, Index, Integer,
                        LargeBinary, String, Table, Unicode, text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


t_Country = Table(
    'Country', metadata,
    Column('C_CD', Unicode(255), unique=True),
    Column('Region', Unicode(255), index=True),
    Column('METADATA', Unicode),
    Column('URL', Unicode(255))
)


t_MSFD10_DESCrit = Table(
    'MSFD10_DESCrit', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('Topic', Unicode(255)),
    Column('GESDescriptorsCriteriaIndicators', Unicode(255)),
    Column('Other', Unicode(255)),
    Column('MSFD10_Target', ForeignKey(u'MSFD10_Targets.MSFD10_Target_ID'), nullable=False)
)


t_MSFD10_FeaturesPressures = Table(
    'MSFD10_FeaturesPressures', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('PhysicalChemicalHabitatsFunctionalPressures', Unicode(255)),
    Column('Other', Unicode(255)),
    Column('MSFD10_Target', ForeignKey(u'MSFD10_Targets.MSFD10_Target_ID'), nullable=False),
    Column('FeatureType', Unicode(100))
)


t_MSFD10_GeneralInformation = Table(
    'MSFD10_GeneralInformation', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('YNCategory', Unicode(255)),
    Column('SupportingTextY', Unicode),
    Column('SupportingTextN', Unicode),
    Column('SupportingTextUnknown', Unicode),
    Column('MSFD10_GeneralInformation_Import', ForeignKey(u'MSFD10_Imports.MSFD10_Import_ID'), nullable=False)
)


class MSFD10Import(Base):
    __tablename__ = 'MSFD10_Imports'
    __table_args__ = (
        Index('MSFD10_Imports_UNIQUE_CountryRegion', 'MSFD10_Import_ReportingCountry', 'MSFD10_Import_ReportingRegion', unique=True),
    )

    MSFD10_Import_ID = Column(Integer, primary_key=True)
    MSFD10_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD10_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFD10_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFD10_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


t_MSFD10_Metadata = Table(
    'MSFD10_Metadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('MethodUsed', Unicode),
    Column('MSFD10_Metadata_Import', ForeignKey(u'MSFD10_Imports.MSFD10_Import_ID'), nullable=False)
)


t_MSFD10_ReportingInformation = Table(
    'MSFD10_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD10_ReportingInformation_Import', ForeignKey(u'MSFD10_Imports.MSFD10_Import_ID'), nullable=False)
)


t_MSFD10_TargetAssesmentArea = Table(
    'MSFD10_TargetAssesmentArea', metadata,
    Column('MarineUnitID', Unicode(42)),
    Column('ReportingFeature', Unicode(42)),
    Column('Topic', Unicode(255)),
    Column('AssessmentAreas', Unicode(42)),
    Column('MSFD10_Target', ForeignKey(u'MSFD10_Targets.MSFD10_Target_ID'), nullable=False)
)


class MSFD10Target(Base):
    __tablename__ = 'MSFD10_Targets'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    ThresholdValue = Column(Unicode)
    ReferencePointType = Column(Unicode(255))
    Baseline = Column(Unicode)
    Proportion = Column(Unicode(255))
    AssessmentMethod = Column(Unicode)
    DevelopmentStatus = Column(Unicode)
    TypeTargetIndicator = Column(Unicode(255))
    TimeScale = Column(Unicode(255))
    InterimGESTarget = Column(Unicode(255))
    CompatibilityExistingTargets = Column(Unicode)
    MSFD10_Targets_Import = Column(ForeignKey(u'MSFD10_Imports.MSFD10_Import_ID'), nullable=False)
    MSFD10_Target_ID = Column(Integer, primary_key=True)

    MSFD10_Import = relationship(u'MSFD10Import')


class MSFD11CommonLabel(Base):
    __tablename__ = 'MSFD11_Common_Labels'

    ID = Column(Integer, primary_key=True)
    value = Column(Unicode(250), nullable=False)
    country = Column(Unicode(250))
    region = Column(Unicode(250))
    group = Column(Unicode(250))
    mpgroup = Column(Unicode(250))
    mpsubgroup = Column(Unicode(250))
    Text = Column(Unicode(1000), nullable=False)


class MSFD11GeneralDescription(Base):
    __tablename__ = 'MSFD11_GeneralDescription'

    ID = Column(Integer, primary_key=True)
    Q1a_Overall_adequacy = Column(Unicode(20), nullable=False)
    Q1b_GapsGES = Column(ForeignKey(u'MSFD11_Q1b_GapsGES.ID'), nullable=False)
    Q1d_CoverageTargets_Habitats = Column(ForeignKey(u'MSFD11_Q1d_CoverageTargets_Habitats.ID'), nullable=False)
    Q1d_CoverageTargets_SpeciesFG = Column(ForeignKey(u'MSFD11_Q1d_CoverageTargets_SpeciesFG.ID'), nullable=False)
    Q1d_CoverageTargets_PhysChem = Column(ForeignKey(u'MSFD11_Q1d_CoverageTargets_PhysChem.ID'), nullable=False)
    Q1d_CoverageTargets_Pressures = Column(ForeignKey(u'MSFD11_Q1d_CoverageTargets_Pressures.ID'), nullable=False)
    Q1d_CoverageTargets_Activities = Column(ForeignKey(u'MSFD11_Q1d_CoverageTargets_Activities.ID'), nullable=False)
    Q1e_Gaps_Plans = Column(Unicode)
    Q3a_RegionalCooperation = Column(Unicode)
    Q3b_TransboundaryImpactsFeatures = Column(Unicode)
    Q3c_EnvironmentalChanges = Column(Unicode)
    Q3d_SourceContaminantsSeafood = Column(Unicode)
    Q3e_AccessAndUseRights = Column(Unicode)
    Q4a_ResponsibleCompetentAuthority = Column(Unicode)
    Q4c_RelationshipToCA = Column(Unicode)

    MSFD11_Q1b_GapsGE = relationship(u'MSFD11Q1bGapsGE')
    MSFD11_Q1d_CoverageTargets_Activity = relationship(u'MSFD11Q1dCoverageTargetsActivity')
    MSFD11_Q1d_CoverageTargets_Habitat = relationship(u'MSFD11Q1dCoverageTargetsHabitat')
    MSFD11_Q1d_CoverageTargets_PhysChem = relationship(u'MSFD11Q1dCoverageTargetsPhysChem')
    MSFD11_Q1d_CoverageTargets_Pressure = relationship(u'MSFD11Q1dCoverageTargetsPressure')
    MSFD11_Q1d_CoverageTargets_SpeciesFG = relationship(u'MSFD11Q1dCoverageTargetsSpeciesFG')


class MSFD11ImportedRow(Base):
    __tablename__ = 'MSFD11_ImportedRow'

    ID = Column(Integer, primary_key=True)
    Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    Table = Column(Unicode(100), nullable=False)
    PK = Column(Integer, nullable=False)
    Import = Column(ForeignKey(u'MSFD11_Imports.ID'), nullable=False)

    MSFD11_Import = relationship(u'MSFD11Import')


class MSFD11Import(Base):
    __tablename__ = 'MSFD11_Imports'

    ID = Column(Integer, primary_key=True)
    Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MemberState = Column(Unicode(2), nullable=False)
    Region = Column(Unicode(3), nullable=False)
    SubProgrammeID = Column(Unicode(50))
    FileName = Column(Unicode)
    Description = Column(Unicode)


class MSFD11MON(Base):
    __tablename__ = 'MSFD11_MON'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    MemberState = Column(Unicode(2), nullable=False)
    Region = Column(Unicode(3), nullable=False)
    GeneralDescription = Column(ForeignKey(u'MSFD11_GeneralDescription.ID'), nullable=False)
    ReporterName = Column(Unicode(255))
    ContactEmail = Column(Unicode(255))
    Organisation = Column(Unicode(255))
    ReportingDate = Column(Unicode(255))
    Import = Column(ForeignKey(u'MSFD11_Imports.ID'), nullable=False)

    MSFD11_GeneralDescription = relationship(u'MSFD11GeneralDescription')
    MSFD11_Import = relationship(u'MSFD11Import')


class MSFD11MONSub(Base):
    __tablename__ = 'MSFD11_MONSub'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    MemberState = Column(Unicode(2), nullable=False)
    Region = Column(Unicode(3), nullable=False)
    SubProgramme = Column(ForeignKey(u'MSFD11_SubProgramme.ID'), nullable=False)
    ReporterName = Column(Unicode(255))
    ContactEmail = Column(Unicode(255))
    Organisation = Column(Unicode(255))
    ReportingDate = Column(Unicode(255))
    Import = Column(ForeignKey(u'MSFD11_Imports.ID'), nullable=False)

    MSFD11_Import = relationship(u'MSFD11Import')
    MSFD11_SubProgramme = relationship(u'MSFD11SubProgramme')


class MSFD11MP(Base):
    __tablename__ = 'MSFD11_MP'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    MPType = Column(ForeignKey(u'MSFD11_MPTypes.ID'), nullable=False)
    ReferenceExistingProgramme = Column(ForeignKey(u'MSFD11_ReferenceExistingProgramme.ID'))
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'))
    MON = Column(ForeignKey(u'MSFD11_MON.ID'), nullable=False)

    MSFD11_MON = relationship(u'MSFD11MON')
    MSFD11_MPType = relationship(u'MSFD11MPType')
    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')
    MSFD11_ReferenceExistingProgramme = relationship(u'MSFD11ReferenceExistingProgramme')


class MSFD11MPType(Base):
    __tablename__ = 'MSFD11_MPTypes'

    ID = Column(Integer, primary_key=True)
    Value = Column(Unicode(50), nullable=False)
    Description = Column(Unicode(150), nullable=False)


class MSFD11MarineUnitID(Base):
    __tablename__ = 'MSFD11_MarineUnitID'

    ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(50), nullable=False)


class MSFD11MonitoringProgramme(Base):
    __tablename__ = 'MSFD11_MonitoringProgramme'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    Q4e_ProgrammeID = Column(Unicode(50), nullable=False)
    Q4f_ProgrammeDescription = Column(Unicode, nullable=False)
    Q5a_DescriptionOther = Column(Unicode(1000))
    Q5b_DescriptionOther = Column(Unicode(1000))
    Q5c_HabitatsOther = Column(Unicode(1000))
    Q5c_SpeciesOther = Column(Unicode(1000))
    Q5c_PhysicalChemicalOther = Column(Unicode(1000))
    Q5c_PressureOther = Column(Unicode(1000))
    Q5d_AdequacyForAssessmentGES = Column(ForeignKey(u'MSFD11_Q5d_AdequacyForAssessmentGES.ID'), nullable=False)
    Q5e_Other = Column(Unicode(1000))
    Q5f_DescriptionGES = Column(Unicode, nullable=False)
    Q5g_GapFillingDateGES = Column(Unicode(20), nullable=False)
    Q5h_PlansGES = Column(Unicode)
    Q6b_AdequacyForAssessmentTargets = Column(ForeignKey(u'MSFD11_Q6b_AdequacyForAssessmentTargets.ID'), nullable=False)
    Q6c_Target = Column(Unicode(20), nullable=False)
    Q6d_DescriptionTargets = Column(Unicode, nullable=False)
    Q6e_GapFillingDateTargets = Column(Unicode(20), nullable=False)
    Q6f_PlansTargets = Column(Unicode)
    Q7a_UsesActivitiesOther = Column(Unicode(1000))
    Q7b_DescriptionActivities = Column(Unicode, nullable=False)
    Q7c_RelevantMeasures = Column(Unicode)
    Q7d_DescriptionMeasures = Column(Unicode)
    Q7e_AdequacyForAssessmentMeasures = Column(ForeignKey(u'MSFD11_Q7e_AdequacyForAssessmentMeasures.ID'))
    Q7f_GapFillingDateActivitiesMeasures = Column(Unicode(20), nullable=False)
    Q8a_Other = Column(Unicode(1000))

    MSFD11_Q5d_AdequacyForAssessmentGE = relationship(u'MSFD11Q5dAdequacyForAssessmentGE')
    MSFD11_Q6b_AdequacyForAssessmentTarget = relationship(u'MSFD11Q6bAdequacyForAssessmentTarget')
    MSFD11_Q7e_AdequacyForAssessmentMeasure = relationship(u'MSFD11Q7eAdequacyForAssessmentMeasure')


class MSFD11MonitoringProgrammeList(Base):
    __tablename__ = 'MSFD11_MonitoringProgramme_List'

    ID = Column(Integer, primary_key=True)
    ElementName = Column(Unicode(255), nullable=False)
    subgroup = Column(Unicode(255))
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'), nullable=False)

    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')


class MSFD11MonitoringProgrammeMarineUnitID(Base):
    __tablename__ = 'MSFD11_MonitoringProgramme_MarineUnitID'

    ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(ForeignKey(u'MSFD11_MarineUnitID.ID'), nullable=False)
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'), nullable=False)

    MSFD11_MarineUnitID = relationship(u'MSFD11MarineUnitID')
    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')


class MSFD11Q1bGapsGE(Base):
    __tablename__ = 'MSFD11_Q1b_GapsGES'

    ID = Column(Integer, primary_key=True)
    GESDescriptorCriteria_D1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_3 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_4 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_5 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_6 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_1_7 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_2_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_2_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D3 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_3_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_3_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_3_3 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D4 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_4_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_4_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_4_3 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D5 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_5_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_5_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_5_3 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D6 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_6_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_6_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D7 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_7_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_7_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D8 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_8_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_8_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D9 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_9_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D10 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_10_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_10_2 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_D11 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_11_1 = Column(Unicode(20), nullable=False)
    GESDescriptorCriteria_11_2 = Column(Unicode(20), nullable=False)


class MSFD11Q1cAssociatedIndicator(Base):
    __tablename__ = 'MSFD11_Q1c_AssociatedIndicator'

    ID = Column(Integer, primary_key=True)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    GapsTargets = Column(ForeignKey(u'MSFD11_Q1c_GapsTargets.ID'), nullable=False)

    MSFD11_Q1c_GapsTarget = relationship(u'MSFD11Q1cGapsTarget')


class MSFD11Q1cEnvironmentalTarget(Base):
    __tablename__ = 'MSFD11_Q1c_EnvironmentalTarget'

    ID = Column(Integer, primary_key=True)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    GapsTargets = Column(ForeignKey(u'MSFD11_Q1c_GapsTargets.ID'), nullable=False)

    MSFD11_Q1c_GapsTarget = relationship(u'MSFD11Q1cGapsTarget')


class MSFD11Q1cGapsTarget(Base):
    __tablename__ = 'MSFD11_Q1c_GapsTargets'

    ID = Column(Integer, primary_key=True)
    TargetsIndicator = Column(Unicode(42))
    AddressedByProgramme = Column(Unicode(20), nullable=False)
    GeneralDescription = Column(ForeignKey(u'MSFD11_GeneralDescription.ID'), nullable=False)

    MSFD11_GeneralDescription = relationship(u'MSFD11GeneralDescription')


class MSFD11Q1dCoverageTargetsActivity(Base):
    __tablename__ = 'MSFD11_Q1d_CoverageTargets_Activities'

    ID = Column(Integer, primary_key=True)
    Activities_RenewableEnergy = Column(Unicode(20), nullable=False)
    Activities_OilGas = Column(Unicode(20), nullable=False)
    Activities_SeaweedOtherSeafood = Column(Unicode(20), nullable=False)
    Activities_GeneticBioprospectMaerl = Column(Unicode(20), nullable=False)
    Activities_Fisheries = Column(Unicode(20), nullable=False)
    Activities_MiningSandGravel = Column(Unicode(20), nullable=False)
    Activities_Dredging = Column(Unicode(20), nullable=False)
    Activities_Desalination = Column(Unicode(20), nullable=False)
    Activities_Aquaculture = Column(Unicode(20), nullable=False)
    Activities_LandClaimDefence = Column(Unicode(20), nullable=False)
    Activities_Ports = Column(Unicode(20), nullable=False)
    Activities_CablesPipelines = Column(Unicode(20), nullable=False)
    Activities_OffshoreStructures = Column(Unicode(20), nullable=False)
    Activities_Defence = Column(Unicode(20), nullable=False)
    Activities_DumpingMunitions = Column(Unicode(20), nullable=False)
    Activities_TourismRecreation = Column(Unicode(20), nullable=False)
    Activities_ResearchSurvey = Column(Unicode(20), nullable=False)
    Activities_Shipping = Column(Unicode(20), nullable=False)
    Activities_SolidWasteDisposal = Column(Unicode(20), nullable=False)
    Activities_StorageGases = Column(Unicode(20), nullable=False)
    Activities_Industry = Column(Unicode(20), nullable=False)
    Activities_AgricultForestry = Column(Unicode(20), nullable=False)
    Activities_Urban = Column(Unicode(20), nullable=False)
    Activities_ActivitiesUsesAll = Column(Unicode(20), nullable=False)
    Activities_UsesActivitiesOther = Column(Unicode(20), nullable=False)
    Activities_UsesActivitiesOther_Description = Column(Unicode)


class MSFD11Q1dCoverageTargetsHabitat(Base):
    __tablename__ = 'MSFD11_Q1d_CoverageTargets_Habitats'

    ID = Column(Integer, primary_key=True)
    Habitats_SeabedHabitatsAll = Column(Unicode(20), nullable=False)
    Habitats_LitRock = Column(Unicode(20), nullable=False)
    Habitats_LitSed = Column(Unicode(20), nullable=False)
    Habitats_ShallRock = Column(Unicode(20), nullable=False)
    Habitats_ShallSed = Column(Unicode(20), nullable=False)
    Habitats_ShelfRock = Column(Unicode(20), nullable=False)
    Habitats_ShelfSed = Column(Unicode(20), nullable=False)
    Habitats_BathAbys = Column(Unicode(20), nullable=False)
    Habitats_WaterColumnHabitatsAll = Column(Unicode(20), nullable=False)
    Habitats_IceHabitat = Column(Unicode(20), nullable=False)
    Habitats_HabitatsDirectiveAnnexI = Column(Unicode(20), nullable=False)
    Habitats_HabitatsOther = Column(Unicode(20), nullable=False)
    Habitats_HabitatsOther_Description = Column(Unicode)


class MSFD11Q1dCoverageTargetsPhysChem(Base):
    __tablename__ = 'MSFD11_Q1d_CoverageTargets_PhysChem'

    ID = Column(Integer, primary_key=True)
    PhysChem_TopographyBathymetry = Column(Unicode(20), nullable=False)
    PhysChem_SeaSurfaceTemperature = Column(Unicode(20), nullable=False)
    PhysChem_SeaBottomTemperature = Column(Unicode(20), nullable=False)
    PhysChem_IceCover = Column(Unicode(20), nullable=False)
    PhysChem_Salinity = Column(Unicode(20), nullable=False)
    PhysChem_CurrentVelocity = Column(Unicode(20), nullable=False)
    PhysChem_WaveExposure = Column(Unicode(20), nullable=False)
    PhysChem_Upwelling = Column(Unicode(20), nullable=False)
    PhysChem_Mixing = Column(Unicode(20), nullable=False)
    PhysChem_Turbidity = Column(Unicode(20), nullable=False)
    PhysChem_Transparency = Column(Unicode(20), nullable=False)
    PhysChem_ResidenceTime = Column(Unicode(20), nullable=False)
    PhysChem_NutrientLevels = Column(Unicode(20), nullable=False)
    PhysChem_OxygenLevels = Column(Unicode(20), nullable=False)
    PhysChem_pH = Column(Unicode(20), nullable=False)
    PhysChem_PhysicalChemicalOther = Column(Unicode(20), nullable=False)
    PhysChem_pH_Description = Column(Unicode)
    PhysChem_PhysicalChemicalOther_Description = Column(Unicode)


class MSFD11Q1dCoverageTargetsPressure(Base):
    __tablename__ = 'MSFD11_Q1d_CoverageTargets_Pressures'

    ID = Column(Integer, primary_key=True)
    Pressures_PhysLoss_Smother = Column(Unicode(20), nullable=False)
    Pressures_PhysLoss_Seal = Column(Unicode(20), nullable=False)
    Pressures_PhysLoss = Column(Unicode(20), nullable=False)
    Pressures_PhysDam_silt = Column(Unicode(20), nullable=False)
    Pressures_PhysDam_abrasion = Column(Unicode(20), nullable=False)
    Pressures_PhysDam_extraction = Column(Unicode(20), nullable=False)
    Pressures_PhysDam = Column(Unicode(20), nullable=False)
    Pressures_PhysDisturbance = Column(Unicode(20), nullable=False)
    Pressures_ChangeHydrology = Column(Unicode(20), nullable=False)
    Pressures_IntroHazSubstOther = Column(Unicode(20), nullable=False)
    Pressures_SystematicReleaseSubst = Column(Unicode(20), nullable=False)
    Pressures_NutrientOrgEnrich = Column(Unicode(20), nullable=False)
    Pressures_InputN_Psubst = Column(Unicode(20), nullable=False)
    Pressures_InputOrganics = Column(Unicode(20), nullable=False)
    Pressures_BioDisturb_other = Column(Unicode(20), nullable=False)
    Pressures_IntroMicroPath = Column(Unicode(20), nullable=False)
    Pressures_IntroNIS = Column(Unicode(20), nullable=False)
    Pressures_ExtractSpeciesAll = Column(Unicode(20), nullable=False)
    Pressures_Acidification = Column(Unicode(20), nullable=False)
    Pressures_Noise = Column(Unicode(20), nullable=False)
    Pressures_Litter = Column(Unicode(20), nullable=False)
    Pressures_ChangeThermal = Column(Unicode(20), nullable=False)
    Pressures_ChangeSalinity = Column(Unicode(20), nullable=False)
    Pressures_IntroSynthComp = Column(Unicode(20), nullable=False)
    Pressures_IntroNonSynthSubst = Column(Unicode(20), nullable=False)
    Pressures_IntroRadioNuclides = Column(Unicode(20), nullable=False)
    Pressures_AcutePollutionEvents = Column(Unicode(20), nullable=False)
    Pressures_ExtractSpeciesFishShellfish = Column(Unicode(20), nullable=False)
    Pressures_ExtractSpeciesMaerl = Column(Unicode(20), nullable=False)
    Pressures_ExtractSpeciesSeaweed = Column(Unicode(20), nullable=False)
    Pressures_ExtractSpeciesOther = Column(Unicode(20), nullable=False)
    Pressures_PressureOther = Column(Unicode(20), nullable=False)
    Pressures_PressureOther_Description = Column(Unicode)


class MSFD11Q1dCoverageTargetsSpeciesFG(Base):
    __tablename__ = 'MSFD11_Q1d_CoverageTargets_SpeciesFG'

    ID = Column(Integer, primary_key=True)
    SpeciesFG_BirdsAll = Column(Unicode(20), nullable=False)
    SpeciesFG_MammalsAll = Column(Unicode(20), nullable=False)
    SpeciesFG_ReptilesAll = Column(Unicode(20), nullable=False)
    SpeciesFG_FishAll = Column(Unicode(20), nullable=False)
    SpeciesFG_CephalopodsAll = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsIntertidalBenthic = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsInshoreSurface = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsInshorePelagic = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsInshoreBenthic = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsInshoreHerbiv = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsOffshoreSurface = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsOffshorePelagic = Column(Unicode(20), nullable=False)
    SpeciesFG_BirdsIce = Column(Unicode(20), nullable=False)
    SpeciesFG_MammalsToothedWhales = Column(Unicode(20), nullable=False)
    SpeciesFG_MammalsBaleenWhales = Column(Unicode(20), nullable=False)
    SpeciesFG_MammalsSeals = Column(Unicode(20), nullable=False)
    SpeciesFG_MammalsIce = Column(Unicode(20), nullable=False)
    SpeciesFG_ReptilesTurtles = Column(Unicode(20), nullable=False)
    SpeciesFG_FishDiadromous = Column(Unicode(20), nullable=False)
    SpeciesFG_FishCoastal = Column(Unicode(20), nullable=False)
    SpeciesFG_FishPelagic = Column(Unicode(20), nullable=False)
    SpeciesFG_FishPelagicElasmobranchs = Column(Unicode(20), nullable=False)
    SpeciesFG_FishDemersal = Column(Unicode(20), nullable=False)
    SpeciesFG_FishDemersalElasmobranchs = Column(Unicode(20), nullable=False)
    SpeciesFG_FishDeep_sea = Column(Unicode(20), nullable=False)
    SpeciesFG_FishDeep_seaElasmobranchs = Column(Unicode(20), nullable=False)
    SpeciesFG_FishIce = Column(Unicode(20), nullable=False)
    SpeciesFG_CephalopodsCoastShelf = Column(Unicode(20), nullable=False)
    SpeciesFG_CephalopodsDeep_sea = Column(Unicode(20), nullable=False)
    SpeciesFG_AnnexII_IV_V_Species = Column(Unicode(20), nullable=False)
    SpeciesFG_WildBirdSpecies = Column(Unicode(20), nullable=False)
    SpeciesFG_FunctionalGroupOther = Column(Unicode(20), nullable=False)
    SpeciesFG_FishCoastal_Description = Column(Unicode)
    SpeciesFG_FishIce_Description = Column(Unicode)
    SpeciesFG_FunctionalGroupOther_Description = Column(Unicode)


class MSFD11Q2aPublicConsultationDate(Base):
    __tablename__ = 'MSFD11_Q2a_PublicConsultationDates'

    ID = Column(Integer, primary_key=True)
    StartDate = Column(DateTime)
    EndDate = Column(DateTime)
    Q2b_PublicConsultationDescription = Column(Unicode)
    GeneralDescription = Column(ForeignKey(u'MSFD11_GeneralDescription.ID'), nullable=False)

    MSFD11_GeneralDescription = relationship(u'MSFD11GeneralDescription')


class MSFD11Q4aResponsibleCompetentAuthority(Base):
    __tablename__ = 'MSFD11_Q4a_ResponsibleCompetentAuthority'

    ID = Column(Integer, primary_key=True)
    Q4a_ResponsibleCompetentAuthority = Column(Unicode)
    GeneralDescription = Column(ForeignKey(u'MSFD11_GeneralDescription.ID'), nullable=False)

    MSFD11_GeneralDescription = relationship(u'MSFD11GeneralDescription')


class MSFD11Q5dAdequacyForAssessmentGE(Base):
    __tablename__ = 'MSFD11_Q5d_AdequacyForAssessmentGES'

    ID = Column(Integer, primary_key=True)
    AdequateData = Column(Unicode(20), nullable=False)
    EstablishedMethods = Column(Unicode(20), nullable=False)
    AdequateUnderstandingGES = Column(Unicode(20), nullable=False)
    AdequateCapacity = Column(Unicode(20), nullable=False)


class MSFD11Q6aAssociatedIndicator(Base):
    __tablename__ = 'MSFD11_Q6a_AssociatedIndicator'

    ID = Column(Integer, primary_key=True)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'), nullable=False)

    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')


class MSFD11Q6aEnvironmentalTarget(Base):
    __tablename__ = 'MSFD11_Q6a_EnvironmentalTarget'

    ID = Column(Integer, primary_key=True)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'), nullable=False)

    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')


class MSFD11Q6aRelevantTarget(Base):
    __tablename__ = 'MSFD11_Q6a_RelevantTarget'

    ID = Column(Integer, primary_key=True)
    RelevantTarget = Column(Unicode(50), nullable=False)
    MonitoringProgramme = Column(ForeignKey(u'MSFD11_MonitoringProgramme.ID'), nullable=False)

    MSFD11_MonitoringProgramme = relationship(u'MSFD11MonitoringProgramme')


class MSFD11Q6bAdequacyForAssessmentTarget(Base):
    __tablename__ = 'MSFD11_Q6b_AdequacyForAssessmentTargets'

    ID = Column(Integer, primary_key=True)
    SuitableData = Column(Unicode(20), nullable=False)
    EstablishedMethods = Column(Unicode(20), nullable=False)
    AdequateCapacity = Column(Unicode(20), nullable=False)


class MSFD11Q7eAdequacyForAssessmentMeasure(Base):
    __tablename__ = 'MSFD11_Q7e_AdequacyForAssessmentMeasures'

    ID = Column(Integer, primary_key=True)
    AdequateData = Column(Unicode(20))
    EstablishedMethods = Column(Unicode(20))
    AdequateUnderstandingGES = Column(Unicode(20))
    AdequateCapacity = Column(Unicode(20))
    AddressesActivitiesPressures = Column(Unicode(20))
    AddressesEffectiveness = Column(Unicode(20))


class MSFD11Q9aElementMonitored(Base):
    __tablename__ = 'MSFD11_Q9a_ElementMonitored'

    ID = Column(Integer, primary_key=True)
    Q9a_ElementMonitored = Column(Unicode, nullable=False)
    SubProgramme = Column(ForeignKey(u'MSFD11_SubProgramme.ID'), nullable=False)

    MSFD11_SubProgramme = relationship(u'MSFD11SubProgramme')


class MSFD11Q9bMeasurementParameter(Base):
    __tablename__ = 'MSFD11_Q9b_MeasurementParameter'

    ID = Column(Integer, primary_key=True)
    mpgroup = Column(Unicode(255), nullable=False)
    mpsubgroup = Column(Unicode(255), nullable=False)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    SubProgramme = Column(ForeignKey(u'MSFD11_SubProgramme.ID'), nullable=False)

    MSFD11_SubProgramme = relationship(u'MSFD11SubProgramme')


class MSFD11ReferenceExistingProgramme(Base):
    __tablename__ = 'MSFD11_ReferenceExistingProgramme'

    ID = Column(Integer, primary_key=True)
    ProgrammeID = Column(Unicode(50), nullable=False)
    ExistingSubProgrammes = Column(Unicode(20), nullable=False)


class MSFD11ReferenceExistingProgrammeMarineUnitID(Base):
    __tablename__ = 'MSFD11_ReferenceExistingProgramme_MarineUnitID'

    ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(ForeignKey(u'MSFD11_MarineUnitID.ID'), nullable=False)
    ReferenceExistingProgramme = Column(ForeignKey(u'MSFD11_ReferenceExistingProgramme.ID'), nullable=False)

    MSFD11_MarineUnitID = relationship(u'MSFD11MarineUnitID')
    MSFD11_ReferenceExistingProgramme = relationship(u'MSFD11ReferenceExistingProgramme')


class MSFD11ReferenceSubProgramme(Base):
    __tablename__ = 'MSFD11_ReferenceSubProgramme'

    ID = Column(Integer, primary_key=True)
    SubMonitoringProgrammeID = Column(Unicode(255), nullable=False)
    SubMonitoringProgrammeName = Column(Unicode(255), nullable=False)
    MP = Column(ForeignKey(u'MSFD11_MP.ID'), nullable=False)

    MSFD11_MP = relationship(u'MSFD11MP')


class MSFD11SubProgramme(Base):
    __tablename__ = 'MSFD11_SubProgramme'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    Q4g_SubProgrammeID = Column(Unicode(42), nullable=False)
    Q4h_TemporalScopeStartDate = Column(Unicode(20), nullable=False)
    Q4h_TemporalScopeEndDate = Column(Unicode(20), nullable=False)
    Q4j_DescriptionSpatialScope = Column(Unicode, nullable=False)
    Q4l_LinksProgrammesDirectivesConventions = Column(Unicode)
    Q9c_MonitoringMethod = Column(Unicode)
    Q9d_DescriptionMethod = Column(Unicode)
    Q9e_Other = Column(Unicode(1000))
    Q9f_Other = Column(Unicode(1000))
    Q9g_SpatialResolutionSampling_Proportion = Column(Unicode(20))
    Q9g_SpatialResolutionSampling_NoSamples = Column(Unicode(1000))
    Q9h_Other = Column(Unicode(1000))
    Q9i_DescriptionSampleRepresentivity = Column(Unicode)
    Q10a_Other = Column(Unicode(1000))
    Q10b_DescriptionDataAggregation = Column(Unicode)
    Q10c_DataType = Column(Unicode, nullable=False)
    Q10c_DataAccessMechanism = Column(Unicode(32), nullable=False)
    Q10c_DataAccessRights = Column(Unicode(20), nullable=False)
    Q10c_INSPIREStandard = Column(Unicode, nullable=False)
    Q10c_DataAvailable = Column(Unicode(20), nullable=False)
    Q10c_Other = Column(Unicode(1000))
    Q10d_DescriptionDataAccess = Column(Unicode, nullable=False)


class MSFD11SubProgrammeIDMatch(Base):
    __tablename__ = 'MSFD11_SubProgrammeID_Match'

    ID = Column(Integer, primary_key=True)
    Q4g_SubProgrammeID = Column(Unicode(50), nullable=False)
    MP_ReferenceSubProgramme = Column(Unicode(50))
    MP_Type = Column(Unicode(50))


class MSFD11SubProgrammeList(Base):
    __tablename__ = 'MSFD11_SubProgramme_List'

    ID = Column(Integer, primary_key=True)
    ElementName = Column(Unicode(255), nullable=False)
    Value = Column(Unicode(255), nullable=False)
    Label = Column(Unicode(1000))
    SubProgramme = Column(ForeignKey(u'MSFD11_SubProgramme.ID'), nullable=False)

    MSFD11_SubProgramme = relationship(u'MSFD11SubProgramme')


class MSFD13ImportedRow(Base):
    __tablename__ = 'MSFD13_ImportedRow'

    ID = Column(Integer, primary_key=True)
    Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    Table = Column(Unicode(100), nullable=False)
    PK = Column(Integer, nullable=False)
    Import = Column(ForeignKey(u'MSFD13_Imports.ID'), nullable=False)

    MSFD13_Import = relationship(u'MSFD13Import')


class MSFD13Import(Base):
    __tablename__ = 'MSFD13_Imports'

    ID = Column(Integer, primary_key=True)
    Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MemberStates = Column(Unicode(20), nullable=False)
    Region = Column(Unicode(20), nullable=False)
    MarineUnitID = Column(Unicode(50), nullable=False)
    FileName = Column(Unicode)
    Description = Column(Unicode)


class MSFD13Measure(Base):
    __tablename__ = 'MSFD13_Measures'

    ID = Column(Integer, primary_key=True)
    ReportID = Column(ForeignKey(u'MSFD13_ReportingInfo.ID'), nullable=False)
    UniqueCode = Column(Unicode(50), nullable=False)
    Name = Column(Unicode)

    MSFD13_ReportingInfo = relationship(u'MSFD13ReportingInfo')


class MSFD13MeasuresInfo(Base):
    __tablename__ = 'MSFD13_MeasuresInfo'

    ID = Column(Integer, primary_key=True)
    ReportID = Column(Integer, nullable=False)
    UniqueCode = Column(Unicode(50), nullable=False)
    MeasureID = Column(ForeignKey(u'MSFD13_Measures.ID'), nullable=False)
    InfoType = Column(Unicode(50))
    InfoText = Column(Unicode)

    MSFD13_Measure = relationship(u'MSFD13Measure')


class MSFD13ReportInfoFurtherInfo(Base):
    __tablename__ = 'MSFD13_ReportInfo_FurtherInfo'

    ID = Column(Integer, primary_key=True)
    ReportID = Column(ForeignKey(u'MSFD13_ReportingInfo.ID'), nullable=False)
    ReportType = Column(Unicode(50))
    URL = Column(String(255, u'Danish_Norwegian_CI_AS'))

    MSFD13_ReportingInfo = relationship(u'MSFD13ReportingInfo')


class MSFD13ReportingInfo(Base):
    __tablename__ = 'MSFD13_ReportingInfo'

    ID = Column(Integer, primary_key=True)
    ObsoleteDate = Column(DateTime)
    MarineUnitID = Column(Unicode(50), nullable=False)
    Region = Column(Unicode(20))
    ReportingDate = Column(Date)
    ReporterName = Column(Unicode(250))
    ReportType = Column(Unicode(20))
    Import = Column(Integer, nullable=False)


class MSFD13ReportingInfoMemberState(Base):
    __tablename__ = 'MSFD13_ReportingInfo_MemberState'

    ID = Column(Integer, primary_key=True)
    ReportID = Column(ForeignKey(u'MSFD13_ReportingInfo.ID'), nullable=False)
    MemberState = Column(Unicode(20), nullable=False)

    MSFD13_ReportingInfo = relationship(u'MSFD13ReportingInfo')


t_MSFD4_GegraphicalAreasID = Table(
    'MSFD4_GegraphicalAreasID', metadata,
    Column('RegionSubRegions', Unicode(255)),
    Column('MemberState', Unicode(255)),
    Column('AreaType', Unicode(255)),
    Column('MarineUnitID', Unicode(42), unique=True),
    Column('MarineUnits_ReportingAreas', Unicode(255)),
    Column('MSFD4_GegraphicalAreasID_Import', ForeignKey(u'MSFD4_Imports.MSFD4_Import_ID'), nullable=False)
)


t_MSFD4_GeograpicalAreasDescription = Table(
    'MSFD4_GeograpicalAreasDescription', metadata,
    Column('MemberState', Unicode),
    Column('RegionSubregion', Unicode),
    Column('Subdivisions', Unicode),
    Column('AssessmentAreas', Unicode),
    Column('MSFD4_GeograpicalAreasDescription_Import', ForeignKey(u'MSFD4_Imports.MSFD4_Import_ID'), nullable=False)
)


class MSFD4Import(Base):
    __tablename__ = 'MSFD4_Imports'

    MSFD4_Import_ID = Column(Integer, primary_key=True)
    MSFD4_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD4_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False, unique=True)
    MSFD4_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')


class MSFD4RegionalCooperation(Base):
    __tablename__ = 'MSFD4_RegionalCooperation'

    RegionsSubRegions = Column(Unicode(50))
    Topic = Column(Unicode(50))
    NatureCoordination = Column(Unicode)
    RegionalCoherence = Column(Unicode(255))
    RegionalCoordinationProblems = Column(Unicode)
    MSFD4_RegionalCooperation_Import = Column(ForeignKey(u'MSFD4_Imports.MSFD4_Import_ID'), nullable=False)
    MSFD4_RegionalCooperation_ID = Column(Integer, primary_key=True)

    MSFD4_Import = relationship(u'MSFD4Import')


class MSFD4RegionalCooperationM(Base):
    __tablename__ = 'MSFD4_RegionalCooperationMS'

    RegionsSubRegions = Column(Unicode(255))
    Article = Column(Unicode(255))
    Countries = Column(Unicode(255))
    MSFD4_RegionalCooperationMS_ID = Column(Integer, primary_key=True)
    MSFD4_RegionalCooperation = Column(ForeignKey(u'MSFD4_RegionalCooperation.MSFD4_RegionalCooperation_ID'), nullable=False)

    MSFD4_RegionalCooperation1 = relationship(u'MSFD4RegionalCooperation')


t_MSFD4_ReportingInformation = Table(
    'MSFD4_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD4_ReportingInformation_Import', ForeignKey(u'MSFD4_Imports.MSFD4_Import_ID'), nullable=False)
)


class MSFD8aEcosystem(Base):
    __tablename__ = 'MSFD8a_Ecosystem'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    Summary1 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Ecosystem_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Ecosystem_ID = Column(Integer, primary_key=True)
    PredominantFeature = Column(Unicode(255))

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_EcosystemFeatures = Table(
    'MSFD8a_EcosystemFeatures', metadata,
    Column('MarineUnitID', Unicode(255), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('FunctionalGroupHabitats', Unicode(255)),
    Column('Other', Unicode(255)),
    Column('MSFD8a_EcosystemFeatures', ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)
)


t_MSFD8a_EcosystemMetadata = Table(
    'MSFD8a_EcosystemMetadata', metadata,
    Column('MarineUnitID', Unicode(255), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Ecosystem_ID', ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)
)


class MSFD8aEcosystemFuturePressure(Base):
    __tablename__ = 'MSFD8a_Ecosystem_FuturePressures'

    MSFD8a_Ecosystem_FuturePressures_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Ecosystem = Column(ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)

    MSFD8a_Ecosystem1 = relationship(u'MSFD8aEcosystem')


class MSFD8aEcosystemPressuresImpact(Base):
    __tablename__ = 'MSFD8a_Ecosystem_PressuresImpacts'

    MSFD8a_Ecosystem_PressuresImpacts_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    PredominantFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Ecosystem = Column(ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)

    MSFD8a_Ecosystem1 = relationship(u'MSFD8aEcosystem')


class MSFD8aEcosystemStatusAssessment(Base):
    __tablename__ = 'MSFD8a_Ecosystem_StatusAssessment'

    MSFD8a_Ecosystem_StatusAssessment_ID = Column(Integer, primary_key=True)
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    TrendStatus = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Ecosystem = Column(ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)

    MSFD8a_Ecosystem1 = relationship(u'MSFD8aEcosystem')


class MSFD8aEcosystemStatusCriterion(Base):
    __tablename__ = 'MSFD8a_Ecosystem_StatusCriteria'

    MSFD8a_Ecosystem_StatusCriteria_ID = Column(Integer, primary_key=True)
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(250))
    MSFD8a_Ecosystem_StatusAssessment = Column(ForeignKey(u'MSFD8a_Ecosystem_StatusAssessment.MSFD8a_Ecosystem_StatusAssessment_ID'), nullable=False)

    MSFD8a_Ecosystem_StatusAssessment1 = relationship(u'MSFD8aEcosystemStatusAssessment')


class MSFD8aEcosystemStatusIndicator(Base):
    __tablename__ = 'MSFD8a_Ecosystem_StatusIndicator'

    MSFD8a_Ecosystem_StatusIndicator_ID = Column(Integer, primary_key=True)
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(250))
    ThresholdValueUnit = Column(Unicode(100))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8a_Ecosystem_StatusAssessment = Column(ForeignKey(u'MSFD8a_Ecosystem_StatusAssessment.MSFD8a_Ecosystem_StatusAssessment_ID'), nullable=False)

    MSFD8a_Ecosystem_StatusAssessment1 = relationship(u'MSFD8aEcosystemStatusAssessment')


class MSFD8aEcosystemSummary2(Base):
    __tablename__ = 'MSFD8a_Ecosystem_Summary2'

    MarineUnitID = Column(Unicode(255), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    Topic = Column(Unicode(255))
    Summary2 = Column(Unicode(255))
    Other = Column(Unicode(255))
    MSFD8a_Ecosystem_Summary2_ID = Column(Integer, primary_key=True)
    MSFD8a_Ecosystem = Column(ForeignKey(u'MSFD8a_Ecosystem.MSFD8a_Ecosystem_ID'), nullable=False)

    MSFD8a_Ecosystem1 = relationship(u'MSFD8aEcosystem')


class MSFD8aFunctional(Base):
    __tablename__ = 'MSFD8a_Functional'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    Summary1 = Column(Unicode(255))
    Summary2 = Column(Unicode(255))
    Sum2Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Functional_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Functional_ID = Column(Integer, primary_key=True)
    PredominantFeature = Column(Unicode(255))

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_FunctionalFeature = Table(
    'MSFD8a_FunctionalFeature', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('FunctionalGroupHabitatsSpecies', Unicode(255)),
    Column('Other', Unicode),
    Column('MSFD8a_FunctionalFeature', ForeignKey(u'MSFD8a_Functional.MSFD8a_Functional_ID'), nullable=False)
)


t_MSFD8a_FunctionalMetadata = Table(
    'MSFD8a_FunctionalMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Functional_ID', ForeignKey(u'MSFD8a_Functional.MSFD8a_Functional_ID'), nullable=False)
)


class MSFD8aFunctionalFuturePressure(Base):
    __tablename__ = 'MSFD8a_Functional_FuturePressures'

    MSFD8a_Functional_FuturePressures_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Functional = Column(ForeignKey(u'MSFD8a_Functional.MSFD8a_Functional_ID'), nullable=False)

    MSFD8a_Functional1 = relationship(u'MSFD8aFunctional')


class MSFD8aFunctionalPressuresImpact(Base):
    __tablename__ = 'MSFD8a_Functional_PressuresImpacts'

    MSFD8a_Functional_PressuresImpacts_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    PredominantFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Functional = Column(ForeignKey(u'MSFD8a_Functional.MSFD8a_Functional_ID'), nullable=False)

    MSFD8a_Functional1 = relationship(u'MSFD8aFunctional')


class MSFD8aFunctionalStatusAssessment(Base):
    __tablename__ = 'MSFD8a_Functional_StatusAssessment'

    MSFD8a_Functional_StatusAssessment_ID = Column(Integer, primary_key=True)
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    TrendStatus = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Functional = Column(ForeignKey(u'MSFD8a_Functional.MSFD8a_Functional_ID'), nullable=False)

    MSFD8a_Functional1 = relationship(u'MSFD8aFunctional')


class MSFD8aFunctionalStatusCriterion(Base):
    __tablename__ = 'MSFD8a_Functional_StatusCriteria'

    MSFD8a_Functional_StatusCriteria_ID = Column(Integer, primary_key=True)
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(250))
    MSFD8a_Functional_StatusAssessment = Column(ForeignKey(u'MSFD8a_Functional_StatusAssessment.MSFD8a_Functional_StatusAssessment_ID'), nullable=False)

    MSFD8a_Functional_StatusAssessment1 = relationship(u'MSFD8aFunctionalStatusAssessment')


class MSFD8aFunctionalStatusIndicator(Base):
    __tablename__ = 'MSFD8a_Functional_StatusIndicator'

    MSFD8a_Functional_StatusIndicator_ID = Column(Integer, primary_key=True)
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode)
    ThresholdValue = Column(Unicode(250))
    ThresholdValueUnit = Column(Unicode(100))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8a_Functional_StatusAssessment = Column(ForeignKey(u'MSFD8a_Functional_StatusAssessment.MSFD8a_Functional_StatusAssessment_ID'), nullable=False)

    MSFD8a_Functional_StatusAssessment1 = relationship(u'MSFD8aFunctionalStatusAssessment')


class MSFD8aHabitat(Base):
    __tablename__ = 'MSFD8a_Habitat'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    SourceClassificationListAuthority = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    Summary1 = Column(Unicode(255))
    Sum1Confidence = Column(Unicode(255))
    Summary2 = Column(Unicode(255))
    Sum2Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Habitat_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Habitat_ID = Column(Integer, primary_key=True)
    PredominantFeature = Column(Unicode(255))

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_HabitatFeature = Table(
    'MSFD8a_HabitatFeature', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('PredominantHabitats', Unicode(255)),
    Column('MSFD8a_HabitatFeature', ForeignKey(u'MSFD8a_Habitat.MSFD8a_Habitat_ID'), nullable=False)
)


t_MSFD8a_HabitatMetadata = Table(
    'MSFD8a_HabitatMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Habitat_ID', ForeignKey(u'MSFD8a_Habitat.MSFD8a_Habitat_ID'), nullable=False)
)


class MSFD8aHabitatFuturePressure(Base):
    __tablename__ = 'MSFD8a_Habitat_FuturePressures'

    MSFD8a_Habitat_FuturePressures_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Habitat = Column(ForeignKey(u'MSFD8a_Habitat.MSFD8a_Habitat_ID'), nullable=False)

    MSFD8a_Habitat1 = relationship(u'MSFD8aHabitat')


class MSFD8aHabitatPressuresImpact(Base):
    __tablename__ = 'MSFD8a_Habitat_PressuresImpacts'

    MSFD8a_Habitat_PressuresImpacts_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    PredominantFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Habitat = Column(ForeignKey(u'MSFD8a_Habitat.MSFD8a_Habitat_ID'), nullable=False)

    MSFD8a_Habitat1 = relationship(u'MSFD8aHabitat')


class MSFD8aHabitatStatusAssessment(Base):
    __tablename__ = 'MSFD8a_Habitat_StatusAssessment'

    MSFD8a_Habitat_StatusAssessment_ID = Column(Integer, primary_key=True)
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    TrendStatus = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Habitat = Column(ForeignKey(u'MSFD8a_Habitat.MSFD8a_Habitat_ID'), nullable=False)

    MSFD8a_Habitat1 = relationship(u'MSFD8aHabitat')


class MSFD8aHabitatStatusCriterion(Base):
    __tablename__ = 'MSFD8a_Habitat_StatusCriteria'

    MSFD8a_Habitat_StatusCriteria_ID = Column(Integer, primary_key=True)
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode)
    MSFD8a_Habitat_StatusAssessment = Column(ForeignKey(u'MSFD8a_Habitat_StatusAssessment.MSFD8a_Habitat_StatusAssessment_ID'), nullable=False)

    MSFD8a_Habitat_StatusAssessment1 = relationship(u'MSFD8aHabitatStatusAssessment')


class MSFD8aHabitatStatusIndicator(Base):
    __tablename__ = 'MSFD8a_Habitat_StatusIndicator'

    MSFD8a_Habitat_StatusIndicator_ID = Column(Integer, primary_key=True)
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode)
    ThresholdValue = Column(Unicode(250))
    ThresholdValueUnit = Column(Unicode(100))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8a_Habitat_StatusAssessment = Column(ForeignKey(u'MSFD8a_Habitat_StatusAssessment.MSFD8a_Habitat_StatusAssessment_ID'), nullable=False)

    MSFD8a_Habitat_StatusAssessment1 = relationship(u'MSFD8aHabitatStatusAssessment')


class MSFD8aImport(Base):
    __tablename__ = 'MSFD8a_Imports'
    __table_args__ = (
        Index('MSFD8a_Imports_UNIQUE_CountryRegion', 'MSFD8a_Import_ReportingCountry', 'MSFD8a_Import_ReportingRegion', unique=True),
    )

    MSFD8a_Import_ID = Column(Integer, primary_key=True)
    MSFD8a_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD8a_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFD8a_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFD8a_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


class MSFD8aNISInventory(Base):
    __tablename__ = 'MSFD8a_NISInventory'

    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    ScientificName = Column(Unicode(255))
    Habitat_FunctionalGroup = Column(Unicode(255))
    InvasiveSpecies = Column(Unicode(255))
    Abundance = Column(Unicode(250))
    AbundanceUnit = Column(Unicode(250))
    AreaofOrigin = Column(Unicode)
    MeansofArrival = Column(Unicode(255))
    DateFirstRecorded = Column(Unicode(255))
    SpatialDistribution1 = Column(Unicode(255))
    TemporalOccurrenceStart = Column(Unicode(255))
    TemporalOccurrenceEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_NISInventory_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_NISInventory_ID = Column(Integer, primary_key=True)

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_NISInventoryMetadata = Table(
    'MSFD8a_NISInventoryMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_NISInventory_ID', ForeignKey(u'MSFD8a_NISInventory.MSFD8a_NISInventory_ID'), nullable=False)
)


class MSFD8aOther(Base):
    __tablename__ = 'MSFD8a_Other'

    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    Summary1 = Column(Unicode)
    Sum1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Other_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Other_ID = Column(Integer, primary_key=True)
    PredominantFeature = Column(Unicode(255))

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_OtherMetadata = Table(
    'MSFD8a_OtherMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(250), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Other_ID', ForeignKey(u'MSFD8a_Other.MSFD8a_Other_ID'), nullable=False)
)


class MSFD8aOtherStatusAssessment(Base):
    __tablename__ = 'MSFD8a_Other_StatusAssessment'

    MSFD8a_Other_StatusAssessment_ID = Column(Integer, primary_key=True)
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    TrendStatus = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Other = Column(ForeignKey(u'MSFD8a_Other.MSFD8a_Other_ID'), nullable=False)

    MSFD8a_Other1 = relationship(u'MSFD8aOther')


class MSFD8aOtherStatusCriterion(Base):
    __tablename__ = 'MSFD8a_Other_StatusCriteria'

    MSFD8a_Other_StatusCriteria_ID = Column(Integer, primary_key=True)
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(250))
    MSFD8a_Other_StatusAssessment = Column(ForeignKey(u'MSFD8a_Other_StatusAssessment.MSFD8a_Other_StatusAssessment_ID'), nullable=False)

    MSFD8a_Other_StatusAssessment1 = relationship(u'MSFD8aOtherStatusAssessment')


class MSFD8aOtherStatusIndicator(Base):
    __tablename__ = 'MSFD8a_Other_StatusIndicator'

    MSFD8a_Other_StatusIndicator_ID = Column(Integer, primary_key=True)
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(250))
    ThresholdValueUnit = Column(Unicode(100))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8a_Other_StatusAssessment = Column(ForeignKey(u'MSFD8a_Other_StatusAssessment.MSFD8a_Other_StatusAssessment_ID'), nullable=False)

    MSFD8a_Other_StatusAssessment1 = relationship(u'MSFD8aOtherStatusAssessment')


class MSFD8aPhysical(Base):
    __tablename__ = 'MSFD8a_Physical'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255), index=True)
    Description = Column(Unicode)
    Summary1 = Column(Unicode(255))
    Sum1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Physical_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Physical_ID = Column(Integer, primary_key=True)

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_PhysicalMetadata = Table(
    'MSFD8a_PhysicalMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255), index=True),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Physical_ID', ForeignKey(u'MSFD8a_Physical.MSFD8a_Physical_ID'), nullable=False)
)


t_MSFD8a_ReportingInformation = Table(
    'MSFD8a_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD8a_ReportingInformation_Import', ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
)


class MSFD8aSpecy(Base):
    __tablename__ = 'MSFD8a_Species'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    SourceClassificationListAuthority = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    Summary1 = Column(Unicode(255))
    Sum1Confidence = Column(Unicode(255))
    Summary2 = Column(Unicode(255))
    Sum2Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Species_Import = Column(ForeignKey(u'MSFD8a_Imports.MSFD8a_Import_ID'), nullable=False)
    MSFD8a_Species_ID = Column(Integer, primary_key=True)
    PredominantFeature = Column(Unicode(255))

    MSFD8a_Import = relationship(u'MSFD8aImport')


t_MSFD8a_SpeciesMetadata = Table(
    'MSFD8a_SpeciesMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255), index=True),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8a_Species_ID', ForeignKey(u'MSFD8a_Species.MSFD8a_Species_ID'), nullable=False)
)


class MSFD8aSpeciesFuturePressure(Base):
    __tablename__ = 'MSFD8a_Species_FuturePressures'

    MSFD8a_Species_FuturePressures_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Species = Column(ForeignKey(u'MSFD8a_Species.MSFD8a_Species_ID'), nullable=False)

    MSFD8a_Specy = relationship(u'MSFD8aSpecy')


class MSFD8aSpeciesPressuresImpact(Base):
    __tablename__ = 'MSFD8a_Species_PressuresImpacts'

    MSFD8a_Species_PressuresImpacts_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    PredominantFeature = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Pressure1Rank = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Pressure2Rank = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Pressure3Rank = Column(Unicode(255))
    Impact1 = Column(Unicode(255))
    Impact2 = Column(Unicode(255))
    Impact3 = Column(Unicode(255))
    Impact4 = Column(Unicode(255))
    Impact5 = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Species = Column(ForeignKey(u'MSFD8a_Species.MSFD8a_Species_ID'), nullable=False)

    MSFD8a_Specy = relationship(u'MSFD8aSpecy')


class MSFD8aSpeciesStatusAssessment(Base):
    __tablename__ = 'MSFD8a_Species_StatusAssessment'

    MSFD8a_Species_StatusAssessment_ID = Column(Integer, primary_key=True)
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    TrendStatus = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8a_Species = Column(ForeignKey(u'MSFD8a_Species.MSFD8a_Species_ID'), nullable=False)

    MSFD8a_Specy = relationship(u'MSFD8aSpecy')


class MSFD8aSpeciesStatusCriterion(Base):
    __tablename__ = 'MSFD8a_Species_StatusCriteria'

    MSFD8a_Species_StatusCriteria_ID = Column(Integer, primary_key=True)
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(250))
    MSFD8a_Species_StatusAssessment = Column(ForeignKey(u'MSFD8a_Species_StatusAssessment.MSFD8a_Species_StatusAssessment_ID'), nullable=False)

    MSFD8a_Species_StatusAssessment1 = relationship(u'MSFD8aSpeciesStatusAssessment')


class MSFD8aSpeciesStatusIndicator(Base):
    __tablename__ = 'MSFD8a_Species_StatusIndicator'

    MSFD8a_Species_StatusIndicator_ID = Column(Integer, primary_key=True)
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(250))
    ThresholdValueUnit = Column(Unicode(100))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8a_Species_StatusAssessment = Column(ForeignKey(u'MSFD8a_Species_StatusAssessment.MSFD8a_Species_StatusAssessment_ID'), nullable=False)

    MSFD8a_Species_StatusAssessment1 = relationship(u'MSFD8aSpeciesStatusAssessment')


class MSFD8bAcidification(Base):
    __tablename__ = 'MSFD8b_Acidification'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Acidification_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_Acidification_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_AcidificationMetadata = Table(
    'MSFD8b_AcidificationMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_Acidification_ID', ForeignKey(u'MSFD8b_Acidification.MSFD8b_Acidification_ID'), nullable=False)
)


class MSFD8bAcidificationActivity(Base):
    __tablename__ = 'MSFD8b_Acidification_Activity'

    MSFD8b_Acidification_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_Acidification_ActivityDescription = Column(ForeignKey(u'MSFD8b_Acidification_ActivityDescription.MSFD8b_Acidification_ActivityDescription_ID'), nullable=False)

    MSFD8b_Acidification_ActivityDescription1 = relationship(u'MSFD8bAcidificationActivityDescription')


class MSFD8bAcidificationActivityDescription(Base):
    __tablename__ = 'MSFD8b_Acidification_ActivityDescription'

    MSFD8b_Acidification_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_Acidification = Column(ForeignKey(u'MSFD8b_Acidification.MSFD8b_Acidification_ID'), nullable=False)

    MSFD8b_Acidification1 = relationship(u'MSFD8bAcidification')


class MSFD8bAcidificationSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_Acidification_SumInfo2_ImpactedElements'

    MSFD8b_Acidification_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_Acidification = Column(ForeignKey(u'MSFD8b_Acidification.MSFD8b_Acidification_ID'), nullable=False)

    MSFD8b_Acidification1 = relationship(u'MSFD8bAcidification')


class MSFD8bExtractionFishShellfish(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    SumInfo2 = Column(Unicode(100))
    SumInfo3 = Column(Unicode(255))
    SumInfo4 = Column(Unicode(255))
    SumInfo5 = Column(Unicode(255))
    MSFD8b_ExtractionFishShellfish_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_ExtractionFishShellfish_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_ExtractionFishShellfishMetadata = Table(
    'MSFD8b_ExtractionFishShellfishMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_ExtractionFishShellfish_ID', ForeignKey(u'MSFD8b_ExtractionFishShellfish.MSFD8b_ExtractionFishShellfish_ID'), nullable=False)
)


class MSFD8bExtractionFishShellfishActivity(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_Activity'

    MSFD8b_ExtractionFishShellfish_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_ExtractionFishShellfish_ActivityDescription = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish_ActivityDescription.MSFD8b_ExtractionFishShellfish_ActivityDescription_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish_ActivityDescription1 = relationship(u'MSFD8bExtractionFishShellfishActivityDescription')


class MSFD8bExtractionFishShellfishActivityDescription(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_ActivityDescription'

    MSFD8b_ExtractionFishShellfish_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_ExtractionFishShellfish = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish.MSFD8b_ExtractionFishShellfish_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish1 = relationship(u'MSFD8bExtractionFishShellfish')


class MSFD8bExtractionFishShellfishAssesment(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_Assesment'

    MSFD8b_ExtractionFishShellfish_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_ExtractionFishShellfish = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish.MSFD8b_ExtractionFishShellfish_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish1 = relationship(u'MSFD8bExtractionFishShellfish')


class MSFD8bExtractionFishShellfishAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_AssesmentCriteria'

    MSFD8b_ExtractionFishShellfish_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_ExtractionFishShellfish_Assesment = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish_Assesment.MSFD8b_ExtractionFishShellfish_Assesment_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish_Assesment1 = relationship(u'MSFD8bExtractionFishShellfishAssesment')


class MSFD8bExtractionFishShellfishAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_AssesmentIndicator'

    MSFD8b_ExtractionFishShellfish_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_ExtractionFishShellfish_Assesment = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish_Assesment.MSFD8b_ExtractionFishShellfish_Assesment_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish_Assesment1 = relationship(u'MSFD8bExtractionFishShellfishAssesment')


class MSFD8bExtractionFishShellfishSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_ExtractionFishShellfish_SumInfo2_ImpactedElements'

    MSFD8b_ExtractionFishShellfish_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode)
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode)
    SpeciesStockAssessment = Column(Unicode(255))
    SpeciesImpacted = Column(Unicode(255))
    MSFD8b_ExtractionFishShellfish = Column(ForeignKey(u'MSFD8b_ExtractionFishShellfish.MSFD8b_ExtractionFishShellfish_ID'), nullable=False)

    MSFD8b_ExtractionFishShellfish1 = relationship(u'MSFD8bExtractionFishShellfish')


class MSFD8bExtractionSeaweedMaerlOther(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_ExtractionSeaweedMaerlOther_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_ExtractionSeaweedMaerlOther_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_ExtractionSeaweedMaerlOtherMetadata = Table(
    'MSFD8b_ExtractionSeaweedMaerlOtherMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ExtractionType', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_ExtractionSeaweedMaerlOther_ID', ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther.MSFD8b_ExtractionSeaweedMaerlOther_ID'), nullable=False)
)


class MSFD8bExtractionSeaweedMaerlOtherActivity(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_Activity'

    MSFD8b_ExtractionSeaweedMaerlOther_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription.MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription1 = relationship(u'MSFD8bExtractionSeaweedMaerlOtherActivityDescription')


class MSFD8bExtractionSeaweedMaerlOtherActivityDescription(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription'

    MSFD8b_ExtractionSeaweedMaerlOther_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ExtractionType = Column(Unicode(255))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_ExtractionSeaweedMaerlOther = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther.MSFD8b_ExtractionSeaweedMaerlOther_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther1 = relationship(u'MSFD8bExtractionSeaweedMaerlOther')


class MSFD8bExtractionSeaweedMaerlOtherAssesment(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_Assesment'

    MSFD8b_ExtractionSeaweedMaerlOther_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_ExtractionSeaweedMaerlOther = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther.MSFD8b_ExtractionSeaweedMaerlOther_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther1 = relationship(u'MSFD8bExtractionSeaweedMaerlOther')


class MSFD8bExtractionSeaweedMaerlOtherAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_AssesmentCriteria'

    MSFD8b_ExtractionSeaweedMaerlOther_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_ExtractionSeaweedMaerlOther_Assesment = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther_Assesment.MSFD8b_ExtractionSeaweedMaerlOther_Assesment_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther_Assesment1 = relationship(u'MSFD8bExtractionSeaweedMaerlOtherAssesment')


class MSFD8bExtractionSeaweedMaerlOtherAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_AssesmentIndicator'

    MSFD8b_ExtractionSeaweedMaerlOther_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode(255))
    MSFD8b_ExtractionSeaweedMaerlOther_Assesment = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther_Assesment.MSFD8b_ExtractionSeaweedMaerlOther_Assesment_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther_Assesment1 = relationship(u'MSFD8bExtractionSeaweedMaerlOtherAssesment')


class MSFD8bExtractionSeaweedMaerlOtherSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_ExtractionSeaweedMaerlOther_SumInfo2_ImpactedElements'

    MSFD8b_ExtractionSeaweedMaerlOther_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    SpeciesStockAssessment = Column(Unicode(255))
    SpeciesImpacted = Column(Unicode(255))
    MSFD8b_ExtractionSeaweedMaerlOther = Column(ForeignKey(u'MSFD8b_ExtractionSeaweedMaerlOther.MSFD8b_ExtractionSeaweedMaerlOther_ID'), nullable=False)

    MSFD8b_ExtractionSeaweedMaerlOther1 = relationship(u'MSFD8bExtractionSeaweedMaerlOther')


class MSFD8bHazardousSubstance(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_HazardousSubstances_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_HazardousSubstances_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_HazardousSubstancesMetadata = Table(
    'MSFD8b_HazardousSubstancesMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('HazardousSubstancesGroup', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_HazardousSubstances_ID', ForeignKey(u'MSFD8b_HazardousSubstances.MSFD8b_HazardousSubstances_ID'), nullable=False)
)


class MSFD8bHazardousSubstancesActivity(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_Activity'

    MSFD8b_HazardousSubstances_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_HazardousSubstances_ActivityDescription = Column(ForeignKey(u'MSFD8b_HazardousSubstances_ActivityDescription.MSFD8b_HazardousSubstances_ActivityDescription_ID'), nullable=False)

    MSFD8b_HazardousSubstances_ActivityDescription1 = relationship(u'MSFD8bHazardousSubstancesActivityDescription')


class MSFD8bHazardousSubstancesActivityDescription(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_ActivityDescription'

    MSFD8b_HazardousSubstances_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    HazardousSubstancesGroup = Column(Unicode(255))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_HazardousSubstances = Column(ForeignKey(u'MSFD8b_HazardousSubstances.MSFD8b_HazardousSubstances_ID'), nullable=False)

    MSFD8b_HazardousSubstance = relationship(u'MSFD8bHazardousSubstance')


class MSFD8bHazardousSubstancesAssesment(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_Assesment'

    MSFD8b_HazardousSubstances_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_HazardousSubstances = Column(ForeignKey(u'MSFD8b_HazardousSubstances.MSFD8b_HazardousSubstances_ID'), nullable=False)

    MSFD8b_HazardousSubstance = relationship(u'MSFD8bHazardousSubstance')


class MSFD8bHazardousSubstancesAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_AssesmentCriteria'

    MSFD8b_HazardousSubstances_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_HazardousSubstances_Assesment = Column(ForeignKey(u'MSFD8b_HazardousSubstances_Assesment.MSFD8b_HazardousSubstances_Assesment_ID'), nullable=False)

    MSFD8b_HazardousSubstances_Assesment1 = relationship(u'MSFD8bHazardousSubstancesAssesment')


class MSFD8bHazardousSubstancesAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_AssesmentIndicator'

    MSFD8b_HazardousSubstances_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode)
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_HazardousSubstances_Assesment = Column(ForeignKey(u'MSFD8b_HazardousSubstances_Assesment.MSFD8b_HazardousSubstances_Assesment_ID'), nullable=False)

    MSFD8b_HazardousSubstances_Assesment1 = relationship(u'MSFD8bHazardousSubstancesAssesment')


class MSFD8bHazardousSubstancesSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_HazardousSubstances_SumInfo2_ImpactedElements'

    MSFD8b_HazardousSubstances_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ReportingFeature = Column(Unicode(255))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    SpeciesStockAssessment = Column(Unicode(255))
    SpeciesImpacted = Column(Unicode(255))
    CASNumber = Column(Unicode)
    MSFD8b_HazardousSubstances = Column(ForeignKey(u'MSFD8b_HazardousSubstances.MSFD8b_HazardousSubstances_ID'), nullable=False)

    MSFD8b_HazardousSubstance = relationship(u'MSFD8bHazardousSubstance')


class MSFD8bHydrologicalProcess(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_HydrologicalProcesses_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_HydrologicalProcesses_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_HydrologicalProcessesMetadata = Table(
    'MSFD8b_HydrologicalProcessesMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_HydrologicalProcesses_ID', ForeignKey(u'MSFD8b_HydrologicalProcesses.MSFD8b_HydrologicalProcesses_ID'), nullable=False)
)


class MSFD8bHydrologicalProcessesActivity(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_Activity'

    MSFD8b_HydrologicalProcesses_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_HydrologicalProcesses_ActivityDescription = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses_ActivityDescription.MSFD8b_HydrologicalProcesses_ActivityDescription_ID'), nullable=False)

    MSFD8b_HydrologicalProcesses_ActivityDescription1 = relationship(u'MSFD8bHydrologicalProcessesActivityDescription')


class MSFD8bHydrologicalProcessesActivityDescription(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_ActivityDescription'

    MSFD8b_HydrologicalProcesses_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_HydrologicalProcesses = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses.MSFD8b_HydrologicalProcesses_ID'), nullable=False)

    MSFD8b_HydrologicalProcess = relationship(u'MSFD8bHydrologicalProcess')


class MSFD8bHydrologicalProcessesAssesment(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_Assesment'

    MSFD8b_HydrologicalProcesses_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_HydrologicalProcesses = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses.MSFD8b_HydrologicalProcesses_ID'), nullable=False)

    MSFD8b_HydrologicalProcess = relationship(u'MSFD8bHydrologicalProcess')


class MSFD8bHydrologicalProcessesAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_AssesmentCriteria'

    MSFD8b_HydrologicalProcesses_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_HydrologicalProcesses_Assesment = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses_Assesment.MSFD8b_HydrologicalProcesses_Assesment_ID'), nullable=False)

    MSFD8b_HydrologicalProcesses_Assesment1 = relationship(u'MSFD8bHydrologicalProcessesAssesment')


class MSFD8bHydrologicalProcessesAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_AssesmentIndicator'

    MSFD8b_HydrologicalProcesses_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode(255))
    MSFD8b_HydrologicalProcesses_Assesment = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses_Assesment.MSFD8b_HydrologicalProcesses_Assesment_ID'), nullable=False)

    MSFD8b_HydrologicalProcesses_Assesment1 = relationship(u'MSFD8bHydrologicalProcessesAssesment')


class MSFD8bHydrologicalProcessesSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_HydrologicalProcesses_SumInfo2_ImpactedElements'

    MSFD8b_HydrologicalProcesses_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_HydrologicalProcesses = Column(ForeignKey(u'MSFD8b_HydrologicalProcesses.MSFD8b_HydrologicalProcesses_ID'), nullable=False)

    MSFD8b_HydrologicalProcess = relationship(u'MSFD8bHydrologicalProcess')


class MSFD8bImport(Base):
    __tablename__ = 'MSFD8b_Imports'
    __table_args__ = (
        Index('MSFD8b_Imports_UNIQUE_CountryRegion', 'MSFD8b_Import_ReportingCountry', 'MSFD8b_Import_ReportingRegion', unique=True),
    )

    MSFD8b_Import_ID = Column(Integer, primary_key=True)
    MSFD8b_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD8b_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFD8b_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFD8b_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


class MSFD8bLitter(Base):
    __tablename__ = 'MSFD8b_Litter'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Litter_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_Litter_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_LitterMetadata = Table(
    'MSFD8b_LitterMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_Litter_ID', ForeignKey(u'MSFD8b_Litter.MSFD8b_Litter_ID'), nullable=False)
)


class MSFD8bLitterActivity(Base):
    __tablename__ = 'MSFD8b_Litter_Activity'

    MSFD8b_Litter_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_Litter_ActivityDescription = Column(ForeignKey(u'MSFD8b_Litter_ActivityDescription.MSFD8b_Litter_ActivityDescription_ID'), nullable=False)

    MSFD8b_Litter_ActivityDescription1 = relationship(u'MSFD8bLitterActivityDescription')


class MSFD8bLitterActivityDescription(Base):
    __tablename__ = 'MSFD8b_Litter_ActivityDescription'

    MSFD8b_Litter_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_Litter = Column(ForeignKey(u'MSFD8b_Litter.MSFD8b_Litter_ID'), nullable=False)

    MSFD8b_Litter1 = relationship(u'MSFD8bLitter')


class MSFD8bLitterAssesment(Base):
    __tablename__ = 'MSFD8b_Litter_Assesment'

    MSFD8b_Litter_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Litter = Column(ForeignKey(u'MSFD8b_Litter.MSFD8b_Litter_ID'), nullable=False)

    MSFD8b_Litter1 = relationship(u'MSFD8bLitter')


class MSFD8bLitterAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_Litter_AssesmentCriteria'

    MSFD8b_Litter_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_Litter_Assesment = Column(ForeignKey(u'MSFD8b_Litter_Assesment.MSFD8b_Litter_Assesment_ID'), nullable=False)

    MSFD8b_Litter_Assesment1 = relationship(u'MSFD8bLitterAssesment')


class MSFD8bLitterAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_Litter_AssesmentIndicator'

    MSFD8b_Litter_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_Litter_Assesment = Column(ForeignKey(u'MSFD8b_Litter_Assesment.MSFD8b_Litter_Assesment_ID'), nullable=False)

    MSFD8b_Litter_Assesment1 = relationship(u'MSFD8bLitterAssesment')


class MSFD8bLitterSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_Litter_SumInfo2_ImpactedElements'

    MSFD8b_Litter_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_Litter = Column(ForeignKey(u'MSFD8b_Litter.MSFD8b_Litter_ID'), nullable=False)

    MSFD8b_Litter1 = relationship(u'MSFD8bLitter')


class MSFD8bMicrobialPathogen(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_MicrobialPathogens_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_MicrobialPathogens_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_MicrobialPathogensMetadata = Table(
    'MSFD8b_MicrobialPathogensMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_MicrobialPathogens_ID', ForeignKey(u'MSFD8b_MicrobialPathogens.MSFD8b_MicrobialPathogens_ID'), nullable=False)
)


class MSFD8bMicrobialPathogensActivity(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens_Activity'

    MSFD8b_MicrobialPathogens_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_MicrobialPathogens_ActivityDescription = Column(ForeignKey(u'MSFD8b_MicrobialPathogens_ActivityDescription.MSFD8b_MicrobialPathogens_ActivityDescription_ID'), nullable=False)

    MSFD8b_MicrobialPathogens_ActivityDescription1 = relationship(u'MSFD8bMicrobialPathogensActivityDescription')


class MSFD8bMicrobialPathogensActivityDescription(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens_ActivityDescription'

    MSFD8b_MicrobialPathogens_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_MicrobialPathogens = Column(ForeignKey(u'MSFD8b_MicrobialPathogens.MSFD8b_MicrobialPathogens_ID'), nullable=False)

    MSFD8b_MicrobialPathogen = relationship(u'MSFD8bMicrobialPathogen')


class MSFD8bMicrobialPathogensAssesment(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens_Assesment'

    MSFD8b_MicrobialPathogens_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_MicrobialPathogens = Column(ForeignKey(u'MSFD8b_MicrobialPathogens.MSFD8b_MicrobialPathogens_ID'), nullable=False)

    MSFD8b_MicrobialPathogen = relationship(u'MSFD8bMicrobialPathogen')


class MSFD8bMicrobialPathogensAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens_AssesmentCriteria'

    MSFD8b_MicrobialPathogens_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_MicrobialPathogens_Assesment = Column(ForeignKey(u'MSFD8b_MicrobialPathogens_Assesment.MSFD8b_MicrobialPathogens_Assesment_ID'), nullable=False)

    MSFD8b_MicrobialPathogens_Assesment1 = relationship(u'MSFD8bMicrobialPathogensAssesment')


class MSFD8bMicrobialPathogensAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_MicrobialPathogens_AssesmentIndicator'

    MSFD8b_MicrobialPathogens_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_MicrobialPathogens_Assesment = Column(ForeignKey(u'MSFD8b_MicrobialPathogens_Assesment.MSFD8b_MicrobialPathogens_Assesment_ID'), nullable=False)

    MSFD8b_MicrobialPathogens_Assesment1 = relationship(u'MSFD8bMicrobialPathogensAssesment')


class MSFD8bNI(Base):
    __tablename__ = 'MSFD8b_NIS'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_NIS_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_NIS_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_NISMetadata = Table(
    'MSFD8b_NISMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_NIS_ID', ForeignKey(u'MSFD8b_NIS.MSFD8b_NIS_ID'), nullable=False)
)


class MSFD8bNISActivity(Base):
    __tablename__ = 'MSFD8b_NIS_Activity'

    MSFD8b_NIS_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_NIS_ActivityDescription = Column(ForeignKey(u'MSFD8b_NIS_ActivityDescription.MSFD8b_NIS_ActivityDescription_ID'), nullable=False)

    MSFD8b_NIS_ActivityDescription1 = relationship(u'MSFD8bNISActivityDescription')


class MSFD8bNISActivityDescription(Base):
    __tablename__ = 'MSFD8b_NIS_ActivityDescription'

    MSFD8b_NIS_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_NIS = Column(ForeignKey(u'MSFD8b_NIS.MSFD8b_NIS_ID'), nullable=False)

    MSFD8b_NI = relationship(u'MSFD8bNI')


class MSFD8bNISAssesment(Base):
    __tablename__ = 'MSFD8b_NIS_Assesment'

    MSFD8b_NIS_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_NIS = Column(ForeignKey(u'MSFD8b_NIS.MSFD8b_NIS_ID'), nullable=False)

    MSFD8b_NI = relationship(u'MSFD8bNI')


class MSFD8bNISAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_NIS_AssesmentCriteria'

    MSFD8b_NIS_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_NIS_Assesment = Column(ForeignKey(u'MSFD8b_NIS_Assesment.MSFD8b_NIS_Assesment_ID'), nullable=False)

    MSFD8b_NIS_Assesment1 = relationship(u'MSFD8bNISAssesment')


class MSFD8bNISAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_NIS_AssesmentIndicator'

    MSFD8b_NIS_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_NIS_Assesment = Column(ForeignKey(u'MSFD8b_NIS_Assesment.MSFD8b_NIS_Assesment_ID'), nullable=False)

    MSFD8b_NIS_Assesment1 = relationship(u'MSFD8bNISAssesment')


class MSFD8bNISSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_NIS_SumInfo2_ImpactedElements'

    MSFD8b_NIS_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_NIS = Column(ForeignKey(u'MSFD8b_NIS.MSFD8b_NIS_ID'), nullable=False)

    MSFD8b_NI = relationship(u'MSFD8bNI')


class MSFD8bNoise(Base):
    __tablename__ = 'MSFD8b_Noise'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Noise_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_Noise_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_NoiseMetadata = Table(
    'MSFD8b_NoiseMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_Noise_ID', ForeignKey(u'MSFD8b_Noise.MSFD8b_Noise_ID'), nullable=False)
)


class MSFD8bNoiseActivity(Base):
    __tablename__ = 'MSFD8b_Noise_Activity'

    MSFD8b_Noise_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_Noise_ActivityDescription = Column(ForeignKey(u'MSFD8b_Noise_ActivityDescription.MSFD8b_Noise_ActivityDescription_ID'), nullable=False)

    MSFD8b_Noise_ActivityDescription1 = relationship(u'MSFD8bNoiseActivityDescription')


class MSFD8bNoiseActivityDescription(Base):
    __tablename__ = 'MSFD8b_Noise_ActivityDescription'

    MSFD8b_Noise_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_Noise = Column(ForeignKey(u'MSFD8b_Noise.MSFD8b_Noise_ID'), nullable=False)

    MSFD8b_Noise1 = relationship(u'MSFD8bNoise')


class MSFD8bNoiseAssesment(Base):
    __tablename__ = 'MSFD8b_Noise_Assesment'

    MSFD8b_Noise_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Noise = Column(ForeignKey(u'MSFD8b_Noise.MSFD8b_Noise_ID'), nullable=False)

    MSFD8b_Noise1 = relationship(u'MSFD8bNoise')


class MSFD8bNoiseAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_Noise_AssesmentCriteria'

    MSFD8b_Noise_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_Noise_Assesment = Column(ForeignKey(u'MSFD8b_Noise_Assesment.MSFD8b_Noise_Assesment_ID'), nullable=False)

    MSFD8b_Noise_Assesment1 = relationship(u'MSFD8bNoiseAssesment')


class MSFD8bNoiseAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_Noise_AssesmentIndicator'

    MSFD8b_Noise_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_Noise_Assesment = Column(ForeignKey(u'MSFD8b_Noise_Assesment.MSFD8b_Noise_Assesment_ID'), nullable=False)

    MSFD8b_Noise_Assesment1 = relationship(u'MSFD8bNoiseAssesment')


class MSFD8bNoiseSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_Noise_SumInfo2_ImpactedElements'

    MSFD8b_Noise_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_Noise = Column(ForeignKey(u'MSFD8b_Noise.MSFD8b_Noise_ID'), nullable=False)

    MSFD8b_Noise1 = relationship(u'MSFD8bNoise')


class MSFD8bNutrient(Base):
    __tablename__ = 'MSFD8b_Nutrients'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Nutrients_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_Nutrients_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_NutrientsMetadata = Table(
    'MSFD8b_NutrientsMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_Nutrients_ID', ForeignKey(u'MSFD8b_Nutrients.MSFD8b_Nutrients_ID'), nullable=False)
)


class MSFD8bNutrientsActivity(Base):
    __tablename__ = 'MSFD8b_Nutrients_Activity'

    MSFD8b_Nutrients_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_Nutrients_ActivityDescription = Column(ForeignKey(u'MSFD8b_Nutrients_ActivityDescription.MSFD8b_Nutrients_ActivityDescription_ID'), nullable=False)

    MSFD8b_Nutrients_ActivityDescription1 = relationship(u'MSFD8bNutrientsActivityDescription')


class MSFD8bNutrientsActivityDescription(Base):
    __tablename__ = 'MSFD8b_Nutrients_ActivityDescription'

    MSFD8b_Nutrients_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_Nutrients = Column(ForeignKey(u'MSFD8b_Nutrients.MSFD8b_Nutrients_ID'), nullable=False)

    MSFD8b_Nutrient = relationship(u'MSFD8bNutrient')


class MSFD8bNutrientsAssesment(Base):
    __tablename__ = 'MSFD8b_Nutrients_Assesment'

    MSFD8b_Nutrients_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode)
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_Nutrients = Column(ForeignKey(u'MSFD8b_Nutrients.MSFD8b_Nutrients_ID'), nullable=False)

    MSFD8b_Nutrient = relationship(u'MSFD8bNutrient')


class MSFD8bNutrientsAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_Nutrients_AssesmentCriteria'

    MSFD8b_Nutrients_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_Nutrients_Assesment = Column(ForeignKey(u'MSFD8b_Nutrients_Assesment.MSFD8b_Nutrients_Assesment_ID'), nullable=False)

    MSFD8b_Nutrients_Assesment1 = relationship(u'MSFD8bNutrientsAssesment')


class MSFD8bNutrientsAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_Nutrients_AssesmentIndicator'

    MSFD8b_Nutrients_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode)
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_Nutrients_Assesment = Column(ForeignKey(u'MSFD8b_Nutrients_Assesment.MSFD8b_Nutrients_Assesment_ID'), nullable=False)

    MSFD8b_Nutrients_Assesment1 = relationship(u'MSFD8bNutrientsAssesment')


class MSFD8bNutrientsSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_Nutrients_SumInfo2_ImpactedElements'

    MSFD8b_Nutrients_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_Nutrients = Column(ForeignKey(u'MSFD8b_Nutrients.MSFD8b_Nutrients_ID'), nullable=False)

    MSFD8b_Nutrient = relationship(u'MSFD8bNutrient')


class MSFD8bPhysicalDamage(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PhysicalDamage_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_PhysicalDamage_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_PhysicalDamageMetadata = Table(
    'MSFD8b_PhysicalDamageMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_PhysicalDamage_ID', ForeignKey(u'MSFD8b_PhysicalDamage.MSFD8b_PhysicalDamage_ID'), nullable=False)
)


class MSFD8bPhysicalDamageActivity(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_Activity'

    MSFD8b_PhysicalDamage_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_PhysicalDamage_ActivityDescription = Column(ForeignKey(u'MSFD8b_PhysicalDamage_ActivityDescription.MSFD8b_PhysicalDamage_ActivityDescription_ID'), nullable=False)

    MSFD8b_PhysicalDamage_ActivityDescription1 = relationship(u'MSFD8bPhysicalDamageActivityDescription')


class MSFD8bPhysicalDamageActivityDescription(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_ActivityDescription'

    MSFD8b_PhysicalDamage_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_PhysicalDamage = Column(ForeignKey(u'MSFD8b_PhysicalDamage.MSFD8b_PhysicalDamage_ID'), nullable=False)

    MSFD8b_PhysicalDamage1 = relationship(u'MSFD8bPhysicalDamage')


class MSFD8bPhysicalDamageAssesment(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_Assesment'

    MSFD8b_PhysicalDamage_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PhysicalDamage = Column(ForeignKey(u'MSFD8b_PhysicalDamage.MSFD8b_PhysicalDamage_ID'), nullable=False)

    MSFD8b_PhysicalDamage1 = relationship(u'MSFD8bPhysicalDamage')


class MSFD8bPhysicalDamageAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_AssesmentCriteria'

    MSFD8b_PhysicalDamage_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_PhysicalDamage_Assesment = Column(ForeignKey(u'MSFD8b_PhysicalDamage_Assesment.MSFD8b_PhysicalDamage_Assesment_ID'), nullable=False)

    MSFD8b_PhysicalDamage_Assesment1 = relationship(u'MSFD8bPhysicalDamageAssesment')


class MSFD8bPhysicalDamageAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_AssesmentIndicator'

    MSFD8b_PhysicalDamage_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_PhysicalDamage_Assesment = Column(ForeignKey(u'MSFD8b_PhysicalDamage_Assesment.MSFD8b_PhysicalDamage_Assesment_ID'), nullable=False)

    MSFD8b_PhysicalDamage_Assesment1 = relationship(u'MSFD8bPhysicalDamageAssesment')


class MSFD8bPhysicalDamageSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_PhysicalDamage_SumInfo2_ImpactedElements'

    MSFD8b_PhysicalDamage_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_PhysicalDamage = Column(ForeignKey(u'MSFD8b_PhysicalDamage.MSFD8b_PhysicalDamage_ID'), nullable=False)

    MSFD8b_PhysicalDamage1 = relationship(u'MSFD8bPhysicalDamage')


class MSFD8bPhysicalLos(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PhysicalLoss_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_PhysicalLoss_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_PhysicalLossMetadata = Table(
    'MSFD8b_PhysicalLossMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_PhysicalLoss_ID', ForeignKey(u'MSFD8b_PhysicalLoss.MSFD8b_PhysicalLoss_ID'), nullable=False)
)


class MSFD8bPhysicalLossActivity(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_Activity'

    MSFD8b_PhysicalLoss_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_PhysicalLoss_ActivityDescription = Column(ForeignKey(u'MSFD8b_PhysicalLoss_ActivityDescription.MSFD8b_PhysicalLoss_ActivityDescription_ID'), nullable=False)

    MSFD8b_PhysicalLoss_ActivityDescription1 = relationship(u'MSFD8bPhysicalLossActivityDescription')


class MSFD8bPhysicalLossActivityDescription(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_ActivityDescription'

    MSFD8b_PhysicalLoss_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_PhysicalLoss = Column(ForeignKey(u'MSFD8b_PhysicalLoss.MSFD8b_PhysicalLoss_ID'), nullable=False)

    MSFD8b_PhysicalLos = relationship(u'MSFD8bPhysicalLos')


class MSFD8bPhysicalLossAssesment(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_Assesment'

    MSFD8b_PhysicalLoss_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PhysicalLoss = Column(ForeignKey(u'MSFD8b_PhysicalLoss.MSFD8b_PhysicalLoss_ID'), nullable=False)

    MSFD8b_PhysicalLos = relationship(u'MSFD8bPhysicalLos')


class MSFD8bPhysicalLossAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_AssesmentCriteria'

    MSFD8b_PhysicalLoss_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_PhysicalLoss_Assesment = Column(ForeignKey(u'MSFD8b_PhysicalLoss_Assesment.MSFD8b_PhysicalLoss_Assesment_ID'), nullable=False)

    MSFD8b_PhysicalLoss_Assesment1 = relationship(u'MSFD8bPhysicalLossAssesment')


class MSFD8bPhysicalLossAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_AssesmentIndicator'

    MSFD8b_PhysicalLoss_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_PhysicalLoss_Assesment = Column(ForeignKey(u'MSFD8b_PhysicalLoss_Assesment.MSFD8b_PhysicalLoss_Assesment_ID'), nullable=False)

    MSFD8b_PhysicalLoss_Assesment1 = relationship(u'MSFD8bPhysicalLossAssesment')


class MSFD8bPhysicalLossSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_PhysicalLoss_SumInfo2_ImpactedElements'

    MSFD8b_PhysicalLoss_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_PhysicalLoss = Column(ForeignKey(u'MSFD8b_PhysicalLoss.MSFD8b_PhysicalLoss_ID'), nullable=False)

    MSFD8b_PhysicalLos = relationship(u'MSFD8bPhysicalLos')


class MSFD8bPollutantEvent(Base):
    __tablename__ = 'MSFD8b_PollutantEvents'

    MarineUnitID = Column(Unicode(42), index=True)
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SumInfo1 = Column(Unicode(255))
    SumInfo1Unit = Column(Unicode(255))
    SumInfo1Confidence = Column(Unicode(255))
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PollutantEvents_Import = Column(ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
    MSFD8b_PollutantEvents_ID = Column(Integer, primary_key=True)

    MSFD8b_Import = relationship(u'MSFD8bImport')


t_MSFD8b_PollutantEventsMetadata = Table(
    'MSFD8b_PollutantEventsMetadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8b_PollutantEvents_ID', ForeignKey(u'MSFD8b_PollutantEvents.MSFD8b_PollutantEvents_ID'), nullable=False)
)


class MSFD8bPollutantEventsActivity(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_Activity'

    MSFD8b_PollutantEvents_Activity_ID = Column(Integer, primary_key=True)
    Activity = Column(Unicode(255))
    ActivityRank = Column(Unicode(255))
    MSFD8b_PollutantEvents_ActivityDescription = Column(ForeignKey(u'MSFD8b_PollutantEvents_ActivityDescription.MSFD8b_PollutantEvents_ActivityDescription_ID'), nullable=False)

    MSFD8b_PollutantEvents_ActivityDescription1 = relationship(u'MSFD8bPollutantEventsActivityDescription')


class MSFD8bPollutantEventsActivityDescription(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_ActivityDescription'

    MSFD8b_PollutantEvents_ActivityDescription_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Description = Column(Unicode)
    Limitations = Column(Unicode)
    MSFD8b_PollutantEvents = Column(ForeignKey(u'MSFD8b_PollutantEvents.MSFD8b_PollutantEvents_ID'), nullable=False)

    MSFD8b_PollutantEvent = relationship(u'MSFD8bPollutantEvent')


class MSFD8bPollutantEventsAssesment(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_Assesment'

    MSFD8b_PollutantEvents_Assesment_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    Status = Column(Unicode(255))
    StatusDescription = Column(Unicode)
    StatusTrend = Column(Unicode(255))
    StatusConfidence = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8b_PollutantEvents = Column(ForeignKey(u'MSFD8b_PollutantEvents.MSFD8b_PollutantEvents_ID'), nullable=False)

    MSFD8b_PollutantEvent = relationship(u'MSFD8bPollutantEvent')


class MSFD8bPollutantEventsAssesmentCriterion(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_AssesmentCriteria'

    MSFD8b_PollutantEvents_AssesmentCriteria_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    CriteriaType = Column(Unicode(255))
    CriteriaOther = Column(Unicode(255))
    MSFD8b_PollutantEvents_Assesment = Column(ForeignKey(u'MSFD8b_PollutantEvents_Assesment.MSFD8b_PollutantEvents_Assesment_ID'), nullable=False)

    MSFD8b_PollutantEvents_Assesment1 = relationship(u'MSFD8bPollutantEventsAssesment')


class MSFD8bPollutantEventsAssesmentIndicator(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_AssesmentIndicator'

    MSFD8b_PollutantEvents_AssesmentIndicator_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    Topic = Column(Unicode(255))
    GESIndicators = Column(Unicode(255))
    OtherIndicatorDescription = Column(Unicode(255))
    ThresholdValue = Column(Unicode(255))
    ThresholdValueUnit = Column(Unicode(255))
    ThresholdProportion = Column(Unicode(255))
    Baseline = Column(Unicode)
    MSFD8b_PollutantEvents_Assesment = Column(ForeignKey(u'MSFD8b_PollutantEvents_Assesment.MSFD8b_PollutantEvents_Assesment_ID'), nullable=False)

    MSFD8b_PollutantEvents_Assesment1 = relationship(u'MSFD8bPollutantEventsAssesment')


class MSFD8bPollutantEventsSumInfo2ImpactedElement(Base):
    __tablename__ = 'MSFD8b_PollutantEvents_SumInfo2_ImpactedElements'

    MSFD8b_PollutantEvents_SumInfo2_ImpactedElements_ID = Column(Integer, primary_key=True)
    MarineUnitID = Column(Unicode(42))
    ImpactType = Column(Unicode(255))
    SumInfo2 = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    Other = Column(Unicode(250))
    MSFD8b_PollutantEvents = Column(ForeignKey(u'MSFD8b_PollutantEvents.MSFD8b_PollutantEvents_ID'), nullable=False)

    MSFD8b_PollutantEvent = relationship(u'MSFD8bPollutantEvent')


t_MSFD8b_ReportingInformation = Table(
    'MSFD8b_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD8b_ReportingInformation_Import', ForeignKey(u'MSFD8b_Imports.MSFD8b_Import_ID'), nullable=False)
)


class MSFD8cDepend(Base):
    __tablename__ = 'MSFD8c_Depend'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255))
    Dependency = Column(Unicode(255))
    Other = Column(Unicode(255))
    MSFD8c_Depend_ID = Column(Integer, primary_key=True)
    MSFD8c_Uses_ID = Column(ForeignKey(u'MSFD8c_Uses.MSFD8c_Uses_ID'), nullable=False)

    MSFD8c_Us = relationship(u'MSFD8cUs')


class MSFD8cImport(Base):
    __tablename__ = 'MSFD8c_Imports'
    __table_args__ = (
        Index('MSFD8c_Imports_UNIQUE_CountryRegion', 'MSFD8c_Import_ReportingCountry', 'MSFD8c_Import_ReportingRegion', unique=True),
    )

    MSFD8c_Import_ID = Column(Integer, primary_key=True)
    MSFD8c_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD8c_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFD8c_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFD8c_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


t_MSFD8c_Metadata = Table(
    'MSFD8c_Metadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('Topic', Unicode(255)),
    Column('AssessmentDateStart', Unicode(255)),
    Column('AssessmentDateEnd', Unicode(255)),
    Column('MethodUsed', Unicode),
    Column('Sources', Unicode),
    Column('MSFD8c_Metadata_Import', ForeignKey(u'MSFD8c_Imports.MSFD8c_Import_ID'), nullable=False)
)


class MSFD8cPressure(Base):
    __tablename__ = 'MSFD8c_Pressures'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255))
    Description = Column(Unicode)
    Pressure1 = Column(Unicode(255))
    Rank1 = Column(Unicode(255))
    Pressure2 = Column(Unicode(255))
    Rank2 = Column(Unicode(255))
    Pressure3 = Column(Unicode(255))
    Rank3 = Column(Unicode(255))
    Limitations = Column(Unicode(255))
    MSFD8c_Pressures_ID = Column(Integer, primary_key=True)
    MSFD8c_Uses_ID = Column(ForeignKey(u'MSFD8c_Uses.MSFD8c_Uses_ID'), nullable=False)

    MSFD8c_Us = relationship(u'MSFD8cUs')


t_MSFD8c_ReportingInformation = Table(
    'MSFD8c_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD8c_ReportingInformation_Import', ForeignKey(u'MSFD8c_Imports.MSFD8c_Import_ID'), nullable=False)
)


class MSFD8cUs(Base):
    __tablename__ = 'MSFD8c_Uses'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255))
    Topic = Column(Unicode(255))
    Description = Column(Unicode)
    SummaryInformation1 = Column(Unicode)
    Summary1Confidence = Column(Unicode(255))
    SummaryInformation2 = Column(Unicode)
    TrendsRecent = Column(Unicode(255))
    RecentTimeStart = Column(Unicode(255))
    RecentTimeEnd = Column(Unicode(255))
    TrendsFuture = Column(Unicode(255))
    FutureTimeStart = Column(Unicode(255))
    FutureTimeEnd = Column(Unicode(255))
    Limitations = Column(Unicode)
    MSFD8c_Uses_Import = Column(ForeignKey(u'MSFD8c_Imports.MSFD8c_Import_ID'), nullable=False)
    MSFD8c_Uses_ID = Column(Integer, primary_key=True)

    MSFD8c_Import = relationship(u'MSFD8cImport')


t_MSFD9_AssessmentAreas = Table(
    'MSFD9_AssessmentAreas', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255)),
    Column('AssessmentAreas', Unicode(42)),
    Column('MSFD9_Descriptor', ForeignKey(u'MSFD9_Descriptors.MSFD9_Descriptor_ID'), nullable=False)
)


class MSFD9Descriptor(Base):
    __tablename__ = 'MSFD9_Descriptors'

    MarineUnitID = Column(Unicode(42), index=True)
    ReportingFeature = Column(Unicode(255))
    DescriptionGES = Column(Unicode)
    ThresholdValue = Column(Unicode)
    ThresholdValueUnit = Column(Unicode)
    ReferencePointType = Column(Unicode(255))
    Baseline = Column(Unicode)
    Proportion = Column(Unicode(255))
    AssessmentMethod = Column(Unicode)
    DevelopmentStatus = Column(Unicode)
    MSFD9_Descriptors_Import = Column(ForeignKey(u'MSFD9_Imports.MSFD9_Import_ID'), nullable=False)
    MSFD9_Descriptor_ID = Column(Integer, primary_key=True)

    MSFD9_Import = relationship(u'MSFD9Import')


t_MSFD9_Features = Table(
    'MSFD9_Features', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('ReportingFeature', Unicode(255)),
    Column('FeaturesPressuresImpacts', Unicode(255)),
    Column('MSFD9_Descriptor', ForeignKey(u'MSFD9_Descriptors.MSFD9_Descriptor_ID'), nullable=False),
    Column('FeatureType', Unicode(255))
)


class MSFD9Import(Base):
    __tablename__ = 'MSFD9_Imports'
    __table_args__ = (
        Index('MSFD9_Imports_UNIQUE_CountryRegion', 'MSFD9_Import_ReportingCountry', 'MSFD9_Import_ReportingRegion', unique=True),
    )

    MSFD9_Import_ID = Column(Integer, primary_key=True)
    MSFD9_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFD9_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFD9_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFD9_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


t_MSFD9_Metadata = Table(
    'MSFD9_Metadata', metadata,
    Column('MarineUnitID', Unicode(42), index=True),
    Column('MethodUsed', Unicode),
    Column('MSFD9_Metadata_Import', ForeignKey(u'MSFD9_Imports.MSFD9_Import_ID'), nullable=False)
)


t_MSFD9_ReportingInformation = Table(
    'MSFD9_ReportingInformation', metadata,
    Column('ReportingFeature', Unicode(255)),
    Column('Name', Unicode(255)),
    Column('Contact', Unicode(255)),
    Column('Organisation', Unicode(255)),
    Column('ReportingDate', Unicode(255)),
    Column('MSFD9_ReportingInformation_Import', ForeignKey(u'MSFD9_Imports.MSFD9_Import_ID'), nullable=False)
)


t_MSFDCommon = Table(
    'MSFDCommon', metadata,
    Column('PrimaryKey', Unicode(255)),
    Column('ForeignKey', Unicode(255)),
    Column('value', Unicode(255)),
    Column('Description', Unicode(255)),
    Column('Topic', Unicode(255))
)


class MSFDFeaturesOverview(Base):
    __tablename__ = 'MSFDFeatures_Overview'

    MSFDFeatures_Overview_ID = Column(Integer, primary_key=True)
    RScode = Column(Unicode(255))
    ReportingSection = Column(Unicode(255))
    RFCode = Column(Unicode(255))
    ReportingFeature = Column(Unicode(255))
    FeatureType = Column(Unicode(255))
    SourceClassificationListAuthority = Column(Unicode(255))
    FeatureRelevant = Column(Unicode(255))
    FeatureReported = Column(Unicode(255))
    Comments = Column(Unicode)
    MSFDFeatures_Overview_Import = Column(ForeignKey(u'MSFDFeatures_Overview_Imports.MSFDFeatures_Overview_Import_ID'), nullable=False)

    MSFDFeatures_Overview_Import1 = relationship(u'MSFDFeaturesOverviewImport')


class MSFDFeaturesOverviewImport(Base):
    __tablename__ = 'MSFDFeatures_Overview_Imports'

    MSFDFeatures_Overview_Import_ID = Column(Integer, primary_key=True)
    MSFDFeatures_Overview_Import_Time = Column(DateTime, nullable=False, server_default=text("(getdate())"))
    MSFDFeatures_Overview_Import_ReportingCountry = Column(ForeignKey(u'ReportingCountries.ReportingCountryCode'), nullable=False)
    MSFDFeatures_Overview_Import_ReportingRegion = Column(ForeignKey(u'ReportingRegions.ReportingRegionCode'), nullable=False)
    MSFDFeatures_Overview_Import_FileName = Column(Unicode(260))

    ReportingCountry = relationship(u'ReportingCountry')
    ReportingRegion = relationship(u'ReportingRegion')


t_MSFD_10_ExtractionFishShellfishImpact = Table(
    'MSFD_10_ExtractionFishShellfishImpact', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Topic', Unicode(255)),
    Column('Method 1: Quantitative stock assessment with reference points', Unicode(255)),
    Column('Method 2: Quantitative stock assessment', Unicode(255)),
    Column('Other method: pct of the fish stock are within safe bio limits', Unicode(255))
)


t_MSFD_11_8cMethodology = Table(
    'MSFD_11_8cMethodology', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Topic', Unicode(255)),
    Column('MethodUsed', Unicode)
)


t_MSFD_12_8cOverview = Table(
    'MSFD_12_8cOverview', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('Features & Characteristics', Unicode(255)),
    Column('Found relevant by MS?', Unicode(255)),
    Column('Reported by MS?', Unicode(255)),
    Column('Comments/justification for not reporting', Unicode)
)


t_MSFD_13_8cDetailed = Table(
    'MSFD_13_8cDetailed', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('UsesActivities', Unicode(255)),
    Column('Description', Unicode),
    Column('Topic', Unicode(255)),
    Column('SummaryInformation1', Unicode(255)),
    Column('Pressure1', Unicode(255)),
    Column('Rank1', Unicode(255)),
    Column('Pressure2', Unicode(255)),
    Column('Rank2', Unicode(255)),
    Column('Pressure3', Unicode(255)),
    Column('Rank3', Unicode(255)),
    Column('InformationGaps', Unicode)
)


t_MSFD_15_9Overview = Table(
    'MSFD_15_9Overview', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('Features & Characteristics', Unicode(255)),
    Column('Found relevant by MS?', Unicode(255)),
    Column('Reported by MS?', Unicode(255)),
    Column('Comments/justification for not reporting', Unicode)
)


t_MSFD_16a_9Detailed = Table(
    'MSFD_16a_9Detailed', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('ListOfGES', Unicode(255)),
    Column('DescriptionGES', Unicode),
    Column('ThresholdValue', Unicode),
    Column('ThresholdValueUnit', Unicode(250)),
    Column('ReferencePointType', Unicode(255)),
    Column('Baseline', Unicode),
    Column('Proportion', Unicode(255))
)


t_MSFD_16b_9GESList = Table(
    'MSFD_16b_9GESList', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('ListOfGES', Unicode(255))
)


t_MSFD_18_10Detailed = Table(
    'MSFD_18_10Detailed', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Targets', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('Description', Unicode),
    Column('ThresholdValue', Unicode),
    Column('ReferencePointType', Unicode(255)),
    Column('Baseline', Unicode),
    Column('Proportion', Unicode(255)),
    Column('TimeScale', Unicode(255)),
    Column('InterimGESTarget', Unicode(255)),
    Column('TargetType', Unicode(255))
)


t_MSFD_19a_10DescriptiorsCriteriaIndicators = Table(
    'MSFD_19a_10DescriptiorsCriteriaIndicators', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Targets', Unicode(255)),
    Column('Target or associated Indicator', Unicode(255)),
    Column('Descriptors Criterion Indicators', Unicode(255)),
    Column('GESOther explanation', Unicode(255))
)


t_MSFD_19b_10PhysicalChemicalFeatures = Table(
    'MSFD_19b_10PhysicalChemicalFeatures', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('Targets', Unicode(42)),
    Column('Target or associated indicator', Unicode(255)),
    Column('FeaturesPressures', Unicode(255)),
    Column('FeatureType', Unicode(100)),
    Column('OtherExplanation', Unicode(255))
)


t_MSFD_1_MarineUnits = Table(
    'MSFD_1_MarineUnits', metadata,
    Column('MarineUnitID', Unicode(42)),
    Column('Name of marine unit/assessment area', Unicode(255)),
    Column('Type of assessment area', Unicode(255)),
    Column('MemberState', Unicode(255)),
    Column('Marine region/subregion', Unicode(255))
)


t_MSFD_2_AreasDeliniation = Table(
    'MSFD_2_AreasDeliniation', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Member States marine waters', Unicode),
    Column('Marine region/subregion', Unicode),
    Column('Formal subdivisions', Unicode),
    Column('Other assessment areas', Unicode)
)


t_MSFD_3_RegionalCooperation = Table(
    'MSFD_3_RegionalCooperation', metadata,
    Column('Regional cooperation for:', Unicode(50)),
    Column('Marine region/subregion', Unicode(50)),
    Column('NatureCoordination', Unicode),
    Column('RegionalCoherence', Unicode(255)),
    Column('RegionalCoordinationProblems', Unicode),
    Column('Countries', Unicode)
)


t_MSFD_4_8aOverview = Table(
    'MSFD_4_8aOverview', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('Features & Characteristics', Unicode(255)),
    Column('PredominantFeature', Unicode(255)),
    Column('Found relevant by MS?', Unicode(255)),
    Column('Reported by MS?', Unicode(255)),
    Column('Comments/justification for not reporting', Unicode)
)


t_MSFD_5a_8aDetail = Table(
    'MSFD_5a_8aDetail', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Feature', Unicode(255)),
    Column('PredominantFeature', Unicode(255)),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('Summary1', Unicode(255)),
    Column('Summary2', Unicode),
    Column('Status', Unicode(255)),
    Column('StatusDescription', Unicode),
    Column('TrendStatus', Unicode(255))
)


t_MSFD_5b_8aPressures = Table(
    'MSFD_5b_8aPressures', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(255)),
    Column('Feature', Unicode(255)),
    Column('PredominantFeature', Unicode(255)),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Pressure1', Unicode(255)),
    Column('Rank1', Unicode(255)),
    Column('Pressure2', Unicode(255)),
    Column('Rank2', Unicode(255)),
    Column('Pressure3', Unicode(255)),
    Column('Rank3', Unicode(255))
)


t_MSFD_5c_8aCriterion = Table(
    'MSFD_5c_8aCriterion', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Feature', Unicode(255)),
    Column('PredominantFeature', Unicode(255)),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('CriteriaType', Unicode(255)),
    Column('CriteriaOtherExplanation', Unicode(250))
)


t_MSFD_5d_8aIndicators = Table(
    'MSFD_5d_8aIndicators', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Feature', Unicode(255)),
    Column('PredominantFeature', Unicode(255)),
    Column('SourceClassificationListAuthority', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('Indicator', Unicode(255)),
    Column('OtherIndicatorExplanation', Unicode(255)),
    Column('ThresholdValue', Unicode(250)),
    Column('ThresholdValueUnit', Unicode(100)),
    Column('ThresholdProportion', Unicode(255)),
    Column('Baseline', Unicode)
)


t_MSFD_6_NISInventory = Table(
    'MSFD_6_NISInventory', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('ReportingFeature', Unicode(255)),
    Column('ScientificName', Unicode(255)),
    Column('Predominant habitat or functional group', Unicode(255))
)


t_MSFD_7_8bOverview = Table(
    'MSFD_7_8bOverview', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('Features & Characteristics', Unicode(255)),
    Column('Found relevant by MS?', Unicode(255)),
    Column('Reported by MS?', Unicode(255)),
    Column('Comments/justification for not reporting', Unicode)
)


t_MSFD_8a_8bDetailed = Table(
    'MSFD_8a_8bDetailed', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Pressure', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('Description', Unicode),
    Column('SumInfo1', Unicode(255)),
    Column('SumInfo1Unit', Unicode(255)),
    Column('Status', Unicode),
    Column('Trend status', Unicode(255))
)


t_MSFD_8b_8bPressures = Table(
    'MSFD_8b_8bPressures', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Pressure', Unicode(255)),
    Column('Activity', Unicode(255)),
    Column('ActivityRank', Unicode(255))
)


t_MSFD_8c_8bCriteria = Table(
    'MSFD_8c_8bCriteria', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Pressure', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('CriteriaType', Unicode(255)),
    Column('CriteriaOtherExplanation', Unicode(255))
)


t_MSFD_8d_8bIndicators = Table(
    'MSFD_8d_8bIndicators', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Pressure', Unicode(255)),
    Column('Topic', Unicode(255)),
    Column('IndicatorType', Unicode(255)),
    Column('IndicatorOtherExplanation', Unicode(255)),
    Column('ThresholdValue', Unicode(255)),
    Column('ThresholdValueUnit', Unicode(255)),
    Column('ThresholdProportion', Unicode(255)),
    Column('Baseline', Unicode(255))
)


t_MSFD_8e_8bImpactedElements = Table(
    'MSFD_8e_8bImpactedElements', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Pressure', Unicode(255)),
    Column('ImpactType', Unicode(255)),
    Column('ImpactedElement', Unicode(255)),
    Column('ElementType', Unicode(255))
)


t_MSFD_9_ExtractionFishShellfishPressure = Table(
    'MSFD_9_ExtractionFishShellfishPressure', metadata,
    Column('MemberState', Unicode(2), nullable=False),
    Column('Marine region/subregion', Unicode(3), nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('Topic', Unicode(255)),
    Column('Number of vessels', Unicode(100)),
    Column('Total tonnage', Unicode(255)),
    Column('Total power', Unicode(255)),
    Column('Total number of fishing days', Unicode(255))
)


t_MS_CompetentAuthorities = Table(
    'MS_CompetentAuthorities', metadata,
    Column('C_CD', Unicode(2), index=True),
    Column('MSCACode', Unicode(42), unique=True),
    Column('Auth_CD', Unicode(40)),
    Column('CompetentAuthorityName', Unicode(100)),
    Column('CompetentAuthorityNameNL', Unicode(100)),
    Column('Acronym', Unicode(25)),
    Column('Street', Unicode(100)),
    Column('City', Unicode(100)),
    Column('CityNL', Unicode(100)),
    Column('Country', Unicode(100)),
    Column('Postcode', Unicode(50)),
    Column('URL_CA', Unicode(250)),
    Column('LegalStatus', Unicode),
    Column('Responsibilities', Unicode),
    Column('Reference', Unicode),
    Column('Membership', Unicode),
    Column('RegionalCoordination', Unicode),
    Column('Import_Time', DateTime),
    Column('Import_FileName', Unicode),
    Column('METADATA', Unicode),
    Column('URL', Unicode)
)


class ReportingCountry(Base):
    __tablename__ = 'ReportingCountries'

    ReportingCountryCode = Column(Unicode(2), primary_key=True)


class ReportingRegion(Base):
    __tablename__ = 'ReportingRegions'

    ReportingRegionCode = Column(Unicode(3), primary_key=True)


t_View_1 = Table(
    'View_1', metadata,
    Column('Q9a_ElementMonitored', Unicode, nullable=False),
    Column('Q4g_SubProgrammeID', Unicode(42), nullable=False)
)


t_View_2 = Table(
    'View_2', metadata,
    Column('Q4e_ProgrammeID', Unicode(50), nullable=False),
    Column('Q4f_ProgrammeDescription', Unicode, nullable=False)
)


t_View_3 = Table(
    'View_3', metadata,
    Column('Q4g_SubProgrammeID', Unicode(42), nullable=False),
    Column('Q4j_DescriptionSpatialScope', Unicode, nullable=False)
)


t_Webform_SpecialFeatures = Table(
    'Webform_SpecialFeatures', metadata,
    Column('Country', Unicode(2), nullable=False),
    Column('Region', Unicode(3), nullable=False),
    Column('RScode', Unicode(255)),
    Column('ReportingSection', Unicode(255)),
    Column('RFCode', Unicode(255)),
    Column('ReportingFeature', Unicode(255)),
    Column('FeatureType', Unicode(255))
)


t_Webform_Target = Table(
    'Webform_Target', metadata,
    Column('Country', Unicode(2), nullable=False),
    Column('Region', Unicode(3), nullable=False),
    Column('Topic', Unicode(255)),
    Column('ReportingFeature', Unicode(255))
)


class Sysdiagram(Base):
    __tablename__ = 'sysdiagrams'
    __table_args__ = (
        Index('UK_principal_name', 'principal_id', 'name', unique=True),
    )

    name = Column(Unicode(128), nullable=False)
    principal_id = Column(Integer, nullable=False)
    diagram_id = Column(Integer, primary_key=True)
    version = Column(Integer)
    definition = Column(LargeBinary)


class MetadataArt193(Base):
    __tablename__ = 'MetadataArt19_3'

    Id = Column(Integer, primary_key=True)
    Country = Column(Unicode(11), nullable=False)
    Region = Column(Unicode(11), nullable=False)


t_MetadataFeatures = Table(
    'MetadataFeatures', metadata,
    Column('IdMetadataArt19_3', Integer, nullable=False),
    Column('MarineUnitID', Unicode(42)),
    Column('ReportingFeature', Unicode(250)),
    Column('DatasetRecord', Unicode),
    Column('DatasetLink', Unicode),
    Column('MetadataStandard', Unicode(20)),
    Column('DateStamp', Unicode(100)),
    Column('Language', Unicode(11))
)
