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
    # TODO: check if x is 0, consider it True
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


        # TODO: filter by descriptor

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
    # TODO: this is hard to implement
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

        self.import_data, self.target_data = self.get_base_data()
        self.features_data = self.get_features_data()

        allrows = [
            self.get_countries_row(),
            self.get_marine_unit_id_nrs(),
            self.get_threshold_value(),
            self.get_reference_point_type(),
            self.get_baseline(),
            self.get_proportion(),
            self.get_type_of_target(),
            self.get_timescale(),
            self.get_interim_of_ges(),
            self.get_compatibility(),
            self.get_physical_features(),
            self.get_predominant_habitats(),
            self.get_functional_groups(),
            self.get_pressures(),
        ]

        return self.template(rows=allrows)

    def get_base_data(self):
        imp = sql.MSFD10Import
        target = sql.MSFD10Target

        count, import_res = db.get_all_records(
            imp,
            imp.MSFD10_Import_ReportingCountry.in_(self.countries),
            imp.MSFD10_Import_ReportingRegion == self.region
        )
        import_ids = [x.MSFD10_Import_ID for x in import_res]

        count, target_res = db.get_all_records(
            target,
            target.MSFD10_Targets_Import.in_(import_ids),
            target.Topic == 'EnvironmentalTarget'
        )

        return import_res, target_res

    def create_feature_row(self, label_name):
        results = []

        row = Row('', results)

        return CompoundRow(label_name, [row])

    def get_features_data(self):
        feat = sql_extra.MSFD10FeaturePressures
        target_ids = [x.MSFD10_Target_ID for x in self.target_data]

        count, feat_res = db.get_all_records(
            feat,
            feat.MSFD10_Target.in_(target_ids),
        )

        return feat_res

    def create_base_row(self, label_name, attr_name):
        results = []

        for country in self.countries:
            import_id = 0
            for imp in self.import_data:
                if imp.MSFD10_Import_ReportingCountry == country:
                    import_id = imp.MSFD10_Import_ID
                    break

            value = ''
            if not import_id:
                results.append(value)
                continue

            for tar in self.target_data:
                if tar.MSFD10_Targets_Import == import_id:
                    value = getattr(tar, attr_name, '')
                    break

            results.append(value)

        row = Row('', results)

        return CompoundRow(label_name, [row])

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        row = Row('Number used',
                  [len(self.all_countries[c]) for c in self.countries])

        return CompoundRow('MarineUnitID', [row])

    def get_threshold_value(self):
        pass

    def get_reference_point_type(self):
        label = 'Reference point type'
        attr = 'ReferencePointType'

        return self.create_base_row(label, attr)

    def get_baseline(self):
        label = 'Baseline'
        attr = 'Baseline'

        return self.create_base_row(label, attr)

    def get_proportion(self):
        label = 'Proportion'
        attr = 'Proportion'

        return self.create_base_row(label, attr)

    def get_type_of_target(self):
        label = 'Type of target/indicator'
        attr = 'TypeTargetIndicator'

        return self.create_base_row(label, attr)

    def get_timescale(self):
        label = 'Timescale'
        attr = 'TimeScale'

        return self.create_base_row(label, attr)

    def get_interim_of_ges(self):
        label = 'Interim or GES target'
        attr = 'InterimGESTarget'

        return self.create_base_row(label, attr)

    def get_compatibility(self):
        label = 'Compatibility with existing targets/indicators'
        attr = 'CompatibilityExistingTargets'

        return self.create_base_row(label, attr)

    def get_physical_features(self):
        label = 'Physical/chemical features'

        return self.create_feature_row(label)

    def get_predominant_habitats(self):
        label = 'Predominant habitats'

        return self.create_feature_row(label)

    def get_functional_groups(self):
        label = 'Functional groups'

        return self.create_feature_row(label)

    def get_pressures(self):
        label = 'Pressures'

        return self.create_feature_row(label)

