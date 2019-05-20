
from eea.cache import cache
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, sql_extra
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.gescomponents import get_descriptor
from wise.msfd.utils import CompoundRow, ItemLabel, ItemList, Row, TableHeader

from .utils import get_percentage, compoundrow
from .base import BaseRegDescRow


def get_key(func, self):
    return self.descriptor + ':' + self.region


class RegDescA92018Row(BaseRegDescRow):
    """"""
    @compoundrow
    def get_gescomp_row(self):
        rows = []
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and (row.GESComponent == crit.id
                            or row.GESComponent.split('/')[0] == crit.id)
                       and row.Features
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            rows.append((ItemLabel(crit.id, crit.title), values))

        return rows

    @compoundrow
    def get_justif_nonuse_row(self):
        rows = []
        values = []
        for country_code, country_name in self.countries:
            data = set([
                u": ".join((row.GESComponent, row.JustificationNonUse))
                for row in self.db_data
                if row.CountryCode == country_code
                   and row.JustificationNonUse
            ])
            value = self.not_rep
            if data:
                value = ItemList(data)

            values.append(value)

        rows.append((u'', values))

        return rows

    @compoundrow
    def get_justif_delay_row(self):
        rows = []
        values = []
        for country_code, country_name in self.countries:
            data = set([
                u": ".join((row.GESComponent, row.JustificationDelay))
                for row in self.db_data
                if row.CountryCode == country_code
                    and row.JustificationDelay
            ])
            value = self.not_rep
            if data:
                value = ItemList(data)

            values.append(value)

        rows.append((u'', values))

        return rows


class RegDescA9(BrowserView):
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
            # ItemList(props)

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
            values.append(ItemList(threshs))

        row = Row('Quantitative values reported', values)

        return CompoundRow('Threshold value(s)', [row])

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    @cache(get_key)
    def get_gescomponents_row(self):
        t = sql_extra.MSFD9Feature
        criterions = get_descriptor(self.descriptor).criterions

        rows = []

        for crit in criterions:
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
