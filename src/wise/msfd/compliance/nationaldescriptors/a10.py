from sqlalchemy import and_  # , or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from Products.Five.browser import BrowserView
from wise.msfd import db, sql


class Article10(BrowserView):
    template = Template('pt/compliance-a10.pt')

    def get_environment_data(self, muids):
        """ Get all data from a table
        :param muids: ['LV-001', 'LV-002', ...]
        :return: table result
        """
        mc = sql.MSFD10Target
        descr_nr = self.descriptor[1:]
        count, res = db.get_all_records(
            mc,
            and_(
                mc.Topic == 'EnvironmentalTarget',
                mc.ReportingFeature.like('%{}%'.format(descr_nr)),
                mc.MarineUnitID.in_(muids)
            )
        )

        if res:
            return res[0]

        return []

    def __call__(self):
        template = self.template
        self.content = template and template() or ""

        return self.content
