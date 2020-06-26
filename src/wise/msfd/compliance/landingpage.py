
import lxml.etree

from pkg_resources import resource_filename

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from .assessment import AssessmentDataMixin
from .base import BaseComplianceView


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

        [[date1, who1, article1, task1, [colspanA, textA, get_data_methodA]],
         [date2, who2, article2, task2, [colspanB, textB, get_data_methodB]]]
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
                get_method = subrow.attrib.get('get-method')
                text = subrow.attrib.get('display-text')

                subrows.append((colspan_type, text, get_method))

            rows.append((date, who, article, task, css_extra, subrows))

        self.rows = rows


class StartLandingPage(BaseComplianceView):
    """ Landing/Home page for assessment module """

    template = ViewPageTemplateFile("pt/landingpage.pt")
    year_defs = _parse_landingpage_xml()

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

    def get_2018_countries(self):
        data = {}

        for folder in self._nat_desc_country_folders:
            url = folder.absolute_url()
            reg_id = folder.id.upper()
            data[reg_id] = url

        return data


    def get_2018_regions(self):
        data = {}

        for folder in self._reg_desc_region_folders:
            url = folder.absolute_url()
            reg_id = folder.id.upper()
            data[reg_id] = url

        return data

    def _make_subrow_row(self, text, data, extra_css_class):
        res = []
        _text = text
        css_class = extra_css_class + " {}"

        res.append((self._nr_of_countries, _text,
                    data.get('ROW', ''), css_class.format('ROW')))

        return res

    def _make_subrow_region(self, text, data, extra_css_class):
        res = []
        _text = text
        css_class = extra_css_class + " {}"

        for region_id, available_countries in self.regions_and_countries:
            if text == '_region':
                _text = region_id

            res.append((len(available_countries), _text,
                        data.get(region_id, ''), css_class.format(region_id)))

        return res

    def _make_subrow_country(self, text, data, extra_css_class):
        res = []
        _text = text
        css_class = extra_css_class + " {}-C"

        for region_id, available_countries in self.regions_and_countries:
            for country in available_countries:
                country_id = country[0]
                country_name = country[1]

                if text == '_country':
                    _text = country_id

                res.append((1, _text, data.get(country_id, ""),
                            css_class.format(region_id)))

        return res

    def make_subrow(self, colspan_type, text, data, extra_css_class):
        make_method = getattr(self, "_make_subrow_" + colspan_type)
        subrow_final = make_method(text, data, extra_css_class)

        return subrow_final

    def __init__(self, context, request, year_def):
        super(BaseLandingPageRow, self).__init__(context, request)

        data = []

        for row in year_def.rows:
            date = row[0]
            who = row[1]
            art = row[2]
            task = row[3]
            css = row[4]
            subrows = row[5]
            _subrows = []

            for subrow in subrows:
                colspan_type = subrow[0]
                text = subrow[1]
                get_data_method = subrow[2]
                subrow_data = getattr(self, get_data_method, self._default)()

                _subrows.append(
                    self.make_subrow(colspan_type, text, subrow_data, css)
                )

            data.append((date, who, art, task, css, _subrows))

        self.data = data

    def __call__(self):
        return self.template(data=self.data)
