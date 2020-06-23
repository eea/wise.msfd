
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
    def __init__(self, year_node):
        date = year_node.attrib.get('date')

        rows = []

        for row in year_node.iterchildren('element'):
            who = row.attrib.get('who')
            article = row.attrib.get('article')
            task = row.attrib.get('task')
            subrows = []

            for subrow in row.iterchildren('row'):
                colspan = subrow.attrib.get('colspan')
                get_method = subrow.attrib.get('get-method')
                text = subrow.attrib.get('display-text')

                subrows.append((colspan, text, get_method))

            rows.append((date, who, article, task, subrows))

        self.rows = rows


class StartLandingPage(BaseComplianceView):
    """ Landing/Home page for assessment module """

    template = ViewPageTemplateFile("pt/landingpage.pt")
    year_defs = _parse_landingpage_xml()

    def __call__(self):
        data = []

        for year_def in self.year_defs:
            # import pdb; pdb.set_trace()
            rendered_row = BaseLandingPageRow(self, self.request, year_def)()

            data.append(rendered_row)

        return self.template(data=data)


class BaseLandingPageRow(BaseComplianceView, AssessmentDataMixin):
    """ Base class with all the needed base methods to build the landing page
        structure
    """

    template = PageTemplateFile('pt/landingpage-row.pt')

    def __init__(self, context, request, year_def):
        super(BaseLandingPageRow, self).__init__(context, request)

        self.data = year_def.rows

    def __call__(self):
        return self.template(data=self.data)


class BaseRegionRow(BaseLandingPageRow):
    data = {
        'BAL': "test link",
        'ATL': "test link",
        'MED': "test link",
        'BLK': 'test link'
    }
