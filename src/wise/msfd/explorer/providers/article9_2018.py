# pylint: skip-file
"""Provider for Article 9 (GES determination), 2018-2024 reporting exercise.

This cycle is read from the **base tables** the legacy ``search`` Article 9
form uses, not from the ``V_ART9_GES_2018`` view:

* ``ART9_GES_GESComponent`` -- one row per GES component (the determination's
  parent), holding the two justification fields and the link to the reported
  information;
* ``ART9_GES_GESDetermination`` -- the determination of a component (GES
  description, determination date, update type);
* ``ART9_GES_GESDetermination_Feature`` -- the features a determination
  covers;
* ``ART9_GES_MarineUnit`` -- the marine reporting units a determination
  covers;
* ``ReportedInformation`` -- the reported file (country and reported date).

The redesigned explorer shows a flat table, so the joins are expanded to one
row per ``(determination, feature, marine reporting unit)``; rows with no
determination, feature or MRU are kept (outer joins) so a component is never
lost. Only the latest reported file of each ``(country, schema)`` is shown,
which is the cut the legacy form applies through ``latest_import_ids_2018``.

The base tables carry no region: the Region/Subregion filter and cell are
derived from the Article 4 MRU publication, like the legacy explorer derived
regions elsewhere.
"""
from __future__ import absolute_import

from sqlalchemy import func, select

from wise.msfd import sql2018
from wise.msfd.explorer.providers.base import (
    BaseProvider,
    Column,
    Facet,
)
from wise.msfd.explorer.providers.regions import MruRegionFacet, MruRegionMixin
from wise.msfd.explorer.serializers import country_label, to_text


class Article9Cycle2018Provider(MruRegionMixin, BaseProvider):
    """GES determinations reported under Article 9 for 2018-2024."""

    article = '9'
    article_slug = 'determination-of-good-environmental-status'
    cycle = '2018'
    cycle_label = '2018 reporting exercise'
    cycle_display = '2018 reporting exercise'
    record_title = 'Article 9 (GES determination)'
    session_name = '2018'

    # Injectable source tables: tests point them at an in-memory database.
    component = sql2018.ART9GESGESComponent.__table__
    reported = sql2018.ReportedInformation.__table__
    determination = sql2018.ART9GESGESDetermination.__table__
    feature = sql2018.ART9GESGESDeterminationFeature.__table__
    marine_unit = sql2018.ART9GESMarineUnit.__table__

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql2018.MRUsPublication.__table__
    region_mru_id_column = 'thematicId'
    region_region_column = 'rZoneId'

    order_by = ('CountryCode', 'GESComponent')

    # Free text / already human readable fields shown as reported.
    blacklist_labels = (
        'MarineReportingUnit', 'GESDescription', 'JustificationDelay',
        'JustificationNonUse', 'DeterminationDate', 'UpdateType',
    )

    def __init__(self, *args, **kwargs):
        component = self.component
        reported = self.reported
        determination = self.determination
        feature = self.feature
        marine_unit = self.marine_unit

        # The base tables are joined in a sub-query so every column keeps its
        # plain name, which is what the provider's column/facet lookups expect
        # (a raw ``Join`` would key its columns by table name).
        self.mapper = select(
            component.c.Id.label('ComponentId'),
            component.c.GESComponent.label('GESComponent'),
            component.c.JustificationDelay.label('JustificationDelay'),
            component.c.JustificationNonUse.label('JustificationNonUse'),
            reported.c.Id.label('ImportId'),
            reported.c.CountryCode.label('CountryCode'),
            reported.c.ReportingDate.label('ReportingDate'),
            determination.c.Id.label('DeterminationId'),
            determination.c.GESDescription.label('GESDescription'),
            determination.c.DeterminationDate.label('DeterminationDate'),
            determination.c.UpdateType.label('UpdateType'),
            feature.c.Feature.label('Feature'),
            marine_unit.c.MarineReportingUnit.label('MarineReportingUnit'),
        ).select_from(
            component
            .join(
                reported,
                component.c.IdReportedInformation == reported.c.Id,
            )
            .outerjoin(
                determination,
                determination.c.IdGESComponent == component.c.Id,
            )
            .outerjoin(
                feature,
                feature.c.IdGESDetermination == determination.c.Id,
            )
            .outerjoin(
                marine_unit,
                marine_unit.c.IdGESDetermination == determination.c.Id,
            )
        ).subquery()

        super(Article9Cycle2018Provider, self).__init__(*args, **kwargs)

    columns = (
        Column('CountryCode', 'Country', 'CountryCode'),
        Column(
            'Region',
            'Region / Subregion',
            'Region',
            min_width=130,
            sortable=False,
        ),
        Column('GESComponent', 'GES Component / Criteria', 'GESComponent'),
        Column('Feature', 'Feature', 'Feature'),
        Column(
            'MarineReportingUnit',
            'Marine Reporting Unit',
            'MarineReportingUnit',
            min_width=150,
        ),
        Column(
            'GESDescription',
            'GES Description',
            'GESDescription',
            expandable=True,
            min_width=280,
        ),
        Column(
            'JustificationDelay',
            'Justification for delay',
            'JustificationDelay',
            expandable=True,
            min_width=200,
        ),
        Column(
            'JustificationNonUse',
            'Justification for non-use',
            'JustificationNonUse',
            expandable=True,
            min_width=200,
        ),
        Column('UpdateType', 'Update type', 'UpdateType', min_width=170),
        Column('DeterminationDate', 'Determination date', 'DeterminationDate'),
        Column('ReportingDate', 'Reported date', 'ReportingDate'),
        Column(
            'ReportingPeriod',
            'Reporting period',
            static='2018 reporting exercise',
            min_width=160,
        ),
    )

    facets = (
        Facet(
            'member_states',
            'Country',
            'CountryCode',
            labeler=country_label,
        ),
        MruRegionFacet('region_subregions', 'Region and Subregion'),
        Facet(
            'update_type',
            'Update type',
            'UpdateType',
            # the reported value is already human readable
            labeler=to_text,
        ),
        Facet(
            'ges_component',
            'GES Component / Criteria',
            'GESComponent',
        ),
        Facet('feature', 'Feature', 'Feature'),
    )

    def base_conditions(self):
        """Keep only the latest reported file of each ``(country, schema)``.

        Mirrors ``db.latest_import_ids_2018``, which the legacy Article 9 form
        applied to the component table.
        """
        inner = self.reported.alias('ri_latest')
        latest = (
            select(func.max(inner.c.Id))
            .group_by(inner.c.CountryCode, inner.c.Schema)
        )

        return [self.mapper.c['ImportId'].in_(latest)]

    def serialize_row(self, row):
        out = super(Article9Cycle2018Provider, self).serialize_row(row)
        cell = self.region_cell(row)

        if cell is not None:
            out['Region'] = cell

        return out
