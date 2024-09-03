#pylint: skip-file
from __future__ import absolute_import
from itertools import chain

from collections import Counter, defaultdict

from sqlalchemy import or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, sql_extra
from wise.msfd.data import muids_by_country
from wise.msfd.gescomponents import FEATURES_DB_2012, get_ges_component
from wise.msfd.translation import get_translated
from wise.msfd.utils import fixedorder_sortkey

from .base import BaseRegComplianceView, BaseRegDescRow
from .utils import (compoundrow, compoundrow2012, newline_separated_itemlist,
                    simple_itemlist)


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
                vals = [get_ges_component(x).title for x in chain(*data)]
                counted = Counter(vals)
                crits = [u'{} ({})'.format(k, v) for k, v in counted.items()]

                value = simple_itemlist(crits)

            values.append(value)

        rows.append(('', values))

        return rows

    @compoundrow
    def get_target_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            data = set([
                row.TargetCode

                for row in self.db_data

                if row.CountryCode == country_code
                and row.TargetCode
            ])
            value = self.not_rep

            if data:
                value = len(data)

            values.append(value)

        rows.append(('Number defined', values))

        return rows

    @compoundrow
    def get_targetcode_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = []
            translated = []
            data = [
                (row.TargetCode, row.Description)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.TargetCode
            ]

            if not data:
                values.append(self.not_rep)

                continue

            for row in set(data):
                target_code = row[0]
                description = row[1]

                transl = get_translated(description, country_code) or ''

                value.append(u"<b>{}</b>: {}".format(target_code, description))
                translated.append(u"<b>{}</b>: {}".format(target_code, transl))

            values.append(
                ('<br>'.join(value), '<br>'.join(translated))
            )

        rows.append(('', values))

        return rows

    @compoundrow
    def get_target_value_row(self):
        rows = []
        values = []

        display_options = ['Reported', 'Not reported']

        for country_code, country_name in self.countries:
            reports = {k: 0 for k in display_options}
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

            for k in display_options:
                v = reports[k]
                percentage = total and (v / float(total)) * 100 or 0

                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    k, v, percentage
                ))

            values.append(simple_itemlist(value, sort=False))

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

            values.append(simple_itemlist(value))

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
                ts_formatted = "{}-{}".format(timescale[0:4], timescale[4:])
                found = len([x for x in data if x == timescale])
                percentage = total and (found / float(total)) * 100 or 0

                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    ts_formatted, found, percentage
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
                upd_formatted = "{}-{}".format(updatedate[0:4], updatedate[4:])
                found = len([x for x in data if x == updatedate])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    upd_formatted, found, percentage
                ))

            values.append(newline_separated_itemlist(value))

        rows.append(('No. of targets per date', values))

        return rows

    @compoundrow
    def get_updatetype_row(self):
        rows = []
        values = []

        order = ['Same as 2012 definition', 'Modified from 2012 definition',
                 'New target']

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

            updatetypes = sorted(set(data),
                                 key=lambda t: fixedorder_sortkey(t, order))

            for updatetype in updatetypes:
                found = len([x for x in data if x == updatetype])
                percentage = total and (found / float(total)) * 100 or 0
                value.append(u"{0} ({1} - {2:0.1f}%)".format(
                    updatetype, found, percentage
                ))

            values.append(simple_itemlist(value, sort=False))

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
        self.region = context._countryregion_folder._subregions
        db.threadlocals.session_name = self.session_name

        self._descriptor = context.descriptor
        self.countries = [
            x[0] for x in context._countryregion_folder._countries_for_region
        ]
        self.all_countries = muids_by_country()
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries.get(c, []))

        self.import_data, self.target_data = self.get_base_data()
        self.features_data = self.get_features_data()

        self.allrows = [
            self.compoundrow2012('Member state', self.get_countries_row()),
            self.compoundrow2012('Marine reporting units',
                                 self.get_marine_unit_id_nrs()),
            self.compoundrow2012('Features', self.get_features_row()),
            self.compoundrow2012('Targets', self.get_targets_row()),
            self.compoundrow2012('Indicators', self.get_indicators_row()),
            self.compoundrow2012('Target/indicator values',
                                 self.get_target_indicators_row()),
            self.compoundrow2012('Proportion of area to achieve values',
                                 self.get_proportions_row()),
            self.compoundrow2012('Reference point type',
                                 self.get_reference_point_row()),
            self.compoundrow2012('Baseline', self.get_baseline_row()),
            self.compoundrow2012('Target/indicator type',
                                 self.get_target_indic_type_row()),
            self.compoundrow2012('Timescale',
                                 self.get_timescale_row()),
            self.compoundrow2012('Interim or GES target',
                                 self.get_interim_or_gestarget_row()),
            self.compoundrow2012(
                'Compatibility with existing targets/ indicators',
                self.get_compatibility_row()
            ),
        ]

    def get_countries_row(self):
        rows = [('', self.countries)]

        return rows
        # return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        rows = [
            ('Number used',
             [len(self.all_countries.get(c, [])) for c in self.countries])
        ]

        return rows
        # return CompoundRow('MarineUnitID', [row])

    def get_features_row(self):
        themes_fromdb = FEATURES_DB_2012
        rows = []
        feature_col = 'PhysicalChemicalHabitatsFunctionalPressures'

        all_features = set([
            getattr(r, feature_col)

            for r in self.features_data
        ])

        all_themes = defaultdict(list)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        for theme, feats in all_themes.items():
            values = []

            for country in self.countries:
                value = []
                muids = self.all_countries.get(country, [])

                for feature in feats:
                    data = [
                        r

                        for r in self.features_data

                        if r.MarineUnitID in muids
                        and getattr(r, feature_col) == feature
                    ]

                    if not data:
                        continue

                    val = u"{} ({})".format(feature, len(data))
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows

    def get_targets_row(self):
        rows = []
        values = []

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            value = len([
                row.ReportingFeature

                for row in self.target_data

                if row.Topic == 'EnvironmentalTarget'
                and row.MarineUnitID in muids
            ])

            if not value:
                value = self.not_rep

            values.append(value)

        rows.append(('Number used', values))

        return rows

    def get_indicators_row(self):
        rows = []
        values = []

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            value = len([
                row.ReportingFeature

                for row in self.target_data

                if row.Topic == 'AssociatedIndicator'
                and row.MarineUnitID in muids
            ])

            if not value:
                value = self.not_rep

            values.append(value)

        rows.append(('Number used', values))

        return rows

    def get_target_indicators_row(self):
        rows = []
        values = []

        types = [
            ('Targets', 'EnvironmentalTarget'),
            ('Indicators', 'AssociatedIndicator'),
        ]

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            value = []

            for label, topic in types:
                data = [
                    row.ThresholdValue

                    for row in self.target_data

                    if row.Topic == topic
                    and row.MarineUnitID in muids
                ]
                found = len([x for x in data if x])
                percentage = data and (found / float(len(data))) * 100 or 0.0
                value.append(u"{} - {} ({:0.1f}%)".format(
                    label, found, percentage)
                )

            values.append(newline_separated_itemlist(value))

        rows.append(('No. with quantitative values', values))

        return rows

    def get_proportions_row(self):
        rows = []
        values = []

        types = [
            ('Targets', 'EnvironmentalTarget'),
            ('Indicators', 'AssociatedIndicator'),
        ]

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            value = []

            for label, topic in types:
                data = [
                    row.Proportion

                    for row in self.target_data

                    if row.Topic == topic and row.MarineUnitID in muids
                        and row.Proportion is not None
                ]
                found = len([x for x in data if x])
                percentage = data and (found / float(len(data))) * 100 or 0.0
                min_ = data and min(data) or 0
                max_ = data and max(data) or 0

                value.append(u"{} - {} ({} {} - {:0.1f}%)".format(
                    min_, max_, found, label, percentage)
                )

            values.append(newline_separated_itemlist(value))

        rows.append(('Range of % values reported', values))

        return rows

    def get_reference_point_row(self):
        col_name = 'ReferencePointType'
        sub_label = 'No. per category'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def get_baseline_row(self):
        col_name = 'Baseline'
        sub_label = 'No. per category'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def get_target_indic_type_row(self):
        col_name = 'TypeTargetIndicator'
        sub_label = 'No. per category'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def get_timescale_row(self):
        col_name = 'TimeScale'
        sub_label = 'No. per time period'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def get_interim_or_gestarget_row(self):
        col_name = 'InterimGESTarget'
        sub_label = 'No. per category'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def get_compatibility_row(self):
        col_name = 'CompatibilityExistingTargets'
        sub_label = 'No. per category'

        return self._get_percentage_per_category_row(col_name, sub_label)

    def _get_percentage_per_category_row(self, col_name, sub_label):
        rows = []
        values = []

        types = [
            ('Targets', 'EnvironmentalTarget'),
            ('Indicators', 'AssociatedIndicator'),
        ]

        for country in self.countries:
            muids = self.all_countries.get(country, [])
            value = []

            for label, topic in types:
                data = [
                    getattr(row, col_name)

                    for row in self.target_data

                    if row.Topic == topic
                    and row.MarineUnitID in muids
                    and getattr(row, col_name)
                ]
                total = len(data)
                found_vals = set([x for x in data if x])

                for v in found_vals:
                    found = len([x for x in data if x == v])
                    percent = data and (found / float(total)) * 100 or 0.0

                    value.append(u"{} ({} {} - {:0.1f}%)".format(
                        v, found, label, percent)
                    )

            values.append(newline_separated_itemlist(value))

        rows.append((sub_label, values))

        return rows

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

    def get_base_data(self):
        imp = sql.MSFD10Import
        target = sql.MSFD10Target
        des_crit = sql_extra.MSFD10DESCrit

        descriptor = self.descriptor
        descriptor_code = descriptor[1:]

        count, import_data = db.get_all_records(
            imp,
            imp.MSFD10_Import_ReportingCountry.in_(self.countries),
            imp.MSFD10_Import_ReportingRegion.in_(self.region)
        )
        import_ids = [x.MSFD10_Import_ID for x in import_data]

        dc_indicator = getattr(des_crit, 'GESDescriptorsCriteriaIndicators')
        count, target_data = db.get_all_records_outerjoin(
            target,
            des_crit,
            target.MSFD10_Targets_Import.in_(import_ids),
            # TODO when dc_indicator is 'NotReported' it can't be matched
            # with the descriptor
            or_(dc_indicator == descriptor,
                dc_indicator.like('{}.%'.format(descriptor_code)))
        )

        return import_data, target_data

    def get_features_data(self):
        feat = sql_extra.MSFD10FeaturePressures
        target_ids = [x.MSFD10_Target_ID for x in self.target_data]

        count, feat_res = db.get_all_records(
            feat,
            feat.MSFD10_Target.in_(target_ids),
        )

        return feat_res
