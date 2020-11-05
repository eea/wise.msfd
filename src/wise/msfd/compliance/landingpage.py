from collections import namedtuple
import lxml.etree

from pkg_resources import resource_filename

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from .assessment import AssessmentDataMixin
from .base import BaseComplianceView
from .vocabulary import REGIONAL_DESCRIPTORS_REGIONS


COLOR_SUFFIX = {
    "country": "-C",
    "country-a": "-CA",
    "region": "",
    "region-a": "-A",
    "row": "",
}


YearRow = namedtuple('YearRow', ['date', 'who', 'article', 'task', 'css_extra',
                                 'subrows'])

SubrowDef = namedtuple('SubrowDef', ['colspan_type', 'text', 'color_class',
                                     'get_method', 'rowspan', 'permission'])

SubrowItem = namedtuple('SubrowItem', ['colspan', 'text', 'href',
                                       'css_class', 'rowspan'])


def _parse_landingpage_xml(path='compliance/landingpage.xml'):
    xmlfile = resource_filename('wise.msfd', path)

    root = lxml.etree.parse(xmlfile).getroot()
    years = root.iterchildren('year')

    res = [LandingPageYearDefinition(y) for y in years]

    return res


class LandingPageYearDefinition(object):
    """ Definition for a year group which is divided into multiple 'rows',
        one row per 'date', 'who', 'article' and 'task'.

        Respectively each 'row' is divided into multiple 'subrows',
        a subrow representing the links for each country, or links
        for a whole region, sometimes a single link for the whole article
    """

    def __init__(self, year_node):
        """ Initialize a year node, represented in the form of a nested list
        with the following structure

        [[date1, who1, article1, task1, css_class1,
            [colspanA, textA, colorA, get_data_methodA]],
         [date2, who2, article2, task2, css_class2,
            [colspanB, textB, colorB, get_data_methodB]]
        ]
        """

        date = year_node.attrib.get('date')
        css_extra = year_node.attrib.get('extra-css-class', '')

        rows = []

        for row in year_node.iterchildren('element'):
            who = row.attrib.get('who')
            article = row.attrib.get('article')
            task = row.attrib.get('task')
            subrows = []

            for subrow in row.iterchildren('row'):
                colspan_type = subrow.attrib.get('colspan')
                color_class = subrow.attrib.get('color-class', colspan_type)
                get_method = subrow.attrib.get('get-method')
                text = subrow.attrib.get('display-text')
                rowspan = int(subrow.attrib.get('rowspan', 1))
                permission = subrow.attrib.get('permission', None)

                subrows.append(SubrowDef(colspan_type, text, color_class,
                                         get_method, rowspan, permission))

            rows.append(YearRow(date, who, article, task, css_extra, subrows))

        self.rows = rows


class StartLandingPage(BaseComplianceView):
    """ Landing/Home page for assessment module """

    template = ViewPageTemplateFile("pt/landingpage.pt")
    year_defs = _parse_landingpage_xml()
    section = 'compliance-start'

    def __call__(self):
        data = []

        for year_def in self.year_defs:
            rendered_row = BaseLandingPageRow(self, self.request, year_def)()

            data.append(rendered_row)

        return self.template(data=data)


class BaseLandingPageRow(BaseComplianceView, AssessmentDataMixin):
    """ Base class with all the needed base methods to build the landing page
        structure
    """

    template = PageTemplateFile('pt/landingpage-row.pt')

    @property
    def _nr_of_countries(self):
        cnt = 0

        for region_folder in self._reg_desc_region_folders:
            available_countries = region_folder._countries_for_region

            cnt += len(available_countries)

        return cnt

    @property
    def regions_and_countries(self):
        res = []

        for region_folder in self._reg_desc_region_folders:
            region_id = region_folder.id.upper()
            available_countries = region_folder._countries_for_region

            res.append((region_id, available_countries))

        return res

    def _default(self):
        return {}

    def get_2018_countries_assess(self):
        return self.get_2018_countries(extra_path='assessments')

    def get_2018_countries_reports(self):
        return self.get_2018_countries(extra_path='reports')

    def get_2018_countries(self, extra_path=''):
        data = {}

        for folder in self._nat_desc_country_folders:
            url = "{}/{}".format(folder.absolute_url(), extra_path)
            reg_id = folder.id.upper()
            data[reg_id] = url

        return data

    def get_2018_regions_assess(self):
        return self.get_2018_regions(extra_path='assessments')

    def get_2018_regions_reports(self):
        return self.get_2018_regions(extra_path='reports')

    def get_2018_regions(self, extra_path=''):
        data = {}

        for folder in self._reg_desc_region_folders:
            url = "{}/{}".format(folder.absolute_url(), extra_path)
            reg_id = folder.id.upper()
            data[reg_id] = url

        return data

    def _make_subrow_row(self, text, data, color_class, extra_css_class,
                         rowspan=1):
        res = []
        _text = text
        color_suffix = COLOR_SUFFIX.get(color_class, "")
        css_class = extra_css_class + " {}{}"

        res.append(
            SubrowItem(self._nr_of_countries, _text, data.get('ROW', ''),
                       css_class.format('ROW', color_suffix), rowspan)
        )

        return res

    def _make_subrow_region(self, text, data, color_class, extra_css_class,
                            rowspan=1):
        res = []
        color_suffix = COLOR_SUFFIX.get(color_class, "")
        css_class = extra_css_class + " {}{}"

        for region_id, available_countries in self.regions_and_countries:
            _text = text.format(region_id)

            if text == '_region':
                _text = [
                    r.title
                    for r in REGIONAL_DESCRIPTORS_REGIONS
                    if r.code == region_id
                ][0]

            res.append(
                SubrowItem(len(available_countries), _text,
                           data.get(region_id, ''),
                           css_class.format(region_id, color_suffix), rowspan)
            )

        return res

    def _make_subrow_country(self, text, data, color_class, extra_css_class,
                             rowspan=1):
        res = []
        color_suffix = COLOR_SUFFIX.get(color_class, "")
        css_class = extra_css_class + " {}{}"

        for region_id, available_countries in self.regions_and_countries:
            for country in available_countries:
                country_id = country[0]
                country_name = country[1]

                _text = text.format(country_id)

                if text == '_country':
                    _text = country_name

                res.append(
                    SubrowItem(1, _text, data.get(country_id, ""),
                               css_class.format(region_id, color_suffix),
                               rowspan)
                )

        return res

    def make_subrow(self, colspan_type, rowspan, text, color_class, css_extra,
                    data):
        make_method = getattr(self, "_make_subrow_" + colspan_type)
        subrow_final = make_method(text, data, color_class, css_extra, rowspan)

        return subrow_final

    def __init__(self, context, request, year_def):
        super(BaseLandingPageRow, self).__init__(context, request)

        data = []

        for row in year_def.rows:
            date = row.date
            who = row.who
            art = row.article
            task = row.task
            css_extra = row.css_extra
            subrows = row.subrows
            _subrows = []

            for subrow_def in subrows:
                colspan_type = subrow_def.colspan_type
                text = subrow_def.text
                color_class = subrow_def.color_class
                get_data_method = subrow_def.get_method
                rowspan = subrow_def.rowspan
                permission = subrow_def.permission

                if permission and not(self.check_permission(permission)):
                    continue

                subrow_data = getattr(self, get_data_method, self._default)()
                _subrows.append(
                    self.make_subrow(colspan_type, rowspan, text, color_class,
                                     css_extra, subrow_data)
                )

            data.append(YearRow(date, who, art, task, css_extra, _subrows))

        self.data = data

    def __call__(self):
        return self.template(data=self.data)
