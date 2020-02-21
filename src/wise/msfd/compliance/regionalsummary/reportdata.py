# -*- coding: utf-8 -*-

from io import BytesIO
from pkg_resources import resource_filename

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from wise.msfd import sql, db
from wise.msfd.compliance.interfaces import (IDescriptorFolder,
                                             INationalDescriptorAssessment,
                                             INationalDescriptorsFolder,
                                             INationalRegionDescriptorFolder)
from wise.msfd.compliance.utils import ordered_regions_sortkey
from wise.msfd.data import get_report_filename
from wise.msfd.translation import get_translated, retrieve_translation
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from lpod.document import odf_new_document
from lpod.toc import odf_create_toc

import pdfkit

from ..nationaldescriptors.a7 import Article7
from ..nationaldescriptors.a34 import Article34
from ..nationaldescriptors.base import BaseView
from .base import BaseRegSummaryView


logger = logging.getLogger('wise.msfd')


class PressuresActivities(BaseRegSummaryView):
    template = ViewPageTemplateFile("pt/pressures-activities.pt")

    pressures_table = sql.t_MSFD_8b_8bPressures

    @property
    @db.use_db_session('2012')
    def pressures(self):
        table = self.pressures_table
        pressures = db.get_unique_from_table(table, 'Pressure')

        return pressures

    @db.use_db_session('2012')
    def get_db_data(self):
        table = self.pressures_table
        columns_needed = ('MemberState', 'Marine region/subregion',
                          'Pressure', 'Activity')
        columns = [
            getattr(table.c, c)
            for c in columns_needed
        ]
        conditions = [
            getattr(table.c, 'Marine region/subregion').in_(
                self._region_folder._subregions
            ),
            table.c.Activity != 'NotReported'
        ]

        _, data = db.get_all_specific_columns(
            columns,
            *conditions
        )

        return data

    def setup_data(self):
        db_data = self.get_db_data()

        rows = []

        for pressure in self.pressures:
            values = []
            for country_id, country_name in self.available_countries:
                activities_for_country = [
                    r.Activity
                    for r in db_data
                    if (r.Pressure == pressure
                        and r.MemberState == country_id)
                ]

                # import pdb; pdb.set_trace()

                values.append("; ".join(activities_for_country))

            rows.append((pressure, values))

        import pdb; pdb.set_trace()

        return rows

    def __call__(self):
        data = self.setup_data()

        return self.template(data=data)


class RegionalSummaryView(BaseRegSummaryView):
    help_text = "HELP TEXT"
    template = ViewPageTemplateFile('pt/report-data.pt')
    year = "2012"

    render_header = True

    # @cache(get_reportdata_key, dependencies=['translation'])
    @timeit
    def render_reportdata(self):
        report_header = self.report_header_template(
            title="Regional summary report: {}".format(
                self.country_name,
            ),
            countries=", ".join([x[1] for x in self.available_countries])
        )
        # trans_edit_html = self.translate_view()()

        self.tables = [
            report_header,
            PressuresActivities(self, self.request),
            # trans_edit_html,
        ]

        template = self.template

        return template(tables=self.tables)

    def __call__(self):
        if 'edit-data' in self.request.form:
            url = "{}/edit".format(self._country_folder.absolute_url())
            return self.request.response.redirect(url)

        report_html = self.render_reportdata()
        self.report_html = report_html

        if 'translate' in self.request.form:
            for value in self._translatable_values:
                retrieve_translation(self.country_code, value)

            messages = IStatusMessage(self.request)
            messages.add(u"Auto-translation initiated, please refresh "
                         u"in a couple of minutes", type=u"info")

        @timeit
        def render_html():
            return self.index()

        return render_html()
