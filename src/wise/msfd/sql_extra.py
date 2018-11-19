from . import sql


class MSFD4GeographicalAreaID(sql.Base):
    __table__ = sql.t_MSFD4_GegraphicalAreasID
    __mapper_args__ = {
        'primary_key': [sql.t_MSFD4_GegraphicalAreasID.c.MarineUnitID]
    }


_t_gad = sql.t_MSFD4_GeograpicalAreasDescription


class MSFD4GeograpicalAreaDescription(sql.Base):
    __table__ = _t_gad
    __mapper_args__ = {
        'primary_key': [_t_gad.c.MSFD4_GeograpicalAreasDescription_Import]
    }


class MSCompetentAuthority(sql.Base):
    __table__ = sql.t_MS_CompetentAuthorities
    __mapper_args__ = {
        'primary_key': [sql.t_MS_CompetentAuthorities.c.MSCACode]
    }


class MSFD9Feature(sql.Base):
    __table__ = sql.t_MSFD9_Features

    __mapper_args__ = {
        'primary_key': [
            sql.t_MSFD9_Features.c.MarineUnitID,
            sql.t_MSFD9_Features.c.FeaturesPressuresImpacts,
        ]
    }


class MSFD10FeaturePressures(sql.Base):
    __table__ = sql.t_MSFD10_FeaturesPressures

    __mapper_args__ = {
        'primary_key': [
            __table__.c.MarineUnitID,
            __table__.c.PhysicalChemicalHabitatsFunctionalPressures,
            __table__.c.Other
        ]
    }


class MSFD10DESCrit(sql.Base):
    __table__ = sql.t_MSFD10_DESCrit

    __mapper_args__ = {
        'primary_key': [
            __table__.c.MarineUnitID,
            __table__.c.ReportingFeature,
            __table__.c.GESDescriptorsCriteriaIndicators,
            __table__.c.MSFD10_Target
        ]
    }
