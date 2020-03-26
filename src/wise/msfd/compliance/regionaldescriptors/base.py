from collections import Counter, defaultdict, namedtuple
from itertools import chain

from plone.api.content import get_state
from plone.api.portal import get_tool
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from wise.msfd.gescomponents import FEATURES_DB_2018, THEMES_2018_ORDER
from wise.msfd.labels import get_label
from wise.msfd.translation import get_detected_lang
from wise.msfd.utils import ItemLabel, fixedorder_sortkey

from .. import interfaces
from .data import REPORT_DEFS
from .utils import (compoundrow, get_nat_desc_country_url,
                    newline_separated_itemlist)

COUNTRY = namedtuple("Country", ["id", "title", "definition", "is_primary"])


class BaseRegComplianceView(BaseComplianceView):
    report_header_template = ViewPageTemplateFile(
        'pt/report-data-header.pt'
    )

    assessment_header_template = ViewPageTemplateFile(
        '../pt/assessment-header.pt'
    )

    section = 'regional-descriptors'
    _translatables = None

    not_rep = u""
    rep = u"Reported"

    @property
    def current_phase(self):
        region_folder = self._countryregion_folder
        state, title = self.process_phase(region_folder)

        return state, title

    @property
    def TRANSLATABLES(self):
        # for 2018, returns a list of field names that are translatable

        if self._translatables:
            return self._translatables

        year = REPORT_DEFS[self.year]

        if self.article in year:
            return year[self.article].get_translatable_fields()

        self._translatables = []

        return self._translatables

    @TRANSLATABLES.setter
    def set_translatables(self, v):
        self._translatables = v

    @property
    def _countryregion_folder(self):
        return self.get_parent_by_iface(
            interfaces.IRegionalDescriptorRegionsFolder
        )

    @property
    def _article_assessment(self):
        return self.get_parent_by_iface(
            interfaces.IRegionalDescriptorAssessment
        )

    @property
    def region_name(self):
        # return REGIONS[self.country_region_code]

        return self._countryregion_folder.title

    @property
    def available_countries(self):
        return self._countryregion_folder._countries_for_region

    def process_phase(self, context=None):
        if context is None:
            context = self.context

        state = get_state(context)
        wftool = get_tool('portal_workflow')
        wf = wftool.getWorkflowsFor(context)[0]        # assumes one wf
        wf_state = wf.states[state]
        title = wf_state.title.strip() or state

        return state, title

    def get_available_countries(self):
        res = [
            # id, title, definition, is_primary
            COUNTRY(x[0], x[1], "", lambda _: True)

            for x in self.available_countries
        ]

        return res

    def translate_value(self, fieldname, value, source_lang):
        is_translatable = fieldname in self.TRANSLATABLES

        v = self.translate_view()

        if not is_translatable:
            return v.cell_tpl(value=value)

        if not value:
            return v.cell_tpl(value=value)

        text = value[0]
        translation = value[1] or ''

        if get_detected_lang(text) == 'en' or not translation:
            return v.cell_tpl(value=text)

        return v.translate_tpl(text=text,
                               translation=translation,
                               can_translate=False,
                               source_lang=source_lang)

        # return v.translate(source_lang=source_lang,
        #                    value=value,
        #                    is_translatable=is_translatable)


class BaseRegDescRow(BaseRegComplianceView):
    def __init__(self, context, request, db_data, descriptor_obj,
                 regions, countries, field):
        super(BaseRegDescRow, self).__init__(context, request)
        # self.context = context
        # self.request = request
        self.db_data = [x._Proxy2018__o for x in db_data]
        self.db_data_proxy = db_data
        # self.descriptor_obj = descriptor_obj
        self.region = regions
        self.countries = countries
        self.field = field

    def get_unique_values(self, field):
        values = set([
            getattr(row, field)

            for row in self.db_data

            if getattr(row, field)
        ])

        return sorted(values)

    def get_label_for_value(self, value):
        label = get_label(value, self.field.label_collection)

        return label

    def make_item_label(self, value):
        return value

        return ItemLabel(value, self.get_label_for_value(value))

    @compoundrow
    def get_countries_row(self):
        url = self.request['URL0']

        reg_main = self._countryregion_folder.id.upper()
        subregions = [r.subregions for r in REGIONAL_DESCRIPTORS_REGIONS
                      if reg_main in r.code]

        rows = []
        country_names = []

        for country in self.context.available_countries:
            value = []
            c_code = country[0]
            c_name = country[1]
            regions = [r.code for r in REGIONAL_DESCRIPTORS_REGIONS
                       if len(r.subregions) == 1 and c_code in r.countries
                       and r.code in subregions[0]]

            for r in regions:
                value.append(get_nat_desc_country_url(url, reg_main,
                                                      c_code, r))

            final = '{} ({})'.format(c_name, ', '.join(value))
            country_names.append(final)

        rows.append(('', country_names))

        return rows

    @compoundrow
    def get_mru_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = set([
                row.MarineReportingUnit

                for row in self.db_data

                if row.CountryCode == country_code
            ])
            values.append(len(value))

        rows.append((u'Number used', values))

        return rows

    @compoundrow
    def get_feature_row(self):
        all_features_reported = self.get_unique_values("Features")
        themes_fromdb = FEATURES_DB_2018

        rows = []
        all_features = []
        all_themes = defaultdict(list)

        for feat in all_features_reported:
            all_features.extend(feat.split(','))
        all_features = set(all_features)

        for feature in all_features:
            if feature not in themes_fromdb:
                all_themes['No theme'].append(feature)

                continue

            theme = themes_fromdb[feature].theme
            all_themes[theme].append(feature)

        all_themes = sorted(
            all_themes.items(),
            key=lambda t: fixedorder_sortkey(t[0], THEMES_2018_ORDER)
        )

        for theme, feats in all_themes:
            values = []

            for country_code, country_name in self.countries:
                value = []
                data = [
                    row.Features.split(',')

                    for row in self.db_data

                    if row.CountryCode == country_code
                    and row.Features
                ]
                all_features_rep = [x for x in chain(*data)]
                count_features = Counter(all_features_rep)

                for feature in feats:
                    cnt = count_features.get(feature, 0)

                    if not cnt:
                        continue

                    label = self.get_label_for_value(feature)
                    val = u"{} ({})".format(label, cnt)
                    value.append(val)

                values.append(newline_separated_itemlist(value))

            rows.append((theme, values))

        return rows
