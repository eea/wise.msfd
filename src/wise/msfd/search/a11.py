from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from .. import db, sql
from ..interfaces import IMarineUnitIDsSelect
from ..base import EmbeddedForm
from ..utils import (all_values_from_field, data_to_xls, db_objects_to_dict,
                     pivot_data, register_form_art11, register_form_section)
from .base import ItemDisplay, ItemDisplayForm, MainForm, MultiItemDisplayForm
from . import interfaces

# default_value_from_field,
# TODO: cache in klass
# ART11_GlOBALS = dict()


class StartArticle11Form(MainForm):
    """
    """

    record_title = 'Article 11'
    name = 'msfd-c2'
    session_name = 'session'

    fields = Fields(interfaces.IStartArticle11)
    fields['monitoring_programme_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.data.get('monitoring_programme_info_type')

        return klass(self, self.request)

    def get_mp_type_ids(self):
        return self.data.get('monitoring_programme_types', [])

    def default_monitoring_programme_types(self):
        field = self.fields['monitoring_programme_types']

        return [int(x) for x in all_values_from_field(self, field)]

    # def default_monitoring_programme_info_type(self):
    #     klass, token = default_value_from_field(
    #         self, self.fields['monitoring_programme_info_type']
    #     )
    #
    #     return klass


class A11MProgMemberStateForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.context.mru_class

        return klass(self, self.request)

    def get_available_marine_unit_ids(self):
        # TODO: use available marine unit ids from t_MSFD4_GegraphicalAreasID

        ms = self.get_selected_member_states()
        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            sql.MSFD11MON.MemberState.in_(ms)
        )
        mon_ids = [str(x).strip() for x in mon_ids]

        mon_prog_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            and_(sql.MSFD11MP.MON.in_(mon_ids)
                 # ,sql.MSFD11MP.MPType.in_(mp_type_ids)
                 )
        )
        mon_prog_ids = [x.strip() for x in mon_prog_ids]

        s = sql.MSFD11MonitoringProgrammeMarineUnitID
        count, marine_units = db.get_all_records_outerjoin(
            sql.MSFD11MarineUnitID,
            s,
            s.MonitoringProgramme.in_(mon_prog_ids)
        )
        mrus = [x.MarineUnitID for x in marine_units]

        return [count, mrus]


class A11MSubMemberStateForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.context.mru_class

        return klass(self, self.request)

    def get_available_marine_unit_ids(self):
        # TODO: use available marine unit ids from t_MSFD4_GegraphicalAreasID

        mp_type_ids = self.context.get_mp_type_ids()
        mptypes_subprog = self.context.get_mptypes_subprog()
        member_states = self.get_selected_member_states()

        submonprog_ids = []

        for x in mp_type_ids:
            submonprog_ids.extend(mptypes_subprog[int(x)])

        subprogramme_ids = db.get_unique_from_mapper(
            sql.MSFD11MONSub,
            'SubProgramme',
            and_(sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids),
                 sql.MSFD11MONSub.MemberState.in_(member_states))
        )

        subprogramme_ids = [int(x) for x in subprogramme_ids]

        q4g_subprogids_1 = db.get_unique_from_mapper(
            sql.MSFD11SubProgramme,
            'Q4g_SubProgrammeID',
            sql.MSFD11SubProgramme.ID.in_(subprogramme_ids)
        )
        q4g_subprogids_2 = db.get_unique_from_mapper(
            sql.MSFD11SubProgrammeIDMatch,
            'MP_ReferenceSubProgramme',
            sql.MSFD11SubProgrammeIDMatch.Q4g_SubProgrammeID.in_(
                q4g_subprogids_1)
        )

        mc_ref_sub = sql.MSFD11ReferenceSubProgramme
        mp_from_ref_sub = db.get_unique_from_mapper(
            sql.MSFD11ReferenceSubProgramme,
            'MP',
            or_(mc_ref_sub.SubMonitoringProgrammeID.in_(q4g_subprogids_1),
                mc_ref_sub.SubMonitoringProgrammeID.in_(q4g_subprogids_2)
                )
        )
        mp_from_ref_sub = [int(x) for x in mp_from_ref_sub]

        mon_prog_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            sql.MSFD11MP.ID.in_(mp_from_ref_sub)
        )

        mc_ = sql.MSFD11MonitoringProgrammeMarineUnitID
        count, marine_units = db.get_all_records_outerjoin(
            sql.MSFD11MarineUnitID,
            mc_,
            mc_.MonitoringProgramme.in_(mon_prog_ids)
        )
        mrus = [x.MarineUnitID for x in marine_units]

        return [count, mrus]


class A11MProgMarineUnitIdForm(EmbeddedForm):
    fields = Fields(IMarineUnitIDsSelect)
    # fields = Fields(interfaces.IMonitoringProgramme)
    fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A11MonProgDisplay(self, self.request)


class A11MSubMarineUnitIdForm(EmbeddedForm):
    fields = Fields(IMarineUnitIDsSelect)
    # fields = Fields(interfaces.IMonitoringSubprogramme)
    fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A11MonSubDisplay(self, self.request)


class A11MonProgDisplay(ItemDisplayForm):
    title = "Monitoring Programmes display"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql.MSFD11MonitoringProgramme
    order_field = 'ID'
    css_class = 'left-side-form'

    def download_results(self):
        mp_type_ids = self.context.context.context.context.get_mp_type_ids()
        mon_prog_ids = self.context.context.context\
            .get_monitoring_programme_ids()

        klass_join_mp = sql.MSFD11MP
        count_mp, data_mp = db.get_all_records_outerjoin(
            self.mapper_class,
            klass_join_mp,
            and_(klass_join_mp.MPType.in_(mp_type_ids),
                 klass_join_mp.MonitoringProgramme.in_(mon_prog_ids)),
        )

        mp_ids = [row.ID for row in data_mp]

        mapper_class_mpl = sql.MSFD11MonitoringProgrammeList
        count_mpl, data_mpl = db.get_all_records(
            mapper_class_mpl,
            mapper_class_mpl.MonitoringProgramme.in_(mp_ids)
        )

        mapper_class_mpmid = sql.MSFD11MonitoringProgrammeMarineUnitID
        count_mpmid, data_mpmid = db.get_all_records_join(
            [
                mapper_class_mpmid.ID,
                mapper_class_mpmid.MonitoringProgramme,
                sql.MSFD11MarineUnitID.MarineUnitID
            ],
            sql.MSFD11MarineUnitID,
            mapper_class_mpmid.MonitoringProgramme.in_(mp_ids)
        )

        mapper_class_rt = sql.MSFD11Q6aRelevantTarget
        count_mpl, data_rt = db.get_all_records(
            mapper_class_rt,
            mapper_class_rt.MonitoringProgramme.in_(mp_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD11MonitoringProgramme', data_mp),
            ('MSFD11MonitoringProgrammeList', data_mpl),
            ('MSFD11MonitorProgMarineUnitID', data_mpmid),
            ('MSFD11Q6aRelevantTarget', data_rt),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        klass_join = sql.MSFD11MP
        needed_ID = self.context.context.context.context.get_mp_type_ids()
        ggp = self.context.context.context
        mon_prog_ids = ggp.get_monitoring_programme_ids()

        if needed_ID:
            [count, item] = db.get_item_by_conditions_joined(
                self.mapper_class,
                klass_join,
                self.order_field,
                and_(klass_join.MPType.in_(needed_ID),
                     klass_join.MonitoringProgramme.in_(mon_prog_ids)),
                page=page
            )
            # import pdb; pdb.set_trace()
            item.whitelist = ['Q4e_ProgrammeID']

            return [count, item]

    def get_extra_data(self):
        if not self.item:
            return {}

        monitoring_programme_id = self.item.ID

        excluded_columns = ('MonitoringProgramme', 'ID')
        mapper_class_mp_list = sql.MSFD11MonitoringProgrammeList
        column = 'MonitoringProgramme'
        result_programme_list = db.get_all_columns_from_mapper(
            mapper_class_mp_list,
            column,
            getattr(mapper_class_mp_list, column) == monitoring_programme_id
        )

        mapper_class_target = sql.MSFD11Q6aRelevantTarget
        targets = db.get_unique_from_mapper(
            mapper_class_target,
            'RelevantTarget',
            getattr(mapper_class_target, column) == monitoring_programme_id
        )

        mapper_class_mp_marine = sql.MSFD11MonitoringProgrammeMarineUnitID
        total, marine_units = db.get_unique_from_mapper_join(
            sql.MSFD11MarineUnitID,
            'MarineUnitID',
            mapper_class_mp_marine,
            'ID',
            getattr(mapper_class_mp_marine, column) == monitoring_programme_id
        )

        element_names = db_objects_to_dict(result_programme_list,
                                           excluded_columns)
        element_names = pivot_data(element_names, 'ElementName')

        res = [
            ('Element Names', element_names),
        ]

        if marine_units:
            res.append(
                ('Marine Unit(s)', {
                    '': [{'MarineUnitIDs': x} for x in marine_units]
                }))

        if targets:
            res.append(
                ('Target(s)', {
                    '': [{'Relevant Targets': x} for x in targets]
                }))

        return res


@register_form_art11
class A11MonitoringProgrammeForm(EmbeddedForm):
    title = "Monitoring Programmes"
    mru_class = A11MProgMarineUnitIdForm

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    # fields = Fields(interfaces.IMonitoringProgramme)
    # fields['regions'].widgetFactory = CheckBoxFieldWidget
    # fields['countries'].widgetFactory = CheckBoxFieldWidget
    # fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A11MProgMemberStateForm(self, self.request)

        # return A11MonProgDisplay(self, self.request)

    # def default_regions(self):
    #     return all_values_from_field(self, self.fields['region_subregions'])
    #
    # def default_countries(self):
    #     regions = self.data.get('regions')
    #
    #     if regions:
    #         mp_type_ids = self.context.get_mp_type_ids()
    #         mon_ids = db.get_unique_from_mapper(
    #             sql.MSFD11MP,
    #             'MON',
    #             sql.MSFD11MP.MPType.in_(mp_type_ids)
    #         )
    #         res = db.get_unique_from_mapper(
    #             sql.MSFD11MON,
    #             'MemberState',
    #             sql.MSFD11MON.ID.in_(mon_ids),
    #             sql.MSFD11MON.Region.in_(regions)
    #         )
    #
    #         return [x.strip() for x in res]
    #
    #     return all_values_from_field(self, self.fields['member_states'])
    #
    # def default_marine_unit_ids(self):
    #     return all_values_from_field(self, self.fields['marine_unit_ids'])

    def get_monitoring_programme_ids(self):
        regions = self.data.get('region_subregions', [])
        countries = self.subform.data.get('member_states', [])
        marine_unit_id = self.subform.subform.data.get('marine_unit_ids', [])
        mp_type_ids = self.context.get_mp_type_ids()

        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            and_(sql.MSFD11MON.MemberState.in_(countries),
                 sql.MSFD11MON.Region.in_(regions))
        )
        mon_prog_ids_from_MP = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            and_(sql.MSFD11MP.MON.in_(mon_ids),
                 sql.MSFD11MP.MPType.in_(mp_type_ids)
                 )
        )
        mon_prog_ids_from_MP = [int(elem) for elem in mon_prog_ids_from_MP]

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            sql.MSFD11MarineUnitID.MarineUnitID.in_(marine_unit_id)
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]

        result = tuple(set(mon_prog_ids_from_MP) & set(mon_prog_ids))

        if not result:
            result = tuple(mon_prog_ids_from_MP + mon_prog_ids)

        return result

    def get_mp_type_ids(self):
        # used by vocabularies, easier to pass from context

        return self.context.get_mp_type_ids()


@register_form_art11
class A11MonitorSubprogrammeForm(EmbeddedForm):
    title = "Monitoring Subprogrammes"
    mru_class = A11MSubMarineUnitIdForm

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    # fields = Fields(interfaces.IMonitoringSubprogramme)
    # fields['regions'].widgetFactory = CheckBoxFieldWidget
    # fields['countries'].widgetFactory = CheckBoxFieldWidget
    # fields['marine_unit_ids'].widgetFactory = CheckBoxFieldWidget

    def __init__(self, context, request):
        EmbeddedForm.__init__(self, context, request)
        self.__mptypes_subprog = None

    def get_mp_type_ids(self):
        # used by vocabularies, easier to pass from context

        return self.context.get_mp_type_ids()

    # creates a mapping between <Monitoring Program Type ID>: SubProgrammes
    def get_mptypes_subprog(self):
        mapping = self.__mptypes_subprog

        if mapping:
            return mapping

        res = {}
        mptypes = db.get_all_columns_from_mapper(sql.MSFD11MPType, 'ID')

        for row in mptypes:
            mpid, value = row.ID, row.Value   # MP_D8, MP_D1_4_6_SeabedHabitats
            mp_ids = db.get_unique_from_mapper(
                sql.MSFD11MP,
                'ID',
                sql.MSFD11MP.MPType == mpid
            )

            # subprogrammes based on monitoring programme
            sub_mon_prog_ids_1 = db.get_unique_from_mapper(
                sql.MSFD11ReferenceSubProgramme,
                'SubMonitoringProgrammeID',
                sql.MSFD11ReferenceSubProgramme.MP.in_(mp_ids)
            )

            # programmes based on Q4g ?
            sub_mon_prog_ids_2 = db.get_unique_from_mapper(
                sql.MSFD11SubProgrammeIDMatch,
                'Q4g_SubProgrammeID',
                sql.MSFD11SubProgrammeIDMatch.MP_Type == value
            )

            # subprogrammes based on Q4g
            sub_mon_prog_ids_3 = db.get_unique_from_mapper(
                sql.MSFD11SubProgrammeIDMatch,
                'Q4g_SubProgrammeID',
                sql.MSFD11SubProgrammeIDMatch.MP_ReferenceSubProgramme.in_(
                    sub_mon_prog_ids_1
                )
            )
            sub_mon_prog_ids_all = (sub_mon_prog_ids_1 +
                                    sub_mon_prog_ids_2 +
                                    sub_mon_prog_ids_3)

            subprogramme_ids = db.get_unique_from_mapper(
                sql.MSFD11SubProgramme,
                'ID',
                sql.MSFD11SubProgramme.Q4g_SubProgrammeID.in_(
                    sub_mon_prog_ids_all
                )
            )
            subprogramme_ids = [int(x) for x in subprogramme_ids]
            res[mpid] = subprogramme_ids

        self.__mptypes_subprog = res

        return res

    def get_subform(self):
        return A11MSubMemberStateForm(self, self.request)
        # return A11MonSubDisplay(self, self.request)

    # def default_countries(self):
    #     # TODO: this needs to be adjusted for subprogrammes
    #
    #     regions = self.data.get('region_subregions')
    #
    #     if regions:
    #         submonprog_ids = []
    #         mptypes_subprog = self.get_mptypes_subprog()
    #         mp_type_ids = self.get_mp_type_ids()
    #
    #         for mid in mp_type_ids:
    #             submonprog_ids.extend(mptypes_subprog[int(mid)])
    #
    #         res = db.get_unique_from_mapper(
    #             sql.MSFD11MONSub,
    #             'MemberState',
    #             sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids),
    #             sql.MSFD11MONSub.Region.in_(regions),
    #         )
    #
    #         return res
    #
    #     return all_values_from_field(self, self.fields['member_states'])
    #
    # def default_regions(self):
    #     return all_values_from_field(self, self.fields['region_subregions'])
    #
    # def default_marine_unit_ids(self):
    #     return all_values_from_field(self, self.fields['marine_unit_ids'])


class A11MonSubDisplay(MultiItemDisplayForm):

    title = "Monitoring Subprogramme display"

    # fields = Fields(interfaces.I11Subprogrammes)

    mapper_class = sql.MSFD11ReferenceSubProgramme
    order_field = "ID"
    css_class = 'left-side-form'

    # extra_data_template = ViewPageTemplateFile('pt/extra-data-item.pt')

    def download_results(self):
        mp_type_ids = self.context.context.context.context.get_mp_type_ids()
        regions = self.context.context.context.data.get('region_subregions',
                                                        [])
        countries = self.context.context.data.get('member_states', [])
        marine_unit_ids = self.context.data.get('marine_unit_ids', [])

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            sql.MSFD11MarineUnitID.MarineUnitID.in_(marine_unit_ids)
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]
        mp_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'ID',
            sql.MSFD11MP.MonitoringProgramme.in_(mon_prog_ids)
        )

        subprogramme_ids = db.get_unique_from_mapper(
            sql.MSFD11MONSub,
            'SubProgramme',
            and_(sql.MSFD11MONSub.MemberState.in_(countries),
                 sql.MSFD11MONSub.Region.in_(regions))
        )
        subprogramme_ids = [int(i) for i in subprogramme_ids]

        q4g_subprogids_1 = db.get_unique_from_mapper(
            sql.MSFD11SubProgramme,
            'Q4g_SubProgrammeID',
            sql.MSFD11SubProgramme.ID.in_(subprogramme_ids)
        )
        q4g_subprogids_2 = db.get_unique_from_mapper(
            sql.MSFD11SubProgrammeIDMatch,
            'MP_ReferenceSubProgramme',
            sql.MSFD11SubProgrammeIDMatch.Q4g_SubProgrammeID.in_(
                q4g_subprogids_1
            )
        )

        klass_join_mp = sql.MSFD11MP
        count_rsp, data_rsp = db.get_all_records_outerjoin(
            self.mapper_class,
            klass_join_mp,
            and_(klass_join_mp.MPType.in_(mp_type_ids),
                 self.mapper_class.MP.in_(mp_ids),
                 or_(self.mapper_class.SubMonitoringProgrammeID.in_(
                     q4g_subprogids_1),
                     self.mapper_class.SubMonitoringProgrammeID.in_(
                         q4g_subprogids_2))
                 ),
        )

        submonitor_programme_ids = [row.SubMonitoringProgrammeID
                                    for row in data_rsp]

        mapper_class_sp = sql.MSFD11SubProgramme
        count_sp, data_sp = db.get_all_records(
            mapper_class_sp,
            mapper_class_sp.Q4g_SubProgrammeID.in_(submonitor_programme_ids)
        )

        subprograme_ids = [row.ID for row in data_sp]

        mapper_class_em = sql.MSFD11Q9aElementMonitored
        count_em, data_em = db.get_all_records(
            mapper_class_em,
            mapper_class_em.SubProgramme.in_(subprograme_ids)
        )

        mapper_class_mp = sql.MSFD11Q9bMeasurementParameter
        count_mp, data_mp = db.get_all_records(
            mapper_class_mp,
            mapper_class_mp.SubProgramme.in_(subprograme_ids)
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD11ReferenceSubProgramme', data_rsp),
            ('MSFD11SubProgramme', data_sp),
            ('MSFD11Q9aElementMonitored', data_em),
            ('MSFD11Q9bMeasurementParameter', data_mp),
        ]

        return data_to_xls(xlsdata)

    def get_db_results(self):
        page = self.get_page()
        # needed_ids = self.context.data.get('monitoring_programme_types', [])
        needed_ids = self.context.context.context.context.get_mp_type_ids()
        klass_join = sql.MSFD11MP

        regions = self.context.context.context.data.get('region_subregions',
                                                        [])
        countries = self.context.context.data.get('member_states', [])
        marine_unit_id = self.context.data.get('marine_unit_ids', [])

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            sql.MSFD11MarineUnitID.MarineUnitID.in_(marine_unit_id)
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]
        mp_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'ID',
            sql.MSFD11MP.MonitoringProgramme.in_(mon_prog_ids)
        )

        subprogramme_ids = db.get_unique_from_mapper(
            sql.MSFD11MONSub,
            'SubProgramme',
            and_(sql.MSFD11MONSub.MemberState.in_(countries),
                 sql.MSFD11MONSub.Region.in_(regions))
        )
        subprogramme_ids = [int(i) for i in subprogramme_ids]

        q4g_subprogids_1 = db.get_unique_from_mapper(
            sql.MSFD11SubProgramme,
            'Q4g_SubProgrammeID',
            sql.MSFD11SubProgramme.ID.in_(subprogramme_ids)
        )
        q4g_subprogids_2 = db.get_unique_from_mapper(
            sql.MSFD11SubProgrammeIDMatch,
            'MP_ReferenceSubProgramme',
            sql.MSFD11SubProgrammeIDMatch.Q4g_SubProgrammeID.in_(
                q4g_subprogids_1
            )
        )

        if needed_ids:
            [count, item] = db.get_item_by_conditions_joined(
                self.mapper_class,
                klass_join,
                self.order_field,
                and_(klass_join.MPType.in_(needed_ids),
                     self.mapper_class.MP.in_(mp_ids),
                     or_(
                         self.mapper_class.SubMonitoringProgrammeID.in_(
                             q4g_subprogids_1
                         ),
                         self.mapper_class.SubMonitoringProgrammeID.in_(
                             q4g_subprogids_2
                         )
                )),
                page=page
            )
            item.whitelist = ['SubMonitoringProgrammeID']

            return [count, item]


@register_form_section(A11MonSubDisplay)
class A11MPExtraInfo(ItemDisplay):
    title = "SubProgramme Info"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    # TODO data from columns SubMonitoringProgrammeID and Q4g_SubProgrammeID
    # do not match, SubMonitoringProgrammeID contains spaces
    def get_db_results(self):
        if not self.context.item:
            return {}

        subprogramme_id = self.context.item.SubMonitoringProgrammeID
        mc = sql.MSFD11SubProgramme

        count, item = db.get_related_record(
            mc, 'Q4g_SubProgrammeID', subprogramme_id)

        mps = sql.MSFD11SubProgrammeIDMatch.MP_ReferenceSubProgramme

        if not item:
            subprogramme_id = db.get_unique_from_mapper(
                sql.MSFD11SubProgrammeIDMatch,
                'Q4g_SubProgrammeID',
                mps == subprogramme_id
            )
            count, item = db.get_related_record(
                mc, 'Q4g_SubProgrammeID', subprogramme_id)

        if item:
            self.subprogramme = getattr(item, 'ID')
        else:
            self.subprogramme = 0

        page = self.get_page()

        return page, item

    def get_extra_data(self):
        mapper_class_element = sql.MSFD11Q9aElementMonitored
        elements_monitored = db.get_all_columns_from_mapper(
            mapper_class_element,
            'Q9a_ElementMonitored',
            mapper_class_element.SubProgramme == self.subprogramme
        )

        mapper_class_measure = sql.MSFD11Q9bMeasurementParameter
        parameters_measured = db.get_all_columns_from_mapper(
            mapper_class_measure,
            'ID',
            mapper_class_measure.SubProgramme == self.subprogramme
        )
        excluded_columns = ('ID', 'SubProgramme')
        parameters_measured = db_objects_to_dict(parameters_measured,
                                                 excluded_columns)
        # parameters_measured = pivot_data(parameters_measured, 'SubProgramme')

        return [
            ('Elements monitored', {
                '': [
                    {'ElementMonitored': x.Q9a_ElementMonitored}

                    for x in elements_monitored
                ]
            }),
            ('Parameters measured', {'': parameters_measured}),
        ]
