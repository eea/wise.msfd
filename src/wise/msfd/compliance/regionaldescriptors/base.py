from collections import Counter, defaultdict, namedtuple
from itertools import chain

from eea.cache import cache

from plone.api.content import get_state
from plone.api.portal import get_tool
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.base import (BaseComplianceView, NAT_DESC_QUESTIONS,
                                       report_data_cache_key)
from wise.msfd.compliance.interfaces import IComplianceModuleFolder
from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from wise.msfd.gescomponents import (FEATURES_DB_2018, THEMES_2018_ORDER,
                                     SUBJECT_2018_ORDER, get_marine_units)
from wise.msfd.labels import get_label
from wise.msfd.translation import get_detected_lang
from wise.msfd.utils import ItemLabel, ItemList, fixedorder_sortkey

from .. import interfaces
from .data import REPORT_DEFS
from .utils import (RegionalCompoundRow, compoundrow, get_nat_desc_country_url,
                    simple_itemlist)

COUNTRY = namedtuple("Country", ["id", "title", "definition", "is_primary"])


class NationalAssessmentMixin:
    year = '2018'

    def make_countries_row(self):
        rows = []
        country_names = []

        for country in self.available_countries:
            c_name = country[1]

            country_names.append(c_name)

        rows.append(('', country_names))

        return rows

    def _conclusion_color(self, score):
        if not score:
            return 0
        from wise.msfd.compliance.assessment import CONCLUSION_COLOR_TABLE

        score_value = score.score_value

        conclusion_color = CONCLUSION_COLOR_TABLE[score_value]

        return conclusion_color

    def _answer_color(self, score):
        from wise.msfd.compliance.assessment import ANSWERS_COLOR_TABLE
        if not score:
            return 0

        conclusion_color = ANSWERS_COLOR_TABLE[score]

        return conclusion_color

    def get_nat_desc_assessment_data(self, country_code, region, descriptor,
                                     article):
        catalog = self.context.portal_catalog
        assessment_module_folder = self.get_parent_by_iface(
            IComplianceModuleFolder
        )

        p = ('/'.join(assessment_module_folder.getPhysicalPath())
             + '/national-descriptors-assessments')
        path = p + "/{}/{}/{}/{}".format(country_code.lower(), region.lower(),
                                         descriptor.lower(), article.lower())

        brains = catalog.searchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
            path={
                "query": path
            }

        )

        if not brains:
            return {}

        obj = brains[0].getObject()

        if not hasattr(obj, 'saved_assessment_data'):
            return {}

        return obj.saved_assessment_data.last()

    def get_adequacy_assessment_data(self):
        if self.article in ['Art10']:
            return self.get_adequacy_assessment_data_art10()

        def get_assessed_elements(self, question):
            muids = []

            elements = {
                x.id: []
                for x in question.get_assessed_elements(self.descriptor_obj,
                                                        muids=muids)
            }

            if not elements:
                elements['All criteria'] = []

            return elements

        answer_tpl = u"<span class='empty-colorbox as-value-{}'/>" \
                     u"<span><b>{}:</b> {}</span>"
        Field = namedtuple('Field', ['name', 'title'])

        countries = self.available_countries
        questions = NAT_DESC_QUESTIONS.get(self.article, [])
        region = self.country_region_code
        subregions = [r.subregions for r in REGIONAL_DESCRIPTORS_REGIONS
                      if region in r.code][0]

        descriptor = self.descriptor
        article = self.article

        res = [
            RegionalCompoundRow(
                self, self.request, Field('Country', 'Country'),
                self.make_countries_row()
            )]

        for question in questions:
            q_id = question.id
            q_def = question.definition
            field = Field(q_id, q_def)

            rows = []
            criteria_values = get_assessed_elements(self, question)
            conclusion_values = []
            summary_values = []

            for country_code, country_name in countries:
                country_concl = []
                country_sums = []
                country_crits = get_assessed_elements(self, question)
                country_regions = [
                    r.code

                    for r in REGIONAL_DESCRIPTORS_REGIONS

                    if len(r.subregions) == 1
                       and country_code in r.countries
                       and r.code in subregions
                ]

                for subregion in country_regions:
                    assess_data = self.get_nat_desc_assessment_data(
                        country_code, subregion, descriptor, article
                    )

                    score = assess_data.get('{}_{}_Score'.format(article,
                                                                 q_id))
                    summary = assess_data.get('{}_{}_Summary'.format(article,
                                                                     q_id))
                    summary = summary or "-"
                    summary = u"<b>{}:</b> {}".format(subregion, summary)

                    conclusion = score and score.conclusion or "-"
                    conclusion = \
                        u"<span class='empty-colorbox as-value-{}'/>" \
                        u"<span><b>{}:</b> {}</span>" \
                        .format(self._conclusion_color(score), subregion,
                                conclusion)

                    country_concl.append(conclusion)
                    country_sums.append(summary)

                    for crit_id in country_crits.keys():
                        option_txt = '-'
                        option_score = 0
                        if question.use_criteria == 'none':
                            option = assess_data.get('{}_{}'.format(
                                article, q_id)
                            )
                        else:
                            option = assess_data.get('{}_{}_{}'.format(
                                article, q_id, crit_id)
                            )
                        if option is not None:
                            option_txt = question.answers[option]
                            option_score = question.scores[option]
                        _val = answer_tpl.format(
                            self._answer_color(option_score),
                            subregion,
                            option_txt
                        )

                        country_crits[crit_id].append(_val)

                for crit_id in criteria_values.keys():
                    criteria_values[crit_id].append(
                        ItemList(country_crits[crit_id])
                    )

                conclusion_values.append(ItemList(country_concl))
                summary_values.append(ItemList(country_sums))

            for crit_id, crit_values in criteria_values.items():
                rows.append((crit_id, crit_values))

            rows = sorted(rows, key=lambda i: i[0])

            rows.append((u'Conclusion', conclusion_values))
            rows.append((u'Summary', summary_values))

            res.append(RegionalCompoundRow(self, self.request, field, rows))

        return res

    def get_adequacy_assessment_data_art10(self):
        def get_assessed_elements(self, question, country_code):
            muids = []

            _region = self.country_region_code
            _subregions = [
                _r.subregions
                for _r in REGIONAL_DESCRIPTORS_REGIONS
                if _region in _r.code
            ][0]

            _country_regions = [
                r.code

                for r in REGIONAL_DESCRIPTORS_REGIONS

                if len(r.subregions) == 1
                   and country_code in r.countries
                   and r.code in _subregions
            ]
            for _subregion in _country_regions:
                _muids = self.muids(
                    country_code.upper(), _subregion.upper(), self.year
                )

                muids.append((_subregion.upper(), _muids))

            elements = {}

            for _subreg, _muids in muids:
                targets = question.get_assessed_elements(self.descriptor_obj,
                                                         muids=_muids)

                elements[_subreg] = targets

            return elements

        answer_tpl = u"<span class='empty-colorbox as-value-{}'/>" \
                     u"<span><b>{}:</b> {}</span>"
        Field = namedtuple('Field', ['name', 'title'])

        countries = self.available_countries
        questions = NAT_DESC_QUESTIONS.get(self.article, [])
        region = self.country_region_code
        subregions = [r.subregions for r in REGIONAL_DESCRIPTORS_REGIONS
                      if region in r.code][0]

        descriptor = self.descriptor
        article = self.article

        res = [
            RegionalCompoundRow(
                self, self.request, Field('Country', 'Country'),
                self.make_countries_row()
            )]

        for question in questions:
            q_id = question.id
            q_def = question.definition
            q_answ = question.answers
            field = Field(q_id, q_def)

            rows = []
            conclusion_values = []
            summary_values = []

            # Init the result with empty values
            answer_values = {
                answer: {country_code: [] for country_code, _ in countries}
                for answer in q_answ
            }

            for country_code, country_name in countries:
                country_concl = []
                country_sums = []
                country_targets = get_assessed_elements(
                    self, question, country_code
                )

                country_regions = [
                    r.code

                    for r in REGIONAL_DESCRIPTORS_REGIONS

                    if len(r.subregions) == 1
                       and country_code in r.countries
                       and r.code in subregions
                ]

                for subregion in country_regions:
                    assess_data = self.get_nat_desc_assessment_data(
                        country_code, subregion, descriptor, article
                    )

                    # Setup the conclusion and the summary
                    score = assess_data.get('{}_{}_Score'.format(article,
                                                                 q_id))
                    summary = assess_data.get('{}_{}_Summary'.format(article,
                                                                     q_id))
                    summary = summary or "-"
                    summary = u"<b>{}:</b> {}".format(subregion, summary)

                    conclusion = score and score.conclusion or "-"
                    conclusion = \
                        u"<span class='empty-colorbox as-value-{}'/>" \
                        u"<span><b>{}:</b> {}</span>" \
                        .format(self._conclusion_color(score), subregion,
                                conclusion)

                    country_concl.append(conclusion)
                    country_sums.append(summary)

                    # Setup the targets
                    subregion_targets = country_targets[subregion]

                    for target in subregion_targets:
                        option = assess_data.get('{}_{}_{}'.format(
                            article, q_id, target.id)
                        )
                        if option is None:
                            continue

                        option_txt = q_answ[option]
                        option_score = question.scores[option]

                        _val = answer_tpl.format(
                            self._answer_color(option_score),
                            subregion,
                            target.title
                        )

                        answer_values[option_txt][country_code].append(_val)

                conclusion_values.append(ItemList(country_concl))
                summary_values.append(ItemList(country_sums))

            # Add rows with the answers and values into the table
            for _answer in q_answ:
                _countries = answer_values[_answer]

                values = [
                    ItemList(values)
                    for country_code, values in _countries.items()
                ]

                rows.append((_answer, values))

            rows.append((u'Conclusion', conclusion_values))
            rows.append((u'Summary', summary_values))

            res.append(RegionalCompoundRow(self, self.request, field, rows))

        return res


class BaseRegComplianceView(BaseComplianceView, NationalAssessmentMixin):
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

    @cache(report_data_cache_key)
    def muids(self, country_code, country_region_code, year):
        """ Get all Marine Units for a country

        :return: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
        """

        return get_marine_units(country_code,
                                country_region_code,
                                year)

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
        rows = []
        country_names = []

        for country in self.context.available_countries:
            c_name = country[1]
            final = '{}'.format(c_name)
            country_names.append(final)

        rows.append(('', country_names))

        return rows

    @compoundrow
    def get_countries_reports_row(self):
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
                report_url = get_nat_desc_country_url(url, reg_main, c_code, r)
                value.append("{}: {}".format(r, report_url))

            country_names.append(simple_itemlist(value))

        rows.append(('', country_names))

        return rows

    @compoundrow
    def get_mru_row_old(self):
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
    def get_mru_row(self):
        rows = []
        values = []

        for country_code, country_name in self.countries:
            value = sorted(set([
                row.MarineReportingUnit

                for row in self.db_data

                if row.CountryCode == country_code
                   and row.MarineReportingUnit
            ]))

            values.append(simple_itemlist(value))

        rows.append((u'MRUs used', values))

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
                all_themes['No subject: No theme'].append(feature)

                continue

            subject_and_theme = "{}: {}".format(
                themes_fromdb[feature].subject, themes_fromdb[feature].theme)
            all_themes[subject_and_theme].append(feature)

        # First sort by THEME
        all_themes = sorted(
            all_themes.items(),
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

                values.append(simple_itemlist(value))

            rows.append((subject_and_theme, values))

        return rows
