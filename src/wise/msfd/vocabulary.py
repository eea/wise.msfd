# -*- coding: utf-8 -*-
# TODO: move most of the stuff here in .search, where it belongs
import json
import unicodedata

from sqlalchemy import and_, or_
from sqlalchemy.sql.schema import Table
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from . import db, sql, sql2018
from .labels import COMMON_LABELS, GES_LABELS

# from eea.cache import cache


def vocab_from_values(values):
    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in values]
    # TODO fix UnicodeDecodeError
    # Article Indicators, country Lithuania
    try:
        terms.sort(key=lambda t: t.title)
    except UnicodeDecodeError:
        pass
    vocab = SimpleVocabulary(terms)

    return vocab


def vocab_from_values_with_count(values, column):
    dict_count = dict()

    for x in values:
        col = getattr(x, column)

        if col in dict_count:
            dict_count[col] += 1
        else:
            dict_count[col] = 1

    terms = [
        SimpleTerm(x, x, "{} [{}]".format(COMMON_LABELS.get(x, x),
                                          dict_count[x]))

        for x in dict_count.keys()
    ]
    # TODO fix UnicodeDecodeError
    # Article Indicators, country Lithuania
    try:
        terms.sort(key=lambda t: t.title)
    except UnicodeDecodeError:
        pass
    vocab = SimpleVocabulary(terms)

    return vocab


def db_vocab(table, column, sort_helper=None):
    """ Builds a vocabulary based on unique values in a column table
    """

    sort_helper = sort_helper or (lambda t: t.title)

    if isinstance(table, Table):
        res = db.get_unique_from_table(table, column)
    elif table.__tablename__ == 'MSFD11_MPTypes':
        res = db.get_all_columns_from_mapper(table, column)
        terms = [
            SimpleTerm(x.ID, x.ID, COMMON_LABELS.get(x.Description,
                                                     x.Description))

            for x in res
        ]
        terms.sort(key=sort_helper)
        vocab = SimpleVocabulary(terms)

        return vocab
    else:
        res = db.get_unique_from_mapper(table, column)

    res = [x.strip() for x in res]

    terms = []
    for x in res:
        try:
            simple_term = SimpleTerm(x, x, COMMON_LABELS.get(x, x))
        except:
            # TODO find a way to create a vocab term with accented chars ex.
            # Nordostatlanten (ANS) och Östersjön (BAL)
            continue
            _x = x.encode('utf-8')
            simple_term = SimpleTerm(x, _x, COMMON_LABELS.get(x, x))

        terms.append(simple_term)

    # terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in res]
    try:
        terms.sort(key=sort_helper)
    except:
        pass

    vocab = SimpleVocabulary(terms)

    return vocab


def get_json_subform_data(json_str, field_title):
    _form_data = [
        field['options']

        for field in json_str['fields']

        if field['label'] == field_title
    ]
    data = [
        x['value']

        for x in _form_data[0]

        if x['checked']
    ]

    return data


def values_to_vocab(values):
    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in values]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def get_region_subregions_vb_factory(context):
    return db_vocab(sql.t_MSFD4_GegraphicalAreasID, 'RegionSubRegions')


@provider(IVocabularyFactory)
def get_region_subregions_vb_factory_art6(context):
    table = sql.MSFD4RegionalCooperation
    column = 'RegionsSubRegions'
    res = db.get_unique_from_mapper(table, column, raw=True)
    terms = []

    for x in res:
        x = x[0]

        # TODO find a way to create a vocab term with accented chars for ex.:
        # Nordostatlanten (ANS) och Östersjön (BAL)
        _x = unicodedata.normalize('NFKD', x).encode('ASCII', 'ignore')
        simple_term = SimpleTerm(_x, _x, COMMON_LABELS.get(x, x))
        terms.append(simple_term)

    terms.sort(key=lambda t: t.title)

    vocab = SimpleVocabulary(terms)

    return vocab

    # return db_vocab(sql.MSFD4RegionalCooperation, 'RegionsSubRegions')


@provider(IVocabularyFactory)
@db.use_db_session('2012')
def get_member_states_vb_factory(context):
    conditions = []

    t = sql.t_MSFD4_GegraphicalAreasID

    if hasattr(context, 'get_selected_region_subregions'):
        regions = context.get_selected_region_subregions()

        if regions:
            conditions.append(t.c.RegionSubRegions.in_(regions))

    count, rows = db.get_all_records(
        t,
        *conditions
    )

    return values_to_vocab(set(x[1] for x in rows))


@provider(IVocabularyFactory)
@db.use_db_session('2018')
def get_member_states_vb_factory_art4(context):
    conditions = []

    t = sql2018.MRUsPublication

    if hasattr(context, 'get_selected_region_subregions'):
        regions = context.get_selected_region_subregions()

        if regions:
            conditions.append(t.Region.in_(regions))

    rows = db.get_unique_from_mapper(
        t,
        'Country',
        *conditions
    )

    return values_to_vocab(rows)


@provider(IVocabularyFactory)
@db.use_db_session('2012')
def get_member_states_vb_factory_art6(context):
    conditions = []

    mci = sql.MSFD4Import
    mcr = sql.MSFD4RegionalCooperation

    if hasattr(context, 'get_selected_region_subregions'):
        regions = context.get_selected_region_subregions()

        if regions:
            conditions.append(mcr.RegionsSubRegions.in_(regions))

    count, rows = db.get_all_records_join(
        [mci.MSFD4_Import_ReportingCountry],
        mcr,
        *conditions
    )
    rows = [x[0] for x in rows]

    if conditions and ('ANS' in regions or 'BAL' in regions):
        rows.append('SE')

    return values_to_vocab(set(rows))


@provider(IVocabularyFactory)
def get_area_type_vb_factory(context):

    t = sql.t_MSFD4_GegraphicalAreasID

    member_states = context.get_selected_member_states()

    if member_states:
        count, rows = db.get_all_records(
            t,
            t.c.MemberState.in_(member_states)
        )

        return values_to_vocab(set(x[2] for x in rows))

    return db_vocab(t, 'AreaType')


def mptypes_sort_helper(term):
    title = term.title

    chars = []

    for c in title[1:]:
        if c.isdigit():
            chars.append(c)

        if c == ',' and '.' not in chars:
            chars.append('.')

    title = title.replace(u'\u2013', '-')

    if 'Biodiversity' in title:
        left, right = title.split('Biodiversity -', 1)
        right = right.strip()

        if '.' not in chars:
            chars.append('.')
        chars.append(str(ord(right[0])))

    f = ''.join(chars)

    return float(f)


@provider(IVocabularyFactory)
def monitoring_programme_vb_factory(context):

    return db_vocab(sql.MSFD11MPType, 'ID', mptypes_sort_helper)


@provider(IVocabularyFactory)
def art11_country(context):
    # vocab w/ filtered countries based on monitoring programs
    monitoring_programs = context.get_mp_type_ids()

    mon_ids = db.get_unique_from_mapper(
        sql.MSFD11MP,
        'MON',
        sql.MSFD11MP.MPType.in_(monitoring_programs)
    )

    res = db.get_unique_from_mapper(
        sql.MSFD11MON,
        'MemberState',
        sql.MSFD11MON.ID.in_(mon_ids)
    )
    res = [x.strip() for x in res]

    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in res]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def art11_country_ms(context):
    # vocab w/ filtered countries based on monitoring subprograms

    ctx = context

    if not hasattr(context, 'subform'):
        ctx = context.context

    submonprog_ids = []
    mptypes_subprog = ctx.subform.get_mptypes_subprog()
    mp_type_ids = context.get_mp_type_ids()

    for mid in mp_type_ids:
        submonprog_ids.extend(mptypes_subprog[int(mid)])

    res = db.get_unique_from_mapper(
        sql.MSFD11MONSub,
        'MemberState',
        sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids)
    )
    res = [x.strip() for x in res]

    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in res]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def art11_region(context):
    if not hasattr(context, 'subform'):
        mp_type_ids = context.context.get_mp_type_ids()
    else:
        mp_type_ids = context.get_mp_type_ids()

    mon_ids = db.get_unique_from_mapper(
        sql.MSFD11MP,
        'MON',
        sql.MSFD11MP.MPType.in_(mp_type_ids)
    )

    res = db.get_unique_from_mapper(
        sql.MSFD11MON,
        'Region',
        sql.MSFD11MON.ID.in_(mon_ids)
    )
    res = [x.strip() for x in res]

    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in res]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def art11_region_ms(context):
    ctx = context

    if not hasattr(context, 'subform'):
        ctx = context.context
    mp_type_ids = ctx.get_mp_type_ids()
    mptypes_subprog = ctx.subform.get_mptypes_subprog()

    submonprog_ids = []

    for x in mp_type_ids:
        submonprog_ids.extend(mptypes_subprog[int(x)])

    res = db.get_unique_from_mapper(
        sql.MSFD11MONSub,
        'Region',
        sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids)
    )
    res = [x.strip() for x in res]

    terms = [SimpleTerm(x, x, COMMON_LABELS.get(x, x)) for x in res]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def art11_marine_unit_id(context):
    # if not hasattr(context, 'subform'):
    #     json_str = json.loads(context.json())
    # else:
    #     json_str = json.loads(context.subform.json())

    # countries_form_data = [
    #     field['options']
    #
    #     for field in json_str['fields']
    #
    #     if field['label'] == 'Country'
    # ]
    # countries = [
    #     country['value']
    #
    #     for country in countries_form_data[0]
    #
    #     if country['checked']
    # ]
    countries = []
    # regions_form_data = [
    #     field['options']
    #
    #     for field in json_str['fields']
    #
    #     if field['label'] == 'Region'
    # ]
    # regions = [
    #     region['value']
    #
    #     for region in regions_form_data[0]
    #
    #     if region['checked']
    # ]
    regions = []

    if countries and regions:
        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            and_(sql.MSFD11MON.MemberState.in_(countries),
                 sql.MSFD11MON.Region.in_(regions))

        )
    elif countries:
        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID',
            sql.MSFD11MON.MemberState.in_(countries)
        )
    else:
        mon_ids = db.get_unique_from_mapper(
            sql.MSFD11MON,
            'ID'
        )

    mon_ids = [str(x).strip() for x in mon_ids]

    mon_prog_ids = db.get_unique_from_mapper(
        sql.MSFD11MP,
        'MonitoringProgramme',
        and_(sql.MSFD11MP.MON.in_(mon_ids))
    )
    mon_prog_ids = [x.strip() for x in mon_prog_ids]

    s = sql.MSFD11MonitoringProgrammeMarineUnitID
    count, marine_units = db.get_all_records_outerjoin(
        sql.MSFD11MarineUnitID,
        s,
        s.MonitoringProgramme.in_(mon_prog_ids)
    )

    terms = [SimpleTerm(x.MarineUnitID, x.MarineUnitID, x.MarineUnitID)
             for x in marine_units]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def art11_marine_unit_id_ms(context):
    ctx = context

    if not hasattr(context, 'subform'):
        ctx = context.context

    mp_type_ids = ctx.get_mp_type_ids()
    mptypes_subprog = ctx.subform.get_mptypes_subprog()

    submonprog_ids = []

    for x in mp_type_ids:
        submonprog_ids.extend(mptypes_subprog[int(x)])

    subprogramme_ids = db.get_unique_from_mapper(
        sql.MSFD11MONSub,
        'SubProgramme',
        sql.MSFD11MONSub.SubProgramme.in_(submonprog_ids)
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
        sql.MSFD11SubProgrammeIDMatch.Q4g_SubProgrammeID.in_(q4g_subprogids_1)
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

    terms = [
        SimpleTerm(x.MarineUnitID, x.MarineUnitID, x.MarineUnitID)

        for x in marine_units
    ]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


def marine_unit_id_vocab(ids):
    # Marine Unit Ids 2012
    count, res = db.get_marine_unit_id_names(ids)

    terms = []

    for id, label in res:
        if label:
            label = u'%s (%s)' % (label, id)
        else:
            label = id
        terms.append(SimpleTerm(id, id, label))
        terms.sort(key=lambda t: t.title)

    # in Article 11 there are some Marine Unit IDs which are not found
    # in t_MSFD4_GegraphicalAreasID, append these separately
    terms_found = [x.value for x in terms]
    terms_to_append = list(set(ids) - set(terms_found))

    for term in terms_to_append:
        label = GES_LABELS.get('mrus', term)

        if label != term:
            label = u'%s (%s)' % (label, term)
        else:
            label = term

        terms.append(SimpleTerm(term, term, label))

    terms.sort(key=lambda t: t.title)

    return SimpleVocabulary(terms)


@provider(IVocabularyFactory)
def marine_unit_ids_vocab_factory(context):
    """ A list of MarineUnitIds based on geodata selected
    """

    count, ids = context.get_available_marine_unit_ids()

    return marine_unit_id_vocab(sorted(ids))


@provider(IVocabularyFactory)
def marine_unit_id_vocab_factory(context):
    """ A list of MarineUnitIds based on availability in target results
    """

    # TODO: explain why this (calling from subform) is needed
    if hasattr(context, 'subform'):
        count, ids = context.subform.get_available_marine_unit_ids()
    else:
        count, ids = context.get_available_marine_unit_ids()

    return marine_unit_id_vocab(sorted(ids))


@provider(IVocabularyFactory)
def a1314_report_types(context):
    # table = sql.MSFD13ReportingInfo
    # column = 'ReportType'
    # values = db.get_unique_from_mapper(table, column)
    # values = reversed(values)
    values = (
        ("Measures", 'Article 13 - Measures'),
        ("Exceptions", 'Article 14 - Exceptions')
    )

    terms = [SimpleTerm(x, x, t) for x, t in values]
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a1314_regions(context):
    return db_vocab(sql.MSFD13ReportingInfo, 'Region')


@provider(IVocabularyFactory)
def a1314_member_states(context):
    regions = context.get_selected_region_subregions()
    report_type = context.data['report_type']

    mc = sql.MSFD13ReportingInfo

    if regions:
        mc_join = sql.MSFD13ReportingInfoMemberState
        count, rows = db.get_all_records_join(
            [mc_join.MemberState],
            mc,
            mc.Region.in_(regions),
            mc.ReportType == report_type
        )

        return values_to_vocab(set(x[0].strip() for x in rows))

    return db_vocab(mc, 'MemberState')


@provider(IVocabularyFactory)
def a1314_unique_codes(context):
    codes = context.data.get('unique_codes')
    terms = [
        SimpleTerm(code, code, u'%s - %s' % (code, name))

        for code, name in codes
    ]
    terms.sort(key=lambda t: t.title)

    return SimpleVocabulary(terms)


@provider(IVocabularyFactory)
def a2018_marine_reporting_unit(context):
    # context_orig = context

    if hasattr(context, 'subform'):
        context = context.subform

    try:
        json_str = json.loads(context.json())
        countries = get_json_subform_data(json_str, 'Country')  # Country Code
    except Exception:
        countries = []

    mapper_class = context.context.context.mapper_class

    def get_res():
        mc_countries = sql2018.ReportedInformation
        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, res = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )

        res = set([x.MarineReportingUnit for x in res])

        return res

    res = get_res()
    vocab = vocab_from_values(res)

    return vocab


@provider(IVocabularyFactory)
def a2018_ges_component_art9(context):
    mapper_class = context.mapper_class

    mc_countries = sql2018.ReportedInformation
    conditions = []

    countries = context.data.get('member_states')
    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, res = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    res = set([x.GESComponent for x in res])

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_feature_art9(context):
    parent = context.context
    mapper_class = parent.mapper_class
    features_mc = parent.features_mc
    determination_mc = parent.determination_mc

    countries = parent.data.get('member_states')
    ges_components = context.data.get('ges_component')

    mc_countries = sql2018.ReportedInformation
    conditions = list()

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    if ges_components:
        conditions.append(mapper_class.GESComponent.in_(ges_components))

    count, id_marine_units = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    id_ges_components = [int(x.Id) for x in id_marine_units]

    count, ids_ges_determination = db.get_all_records_join(
        [determination_mc.IdGESComponent,
         features_mc.Feature],
        features_mc,
        determination_mc.IdGESComponent.in_(id_ges_components)
    )
    res = [x.Feature for x in ids_ges_determination]
    res = tuple(set(res))

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_feature_art81c(context):
    mapper_class = context.mapper_class
    features_mc = context.features_mc

    countries = context.data.get('member_states')

    mc_countries = sql2018.ReportedInformation
    conditions = list()

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, id_marine_units = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    id_marine_units = [int(x.Id) for x in id_marine_units]

    res = db.get_unique_from_mapper(
        features_mc,
        'Feature',
        features_mc.IdMarineUnit.in_(id_marine_units)
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_feature(context):
    # if not hasattr(context, 'features_mc'):
    #     context = context.context

    mapper_class = context.mapper_class
    features_mc = context.features_mc
    features_rel_col = context.features_relation_column
    target_mc = context.target_mc

    countries = context.data.get('member_states', [])
    mc_countries = sql2018.ReportedInformation
    conditions = []

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, id_marine_units = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    id_marine_units = [int(x.Id) for x in id_marine_units]

    id_targets = db.get_unique_from_mapper(
        target_mc,
        'Id',
        target_mc.IdMarineUnit.in_(id_marine_units)
    )

    res = db.get_unique_from_mapper(
        features_mc,
        'Feature',
        getattr(features_mc, features_rel_col).in_(id_targets)
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_ges_component(context):
    parent = context.context

    # if not hasattr(context, 'ges_components_mc'):
    #     context = context.context

    mapper_class = parent.mapper_class
    features_mc = parent.features_mc
    features_rel_col = parent.features_relation_column
    ges_components_mc = parent.ges_components_mc
    ges_comp_rel_col = parent.ges_components_relation_column
    target_mc = parent.target_mc

    countries = parent.data.get('member_states', [])
    features = context.data.get('feature', [])

    mc_countries = sql2018.ReportedInformation
    conditions = []

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, id_marine_units = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    id_marine_units = [int(x.Id) for x in id_marine_units]

    conditions = []
    conditions.append(target_mc.IdMarineUnit.in_(id_marine_units))

    if features:
        id_features = db.get_unique_from_mapper(
            features_mc,
            features_rel_col,
            features_mc.Feature.in_(features)
        )
        conditions.append(target_mc.Id.in_(id_features))

    id_targets = db.get_unique_from_mapper(
        target_mc,
        'Id',
        *conditions
    )

    res = db.get_unique_from_mapper(
        ges_components_mc,
        'GESComponent',
        getattr(ges_components_mc, ges_comp_rel_col).in_(id_targets)
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_ges_component_ind(context):
    mapper_class = context.mapper_class
    ges_comp_mc = context.ges_components_mc

    countries = context.data.get('member_states')

    mc_countries = sql2018.ReportedInformation
    conditions = []

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, ids_indicator = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    ids_indicator = [int(x.Id) for x in ids_indicator]

    res = db.get_unique_from_mapper(
        ges_comp_mc,
        'GESComponent',
        ges_comp_mc.IdIndicatorAssessment.in_(ids_indicator)
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_feature_ind(context):
    parent = context.context

    mapper_class = parent.mapper_class
    ges_comp_mc = parent.ges_components_mc
    features_mc = parent.features_mc

    countries = parent.data.get('member_states')
    ges_components = context.data.get('ges_component')

    mc_countries = sql2018.ReportedInformation

    conditions = []

    if countries:
        conditions.append(mc_countries.CountryCode.in_(countries))

    count, ids_indicator = db.get_all_records_outerjoin(
        mapper_class,
        mc_countries,
        *conditions
    )
    ids_indicator = [int(x.Id) for x in ids_indicator]

    conditions = list()
    conditions.append(ges_comp_mc.IdIndicatorAssessment.in_(ids_indicator))

    if ges_components:
        conditions.append(ges_comp_mc.GESComponent.in_(ges_components))

    ids_ges_comp = db.get_unique_from_mapper(
        ges_comp_mc,
        'Id',
        *conditions
    )
    ids_ges_comp = [int(x) for x in ids_ges_comp]

    res = db.get_unique_from_mapper(
        features_mc,
        'Feature',
        features_mc.IdGESComponent.in_(ids_ges_comp)
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_mru_ind(context):
    if not hasattr(context, 'mapper_class'):
        context = context.context

    json_str = json.loads(context.json())
    json_str_subform = json.loads(context.subform.json())
    mapper_class = context.mapper_class
    ges_comp_mc = context.ges_components_mc
    features_mc = context.features_mc
    marine_mc = context.marine_mc

    countries = get_json_subform_data(json_str, 'Country')  # Country Code
    ges_components = get_json_subform_data(json_str_subform, 'GES Component')
    features = get_json_subform_data(json_str_subform, 'Feature')  # Feature

    mc_countries = sql2018.ReportedInformation

    # key = (mapper_class.__name__,
    #        str(countries),
    #        str(ges_components),
    #        str(features)
    #        )

    # @cache(lambda func: key)
    def get_res():
        conditions = []

        if countries:
            conditions.append(mc_countries.CountryCode.in_(countries))

        count, ids_indicator = db.get_all_records_outerjoin(
            mapper_class,
            mc_countries,
            *conditions
        )
        ids_indicator = [int(x.Id) for x in ids_indicator]

        conditions = list()

        if features:
            conditions.append(features_mc.Feature.in_(features))

        if ges_components:
            conditions.append(ges_comp_mc.GESComponent.in_(ges_components))
        count, ids_ind_ass = db.get_all_records_outerjoin(
            ges_comp_mc,
            features_mc,
            *conditions
        )
        ids_ind_ass = [int(x.IdIndicatorAssessment) for x in ids_ind_ass]

        ids_indicator = tuple(set(ids_indicator) & set(ids_ind_ass))

        count, marine_units = db.get_all_records_join(
            [mapper_class.Id, marine_mc.MarineReportingUnit],
            marine_mc,
            mapper_class.Id.in_(ids_indicator),
        )
        res = [x.MarineReportingUnit for x in marine_units]
        res = tuple(set(res))
        # res = ['MarineReportingUnit%s' % x for x in range(0, 10)]

        return res

    res = get_res()

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_country(context):
    mapper_class = context.subform.mapper_class

    count, res = db.get_all_records_outerjoin(
        sql2018.ReportedInformation,
        mapper_class
    )

    res = [x.CountryCode for x in res]
    res = list(set(res))

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2018_country_art9(context):
    mapper_class = sql2018.ART9GESGESComponent
    mc_countries = sql2018.ReportedInformation
    conditions = []

    # This became the first form in the chain, we no longer filter

    # ges_components = context.data.get('ges_component')
    # if ges_components:
    #     conditions.append(mapper_class.GESComponent.in_(ges_components))

    count, res = db.get_all_records_join(
        [mapper_class.GESComponent, mc_countries.CountryCode],
        mc_countries,
        *conditions
    )

    res = [x.CountryCode for x in res]
    res = list(set(res))

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2012_ges_components_art9(context):
    mc = sql.MSFD9Descriptor
    conditions = []

    mrus = context.subform.get_form_data_by_key(context, 'marine_unit_ids')

    if mrus:
        conditions.append(mc.MarineUnitID.in_(mrus))

    res = db.get_unique_from_mapper(
        mc,
        'ReportingFeature',
        *conditions
    )

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a2012_ges_components_art10(context):
    t = sql.t_MSFD10_DESCrit
    mc = sql.MSFD10Target

    conditions = []

    mrus = context.get_form_data_by_key(context, 'marine_unit_ids')

    if mrus:
        conditions.append(mc.MarineUnitID.in_(mrus))

    sess = db.session()
    q = sess.query(t.c.GESDescriptorsCriteriaIndicators).\
        join(mc, mc.MSFD10_Target_ID == t.c.MSFD10_Target).\
        filter(*conditions)

    res = set([x[0] for x in q])

    return vocab_from_values(res)


@provider(IVocabularyFactory)
def a18_ges_component(context):
    """ Vocabulary for article 18 Ges components
    """

    ges_components = context.get_ges_components()

    return vocab_from_values(ges_components)

