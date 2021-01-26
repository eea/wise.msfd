from plone.app.layout.viewlets.common import TitleViewlet

from ..regionalsummary.base import BaseRegSummaryView
from .base import BaseRegComplianceView
from .main import (RegDescRegionOverviewReports, RegDescRegionOverviewAssessments)


class ReportTitleViewlet(TitleViewlet, BaseRegComplianceView):
    @property
    def page_title(self):
        params = {
            'article': self.article,
            'year': self.view.year,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
        }

        return (u'MS/{article}/{year}/{descriptor}/'
                u'{region}'.format(**params))


class ReportTitleViewletOverview(TitleViewlet, BaseRegComplianceView):

    @property
    def page_title(self):
        params = {
            'region': self.country_region_name,
            'year': self.view.report_year,
        }

        return (u'MS/Art11/{year}/'
                u'{region}/Overview'.format(**params))


class AssessmentEditTitleViewlet(TitleViewlet, BaseRegComplianceView):
    @property
    def page_title(self):
        params = {
            'article': self.article,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
        }

        return (u"Edit COM/{article}/2018/{descriptor}/"
                u"{region}".format(**params))


class ArticleTitleViewlet(TitleViewlet, BaseRegComplianceView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'descriptor': self.descriptor_title,
            'region': self.country_region_name,
        }

        return (u'COM/{article}/2018/{descriptor}/'
                u'{region}'.format(**params))


class SummaryRegionTitleViewlet(TitleViewlet, BaseRegSummaryView):
    @property
    def page_title(self):
        params = {
            'region': self.region_name
        }

        return u'COM/Art12/2018/{region}-Summary'.format(**params)


class RegionStartReportsTitleViewlet(TitleViewlet,
                                     RegDescRegionOverviewReports):

    @property
    def page_title(self):
        params = {
            'region': self.country_region_name
        }

        return u'MS/{region}'.format(**params)


class RegionStartAssessmentsTitleViewlet(TitleViewlet,
                                         RegDescRegionOverviewAssessments):

    @property
    def page_title(self):
        params = {
            'region': self.country_region_name
        }

        return u'COM/{region}'.format(**params)
