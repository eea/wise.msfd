from collections import namedtuple

from plone.api.content import get_state
from plone.api.portal import get_tool
from wise.msfd.compliance.base import BaseComplianceView
from wise.msfd.compliance.vocabulary import REGIONS
from wise.msfd.gescomponents import get_label
from wise.msfd.utils import ItemLabel

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from .. import interfaces
from .data import REPORT_DEFS
from .utils import compoundrow

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
        return REGIONS[self.country_region_code]

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

        return v.translate(source_lang=source_lang,
                           value=value,
                           is_translatable=is_translatable)


class BaseRegDescRow(BaseRegComplianceView):
    not_rep = u""
    rep = u"Reported"

    def __init__(self, context, request, db_data, descriptor_obj,
                 region, countries, field):
        super(BaseRegDescRow, self).__init__(context, request)
        # self.context = context
        # self.request = request
        self.db_data = [x._Proxy2018__o for x in db_data]
        self.db_data_proxy = db_data
        # self.descriptor_obj = descriptor_obj
        self.region = region
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
        rows = []
        country_names = [x[1] for x in self.context.available_countries]
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
        rows = []
        features = self.get_unique_values("Features")
        all_features = []
        for feat in features:
            all_features.extend(feat.split(','))

        for feature in set(all_features):
            values = []
            for country_code, country_name in self.countries:
                exists = [
                    row
                    for row in self.db_data
                    if row.CountryCode == country_code
                        and row.Features
                        and feature in row.Features.split(',')
                ]
                value = self.not_rep
                if exists:
                    value = self.rep

                values.append(value)

            rows.append((self.make_item_label(feature), values))

        return rows
