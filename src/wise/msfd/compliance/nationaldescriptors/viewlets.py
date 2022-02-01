from __future__ import absolute_import
from plone.app.layout.viewlets.common import TitleViewlet as BaseTitleViewlet

from ..nationalsummary.base import BaseNatSummaryView
from .base import BaseView
from .main import (NatDescCountryOverviewAssessments,
                   NatDescCountryOverviewReports)


class ReportTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
            'year': self.view.report_year,
        }

        return (u'MS/{article}/{year}/{descriptor}/'
                u'{country}/{region}'.format(**params))


class ReportTitleViewletOverview(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'country': self.country_name,
            'region': self.country_region_name,
            'year': self.view.report_year,
        }

        return (u'MS/Art11/{year}/'
                u'{country}/{region}/Overview'.format(**params))


class SecondaryReportTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
            'year': self.view.report_year,
        }

        return (u'MS/{article}/'
                u'{year}/{country}'.format(**params))


class AssessmentEditTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
        }

        return (u'Edit COM/{article}/2018/{descriptor}/'
                u'{country}/{region}'.format(**params))


class AssessmentEditTitleViewletSecondary(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
        }

        return (u'Edit COM/{article}/2018/'
                u'{country}'.format(**params))


class ArticleTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
        }

        return (u'COM/{article}/2018/{descriptor}/'
                u'{country}/{region}'.format(**params))


class SecondaryArticleTitleViewlet(BaseTitleViewlet, BaseView):
    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_name,
        }

        return u'COM/{article}/{country}'.format(**params)


class SummaryCountryTitleViewlet(BaseTitleViewlet, BaseNatSummaryView):
    @property
    def page_title(self):
        params = {
            'country': self.country_name
        }

        return u'COM/Art12/2018/{country}-Summary'.format(**params)


class CountryStartReportsTitleViewlet(BaseTitleViewlet,
                                      NatDescCountryOverviewReports):

    @property
    def page_title(self):
        params = {
            'country': self.country_name
        }

        return u'MS/{country}'.format(**params)


class CountryStartAssessmentsTitleViewlet(BaseTitleViewlet,
                                          NatDescCountryOverviewAssessments):

    @property
    def page_title(self):
        params = {
            'country': self.country_name
        }

        return u'COM/{country}'.format(**params)
