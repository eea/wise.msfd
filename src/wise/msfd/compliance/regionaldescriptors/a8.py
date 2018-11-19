
from eea.cache import cache

from wise.msfd import db, sql, sql_extra
from wise.msfd.gescomponents import get_ges_criterions
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)

from ..base import BaseComplianceView
from .utils import (Row, CompoundRow, TableHeader, List,
                    countries_in_region, muids_by_country, get_key,
                    get_percentage)


class RegDescA8(BaseComplianceView):
    session_name = '2012'
    template = ViewPageTemplateFile('pt/report-data-table.pt')

    @property
    def descriptor(self):
        return 'D5'

    def __call__(self):
        db.threadlocals.session_name = self.session_name

        self.region = 'BAL'

        self.countries = countries_in_region(self.region)
        self.all_countries = muids_by_country()

        self.import_data = self.get_import_data()

        allrows = [
            self.get_countries(),
            self.get_marine_unit_id_nrs(),
            self.get_suminfo1(),
            self.get_suminfo2(),
            self.get_criteria_status(),
            self.get_activity_type(),
            self.get_assessment_date()
        ]

        return self.template(rows=allrows)

    def get_import_data(self):
        mc = sql.MSFD8bImport

        count, res = db.get_all_records(
            mc,
            mc.MSFD8b_Import_ReportingRegion == self.region
        )

        return res

    def get_import_id(self, country):
        for imp in self.import_data:
            if imp.MSFD8b_Import_ReportingCountry == country:
                import_id = imp.MSFD8b_Import_ID

                return import_id

        return 0

    def get_countries(self):
        return TableHeader('Member state', self.countries)

    def get_marine_unit_id_nrs(self):
        row = Row('Number used',
                  [len(self.all_countries[c]) for c in self.countries])

        return CompoundRow('MarineUnitID [Reporting area]', [row])

    def get_suminfo1(self):
        pass

    def get_suminfo2(self):
        pass

    def get_criteria_status(self):
        pass

    def get_activity_type(self):
        pass

    def get_assessment_date(self):
        pass
