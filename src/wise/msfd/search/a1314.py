""" Forms and views for Article 13-14 search
"""
from sqlalchemy import and_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..db import get_all_records, get_all_records_join
from ..interfaces import IMarineUnitIDsSelect
from .. labels import COMMON_LABELS, GES_LABELS
from ..utils import default_value_from_field
from .base import ItemDisplayForm, MainForm
from .utils import data_to_xls, register_form_art1314

# all_values_from_field,#


class StartArticle1314Form(MainForm):
    fields = Fields(interfaces.IStartArticles1314)
    name = 'msfd-c3'

    session_name = '2012'

    def get_subform(self):
        klass = self.data.get('report_type')

        return klass(self, self.request)

    # This is needed because of metatype weirdness. Would be nice to have an
    # explanation of why this happens, only for this MainForm
    def default_report_type(self):
        return default_value_from_field(self, self.fields['report_type'])


@register_form_art1314
class Article13Form(EmbeddedForm):
    record_title = title = 'Article 13 - Measures'
    report_type = "Measures"
    session_name = '2012'

    fields = Fields(interfaces.IArticles1314Region)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


# @register_form_art1314
class StartArticle14Form(MainForm):
    record_title = title = 'Article 14 - Exceptions'
    report_type = "Exceptions"
    session_name = '2012'
    name = 'msfd-a14'

    fields = Fields(interfaces.IArticles1314Region)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return MemberStatesForm(self, self.request)


class MemberStatesForm(EmbeddedForm):
    """ Select the member states based on region
    """
    fields = Fields(interfaces.IA1314MemberStates)

    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        mc = sql.MSFD13ReportingInfo
        report_type = self.context.report_type
        count, mrus = self.get_available_marine_unit_ids()

        count, res = db.get_all_records(
            mc.ID,
            mc.MarineUnitID.in_(mrus),
            mc.ReportType == report_type
        )
        self.data['report_ids'] = [x[0] for x in res]

        mc = sql.MSFD13Measure

        count, res = db.get_all_records(
            mc,
            mc.ReportID.in_(self.data['report_ids'])
        )
        res = set([x.UniqueCode for x in set(res)])
        self.data['unique_codes'] = sorted(res)

        return A1314ItemDisplay(self, self.request)

    def get_available_marine_unit_ids(self):
        # TODO: use available marine unit ids from t_MSFD4_GegraphicalAreasID
        mc = sql.MSFD13ReportingInfo

        ms = self.get_selected_member_states()
        report_type = self.context.report_type

        count, res = db.get_all_records_join(
            [mc.MarineUnitID],
            sql.MSFD13ReportingInfoMemberState,
            and_(sql.MSFD13ReportingInfoMemberState.MemberState.in_(ms),
                 mc.ReportType == report_type),
        )

        return [count, [x[0] for x in res]]


class MarineUnitIDsForm(MarineUnitIDSelectForm):
    """ Select the MarineUnitID based on MemberState, Region and Area
    """

    # TODO: properly show only available marine unit ids

    def get_available_marine_unit_ids(self):
        return self.context.get_available_marine_unit_ids()

    def get_subform(self):
        mc = sql.MSFD13ReportingInfo
        report_klass = self.get_form_data_by_key(self, 'report_type')
        report_type = report_klass.report_type

        count, res = db.get_all_records(
            mc.ID,
            mc.MarineUnitID == self.data.get('marine_unit_id', ''),
            mc.ReportType == report_type
        )
        self.data['report_ids'] = [x[0] for x in res]

        mc = sql.MSFD13Measure

        count, res = db.get_all_records(
            mc,
            mc.ReportID.in_(self.data['report_ids'])
        )
        # res = set([(x.UniqueCode, x.Name) for x in set(res)])
        res = set([x.UniqueCode for x in set(res)])
        self.data['unique_codes'] = sorted(res)

        return A1314ItemDisplay(self, self.request)

        # return UniqueCodesForm(self, self.request)


class UniqueCodesForm(EmbeddedForm):
    """ Select the unique codes
    """

    fields = Fields(interfaces.IA1314UniqueCodes)

    fields['unique_codes'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A1314ItemDisplay(self, self.request)


class A1314ItemDisplay(ItemDisplayForm):
    """ The implementation for the Article 9 (GES determination) form
    """
    extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')
    pivot_template = ViewPageTemplateFile('pt/extra-data-pivot-notselect.pt')

    mapper_class = sql.MSFD13MeasuresInfo
    order_field = 'ID'
    css_class = 'left-side-form'
    
    blacklist = ['ReportID', 'MeasureID']
    use_blacklist = True

    reported_date_info = {
        'mapper_class': sql.MSFD13Import,
        'col_import_id': 'ID',
        'col_import_time': 'Time',
        'col_filename': 'FileName'
    }

    def get_import_id(self):
        report_id = self.item.ReportID

        _, res = db.get_related_record(
            sql.MSFD13ReportingInfo,
            'ID',
            report_id
        )

        import_id = res.Import

        return import_id

    def get_record_title(self):
        values = {
            "Measures": 'Article 13 - Measures',
            "Exceptions": 'Article 14 - Exceptions'
        }

        report_type = self.context.context.report_type

        record_title = values[report_type]

        return record_title

    def get_current_country(self):
        if not self.item:
            return

        mc = sql.MSFD13ReportingInfoMemberState
        report_id = self.item.ReportID

        count, data = get_all_records(
            mc,
            mc.ReportID == report_id
        )
        country_code = data[0].MemberState
        print_value = self.print_value(country_code)

        return print_value

    def download_results(self):
        mc_join = sql.MSFD13ReportingInfoMemberState

        mc_fields = self.get_obj_fields(self.mapper_class, False)
        fields = [mc_join.MemberState] + \
                 [getattr(self.mapper_class, field) for field in mc_fields]

        codes = self.context.data.get('unique_codes', [])

        sess = db.session()
        q = sess.query(*fields).\
            join(mc_join, self.mapper_class.ReportID == mc_join.ReportID).\
            filter(self.mapper_class.UniqueCode.in_(codes))
        data = [x for x in q]

        report_ids = [row.ReportID for row in data]
        mc_report = sql.MSFD13ReportInfoFurtherInfo
        count, data_report = get_all_records(
            mc_report,
            mc_report.ReportID.in_(report_ids)
        )

        xlsdata = [
            ('MSFD13MeasuresInfo', data),  # worksheet title, row data
            ('MSFD13ReportInfoFurtherInfo', data_report),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        mc = self.mapper_class
        mc_join = sql.MSFD13Measure
        mc_import = sql.MSFD13ReportingInfo

        count, item, extra_data = db.get_collapsed_item(
            mc,
            mc_join,
            self.order_field,
            [{'InfoType': ['InfoText']}],
            mc.UniqueCode.in_(self.context.data.get('unique_codes', [])),
            page=page,
            mc_join_cols=['Name']
        )

        report_id = item.ReportID
        _, mru = db.get_related_record(mc_import, 'ID', report_id)

        mru = mru.MarineUnitID

        env_target_labels = getattr(GES_LABELS, 'env_targets')

        env_targets = extra_data.items()[0][1]["RelevantEnvironmentalTargets"]

        for row in env_targets:
            label = env_target_labels[mru].get(row['InfoText'], '')
            if label:
                row['InfoText'] = label

        self.extra_data = extra_data.items()

        return [count, item]

    def get_extra_data(self):
        if not self.item:
            return {}

        report_id = self.item.ReportID
        mc = sql.MSFD13ReportInfoFurtherInfo

        count, item = db.get_related_record(mc, 'ReportID', report_id)

        if not item:
            return '', {}

        return ('Report info', item)

    def extras(self):
        html = self.pivot_template(extra_data=self.extra_data)
        extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

        report_id = self.item.ReportID
        mc = sql.MSFD13ReportingInfo

        count, marine_units = db.get_all_records(
            mc,
            mc.ID == report_id
        )

        marine_units = [x.MarineUnitID for x in marine_units]

        mrus_extra = [
            ('', {
                '': [{'Marine Unit(s)': x} for x in marine_units]
            })
        ]

        return (self.extra_data_template() + html +
                extra_data_template(self, extra_data=mrus_extra))

    def custom_print_value(self, row_label, val):
        """ Used to create a customized print value, like adding the
            descriptor code into the label
            for a specific data section(row_label)

        :param row_label: 'RelevantGESDescriptors'
        :param val: 'D5'
        :return:
        """

        row_labels = ('RelevantGESDescriptors', )

        if row_label in row_labels:
            label = COMMON_LABELS.get(val, val)
            value = '<span title="{0}">({0}) {1}</span>'.format(val, label)

            return value

        return self.print_value(val)
