from plone.app.layout.viewlets.common import TitleViewlet as BaseTitleViewlet

from .base import BaseView


class TitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'country': self.country_code,
            'region': self.country_region_code,
            'article': self.article,
            'descriptor': self.descriptor_title,
            'year': self.view.report_year,
        }

        return (u'{country}/{region}/{descriptor}/'
                u'{article}/{year}-Report'.format(**params))


class EditAssessmentTitleViewlet(BaseTitleViewlet, BaseView):

    @property
    def page_title(self):
        params = {
            'country': self.country_code,
            'region': self.country_region_code,
            'descriptor': self.descriptor,
            'article': self.article,
        }

        return (u'{country}/{region}/'
                u'{descriptor}/{article}-Assessment'.format(**params))
