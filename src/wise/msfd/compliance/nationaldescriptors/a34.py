import logging

from collections import defaultdict
from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018, sql_extra
from wise.msfd.data import get_xml_report_data
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import (Item, ItemLabel, ItemList, Node, RawRow,  # Row,
                             RelaxedNode, natural_sort_key, to_html)

from ..base import BaseArticle2012

# from .data import REPORT_DEFS

logger = logging.getLogger('wise.msfd')


NSMAP = {
    "w": "http://water.eionet.europa.eu/schemas/dir200856ec",
    "c": "http://water.eionet.europa.eu/schemas/dir200856ec/mscommon",
}


def xp(xpath, node):
    return node.xpath(xpath, namespaces=NSMAP)


@db.use_db_session('2012')
def _get_a8910_2020_mrus():
    count, res = db.get_all_specific_columns(
        [sql_extra.MSFD4GeographicalAreaID.MarineUnitID]
    )
    out = [x[0] for x in res]

    return out


@db.use_db_session('2012')
def _get_a11_2014_mrus():
    count, res = db.get_all_specific_columns(
        [sql.MSFD11MarineUnitID.MarineUnitID]
    )
    out = [x[0] for x in res]

    return out


@db.use_db_session('2012')
def _get_1314_2016_mrus():
    count, res = db.get_all_specific_columns(
        [sql.MSFD13Import.MarineUnitID]
    )
    out = [x[0] for x in res]

    return out


@db.use_db_session('2012')
def _get_8910_2018_mrus():
    count, res = db.get_all_specific_columns(
        [sql2018.MRUsPublication.thematicId]
    )
    out = [x[0] for x in res]

    return out


@db.use_db_session('2018')
def _get_18_2019_mrus():
    return []


@db.use_db_session('2018')
def _get_11_2020_mrus():
    table = sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit
    count, res = db.get_all_specific_columns(
        [table.MarineReportingUnit]
    )
    out = [x[0] for x in res]

    return out


def get_mru_usage_per_article():
    out = {
        'Art. 8-9-10 (2012)': _get_a8910_2020_mrus(),
        'Art. 11 (2014)': _get_a11_2014_mrus(),
        'Art. 13-14 (2016)': _get_1314_2016_mrus(),
        'Art. 17 (8-9-10) (2018)': _get_8910_2018_mrus(),
        'Art. 18 (2019)': _get_18_2019_mrus(),
        'Art. 17 (11) (2020)': _get_11_2020_mrus(),

    }

    return out


MRU_USAGE_PER_ART = get_mru_usage_per_article()


class A34Item(Item):
    def __init__(self, parent, node, description):

        super(A34Item, self).__init__([])

        self.parent = parent
        self.node = node
        self.description = description
        self.g = RelaxedNode(node, NSMAP)

        # self.id = node.find('w:ReportingFeature', namespaces=NSMAP).text

        attrs = [
            ('Member state description', self.member_state_descr),
            ('Region / subregion description', self.region_subregion),
            ('Subdivisions', self.subdivisions),
            ('Marine reporting units description', self.assessment_areas),
            ('Region or subregion', self.region_or_subregion),
            ('Member state', self.member_state),
            ('Area type', self.area_type),
            ('Marine Reporting Unit', self.mru_id),
            ('MRU Name', self.marine_reporting_unit),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

    def member_state_descr(self):
        text = xp('w:MemberState/text()', self.description)

        return text and text[0] or ''

    def region_subregion(self):
        text = xp('w:RegionSubregion/text()', self.description)

        return text and text[0] or ''

    def subdivisions(self):
        text = xp('w:Subdivisions/text()', self.description)

        return text and text[0] or ''

    def assessment_areas(self):
        text = xp('w:AssessmentAreas/text()', self.description)

        return text and text[0] or ''

    def region_or_subregion(self):
        v = self.g['w:RegionSubRegions/text()']

        return v and v[0] or ''

    def member_state(self):
        v = self.g['w:MemberState/text()']

        return v and v[0] or ''

    def area_type(self):
        v = self.g['w:AreaType/text()']

        return v and v[0] or ''

    def mru_id(self):
        v = self.g['w:MarineUnitID/text()']

        return v and v[0] or ''

    def marine_reporting_unit(self):
        v = self.g['w:MarineUnits_ReportingAreas/text()']

        return v and v[0] or ''


class Article34(BaseArticle2012):
    """ Article 3 & 4 implementation

    klass(self, self.request, self.country_code, self.country_region_code,
            self.descriptor, self.article, self.muids)
    """

    root = None
    year = '2012'

    template = Template('pt/report-data-secondary.pt')
    help_text = ""

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article,  muids, filename):

        super(Article34, self).__init__(context, request, country_code,
                                        region_code, descriptor, article,
                                        muids)

        self.filename = filename

    def sort_cols(self, cols):
        sorted_cols = sorted(
            cols, key=lambda _r: (
                _r['Region / subregion description'],
                _r['Area type'],
                _r['Marine Reporting Unit']
            )
        )

        return sorted_cols

    def setup_data(self):
        filename = self.filename
        text = get_xml_report_data(filename)
        self.root = fromstring(text)

        nodes = xp('//w:GeographicalBoundariesID', self.root)
        description = xp('//w:Description', self.root)[0]

        cols = []

        for node in nodes:
            item = A34Item(self, node, description)
            cols.append(item)

        sorted_cols = self.sort_cols(cols)

        self.rows = []

        for col in sorted_cols:
            for name in col.keys():
                values = []

                for inner in sorted_cols:
                    values.append(inner[name])

                raw_values = []
                vals = []

                for v in values:
                    raw_values.append(v)
                    vals.append(self.context.translate_value(
                        name, v, self.country_code))

                row = RawRow(name, vals, raw_values)
                self.rows.append(row)

            break       # only need the "first" row

        self.cols = sorted_cols

    def __call__(self):
        if self.root is None:
            self.setup_data()

        return self.template()


class A34Item_2018_mru(Item):
    def __init__(self, node, show_mru_usage=False):

        super(A34Item_2018_mru, self).__init__([])

        self.node = node
        self.g = RelaxedNode(node, NSMAP)

        attrs = [
            ('Region or subregion', self.region_or_subregion()),
            ('Member state', self.member_state()),
            ('Area type', self.area_type()),
            ('Marine Reporting Unit', self.mru_id()),
            ('MRU Name', self.marine_reporting_unit()),
        ]

        if show_mru_usage:
            attrs.extend([
                ('Art. 8-9-10 (2012)',
                 self.check_mru_usage('Art. 8-9-10 (2012)')),
                ('Art. 11 (2014)', self.check_mru_usage('Art. 11 (2014)')),
                ('Art. 13-14 (2016)',
                 self.check_mru_usage('Art. 13-14 (2016)')),
                ('Art. 17 (8-9-10) (2018)',
                 self.check_mru_usage('Art. 17 (8-9-10) (2018)')),
                ('Art. 18 (2019)', self.check_mru_usage('Art. 18 (2019)')),
                ('Art. 17 (11) (2020)',
                 self.check_mru_usage('Art. 17 (11) (2020)')),
            ])

        for title, value in attrs:
            self[title] = value
            setattr(self, title, value)

    def default(self):
        return ''

    def check_mru_usage(self, art):
        mru = self.mru_id()

        if mru in MRU_USAGE_PER_ART[art]:
            return 'Used'

        return ''

    def region_or_subregion(self):
        v = self.g['w:RegionSubRegions/text()']

        return v and v[0] or ''

    def member_state(self):
        v = self.g['w:MemberState/text()']

        return v and v[0] or ''

    def area_type(self):
        v = self.g['w:AreaType/text()']

        return v and v[0] or ''

    def mru_id(self):
        v = self.g['w:MarineUnitID/text()']

        return v and v[0] or ''

    def marine_reporting_unit(self):
        v = self.g['w:MarineUnits_ReportingAreas/text()']

        return v and v[0] or ''


class A34Item_2018_main(Item):
    mrus_template = Template('pt/mrus-table-art34.pt')
    TRANSLATABLES_EXTRA = ['MRU Name']

    def __init__(self, context, request, description, mru_nodes,
                 root, previous_mrus=None, show_mru_usage=False):

        super(A34Item_2018_main, self).__init__([])
        self.description = description
        self.root = root
        self.context = context
        self.request = request

        attrs = [
            ('Member state marine waters', self.member_state_descr),
            ('Region / subregion description', self.region_subregion),
            ('Subdivisions', self.subdivisions),
            ('Marine reporting units description', self.assessment_areas),
        ]

        for title, getter in attrs:
            self[title] = getter()
            setattr(self, title, getter())

        mrus = []

        for node in mru_nodes:
            item = A34Item_2018_mru(node, show_mru_usage)
            mrus.append(item)

        sorted_mrus = sorted(mrus, key=lambda x: x['Marine Reporting Unit'])
        self._mrus = sorted_mrus
        self.available_mrus = [
            x['Marine Reporting Unit'] for x in sorted_mrus
        ]
        self.available_regions = set(
            [x['Region or subregion'] for x in sorted_mrus]
        )
        self.previous_mrus = previous_mrus or []
        item_labels = sorted_mrus and sorted_mrus[0].keys() or ""

        sorted_mrus = self.mrus_template(
            item_labels=item_labels,
            item_values=sorted_mrus,
            previous_mrus=self.previous_mrus,
            country_code=self.context.country_code,
            translate_value=self.translate_value
        )

        self['MRUs'] = sorted_mrus
        setattr(self, 'MRUs', sorted_mrus)

        # Region or subregion Member state    Area type   MRU ID  Marine
        # reporting unit  Marine reporting unit

        cooperation_attrs = [
            ('Region/ subregion', self.coop_region_subregion()),
            ('Art. 8 countries involved',
             self.coop_by_params('Art8', 'CountriesInvolved')),
            ('Art. 8 nature of coordination',
             self.coop_by_params('Art8', 'NatureCoordination')),
            ('Art. 8 regional coherence',
             self.coop_by_params('Art8', 'RegionalCoherence')),
            ('Art. 8 regional coherence problems',
             self.coop_by_params('Art8', 'RegionalCoordinationProblems')),
            ('Art. 9 countries involved',
             self.coop_by_params('Art9', 'CountriesInvolved')),
            ('Art. 9 nature of coordination',
             self.coop_by_params('Art9', 'NatureCoordination')),
            ('Art. 9 regional coherence',
             self.coop_by_params('Art9', 'RegionalCoherence')),
            ('Art. 9 regional coherence problems',
             self.coop_by_params('Art9', 'RegionalCoordinationProblems')),
            ('Art. 10 countries involved',
             self.coop_by_params('Art10', 'CountriesInvolved')),
            ('Art. 10 nature of coordination',
             self.coop_by_params('Art10', 'NatureCoordination')),
            ('Art. 10 regional coherence',
             self.coop_by_params('Art10', 'RegionalCoherence')),
            ('Art. 10 regional coherence problems',
             self.coop_by_params('Art10', 'RegionalCoordinationProblems')),

        ]

        for title, data in cooperation_attrs:
            self[title] = data
            setattr(self, title, data)

    def get_translatable_extra_data(self):
        """ Get the translatable fields from the MRU nodes

        :return: a list of values to translate
        """
        res = []

        for row in self._mrus:
            for field in self.TRANSLATABLES_EXTRA:
                value = getattr(row, field, None)
                if not value:
                    continue

                res.append(value)

        return set(res)

    def translate_value(self, fieldname, value, source_lang):
        is_translatable = fieldname in self.TRANSLATABLES_EXTRA
        v = self.context.context.translate_view()

        return v.translate(source_lang=source_lang,
                           value=value,
                           is_translatable=is_translatable)

    def sort_mrus(self, cols):
        sorted_cols = sorted(
            cols, key=lambda _r: (
                _r['Member state'],
                _r['Region or subregion'],
                _r['Marine Reporting Unit'],
                _r['MRU Name']
            )
        )

        return sorted_cols

    def member_state_descr(self):
        text = xp('w:MemberState/text()', self.description)

        return text and text[0] or ''

    def region_subregion(self):
        text = xp('w:RegionSubregion/text()', self.description)

        return text and text[0] or ''

    def subdivisions(self):
        text = xp('w:Subdivisions/text()', self.description)

        return text and text[0] or ''

    def assessment_areas(self):
        text = xp('w:AssessmentAreas/text()', self.description)

        return text and text[0] or ''

    def coop_region_subregion(self):
        texts = xp('//w:Cooperation/w:RegionsSubRegions/text()', self.root)

        return texts and ' !!! '.join(set(texts)) or ''

    def coop_by_params(self, article, node_name):
        xpath = '//w:Cooperation[w:Topic = "{}"]' \
                '/w:{}/descendant-or-self::*/text()'.format(article, node_name)

        texts = xp(xpath, self.root)

        return texts and ', '.join(set(sorted(texts))) or ''


class Article34_2018(BaseArticle2012):
    """ Implementation for Article 3/4 2018 reported data
    """

    year = '2012'
    root = None

    template = Template('pt/report-data-secondary.pt')
    help_text = ""

    def __init__(self, context, request, country_code, region_code,
                 descriptor, article, muids, filename=None,
                 previous_mrus=None, show_mru_usage=False):

        # TODO: use previous_mrus to highlight this file MRUs according to edit
        # status: added or deleted
        super(Article34_2018, self).__init__(context, request, country_code,
                                             region_code, descriptor, article,
                                             muids)
        self.filename = filename
        self.previous_mrus = previous_mrus
        self.show_mru_usage = show_mru_usage

    def get_report_file_root(self, filename=None):
        if self.root is None:
            self.setup_data()

        return self.root

    def setup_data(self):
        filename = self.filename
        text = get_xml_report_data(filename)
        self.root = fromstring(text)

        mru_nodes = xp('//w:GeographicalBoundariesID', self.root)
        description = xp('//w:Description', self.root)[0]
        # cooperation_nodes = xp('//w:Cooperation', self.root)

        # TODO: also send the previous file data
        main_node = A34Item_2018_main(
            self, self.request, description, mru_nodes, self.root,
            self.previous_mrus, self.show_mru_usage
        )
        self.translatable_extra_data = main_node.get_translatable_extra_data()
        self.available_mrus = main_node.available_mrus
        self.available_regions = main_node.available_regions
        self.rows = []

        # TODO: this code needs to be explained. It's hard to understand what
        # its purpose is

        for name in main_node.keys():
            values = []

            for inner in [main_node]:
                values.append(inner[name])

            raw_values = []
            vals = []

            for v in values:
                raw_values.append(v)
                vals.append(self.context.translate_value(
                    name, v, self.country_code))

            row = RawRow(name, vals, raw_values)
            self.rows.append(row)

        self.cols = [main_node]

    def __call__(self):
        if self.root is None:
            self.setup_data()

        return self.template()
