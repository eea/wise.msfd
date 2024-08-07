#pylint: skip-file
from __future__ import absolute_import
import logging

from collections import defaultdict
from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form.field import Fields

from . import interfaces
from .. import db, sql
from ..base import EmbeddedForm, MarineUnitIDSelectForm
from ..utils import all_values_from_field, db_objects_to_dict, group_data
from .base import ItemDisplay, ItemDisplayForm, MainForm, MultiItemDisplayForm
from .utils import register_form_art11, register_form_section
import six


logger = logging.getLogger('wise.msfd')


class StartArticle11Form(MainForm):
    """
    """

    # record_title = 'Article 11'
    name = 'monitoring-programmes'
    session_name = '2012'

    fields = Fields(interfaces.IStartArticle11)
    # fields['monitoring_programme_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.data.get('monitoring_programme_info_type')
        session_name = klass.session_name
        db.threadlocals.session_name = session_name

        return klass(self, self.request)

    def get_latest_import_ids(self):
        mp = sql.MSFD11Import

        count, res = db.get_all_records(
            mp,
            # rows with higher ID than 710 do not have data in MSFD11_MP table
            # mp.ID < 710
        )

        uniques = defaultdict(dict)

        for row in res:
            id = row.ID
            time = row.Time

            key = "-".join((
                row.MemberState,
                row.Region,
                row.SubProgrammeID or '',
                # row.FileName
            ))

            if id >= uniques.get(key, {}).get('id', id):
                uniques[key] = {'id': id, 'time': time}

        result = [d['id'] for d in uniques.values()]

        return result


class Article11MonitoringProgrammeType(EmbeddedForm):
    fields = Fields(interfaces.IArticle11MonitoringProgrammeType)
    fields['monitoring_programme_types'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        klass = self.context.context.mru_class

        return klass(self, self.request)

    def get_available_marine_unit_ids(self):
        return self.context.get_available_marine_unit_ids(
            mp_type_ids=self.get_mp_type_ids())

    def get_mp_type_ids(self):
        return self.data.get('monitoring_programme_types', [])

    def default_monitoring_programme_types(self):
        field = self.fields['monitoring_programme_types']

        return [int(x) for x in all_values_from_field(self, field)]


class A11MProgMemberStateForm(EmbeddedForm):
    fields = Fields(interfaces.IMemberStates)
    fields['member_states'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return Article11MonitoringProgrammeType(self, self.request)

        klass = self.context.mru_class

        return klass(self, self.request)

    def get_available_marine_unit_ids(self, mp_type_ids=None):
        # TODO: use available marine unit ids from t_MSFD4_GegraphicalAreasID

        # mp_type_ids = self.subform.get_mp_type_ids()

        ms = self.get_selected_member_states()
        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            sql.MSFD11MON.MemberState.in_(ms),
            sql.MSFD11MON.Import.in_(
                self.context.context.get_latest_import_ids()
            ),
        )

        mon_ids = [str(x).strip() for x in mon_ids]

        mon_prog_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            and_(sql.MSFD11MP.MON.in_(mon_ids),
                 sql.MSFD11MP.MPType.in_(mp_type_ids),
                 sql.MSFD11MP.MonitoringProgramme.isnot(None))
        )
        mon_prog_ids = [x.strip() for x in mon_prog_ids if x]

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
        return Article11MonitoringProgrammeType(self, self.request)

        klass = self.context.mru_class

        return klass(self, self.request)

    def get_available_marine_unit_ids(self, mp_type_ids=None):
        # TODO: use available marine unit ids from t_MSFD4_GegraphicalAreasID

        # mp_type_ids = self.context.get_mp_type_ids()
        mptypes_subprog = self.context.get_mptypes_subprog()
        member_states = self.get_selected_member_states()

        submonprog_ids = []

        # logger.info('mp_type_ids: %s', mp_type_ids)

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
            sql.MSFD11MP.ID.in_(mp_from_ref_sub),
            sql.MSFD11MP.MonitoringProgramme.isnot(None),
            sql.MSFD11MP.MPType.in_(mp_type_ids)
        )

        mc_ = sql.MSFD11MonitoringProgrammeMarineUnitID
        count, marine_units = db.get_all_records_outerjoin(
            sql.MSFD11MarineUnitID,
            mc_,
            mc_.MonitoringProgramme.in_(mon_prog_ids)
        )
        mrus = [x.MarineUnitID for x in marine_units]

        return [count, mrus]


class A11MProgMarineUnitIdForm(MarineUnitIDSelectForm):

    def get_available_marine_unit_ids(self):
        return self.context.get_available_marine_unit_ids()

    def get_subform(self):
        return A11MonProgDisplay(self, self.request)


class A11MSubMarineUnitIdForm(MarineUnitIDSelectForm):

    def get_available_marine_unit_ids(self):
        return self.context.get_available_marine_unit_ids()

    def get_subform(self):
        return A11MonSubDisplay(self, self.request)


class A11MonProgDisplay(ItemDisplayForm):
    title = "Monitoring Programmes display"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')
    mapper_class = sql.MSFD11MonitoringProgramme
    order_field = 'ID'
    css_class = 'left-side-form'

    blacklist = ['Q5d_AdequacyForAssessmentGES',
                 'Q6b_AdequacyForAssessmentTargets']
    use_blacklist = True

    reported_date_info = {
        'mapper_class': sql.MSFD11Import,
        'col_import_id': 'ID',
        'col_import_time': 'Time',
        'col_filename': 'FileName'
    }

    def get_import_id(self):
        if hasattr(self, '_import_id'):
            return self._import_id

        monitoring_programme = self.item.ID
        mc = sql.MSFD11MON
        mc_join = sql.MSFD11MP

        _, res = db.get_all_records_outerjoin(
            mc,
            mc_join,
            mc_join.MonitoringProgramme == monitoring_programme
        )

        import_id = res.Import

        return import_id

    def get_current_country(self):
        """ Calls the get_current_country from super class (BaseUtil)
            which is a general implementation for getting the country.
            Some MRUs are missing from the t_MSFD4_GegraphicalAreasID,
            and we need an alternative way to retrieve the country
        """

        country = super(A11MonProgDisplay, self).get_current_country()

        if country:
            return country

        monitoring_programme = self.item.ID
        mc = sql.MSFD11MON
        mc_join = sql.MSFD11MP

        _, res = db.get_all_records_outerjoin(
            mc,
            mc_join,
            mc_join.MonitoringProgramme == monitoring_programme
        )

        country = self.print_value(res[0].MemberState, 'CountryCode')

        self._import_id = res[0].Import

        return country

    def download_results(self):
        mp_type_ids = self.context.get_mp_type_ids()
        mon_prog_ids = self.context.context.context \
            .get_monitoring_programme_ids()

        klass_join_mp = sql.MSFD11MP
        klass_join_mon = sql.MSFD11MON

        mc_fields = self.get_obj_fields(self.mapper_class, False)
        fields = [klass_join_mon.MemberState] + \
                 [getattr(self.mapper_class, field) for field in mc_fields]

        sess = db.session()
        res = sess.query(*fields). \
            join(klass_join_mp,
                 self.mapper_class.ID == klass_join_mp.MonitoringProgramme). \
            join(klass_join_mon, klass_join_mp.MON == klass_join_mon.ID). \
            filter(and_(klass_join_mp.MPType.in_(mp_type_ids),
                        klass_join_mp.MonitoringProgramme.in_(mon_prog_ids),
                        klass_join_mon.Import.in_(
                            self.context.context.context.context
                                .get_latest_import_ids())
                        ),
                   )
        data_mp = [x for x in res]

        mp_ids = [row.ID for row in data_mp]

        mapper_class_mpl = sql.MSFD11MonitoringProgrammeList
        count_mpl, data_mpl = db.get_all_records(
            mapper_class_mpl,
            mapper_class_mpl.MonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mapper_class_mpmid = sql.MSFD11MonitoringProgrammeMarineUnitID
        count_mpmid, data_mpmid = db.get_all_records_join(
            [
                mapper_class_mpmid.ID,
                mapper_class_mpmid.MonitoringProgramme,
                sql.MSFD11MarineUnitID.MarineUnitID
            ],
            sql.MSFD11MarineUnitID,
            mapper_class_mpmid.MonitoringProgramme.in_(mp_ids),
            raw=True
        )

        mapper_class_rt = sql.MSFD11Q6aRelevantTarget
        count_mpl, data_rt = db.get_all_records(
            mapper_class_rt,
            mapper_class_rt.MonitoringProgramme.in_(mp_ids),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD11MonitoringProgramme', data_mp),
            ('MSFD11MonitoringProgrammeList', data_mpl),
            ('MSFD11MonitorProgMarineUnitID', data_mpmid),
            ('MSFD11Q6aRelevantTarget', data_rt),
        ]

        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        klass_join = sql.MSFD11MP
        ggp = self.context.context
        needed_ID = self.context.get_mp_type_ids()
        mon_prog_ids = ggp.context.get_monitoring_programme_ids()
        # muids = [self.get_form_data_by_key(self, 'marine_unit_id')]

        s = sql.MSFD11MonitoringProgrammeMarineUnitID
        count, marine_units = db.get_all_records_outerjoin(
            s,
            sql.MSFD11MarineUnitID,
            # sql.MSFD11MarineUnitID.MarineUnitID.in_(muids)
        )
        mp_ids_mru = [x.MonitoringProgramme for x in marine_units]

        if needed_ID:
            [count, item] = db.get_item_by_conditions_joined(
                self.mapper_class,
                klass_join,
                self.order_field,
                and_(klass_join.MPType.in_(needed_ID),
                     klass_join.MonitoringProgramme.in_(mon_prog_ids),
                     klass_join.MonitoringProgramme.in_(mp_ids_mru)
                     ),
                page=page
            )

            if item:
                item.whitelist = ['Q4e_ProgrammeID']

            return [count, item]

    def get_extra_data(self):
        if not self.item:
            return {}

        res = []

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
        element_names = group_data(element_names, 'ElementName')

        q5d_adequacy_id = self.item.Q5d_AdequacyForAssessmentGES
        count, q5d_adequacy = db.get_all_records(
            sql.MSFD11Q5dAdequacyForAssessmentGE,
            sql.MSFD11Q5dAdequacyForAssessmentGE.ID == q5d_adequacy_id
        )
        q5d_adequacy = db_objects_to_dict(q5d_adequacy, excluded_columns)
        if q5d_adequacy:
            res.append(('Adequacy for assessment GES', {'': q5d_adequacy})),

        q6b_adequacy_id = self.item.Q6b_AdequacyForAssessmentTargets
        count, q6b_adequacy = db.get_all_records(
            sql.MSFD11Q6bAdequacyForAssessmentTarget,
            sql.MSFD11Q6bAdequacyForAssessmentTarget.ID == q6b_adequacy_id
        )
        q6b_adequacy = db_objects_to_dict(q6b_adequacy, excluded_columns)
        if q6b_adequacy:
            res.append(('Adequacy for assessment targets', {'': q6b_adequacy})),

        res.append(('Other information', element_names))

        if marine_units:
            res.append(
                ('', {
                    '': [{'Marine unit(s)': x} for x in marine_units]
                }))

        if targets:
            res.append(
                ('', {
                    '': [{'Relevant target(s)': x} for x in targets]
                }))

        return res


@register_form_art11
class A11MonitoringProgrammeForm(EmbeddedForm):
    record_title = 'Article 11 (Monitoring Programmes)'
    title = "2014 Monitoring strategies (programmes)"
    # mru_class = A11MProgMarineUnitIdForm
    mru_class = A11MonProgDisplay
    session_name = '2012'

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def get_subform(self):
        return A11MProgMemberStateForm(self, self.request)

    def get_monitoring_programme_ids(self):
        regions = self.data.get('region_subregions', [])
        countries = self.subform.data.get('member_states', [])
        marine_unit_id = self.subform.subform.data.get('marine_unit_ids', [])
        # mp_type_ids = self.context.get_mp_type_ids()

        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            and_(sql.MSFD11MON.MemberState.in_(countries),
                 sql.MSFD11MON.Region.in_(regions),
                 sql.MSFD11MON.Import.in_(
                     self.context.get_latest_import_ids()
                 ))
        )
        mon_prog_ids_from_MP = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            and_(sql.MSFD11MP.MON.in_(mon_ids),
                 # sql.MSFD11MP.MPType.in_(mp_type_ids),
                 sql.MSFD11MP.MonitoringProgramme.isnot(None)
                 )
        )

        mon_prog_ids_from_MP = [int(elem) for elem in mon_prog_ids_from_MP]

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            sql.MSFD11MarineUnitID.MarineUnitID.in_(marine_unit_id)
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]

        # result = tuple(set(mon_prog_ids_from_MP) & set(mon_prog_ids))
        result = tuple(set(mon_prog_ids_from_MP))

        if not result:
            # result = tuple(mon_prog_ids_from_MP + mon_prog_ids)
            result = tuple(mon_prog_ids_from_MP)

        return result

    def get_mp_type_ids(self):
        # used by vocabularies, easier to pass from context

        return self.context.get_mp_type_ids()


class A11MonSubDisplay(MultiItemDisplayForm):

    title = "Monitoring Subprogramme display"

    mapper_class = sql.MSFD11ReferenceSubProgramme
    order_field = "ID"
    css_class = 'left-side-form'

    blacklist = ['MP']
    use_blacklist = True

    reported_date_info = {
        'mapper_class': sql.MSFD11Import,
        'col_import_id': 'ID',
        'col_import_time': 'Time',
        'col_filename': 'FileName'
    }

    def get_import_id(self):
        if hasattr(self, '_import_id'):
            return self._import_id

        sub_programme = self.item.ID
        mc = sql.MSFD11MONSub

        _, res = db.get_related_record(
            mc,
            'SubProgramme',
            sub_programme
        )

        import_id = res.Import

        return import_id

    def get_current_country(self):
        """ Calls the get_current_country from super class (BaseUtil)
            which is a general implementation for getting the country.
            Some MRUs are missing from the t_MSFD4_GegraphicalAreasID,
            and we need an alternative way to retrieve the country
        """

        country = super(A11MonSubDisplay, self).get_current_country()

        if country:
            return country

        sub_programme = self.item.ID
        mc = sql.MSFD11MONSub

        _, res = db.get_related_record(
            mc,
            'SubProgramme',
            sub_programme
        )

        country = self.print_value(res.MemberState, 'CountryCode')

        self._import_id = res.Import

        return country

    def download_results(self):
        mp_type_ids = self.context.get_mp_type_ids()
        regions = self.get_form_data_by_key(self, 'region_subregions')
        countries = self.get_form_data_by_key(self, 'member_states')
        # marine_unit_ids = [self.get_form_data_by_key(self, 'marine_unit_id')]
        mptypes_subprog = self.context.context.context. \
            get_mptypes_subprog()

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            raw=True
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]
        mp_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'ID',
            sql.MSFD11MP.MonitoringProgramme.in_(mon_prog_ids),
            raw=True
        )

        subprogramme_ids = db.get_unique_from_mapper(
            sql.MSFD11MONSub,
            'SubProgramme',
            and_(sql.MSFD11MONSub.MemberState.in_(countries),
                 sql.MSFD11MONSub.Region.in_(regions),
                 sql.MSFD11MONSub.Import.in_(
                     self.context.context.context.context.
                         get_latest_import_ids())
                 ),
            raw=True
        )
        subprogramme_ids = [int(i) for i in subprogramme_ids]

        q4g_subprogids_1 = db.get_unique_from_mapper(
            sql.MSFD11SubProgramme,
            'Q4g_SubProgrammeID',
            sql.MSFD11SubProgramme.ID.in_(subprogramme_ids),
            raw=True
        )
        q4g_subprogids_2 = db.get_unique_from_mapper(
            sql.MSFD11SubProgrammeIDMatch,
            'MP_ReferenceSubProgramme',
            sql.MSFD11SubProgrammeIDMatch.Q4g_SubProgrammeID.in_(
                q4g_subprogids_1
            ),
            raw=True
        )

        klass_join_mp = sql.MSFD11MP
        klass_join_mon = sql.MSFD11MON

        mc_fields = self.get_obj_fields(self.mapper_class, False)
        fields = [klass_join_mon.MemberState] + \
                 [getattr(self.mapper_class, field) for field in mc_fields]

        sess = db.session()
        res = sess.query(*fields). \
            join(klass_join_mp,
                 self.mapper_class.MP == klass_join_mp.ID). \
            join(klass_join_mon, klass_join_mp.MON == klass_join_mon.ID). \
            filter(
            and_(klass_join_mp.MPType.in_(mp_type_ids),
                 self.mapper_class.MP.in_(mp_ids),
                 or_(self.mapper_class.SubMonitoringProgrammeID.in_(
                     q4g_subprogids_1),
                     self.mapper_class.SubMonitoringProgrammeID.in_(
                         q4g_subprogids_2))
                 )
            )
        data_rsp = [x for x in res]

        submonitor_programme_ids = [row.SubMonitoringProgrammeID
                                    for row in data_rsp]

        needed_subprogids = []
        for mpid, subprogids in mptypes_subprog.items():
            if mpid in mp_type_ids:
                needed_subprogids.extend(subprogids)

        mapper_class_sp = sql.MSFD11SubProgramme
        count_sp, data_sp = db.get_all_records(
            mapper_class_sp,
            mapper_class_sp.Q4g_SubProgrammeID.in_(submonitor_programme_ids),
            mapper_class_sp.ID.in_(subprogramme_ids),
            mapper_class_sp.ID.in_(needed_subprogids),
            raw=True
        )

        subprograme_ids = [row.ID for row in data_sp]

        mapper_class_em = sql.MSFD11Q9aElementMonitored
        count_em, data_em = db.get_all_records(
            mapper_class_em,
            mapper_class_em.SubProgramme.in_(subprograme_ids),
            raw=True
        )

        mapper_class_mp = sql.MSFD11Q9bMeasurementParameter
        count_mp, data_mp = db.get_all_records(
            mapper_class_mp,
            mapper_class_mp.SubProgramme.in_(subprograme_ids),
            raw=True
        )

        xlsdata = [
            # worksheet title, row data
            ('MSFD11SubProgramme', data_sp),
            ('MSFD11ReferenceSubProgramme', data_rsp),
            ('MSFD11Q9aElementMonitored', data_em),
            ('MSFD11Q9bMeasurementParameter', data_mp),
        ]
        
        return xlsdata

    def get_db_results(self):
        page = self.get_page()
        needed_ids = self.context.get_mp_type_ids()
        # klass_join = sql.MSFD11MP
        mptypes_subprog = self.context.context.context. \
            get_mptypes_subprog()

        regions = self.get_form_data_by_key(self, 'region_subregions')
        countries = self.get_form_data_by_key(self, 'member_states')
        # marine_unit_id = [self.get_form_data_by_key(self, 'marine_unit_id')]

        count, mon_prog_ids = db.get_all_records_outerjoin(
            sql.MSFD11MonitoringProgrammeMarineUnitID,
            sql.MSFD11MarineUnitID,
            # sql.MSFD11MarineUnitID.MarineUnitID.in_(marine_unit_id)
        )
        mon_prog_ids = [row.MonitoringProgramme for row in mon_prog_ids]
        mp_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MPType',
            sql.MSFD11MP.MonitoringProgramme.in_(mon_prog_ids),
            sql.MSFD11MP.MPType.in_(needed_ids)
        )

        needed_subprogids = []
        for mpid, subprogids in mptypes_subprog.items():
            if six.text_type(mpid) in mp_ids:
                needed_subprogids.extend(subprogids)

        subprogramme_ids = db.get_unique_from_mapper(
            sql.MSFD11MONSub,
            'SubProgramme',
            and_(sql.MSFD11MONSub.MemberState.in_(countries),
                 sql.MSFD11MONSub.Region.in_(regions),
                 sql.MSFD11MONSub.Import.in_(
                     self.context.context.context.context.
                         get_latest_import_ids())
                 )
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
            mc = sql.MSFD11SubProgramme

            count, item = db.get_item_by_conditions(
                mc,
                'Q4g_SubProgrammeID',
                mc.ID.in_(subprogramme_ids),
                mc.ID.in_(needed_subprogids),
                or_(mc.Q4g_SubProgrammeID.in_(q4g_subprogids_1),
                    mc.Q4g_SubProgrammeID.in_(q4g_subprogids_2)),
                page=page
            )

            if item:
                item.whitelist = ['Q4g_SubProgrammeID']

            return [count, item]


@register_form_art11
class A11MonitorSubprogrammeForm(EmbeddedForm):
    record_title = 'Article 11 (Monitoring Subprogrammes)'
    title = "2014 Monitoring programmes (sub-programmes)"
    # mru_class = A11MSubMarineUnitIdForm
    mru_class = A11MonSubDisplay
    session_name = '2012'

    fields = Fields(interfaces.IRegionSubregions)
    fields['region_subregions'].widgetFactory = CheckBoxFieldWidget

    def __init__(self, context, request):
        EmbeddedForm.__init__(self, context, request)
        self.__mptypes_subprog = None

    def get_mp_type_ids(self):
        # used by vocabularies, easier to pass from context

        return self.context.get_mp_type_ids()

    def get_mptypes_subprog(self):
        """ Creates a mapping between "Monitoring Program Type ID(MP)":
        SubProgrammes(SubProgrammeID)

        :return: {13: [1,2,3,4], 8: [5,6,7,8], ...}
        """

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


@register_form_section(A11MonSubDisplay)
class A11MPExtraInfo(ItemDisplay):
    title = "Reference SubProgramme"

    extra_data_template = ViewPageTemplateFile('pt/extra-data-pivot.pt')

    blacklist = ['MP']
    use_blacklist = True

    # TODO data from columns SubMonitoringProgrammeID and Q4g_SubProgrammeID
    # do not match, SubMonitoringProgrammeID contains spaces
    def get_db_results(self):
        if not self.context.item:
            return {}

        subprogramme_id = self.context.item.Q4g_SubProgrammeID
        mc = sql.MSFD11ReferenceSubProgramme

        count, item = db.get_related_record(
            mc, 'SubMonitoringProgrammeID', subprogramme_id)

        mps = sql.MSFD11SubProgrammeIDMatch.MP_ReferenceSubProgramme

        if not item:
            subprogramme_id = db.get_unique_from_mapper(
                sql.MSFD11SubProgrammeIDMatch,
                'Q4g_SubProgrammeID',
                mps == subprogramme_id
            )
            item = None
            if subprogramme_id:
                count, item = db.get_related_record(
                    mc, 'SubMonitoringProgrammeID', subprogramme_id)

        if item:
            self.subprogramme = getattr(self.context.item, 'ID')
            item.whitelist = ['SubMonitoringProgrammeID']
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

        subprogramme_id = self.context.item.Q4g_SubProgrammeID

        mc_ref_sub = sql.MSFD11ReferenceSubProgramme
        mp_from_ref_sub = db.get_unique_from_mapper(
            sql.MSFD11ReferenceSubProgramme,
            'MP',
            mc_ref_sub.SubMonitoringProgrammeID == subprogramme_id,
        )
        mp_from_ref_sub = [int(x) for x in mp_from_ref_sub]

        mon_prog_ids = db.get_unique_from_mapper(
            sql.MSFD11MP,
            'MonitoringProgramme',
            sql.MSFD11MP.ID.in_(mp_from_ref_sub),
            sql.MSFD11MP.MonitoringProgramme.isnot(None)
        )

        mc_ = sql.MSFD11MonitoringProgrammeMarineUnitID
        count, marine_units = db.get_all_records_outerjoin(
            sql.MSFD11MarineUnitID,
            mc_,
            mc_.MonitoringProgramme.in_(mon_prog_ids)
        )
        marine_units = [x.MarineUnitID for x in marine_units]

        return [
            ('', {
                '': [
                    {'Elements monitored': x.Q9a_ElementMonitored}

                    for x in elements_monitored
                ]
            }),
            ('', {'Parameters measured': parameters_measured}),
            ('', {
                '': [{'Marine Unit(s)': x} for x in marine_units]
            })
        ]
