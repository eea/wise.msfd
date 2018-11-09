from collections import defaultdict

from eea.cache import cache
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from wise.msfd import db, sql, sql_extra
from wise.msfd.gescomponents import get_ges_criterions

from ..base import BaseComplianceView

# TODO: AreaType for each record can be AA_AssessmentArea, SR_SubRegion and
# so on. Which one we use?


def get_percentage(values):
    """ Compute percentage of true-ish values in the list
    """
    trues = len([x for x in values if x])

    return (trues * 100.0) / len(values)


class TemplateMixin:
    template = None

    def __call__(self):
        return self.template(**self.__dict__)


class List(TemplateMixin):
    template = PageTemplateFile('pt/list.pt')

    def __init__(self, rows):
        self.rows = rows


class CompoundRow(TemplateMixin):
    multi_row = PageTemplateFile('pt/compound-row.pt')
    one_row = PageTemplateFile('pt/compound-one-row.pt')

    @property
    def template(self):
        if self.rowspan > 1:
            return self.multi_row

        return self.one_row

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows
        self.rowspan = len(rows)


class Row(TemplateMixin):
    template = PageTemplateFile('pt/simple-row.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class TableHeader(TemplateMixin):
    template = PageTemplateFile('pt/table-header.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


def get_key(func, self):
    return self.descriptor + ':' + self.region


class RegDescA9(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.region = 'BAL'

        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        allrows = [
            self.get_countries_row(),
            self.get_reporting_area_row(),
            self.get_features_reported_row(),
            self.get_gescomponents_row(),
            self.get_threshold_values(),
            self.get_proportion_values(),
        ]

        return self.template(rows=allrows)

    @cache(get_key)
    def get_proportion_values(self):
        t = sql.MSFD9Descriptor

        values = []

        for c in self.countries:
            muids = self.all_countries[c]
            count, props = db.get_all_records(
                t,
                t.MarineUnitID.in_(muids),
                raw=True
            )
            vs = [x.Proportion for x in props]
            v = '{:.2f}%'.format(get_percentage(vs))
            # TODO: need to change the percentage to labels based on ranges
            values.append(v)
            # List(props)

        row = Row('Quantitative values reported', values)

        return CompoundRow('Proportion', [row])

    @cache(get_key)
    def get_threshold_values(self):
        t = sql.MSFD9Descriptor

        values = []

        for c in self.countries:
            muids = self.all_countries[c]
            threshs = db.get_unique_from_mapper(
                t,
                'ThresholdValue',
                t.MarineUnitID.in_(muids),
            )
            # TODO: needs to interpret values, instead of listing
            values.append(List(threshs))

        row = Row('Quantitative values reported', values)

        return CompoundRow('Threshold value(s)', [row])

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    @cache(get_key)
    def get_gescomponents_row(self):
        t = sql_extra.MSFD9Feature
        ges = get_ges_criterions(self.descriptor)

        rows = []

        for crit in ges:
            crit_ids = crit.all_ids()
            values = []

            for country in self.countries:
                muids = self.all_countries[country]
                count = db.count_items(
                    t.ReportingFeature,
                    t.ReportingFeature.in_(crit_ids),
                    t.MarineUnitID.in_(muids)
                )
                has = bool(count)
                values.append(has and 'Reported' or '')

            row = Row(crit.title, values)
            rows.append(row)

        return CompoundRow(
            'GES component [Reporting feature]',
            rows
        )

    @cache(get_key)
    def get_reporting_area_row(self):
        row = Row('Number of MRUs used',
                  [len(self.all_countries[c]) for c in self.countries])

        return CompoundRow('Reporting area(s)[MarineUnitID]', [row])

    # TODO: this takes a long time to generate, it needs caching
    @cache(get_key)
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

        return CompoundRow('Feature(s) reported [Feature]', rows)


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


class RegDescA11(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.region = 'BAL'

        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        allrows = [
            self.get_countries_row(),
            self.get_elements_monitored(),
        ]

        return self.template(rows=allrows)

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    def get_elements_monitored(self):
        # MONSub = sql_extra.MSFD11MONSub
        all_elements = get_monitored_elements(self.countries)

        for el in all_elements:
            print el.Q9a_ElementMonitored

        rows = []

        return CompoundRow(
            'Elements monitored',
            rows
        )


@db.use_db_session('2012')
def get_monitored_elements(countryids):
    MS = sql.MSFD11MONSub
    EM = sql.MSFD11Q9aElementMonitored
    SP = sql.MSFD11SubProgramme

    sess = db.session()
    q = sess.query(EM)\
        .filter(EM.SubProgramme == SP.ID)\
        .filter(SP.ID == MS.SubProgramme)\
        .filter(MS.MemberState.in_(countryids))

    return q.all()


class RegDescA10(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.region = 'BAL'

        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        allrows = [
            self.get_countries_row(),
            self.get_threshold_value(),
        ]

        return self.template(rows=allrows)

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    def get_threshold_value(self):
        pass
