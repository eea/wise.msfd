""" Classes and views to implement the National Descriptors compliance page
"""

from collections import namedtuple  # defaultdict,

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template

from ..base import BaseComplianceView  # , Container

# from wise.msfd import db, sql, sql2018
# from wise.msfd.base import BaseUtil, EmbededForm, MainFormWrapper
# from wise.msfd.gescomponents import get_ges_criterions
# from z3c.form.field import Fields
# from z3c.form.form import Form
#
# from ..vocabulary import form_structure
# from .a8 import Article8
# from .a10 import Article10

CountryStatus = namedtuple('CountryStatus', ['name', 'status', 'url'])


def get_assessment_data_2012(*args):
    """ Returns the 2012 assessment data, from COM_Assessments_2012 table
    """

    return []


def get_assessment_data_2018(*args):
    """ Returns the 2018 assessment data, from COM_Assessments table
    """

    return []


class NationalDescriptorsOverview(BaseComplianceView):
    name = 'nat-desc-start'

    def countries(self):
        countries = self.context.contentValues()

        return [CountryStatus(country.Title(), 'phase0',
                              country.absolute_url()) for country in countries]


class NationalDescriptorCountryOverview(BaseComplianceView):
    name = 'nat-desc-country-start'

    def get_status(self):
        return "Phase 1"

    def get_articles(self):
        return ['Art8', 'Art9', 'Art10']

    def get_descriptors(self):
        return self.context.contentValues()


class NationalDescriptorArticleView(BaseComplianceView):
    name = 'nat-desc-art-view'
    assessment_data_2012_tpl = Template('./pt/assessment-data-2012.pt')
    assessment_data_2018_tpl = Template('./pt/assessment-data-2018.pt')

    def __init__(self, context, request):
        super(NationalDescriptorArticleView, self).__init__(context, request)

        data = get_assessment_data_2012(
            self.country_code,
            self.descriptor,
            self.article
        )
        self.assessment_data_2012 = self.assessment_data_2012_tpl(data=data)

        data = get_assessment_data_2018(
            self.country_code,
            self.descriptor,
            self.article
        )
        self.assessment_data_2018 = self.assessment_data_2018_tpl(data=data)
