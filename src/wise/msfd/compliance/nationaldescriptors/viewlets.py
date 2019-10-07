from plone.app.layout.viewlets.common import TitleViewlet as BaseTitleViewlet

from .base import BaseView


class ReportTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_code,
            'descriptor': self.descriptor_title,
            'region': self.country_region_code,
            'year': self.view.report_year,
        }

        return (u'{country}/{region}/{descriptor}/'
                u'{article}/{year}-Report'.format(**params))


class AssessmentEditTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_code,
            'descriptor': self.descriptor,
            'region': self.country_region_code,
        }

        return (u'{country}/{region}/'
                u'{descriptor}/{article}-Assessment'.format(**params))


class ArticleTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'article': self.article,
            'country': self.country_code,
            'descriptor': self.descriptor,
            'region': self.country_region_code,
        }

        return (u'{country}/{region}/'
                u'{descriptor}/{article}-Overview'.format(**params))
