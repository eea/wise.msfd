
from collections import defaultdict

from eea.cache import cache
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, sql_extra
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.gescomponents import (get_descriptor, FEATURES_DB_2012,
                                     FEATURES_DB_2018)
from wise.msfd.utils import CompoundRow, ItemLabel, ItemList, Row, TableHeader

from .utils import (compoundrow, compoundrow2012, emptyline_separated_itemlist,
                    newline_separated_itemlist, get_percentage)
from .base import BaseRegDescRow, BaseRegComplianceView


def get_key(func, self):
    key = ":".join((
        func.__name__,
        'reg-desc',
        self.descriptor,
        ''.join(self.region),
        self.article
    ))

    return key


class RegDescA92018Row(BaseRegDescRow):
    year = '2018'

    @compoundrow
    def get_gescomp_row(self):
        rows = []
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []
            for country_code, country_name in self.countries:
                data = [
                    row.GESDescription
                    for row in self.db_data
                    if row.CountryCode == country_code
                       and (row.GESComponent == crit.id
                            or row.GESComponent.split('/')[0] == crit.id)
                       and row.Features
                ]
                value = self.not_rep
                if data:
                    # value = ItemList(set(data))
                    value = emptyline_separated_itemlist(data)

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
                # value = NewlineSeparatedItemList(data)
                value = emptyline_separated_itemlist(data)
                # value = u"".join(set(data))

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
                value = emptyline_separated_itemlist(data)

            values.append(value)

        rows.append((u'', values))

        return rows


class RegDescA92012(BaseRegComplianceView):
    session_name = '2012'
    year = "2012"
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    def __init__(self, context, request):
        super(RegDescA92012, self).__init__(context, request)
        self.region = context._countryregion_folder._subregions
        self._descriptor = context.descriptor

        db.threadlocals.session_name = self.session_name

        self.countries = [
            x[0] for x in context._countryregion_folder._countries_for_region
        ]
        self.all_countries = muids_by_country(self.region)
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries.get(c, []))

        self.allrows = [
            self.compoundrow2012('Member state', self.get_countries_row()),
            self.compoundrow2012('Marine reporting units',
                                 self.get_reporting_area_row()),
            self.compoundrow2012('Features',
                                 self.get_features_reported_row()),
            self.compoundrow2012('GES description',
                                 self.get_gescomponents_row()),
            self.compoundrow2012('Threshold values',
                                 self.get_threshold_values()),
            self.compoundrow2012(
                'Proportion of area to achieve threshold values',
                self.get_proportion_values()
            ),
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

    @cache(get_key)
    def get_proportion_values(self):
        t = sql.MSFD9Descriptor
        descriptor = self.descriptor_obj
        criterions = descriptor.all_ids()

        values = []

        for c in self.countries:
            muids = self.all_countries.get(c, [])
            count, data = db.get_all_records(
                t,
                t.MarineUnitID.in_(muids),
                t.ReportingFeature.in_(criterions)
                # raw=True
            )

            props = [x.Proportion for x in data if x.Proportion]
            percentage = count and (len(props) / float(count)) * 100 or 0.0
            min_ = props and min(props) or 0
            max_ = props and max(props) or 0
            value = u"{:0.1f}% ({} - {})".format(percentage, min_, max_)

            values.append(value)

        rows = [('% of criteria with values (range of values reported)',
                 values)]

        return rows
        # return RegionalCompoundRow('Proportion', rows)

    @cache(get_key)
    def get_threshold_values(self):
        t = sql.MSFD9Descriptor
        descriptor = self.descriptor_obj
        criterions = descriptor.all_ids()

        values = []

        for c in self.countries:
            muids = self.all_countries.get(c, [])
            count, data = db.get_all_records(
                t,
                t.MarineUnitID.in_(muids),
                t.ReportingFeature.in_(criterions)
            )

            threshs = len([x for x in data if x.ThresholdValue])
            percentage = count and (threshs / float(count)) * 100 or 0.0
            value = u"{:0.1f}% ({})".format(percentage, count)

            values.append(value)

        rows = [('% of criteria with values (no. of criteria)', values)]

        return rows
        # return RegionalCompoundRow('Threshold value(s)', rows)

    def get_countries_row(self):
        rows = [('', self.countries)]

        return rows
        # return RegionalCompoundRow('Member state', rows)

    @cache(get_key)
    def get_gescomponents_row(self):
        t = sql.MSFD9Descriptor

        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        rows = []

        for crit in criterions:
            crit_ids = crit.all_ids()

            if crit.is_descriptor():
                crit_ids = [crit.id]

            values = []

            for country in self.countries:
                muids = self.all_countries.get(country, [])
                data = db.get_unique_from_mapper(
                    t,
                    'DescriptionGES',
                    t.ReportingFeature.in_(crit_ids),
                    t.MarineUnitID.in_(muids)
                )
                value = self.not_rep
                if data:
                    value = emptyline_separated_itemlist(data)

                values.append(value)

            row = (crit.title, values)
            rows.append(row)

        return rows
        # return RegionalCompoundRow('GES component [Reporting feature]', rows)

    @cache(get_key)
    def get_reporting_area_row(self):
        rows = [
            ('Number used',
             [len(self.all_countries.get(c, [])) for c in self.countries])
        ]

        return rows
        # return RegionalCompoundRow('Reporting area(s)[MarineUnitID]', rows)

    @cache(get_key)
    def get_features_reported_row(self):
        themes_fromdb = FEATURES_DB_2012

        t = sql_extra.MSFD9Feature
        all_features = sorted(db.get_unique_from_mapper(
            t,
            'FeaturesPressuresImpacts',
            t.ReportingFeature == self.descriptor,
        ))

        rows = []
        all_themes = defaultdict(list)
        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme/Unknown'].append(feature)
                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        for theme, feats in all_themes.items():
            values = []

            for country in self.countries:
                value = []
                muids = self.all_countries.get(country, [])

                for feature in feats:
                    count = db.count_items(
                        t.FeaturesPressuresImpacts,
                        t.FeaturesPressuresImpacts == feature,
                        t.MarineUnitID.in_(muids)
                    )
                    if not count:
                        continue

                    val = u"{} ({})".format(feature, count)
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

            return rows
            # return RegionalCompoundRow('Feature(s) reported [Feature]', rows)
