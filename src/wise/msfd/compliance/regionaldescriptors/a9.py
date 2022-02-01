
from __future__ import absolute_import
from collections import Counter, defaultdict
from itertools import chain

from eea.cache import cache
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, sql_extra
from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from wise.msfd.data import muids_by_country
from wise.msfd.gescomponents import (FEATURES_DB_2012, FEATURES_DB_2018,
                                     SUBJECT_2018_ORDER, THEMES_2018_ORDER,
                                     get_features)
from wise.msfd.translation import get_translated
from wise.msfd.utils import ItemLabel, current_date, fixedorder_sortkey

from .base import BaseRegComplianceView, BaseRegDescRow
from .utils import (compoundrow, compoundrow2012, emptyline_separated_itemlist,
                    get_nat_desc_country_url, multilinerow,
                    newline_separated_itemlist, simple_itemlist)


def get_key(func, self):
    key = ":".join((
        func.__name__,
        'reg-desc',
        self.descriptor,
        ''.join(self.region),
        self.article,
        current_date()
    ))

    return key


class RegDescA92018Row(BaseRegDescRow):
    year = '2018'

    @multilinerow
    def get_feature_row(self):
        all_features_reported = self.get_unique_values("Features")
        themes_fromdb = FEATURES_DB_2018

        rows = []
        all_features = []
        all_themes = defaultdict(list)

        for feat in all_features_reported:
            all_features.extend(feat.split(','))
        all_features = sorted(set(all_features))

        ok_features = all_features

        if self.descriptor.startswith('D1') and '.' in self.descriptor:
            ok_features = set([f.name for f in get_features(self.descriptor)])

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No subject: No theme'].append(feature)

                continue

            subject_and_theme = "{}: {}".format(
                themes_fromdb[feature].subject, themes_fromdb[feature].theme)
            all_themes[subject_and_theme].append(feature)

        # First sort by THEME
        all_themes = sorted(
            list(all_themes.items()),
            key=lambda t: fixedorder_sortkey(t[0].split(': ')[1],
                                             THEMES_2018_ORDER)
        )

        # Second sort by SUBJECT
        all_themes = sorted(
            all_themes,
            key=lambda t: fixedorder_sortkey(t[0].split(': ')[0],
                                             SUBJECT_2018_ORDER)
        )

        for subject_and_theme, feats in all_themes:
            for feature in feats:
                if feature not in ok_features:
                    continue

                values = []
                feature_label = self.get_label_for_value(feature)

                for country_code, country_name in self.countries:
                    value = []
                    data = [
                        row.GESComponent

                        for row in self.db_data

                        if row.CountryCode == country_code
                        and row.Features
                           and feature in row.Features.split(',')
                    ]

                    count_gescomps = Counter(data)

                    if count_gescomps:
                        value = [
                            u'{} ({})'.format(k, v)
                            for k, v in count_gescomps.items()
                        ]

                    values.append(simple_itemlist(value))

                rows.append((subject_and_theme, feature_label, values))

        return rows

    @compoundrow
    def get_gescomp_row(self):
        rows = []
        descriptor = self.descriptor_obj
        criterions = [descriptor] + descriptor.sorted_criterions()

        for crit in criterions:
            values = []

            for country_code, country_name in self.countries:
                orig = []
                translated = []
                data = set([
                    row.GESDescription

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and (row.GESComponent == crit.id
                         or row.GESComponent.split('/')[0] == crit.id)
                    and row.Features
                ])

                if not data:
                    values.append(self.not_rep)

                    continue

                for ges_descr in data:
                    transl = get_translated(ges_descr, country_code) or ''

                    orig.append(ges_descr)
                    translated.append(transl)

                value = (emptyline_separated_itemlist(orig),
                         emptyline_separated_itemlist(translated))

                values.append(value)

            rows.append((ItemLabel(crit.id, crit.title), values))

        return rows

    @compoundrow
    def get_determination_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            dates = defaultdict(set)

            for row in self.db_data:
                if row.CountryCode != country_code:
                    continue

                determination_date = row.DeterminationDate

                if not determination_date:
                    continue

                d_date = "{}-{}".format(determination_date[:4],
                                        determination_date[-2:])

                ges_comp = row.GESComponent

                dates[d_date].add(ges_comp)

            value = ''

            if dates:
                value = [
                    "{} ({})".format(k, ', '.join(v))
                    for k, v in dates.items()
                ]

            values.append(simple_itemlist(value))

        rows.append((u'', values))

        return rows

    @compoundrow
    def get_updatetype_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            dates = defaultdict(set)

            for row in self.db_data:
                if row.CountryCode != country_code:
                    continue

                update_type = row.UpdateType

                if not update_type:
                    continue

                ges_comp = row.GESComponent

                dates[update_type].add(ges_comp)

            value = ''

            if dates:
                value = [
                    "{} ({})".format(k, ', '.join(v))
                    for k, v in dates.items()
                ]

            values.append(simple_itemlist(value))

        rows.append((u'', values))

        return rows

    @compoundrow
    def get_justif_nonuse_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            orig = []
            translated = []
            data = set([
                (row.GESComponent, row.JustificationNonUse)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.JustificationNonUse
            ])

            if not data:
                values.append(self.not_rep)

                continue

            for row in data:
                ges_comp = row[0]
                justification = row[1]
                transl = get_translated(justification, country_code)

                orig.append(u'{}: {}'.format(ges_comp, justification))
                translated.append(u'{}: {}'.format(ges_comp, transl))

            value = (emptyline_separated_itemlist(orig),
                     emptyline_separated_itemlist(translated))

            values.append(value)

        rows.append((u'', values))

        return rows

    @compoundrow
    def get_justif_delay_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            orig = []
            translated = []
            data = set([
                (row.GESComponent, row.JustificationDelay)

                for row in self.db_data

                if row.CountryCode == country_code
                and row.JustificationDelay
            ])

            if not data:
                values.append(self.not_rep)

                continue

            for row in data:
                ges_comp = row[0]
                justification = row[1]
                transl = get_translated(justification, country_code)

                orig.append(u'{}: {}'.format(ges_comp, justification))
                translated.append(u'{}: {}'.format(ges_comp, transl))

            value = (emptyline_separated_itemlist(orig),
                     emptyline_separated_itemlist(translated))

            values.append(value)

        rows.append((u'', values))

        return rows


class RegDescA92012(BaseRegComplianceView):
    session_name = '2012'
    year = "2012"
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    def __init__(self, context, request):
        super(RegDescA92012, self).__init__(context, request)
        # confusing naming, self.region is a list of regions
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

        _translatables = [
            'GES description'
        ]

        self.TRANSLATABLES.extend(_translatables)

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

    @cache(get_key, dependencies=['translation'])
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

    @cache(get_key, dependencies=['translation'])
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
        url = self.request['URL0']

        reg_main = self._countryregion_folder.id.upper()
        subregions = [r.subregions for r in REGIONAL_DESCRIPTORS_REGIONS
                      if reg_main in r.code]

        rows = []
        country_names = []

        # rows = [('', self.countries)]

        for country in self.countries:
            value = []
            regions = [r.code for r in REGIONAL_DESCRIPTORS_REGIONS
                       if len(r.subregions) == 1 and country in r.countries
                       and r.code in subregions[0]]

            for r in regions:
                value.append(get_nat_desc_country_url(url, reg_main,
                                                      country, r))

            final = '{} ({})'.format(country, ', '.join(value))
            country_names.append(final)

        rows.append(('', country_names))

        return rows
        # return RegionalCompoundRow('Member state', rows)

    @cache(get_key, dependencies=['translation'])
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
                orig = []
                translated = []

                muids = self.all_countries.get(country, [])
                data = db.get_unique_from_mapper(
                    t,
                    'DescriptionGES',
                    t.ReportingFeature.in_(crit_ids),
                    t.MarineUnitID.in_(muids)
                )
                value = self.not_rep

                for _d in data:
                    transl = get_translated(_d, country) or ''

                    orig.append(_d)
                    translated.append(transl)

                if data:
                    value = (emptyline_separated_itemlist(orig),
                             emptyline_separated_itemlist(translated))

                values.append(value)

            row = (crit.title, values)
            rows.append(row)

        return rows
        # return RegionalCompoundRow('GES component [Reporting feature]', rows)

    @cache(get_key, dependencies=['translation'])
    def get_reporting_area_row(self):
        rows = [
            ('Number used',
             [len(self.all_countries.get(c, [])) for c in self.countries])
        ]

        return rows
        # return RegionalCompoundRow('Reporting area(s)[MarineUnitID]', rows)

    @cache(get_key, dependencies=['translation'])
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
