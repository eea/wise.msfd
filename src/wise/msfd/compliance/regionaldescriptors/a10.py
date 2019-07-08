from collections import defaultdict
from itertools import chain
from sqlalchemy import or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, sql_extra
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.gescomponents import get_ges_component
from wise.msfd.utils import ItemLabel, ItemList

from .base import BaseRegDescRow, BaseRegComplianceView
from .utils import compoundrow, compoundrow2012, newline_separated_itemlist


class RegDescA102018Row(BaseRegDescRow):
    year = '2018'

    @compoundrow
    def get_gescomp_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.GESComponents.split(',')
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.GESComponents
            ]
            value = self.not_rep
            if data:
                vals = set([x for x in chain(*data)])
                crits = [
                    get_ges_component(c).title
                    for c in vals
                ]
                value = newline_separated_itemlist(crits)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_target_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = [
                row.TargetCode
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.TargetCode
            ]
            value = self.not_rep
            if data:
                value = len(data)

            values.append(value)

        rows.append(('Number defined', values))

        return rows

    @compoundrow
    def get_target_value_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            reports = {'Reported': 0, 'Not reported': 0}
            value = []
            data = [
                row.TargetValue
                for row in self.db_data
                if row.CountryCode == country_code
                    and (row.Parameter or row.Element)
            ]
            total = len(data)

            if not data:
                values.append(self.not_rep)
                continue

            for target_val in data:
                if target_val:
                    reports['Reported'] += 1
                    continue

                reports['Not reported'] += 1

            for k, v in reports.items():
                percentage = total and (v / float(total)) * 100 or 0

                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    k, v, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of parameters/elements with quantitative values',
                     values))

        return rows

    @compoundrow
    def get_targetstatus_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            tar_status_counter = defaultdict(int)
            value = []

            data = [
                row.TargetStatus
                for row in self.db_data
                if row.CountryCode == country_code
                   and (row.Parameter or row.Element)
            ]
            total = len(data)

            if not data:
                values.append(self.not_rep)
                continue

            for target_status in data:
                if not target_status:
                    tar_status_counter['Status not reported'] += 1
                    continue

                tar_status_counter[target_status] += 1

            for k, v in tar_status_counter.items():
                percentage = total and (v / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(k, v, percentage))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of assessments per category', values))

        return rows

    @compoundrow
    def get_assessmentperiod_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.AssessmentPeriod
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.AssessmentPeriod
            ]
            total = len(data)

            if not total:
                values.append(self.not_rep)
                continue

            for period in set(data):
                found = len([x for x in data if x == period])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    period, found, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of targets per period', values))

        return rows

    @compoundrow
    def get_timescale_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.TimeScale
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.TimeScale
            ]
            total = len(data)
            if not total:
                values.append(self.not_rep)
                continue

            for timescale in set(data):
                found = len([x for x in data if x == timescale])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    timescale, found, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of targets per date', values))

        return rows

    @compoundrow
    def get_updatedate_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.UpdateDate
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.UpdateDate
            ]
            total = len(data)

            if not total:
                values.append(self.not_rep)
                continue

            for updatedate in set(data):
                found = len([x for x in data if x == updatedate])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    updatedate, found, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of targets per date', values))

        return rows

    @compoundrow
    def get_updatetype_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            data = [
                row.UpdateType
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.UpdateType
            ]
            total = len(data)

            if not total:
                values.append(self.not_rep)
                continue

            for updatetype in set(data):
                found = len([x for x in data if x == updatetype])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    updatetype, found, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of targets per category', values))

        return rows

    @compoundrow
    def get_indicators_row(self):
        rows = []
        values = []
        for country_code, country_name in self.countries:
            data = set([
                row.Indicators
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.Indicators
            ])
            value = self.not_rep
            if data:
                value = len(data)

            values.append(value)

        rows.append(('No. of different indicators reported', values))

        return rows

    @compoundrow
    def get_measures_row(self):
        rows = []
        values = []
        for country_code, country_name in self.countries:
            data = set([
                row.Measures
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.Measures
            ])
            value = self.not_rep
            if data:
                value = len(data)

            values.append(value)

        rows.append(('No. of different measures reported', values))

        return rows


class RegDescA102012(BaseRegComplianceView):
    # TODO: this is hard to implement
    session_name = '2012'
    year = "2012"
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    def __init__(self, context, request):
        super(RegDescA102012, self).__init__(context, request)
        self.region = context.country_region_code
        db.threadlocals.session_name = self.session_name

        self._descriptor = context.descriptor
        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        self.import_data, self.target_data = self.get_base_data()
        self.features_data = self.get_features_data()

        self.allrows = [
            self.compoundrow2012('Member state', self.get_countries_row()),
            self.compoundrow2012('MarineUnitID', self.get_marine_unit_id_nrs()),
            self.compoundrow2012('Threshold value [TargetValue]',
                                 self.get_threshold_value()),
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

    def __call__(self):
        return self.template(rows=self.allrows)

    @property
    def descriptor(self):
        descriptor = self._descriptor
        if descriptor.startswith("D1."):
            descriptor = "D1"

        return descriptor

    @property
    def available_countries(self):
        return [(x, x) for x in self.countries]

    def compoundrow2012(self, title, rows):
        return compoundrow2012(self, title, rows)

    def get_import_id(self, country):
        for imp in self.import_data:
            if imp.MSFD10_Import_ReportingCountry == country:
                import_id = imp.MSFD10_Import_ID

                return import_id

        return 0

    def get_base_data(self):
        imp = sql.MSFD10Import
        target = sql.MSFD10Target
        des_crit = sql_extra.MSFD10DESCrit

        descriptor = self.descriptor
        descriptor_code = descriptor[1:]

        count, import_data = db.get_all_records(
            imp,
            imp.MSFD10_Import_ReportingCountry.in_(self.countries),
            imp.MSFD10_Import_ReportingRegion == self.region
        )
        import_ids = [x.MSFD10_Import_ID for x in import_data]

        dc_indicator = getattr(des_crit, 'GESDescriptorsCriteriaIndicators')
        count, target_data = db.get_all_records_outerjoin(
            target,
            des_crit,
            target.MSFD10_Targets_Import.in_(import_ids),
            target.Topic == 'EnvironmentalTarget',
            or_(dc_indicator == descriptor,
                dc_indicator.like('{}.%'.format(descriptor_code)))
        )

        return import_data, target_data

    def create_base_row(self, label_name, attr_name):
        results = []

        for country in self.countries:
            import_id = self.get_import_id(country)

            value = ''

            if not import_id:
                results.append(value)

                continue

            for tar in self.target_data:
                if tar.MSFD10_Targets_Import == import_id:
                    value = getattr(tar, attr_name, '')

                    break

            results.append(value)

        rows = [('', results)]

        return self.compoundrow2012(label_name, rows)

    def get_features_data(self):
        feat = sql_extra.MSFD10FeaturePressures
        target_ids = [x.MSFD10_Target_ID for x in self.target_data]

        count, feat_res = db.get_all_records(
            feat,
            feat.MSFD10_Target.in_(target_ids),
        )

        return feat_res

    def create_feature_row(self, label_name):
        rows = []

        features = []

        for row in self.features_data:
            if row.FeatureType == label_name:
                val = row.PhysicalChemicalHabitatsFunctionalPressures
                features.append(val)

                val_other = row.Other

                if val_other:
                    features.append(val_other)

        features = sorted(set(features))

        for feature in features:
            results = []

            for country in self.countries:
                import_id = self.get_import_id(country)

                value = ''

                if not import_id:
                    import pdb; pdb.set_trace()
                    # results.append(value)
                    # continue

                target_ids = []

                for tar in self.target_data:
                    if tar.MSFD10_Targets_Import == import_id:
                        target_ids.append(tar.MSFD10_Target_ID)

                for r in self.features_data:
                    if r.MSFD10_Target not in target_ids:
                        continue

                    if r.FeatureType != label_name:
                        continue

                    feat = r.PhysicalChemicalHabitatsFunctionalPressures

                    if feat == feature or r.Other == feature:
                        value = 'Reported'

                        break

                results.append(value)

            row = (feature, results)
            rows.append(row)

        return self.compoundrow2012(label_name, rows)

    def get_countries_row(self):
        rows = [('', self.countries)]

        return rows
        # return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        rows = [
            ('Number used',
             [len(self.all_countries[c]) for c in self.countries])
        ]

        return rows
        # return CompoundRow('MarineUnitID', [row])

    # TODO how to implement this
    def get_threshold_value(self):
        results = ['Not implemented'] * len(self.countries)
        rows = [('Quantitative values provided', results)]

        return rows
        # return CompoundRow('Threshold value [TargetValue]', [row] )

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
        label = 'Functional group'

        return self.create_feature_row(label)

    def get_pressures(self):
        label = 'Pressures'

        return self.create_feature_row(label)
