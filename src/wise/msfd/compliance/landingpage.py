from collections import namedtuple
import lxml.etree

from pkg_resources import resource_filename

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from .assessment import AssessmentDataMixin
from .base import BaseComplianceView
from .vocabulary import REGIONAL_DESCRIPTORS_REGIONS, REPORTING_HISTORY_ENV


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
                                     'get_method', 'rowspan', 'permission',
                                     'msfd_article', 'report_type'])

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

        [YearRow(date, who, article, task, css_extra,[
            SubrowDef1(colspan_type, text, color_class,
                        get_method, rowspan, permission, msfd_article),
            SubrowDef2(colspan_type, text, color_class,
                        get_method, rowspan, permission, msfd_article)
            ],
         YearRow2...,
         YearRow3...,
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
                msfd_article = subrow.attrib.get('msfd-article', None)
                report_type = subrow.attrib.get('report-type', None)

                subrows.append(SubrowDef(colspan_type, text, color_class,
                                         get_method, rowspan, permission,
                                         msfd_article, report_type))

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


class LandingpageDataMixin:
    """ Class to hold all the methods to get the urls displayed on the
    landingpage
    """

    def _get_location_url(self, article, country_code, report_type,
                          file_name=None):
        for row in REPORTING_HISTORY_ENV:
            if article != row.MSFDArticle:
                continue

            if country_code != row.CountryCode:
                continue

            if report_type != row.ReportType:
                continue

            if file_name and file_name != row.FileName:
                continue

            return row.LocationURL

        return None

    def _get_2018_countries(self, extra_path=''):
        data = {}

        for folder in self._nat_desc_country_folders:
            url = "{}/{}".format(folder.absolute_url(), extra_path)
            country_id = folder.id.upper()
            data[country_id] = url

        return data

    def _get_2018_regions(self, extra_path=''):
        data = {}

        for folder in self._reg_desc_region_folders:
            url = "{}/{}".format(folder.absolute_url(), extra_path)
            reg_id = folder.id.upper()
            data[reg_id] = url

        return data

    def _get_from_env_row(self, msfd_article, report_type):
        url = self._get_location_url(msfd_article, 'COM', report_type)

        return {"ROW": url}

    def _get_from_env_country(self, msfd_article, report_type):
        data = {}

        for folder in self._nat_desc_country_folders:
            country_id = folder.id.upper()
            url = self._get_location_url(msfd_article, country_id, report_type)
            data[country_id] = url

        return data

    def _get_from_env_region(self, msfd_article, report_type):
        data = {}

        for folder in self._reg_desc_region_folders:
            reg_id = folder.id.upper()
            url = self._get_location_url(msfd_article, reg_id, report_type)
            data[reg_id] = url

        return data

    def _default(self, *args):
        return {}

    def _get_from_env_multilink(self, links):
        data = {"ROW": []}

        for link in links:
            msfd_article = link[0]
            report_type = link[1]
            file_name = link[2]
            url = self._get_location_url(msfd_article, 'COM', report_type,
                                         file_name)

            data["ROW"].append((url, file_name))

        return data


    def get_header_countries(self, *args):
        return self._get_2018_countries()

    def get_header_regions(self, *args):
        return self._get_2018_regions()

    def get_from_env_2016_art16(self, *args):
        msfd_article = args[1]
        links = (
            # article, report_type, file_name
            (msfd_article, 'Commission report', 'COM(2018)562.pdf'),
            (msfd_article, 'Commission Staff Working Document',
             'SWD(2018)393 final.pdf'),
            (msfd_article, 'Commission Staff Working Document',
             'SWD(2019) 510 final')
        )

        return self._get_from_env_multilink(links)

    def get_from_env_2016_art9_3(self, *args):
        msfd_article = args[1]
        links = (
            # article, report_type, file_name
            (msfd_article, 'Commission decision',
             'Commission Decision (EU) 2017/848'),
            ('Annex III', 'Commission directive',
             'Commission Directive (EU) 2017/845'),
        )

        return self._get_from_env_multilink(links)

    def get_from_env_simple(self, *args):
        """ Get url from MSFD reporting history ENV using the msfd-article
            and country_code or region code

            Return single url for each country/region
        """
        colspan_type = args[0]
        msfd_article = args[1]
        report_type = args[2]

        get_method = getattr(self, "_get_from_env_" + colspan_type)
        data = get_method(msfd_article, report_type)

        return data

    def get_2018_countries_assess(self, *args):
        return self._get_2018_countries(extra_path='assessments')

    def get_2018_countries_reports(self, *args):
        return self._get_2018_countries(extra_path='reports')

    def get_2018_regions_assess(self, *args):
        return self._get_2018_regions(extra_path='assessments')

    def get_2018_regions_reports(self, *args):
        return self._get_2018_regions(extra_path='reports')


class BaseLandingPageRow(BaseComplianceView, AssessmentDataMixin,
                         LandingpageDataMixin):
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
                msfd_article = subrow_def.msfd_article
                report_type = subrow_def.report_type

                if permission and not(self.check_permission(permission)):
                    continue

                _get_method = getattr(self, get_data_method, self._default)
                subrow_data = _get_method(colspan_type, msfd_article,
                                          report_type)

                _subrows.append(
                    self.make_subrow(colspan_type, rowspan, text, color_class,
                                     css_extra, subrow_data)
                )

            data.append(YearRow(date, who, art, task, css_extra, _subrows))

        self.data = data

    def __call__(self):
        return self.template(data=self.data)
