import logging
from sqlalchemy import or_

from zope.interface import implements
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql2018
from wise.msfd.compliance.interfaces import IReportDataView
from wise.msfd.utils import (CompoundRow, ItemList, items_to_rows, timeit,
                             natural_sort_key, Row)

from .a9 import RegDescA92018Row
from .base import BaseRegComplianceView
from .data import get_report_definition

logger = logging.getLogger('wise.msfd')


class RegReportData2018(BaseRegComplianceView):
    # implements(IReportDataView)

    help_text = "HELP TEXT"

    Art8 = ViewPageTemplateFile('pt/report-data.pt')
    Art9 = ViewPageTemplateFile('pt/report-data.pt')
    Art10 = ViewPageTemplateFile('pt/report-data.pt')

    def get_countries_row(self):
        country_names = [x[1] for x in self.available_countries]

        # return TableHeader('Member state', country_names)
        return CompoundRow("Member state", [Row("", country_names)])

    @property
    def get_data_from_view_Art9(self):
        t = sql2018.t_V_ART9_GES_2018
        descriptor = self.descriptor_obj
        all_ids = list(descriptor.all_ids())

        if self.descriptor.startswith('D1.'):
            all_ids.append('D1')

        count, q = db.get_all_records_ordered(
            t,
            ('GESComponent',),
            or_(t.c.Region == self.country_region_code,
                t.c.Region.is_(None)),
            t.c.GESComponent.in_(all_ids),
        )

        return q

    @db.use_db_session('2018')
    def get_report_data(self):
        db_data = getattr(self, 'get_data_from_view_' + self.article, None)

        countries = self.available_countries
        region = self.country_region_code
        descriptor_obj = self.descriptor_obj

        fields = get_report_definition('2018', self.article).get_fields()

        result = [self.get_countries_row()]

        for field in fields:
            if not field.getrowdata:
                continue

            row_class = RegDescA92018Row(db_data, descriptor_obj, region,
                                         countries, field)
            field_data = getattr(row_class, field.getrowdata)()
            result.append(field_data)

        return result

    # @cache(get_reportdata_key, dependencies=['translation'])
    def render_reportdata(self):
        logger.info("Quering database for 2018 report data: %s %s %s",
                    self.country_region_code, self.article,
                    self.descriptor)

        data = self.get_report_data()

        report_header = self.report_header_template(
            title="Member State report: {} / {} / {} / 2018".format(
                self.country_region_name,
                self.descriptor_title,
                self.article
            ),
            factsheet=None,
            # TODO: find out how to get info about who reported
            report_by='Report by',
            report_due='2018-10-15',
            help_text=self.help_text
        )

        template = getattr(self, self.article, None)

        return template(data=data, report_header=report_header)

    def __call__(self):
        report_html = self.render_reportdata()
        self.report_html = report_html

        @timeit
        def render_html():
            return self.index()

        return render_html()