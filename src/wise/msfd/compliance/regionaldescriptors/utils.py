from collections import defaultdict, namedtuple

# TODO: AreaType for each record can be AA_AssessmentArea, SR_SubRegion and
# so on. Which one we use?
from eea.cache import cache
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql_extra

from ..base import BaseComplianceView

CompoundRow = namedtuple('CompoundRow', ['title', 'rows', 'rowspan'])
Row = namedtuple('Row', ['title', 'values'])


def f():
    import pdb; pdb.set_trace()


class RegDescDemo(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-2col-header.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.countries = countries_in_region('BAL')
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        allrows = [
            self.get_reporting_area_row(),
            self.get_features_reported_row(),
        ]

        return self.template(rows=allrows)

    @cache(f)
    def get_reporting_area_row(self):
        row = Row('Number of MRUs used',
                  [len(self.all_countries[c]) for c in self.countries])
        rows = [row]

        return CompoundRow('Reporting area(s)[MarineUnitID]', rows, 1)

    # TODO: this takes a long time to generate, it needs caching
    def get_features_reported_row(self):
        t = sql_extra.MSFD9Feature
        all_features = sorted(db.get_unique_from_mapper(
            t,
            'FeaturesPressuresImpacts',
            t.ReportingFeature == self.descriptor,
        ))

        rows = []

        for feature in all_features:
            values = []

            for country in self.countries:
                muids = self.all_countries[country]
                count = db.count_items(
                    t.FeaturesPressuresImpacts,
                    t.FeaturesPressuresImpacts == feature,
                    t.MarineUnitID.in_(muids)
                )
                has = bool(count)
                values.append(has and 'Reported' or '')

            row = Row(feature, values)
            rows.append(row)

        return CompoundRow('Feature(s) reported [Feature]', rows, len(rows))


@db.use_db_session('2012')
def all_regions():
    """ Return a list of region ids
    """

    return db.get_unique_from_mapper(
        sql_extra.MSFD4GeographicalAreaID,
        'RegionSubRegions'
    )


@db.use_db_session('2012')
def countries_in_region(regionid):
    """ Return a list of (<countryid>, <marineunitids>) pairs
    """
    t = sql_extra.MSFD4GeographicalAreaID

    return db.get_unique_from_mapper(
        t,
        'MemberState',
        t.RegionSubRegions == regionid
     )


@db.use_db_session('2012')
def muids_by_country():
    t = sql_extra.MSFD4GeographicalAreaID
    count, records = db.get_all_records(t)
    res = defaultdict(list)

    for rec in records:
        res[rec.MemberState].append(rec.MarineUnitID)

    return dict(**res)
