# pylint: skip-file
"""Article 19.3 "Datasets used" -- 2020 Article 11 monitoring programmes.

Reads the base tables the legacy 2020 Article 11 form uses:

* ``ART11_Programmes_MonitoringProgramme_DataAccess`` -- one row per filed data
  access reference (the result grain);
* ``ART11_Programmes_MonitoringProgramme`` -- the programme (code and name);
* ``ART11_Programmes_MonitoringProgramme_MarineReportingUnit`` -- the marine
  reporting units the programme covers;
* ``ART11_Strategies_MonitoringStrategy`` and its programme link -- the
  descriptor(s) a programme implements, matched by programme *code*;
* ``ReportedInformation`` -- the reported file (country, reported date).

The descriptor and marine-unit child tables are packed to one cell per
programme and joined to the data-access row. The Region/Subregion filter and
cell are derived from the Article 4 MRU publication.
"""
from __future__ import absolute_import

from sqlalchemy import func, select

from wise.msfd import sql2018
from wise.msfd.explorer.providers.article19_base import (
    MULTI_SEPARATOR,
    Article19DatasetsProvider,
    packed_cell,
)
from wise.msfd.explorer.providers.base import (
    Column,
    Facet,
    MultiValueFacet,
)
from wise.msfd.explorer.providers.regions import MruRegionFacet
from wise.msfd.explorer.serializers import country_label

INFORMATION_TYPE = '2020 Article 11 Monitoring programmes'


class Article19Cycle2020Provider(Article19DatasetsProvider):
    """Datasets reported under Article 19.3 for the 2020 monitoring programme."""

    cycle = '2020'
    cycle_label = INFORMATION_TYPE
    cycle_display = INFORMATION_TYPE
    #: the 2020 data lives in the same database session as the 2018 exercise.
    session_name = '2018'

    # Injectable source tables: tests point them at an in-memory database.
    data_access = sql2018.ART11ProgrammesMonitoringProgrammeDataAcces.__table__
    programme = sql2018.ART11ProgrammesMonitoringProgramme.__table__
    marine_unit = (
        sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit.__table__
    )
    strategy = sql2018.ART11StrategiesMonitoringStrategy.__table__
    strategy_programme = (
        sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme.__table__
    )
    reported = sql2018.ReportedInformation.__table__

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql2018.MRUsPublication.__table__
    region_mru_id_column = 'thematicId'
    region_region_column = 'rZoneId'
    region_mru_column = 'MarineReportingUnit'

    order_by = ('CountryCode', 'ProgrammeCode', 'DataAccess')

    def __init__(self, *args, **kwargs):
        data_access = self.data_access
        programme = self.programme
        reported = self.reported

        # A descriptor is linked to its monitoring programmes by *code*, not
        # by a foreign key. The legacy form upper-cased both sides of the
        # comparison; keep that so the mapping also works on a case sensitive
        # database (the SQLite harness).
        descriptors = select(
            programme.c.Id.label('IdMonitoringProgramme'),
            self.strategy.c.Descriptor.label('Descriptor'),
        ).select_from(
            self.strategy_programme
            .join(
                self.strategy,
                self.strategy_programme.c.IdMonitoringStrategy ==
                self.strategy.c.Id,
            )
            .join(
                programme,
                func.upper(programme.c.ProgrammeCode) ==
                func.upper(self.strategy_programme.c.MonitoringProgrammes),
            )
        ).distinct().subquery()

        descriptor_cell = packed_cell(
            descriptors, ['IdMonitoringProgramme'], 'Descriptor', 'Descriptor'
        )
        marine_unit = packed_cell(
            self.marine_unit, ['IdMonitoringProgramme'],
            'MarineReportingUnit', 'MarineReportingUnit',
        )

        self.mapper = select(
            data_access.c.Id.label('DataAccessId'),
            data_access.c.DataAccess.label('DataAccess'),
            programme.c.ProgrammeCode.label('ProgrammeCode'),
            programme.c.ProgrammeName.label('ProgrammeName'),
            reported.c.CountryCode.label('CountryCode'),
            reported.c.ReportingDate.label('ReportingDate'),
            descriptor_cell.c.Descriptor.label('Descriptor'),
            marine_unit.c.MarineReportingUnit.label('MarineReportingUnit'),
        ).select_from(
            data_access
            .join(
                programme,
                data_access.c.IdMonitoringProgramme == programme.c.Id,
            )
            .join(
                reported,
                programme.c.IdReportedInformation == reported.c.Id,
            )
            .outerjoin(
                descriptor_cell,
                descriptor_cell.c.IdMonitoringProgramme == programme.c.Id,
            )
            .outerjoin(
                marine_unit,
                marine_unit.c.IdMonitoringProgramme == programme.c.Id,
            )
        ).subquery()

        super(Article19Cycle2020Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column(
            'Region',
            'Region / Subregion',
            'Region',
            min_width=200,
            sortable=False,
        ),
        Column(
            'Descriptor',
            'Descriptor',
            'Descriptor',
            format='multi',
            separator=MULTI_SEPARATOR,
            min_width=200,
        ),
        Column('ProgrammeCode', 'Programme code', 'ProgrammeCode'),
        Column(
            'ProgrammeName',
            'Programme name',
            'ProgrammeName',
            expandable=True,
            min_width=250,
        ),
        Column(
            'DataAccess',
            'Data access',
            'DataAccess',
            expandable=True,
            min_width=250,
        ),
        Column(
            'ReportingDate', 'Reported date', 'ReportingDate', format='date'
        ),
        Column(
            'InformationType',
            'Information type',
            static=INFORMATION_TYPE,
            min_width=170,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'CountryCode',
            labeler=country_label,
        ),
        MruRegionFacet(
            'region_subregions',
            'Region and Subregion',
            mru_column='MarineReportingUnit',
            packed=True,
            separator=MULTI_SEPARATOR,
        ),
        MultiValueFacet(
            'descriptor',
            'Descriptor',
            'Descriptor',
            separator=MULTI_SEPARATOR,
        ),
    )
