# pylint: skip-file
"""Article 19.3 "Datasets used" -- 2012 Article 19.3 information type.

Reads the pair of legacy tables the 2012 form uses:

* ``MetadataFeatures`` -- one row per filed dataset record (the result grain),
  carrying the marine reporting unit, the reporting feature, the dataset
  record / link, the metadata standard, the date stamp and the language;
* ``MetadataArt19_3`` -- the reporting metadata (country), keyed by
  ``IdMetadataArt19_3``. Its ``Country`` code is right padded, so it is trimmed
  on the wire.

The Region/Subregion filter and cell are derived from the Article 4 marine
units (``MSFD4_GegraphicalAreasID``), which maps each ``MarineUnitID`` to its
``RegionSubRegions``.
"""
from __future__ import absolute_import

from sqlalchemy import func, or_, select

from wise.msfd import sql
from wise.msfd.explorer.providers.article19_base import (
    Article19DatasetsProvider)
from wise.msfd.explorer.providers.base import Column, Facet
from wise.msfd.explorer.providers.regions import MruRegionFacet
from wise.msfd.explorer.serializers import country_label

INFORMATION_TYPE = '2012 Article 19.3'


class Article19Cycle2012Provider(Article19DatasetsProvider):
    """Datasets reported under Article 19.3 for the 2012 exercise."""

    cycle = '2012'
    cycle_label = INFORMATION_TYPE
    cycle_display = INFORMATION_TYPE
    session_name = '2012'

    # Injectable source tables: tests point them at an in-memory database.
    features = sql.t_MetadataFeatures
    metadata = sql.MetadataArt193.__table__

    #: Article 4 MRU publication used to derive the region of each MRU.
    region_mru_table = sql.t_MSFD4_GegraphicalAreasID
    region_mru_id_column = 'MarineUnitID'
    region_region_column = 'RegionSubRegions'
    region_mru_column = 'MarineUnitID'

    order_by = ('CountryCode', 'MarineUnitID')

    #: Country codes the legacy 2012 form never offered, and therefore never
    #: displayed. They are landlocked reporting placeholders rather than
    #: marine Member States: ``a19_member_states`` in ``search/vocabulary.py``
    #: built the country filter with ``mc.Country.not_in(['At', 'HU'])``, and
    #: the display form could only ever be reached through that filter.
    #:
    #: The exclusion matters for the data as filed. ``MetadataArt19_3`` row
    #: ``Id=12`` is stored as ``Country='AT'``, yet every one of its 338
    #: ``MetadataFeatures`` children carries an Italian marine reporting unit
    #: (``IT-AS-*`` / ``IT-MS-*``) and Italian dataset links -- the country
    #: code is wrong in the source database. There is no ``IT`` metadata row
    #: to join to, so dropping ``AT`` reproduces the legacy explorer (which
    #: never surfaced those rows as Austria) instead of mislabelling 338
    #: Italian datasets as Austrian.
    excluded_countries = ('AT', 'HU')

    def base_conditions(self):
        """Drop the landlocked placeholder countries the legacy form hid.

        ``base_conditions`` is folded into both the results query and each
        facet's cross-filtered option counts, so excluding the country here
        also keeps it out of the Country facet. Rows whose metadata row is
        missing (``CountryCode`` is ``NULL``) are kept, matching the outer
        join above.
        """
        country = self.mapper.c['CountryCode']

        return [or_(country.is_(None),
                    ~country.in_(self.excluded_countries))]

    def __init__(self, *args, **kwargs):
        features = self.features
        metadata = self.metadata

        self.mapper = select(
            features.c.MarineUnitID.label('MarineUnitID'),
            features.c.ReportingFeature.label('ReportingFeature'),
            features.c.DatasetRecord.label('DatasetRecord'),
            features.c.DatasetLink.label('DatasetLink'),
            features.c.MetadataStandard.label('MetadataStandard'),
            features.c.DateStamp.label('DateStamp'),
            features.c.Language.label('Language'),
            func.rtrim(metadata.c.Country).label('CountryCode'),
        ).select_from(
            features.outerjoin(
                metadata,
                features.c.IdMetadataArt19_3 == metadata.c.Id,
            )
        ).subquery()

        super(Article19Cycle2012Provider, self).__init__(*args, **kwargs)

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
            'MarineUnitID',
            'Marine Reporting Unit',
            'MarineUnitID',
            format='mru',
            min_width=200,
        ),
        Column(
            'ReportingFeature',
            'Reporting feature',
            'ReportingFeature',
            min_width=200,
        ),
        Column(
            'DatasetRecord',
            'Dataset record',
            'DatasetRecord',
            expandable=True,
            min_width=250,
        ),
        Column('DatasetLink', 'Dataset link', 'DatasetLink', min_width=220),
        Column(
            'MetadataStandard',
            'Metadata standard',
            'MetadataStandard',
            min_width=160,
        ),
        Column('DateStamp', 'Date stamp', 'DateStamp', min_width=140),
        Column('Language', 'Language', 'Language', min_width=100),
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
            mru_column='MarineUnitID',
            packed=False,
        ),
    )
