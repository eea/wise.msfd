from __future__ import absolute_import
from __future__ import print_function
import logging
import os
import threading

from collections import defaultdict

from sqlalchemy import create_engine, distinct, func, and_, or_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.relationships import RelationshipProperty
from zope.sqlalchemy import register

from eea.cache import cache

from . import sql, sql2018
from .utils import db_result_key, group_query
import six
from six.moves import zip

env = os.environ.get
DSN = env('MSFDURI', 'mssql+pymssql://SA:bla3311!@msdb')  # ?charset=utf8mb4
USE_MOCKSESSION = env('USE_MOCKSESSION', False)
DBS = {
    '2012': env('MSFD_db_default', 'MarineDB_public'),
    '2018': env('MSFD_db_2018', 'MSFD2018_production')  # has all needed views
    # MSFD2018_sandbox_25102018
    # MSFD2018_production_v2
}

# DBS = {
#     'session': env('MSFD_db_default', 'MarineDB'),
#     'session_2018': env('MSFD_db_2018', 'MSFD2018_sandbox')
# }

USE_DB = 'USE {}'

threadlocals = threading.local()

logger = logging.getLogger('wise.msfd')


class MockQuery(list):
    """ Mock query object """

    @staticmethod
    def count():
        return 0

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def order_by(self, *args, **kwargs):
        return self


class MockSession(object):
    """ Our code is dependent on the MSFD database availability
        This session is used when the MSFD database is offline
    """

    def __init__(self):
        self._query = MockQuery()
        self.dirty = []

    def flush(self):
        pass

    # This is used to mimic the session.query call
    def query(self, *args, **kwargs):
        return self._query


def session():
    if USE_MOCKSESSION:
        print("Using MockSession()")

        return MockSession()

    session_name = getattr(threadlocals, 'session_name')

    if not session_name:
        raise ValueError("Please provide a session name for DB.")

    # print "Using session", session_name, DSN
    # print "DBS", DBS

    if hasattr(threadlocals, session_name):
        return getattr(threadlocals, session_name)

    try:
        session = _make_session(DSN)
        session.execute(USE_DB.format(DBS[session_name]))
        print("Session DSN: ", DSN)
        print("Session DBS: ", DBS[session_name])
    except:
        # TODO this is a temporary solution
        # Is it possible to switch back to MSFD database when it is online
        # without restarting?
        print("Unable to connect to: ", DSN)
        print("Using MockSession()")

        return MockSession()

    session.rollback()
    setattr(threadlocals, session_name, session)

    return session


def switch_session(func):
    """ Decorator to save the session name and switch back after function runs
    """

    def inner(*args, **kwargs):
        saved_session = getattr(threadlocals, 'session_name', None)

        res = func(*args, **kwargs)

        threadlocals.session_name = saved_session

        return res

    return inner


def use_db_session(session_name):
    """ A decorator factory that will switch the session based on provided name
    """

    def wrapped(func):
        """ Decorator to save the session name and switch back after function runs
        """

        def inner(*args, **kwargs):
            saved_session = getattr(threadlocals, 'session_name', None)

            threadlocals.session_name = session_name
            res = func(*args, **kwargs)

            threadlocals.session_name = saved_session

            return res

        return inner

    return wrapped


def _make_session(dsn):
    engine = create_engine(dsn,  # , encoding="utf8"
                           pool_recycle=1800,
                           pool_pre_ping=True,
                           connect_args={'timeout': 60}
                           )
    Session = scoped_session(sessionmaker(bind=engine))
    Session.expire_on_commit = False
    register(Session, keep_session=True)

    return Session()


@cache(db_result_key)
def get_unique_from_table(table, column):
    """ Retrieves unique values for a column table
    """
    col = getattr(table.c, column)

    sess = session()
    try:
        res = sess.query(col).distinct().order_by(col)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return sorted([x[0] for x in res])


@cache(db_result_key)
def get_unique_from_mapper(mapper_class, column, *conditions, **kwargs):
    """ Retrieves unique values for a mapper class
    """
    raw = kwargs.pop('raw', False)
    col = getattr(mapper_class, column)

    sess = session()
    try:
        res = sess.query(col)\
            .filter(*conditions)\
            .distinct()\
            .order_by(col)

        res_unicode = [six.text_type(x[0]).strip() for x in res]
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    if raw:
        return res

    return res_unicode


# @cache(db_result_key)
def get_unique_from_mapper_join(
        mapper_class,
        column,
        klass_join,
        order_field,
        *conditions,
        **kwargs):
    """ Retrieves unique values for a mapper class
    """
    page = kwargs.get('page', 0)
    col = getattr(mapper_class, column)

    sess = session()
    try:
        q = sess.query(col).join(klass_join).filter(
            *conditions
        ).order_by(order_field)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    total = q.count()
    item = q.offset(page).limit(1).first()

    return [total, item]


@cache(db_result_key)
def get_all_columns_from_mapper(mapper_class, column, *conditions, **kw):
    """ Retrieves all columns for a mapper class
    """
    # TODO: rename this method to get_column_from_mapper
    col = getattr(mapper_class, column)

    sess = session()
    try:
        res = sess.query(mapper_class).filter(*conditions).order_by(col)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return_value = [x for x in res]

    return return_value


def get_marine_unit_ids(**data):
    """ Return a list of available MarineUnitIDs for the query
    """
    table = sql.t_MSFD4_GegraphicalAreasID
    col = table.c.MarineUnitID

    sess = session()

    conditions = []

    if 'member_states' in data:
        conditions.append(table.c.MemberState.in_(data['member_states']))

    if 'marine_unit_ids' in data:
        return len(data['marine_unit_ids']), data['marine_unit_ids']

    # This condition was commented, but it should be active
    # we need to filter by regions
    if 'region_subregions' in data:
        conditions.append(table.c.RegionSubRegions.in_(
            data['region_subregions']))

    if 'area_types' in data and data['area_types']:
        conditions.append(table.c.AreaType.in_(data['area_types']))

    try:
        query = sess.query(col).filter(
            *conditions
            # table.c.RegionSubRegions.in_(data['region_subregions']),
            # table.c.AreaType.in_(data['area_types']),
        )
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    l = sorted([x[0] for x in query])

    return (query.count(), l)


# def group(l, p):
#     res = defaultdict(list)
#
#     for row in l:
#         pass
#
#     return l


# @cache(db_result_key)
def get_collapsed_item(mapper_class, klass_join, order_field, collapses,
                       *conditions, **kwargs):
    """ Group items
    """
    page = kwargs.get('page', 0)
    mc_join_cols = kwargs.get('mc_join_cols', [])
    sess = session()

    order_field = getattr(mapper_class, order_field)
    cols = []
    blacklist = []

    for d in collapses:
        for k, v in d.items():
            blacklist.append(k)
            blacklist.extend(v)

    for name, var in vars(mapper_class).items():
        if name in blacklist:
            continue

        if name.startswith('_'):
            continue

        if getattr(var, 'primary_key', False) is True:
            continue

        prop = var.property

        if isinstance(prop, RelationshipProperty):
            continue

        cols.append(name)

    mapped_cols_join = [getattr(klass_join, n) for n in mc_join_cols]
    mapped_cols = [getattr(mapper_class, n) for n in cols]
    all_cols = mapped_cols + mapped_cols_join

    try:
        q = sess.query(*all_cols).join(klass_join).filter(*conditions).distinct()
        all_items = q.all()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    total = len(all_items)
    item_values = all_items[page]
    # print("Item values", item_values)
    # item = q.offset(page).limit(1).first()
    # total = q.count()

    collapse_conditions = [mc == v for mc, v in zip(mapped_cols, item_values)]
    # item = mapper_class(**{c: v for c, v in zip(cols, item_values)})
    item = item_values

    extra_data = {}

    try:
        for d in collapses:
            for k, cs in d.items():
                cols = [k] + cs
                c_cols = [getattr(mapper_class, c) for c in cols]
                q = sess.query(*c_cols).filter(*collapse_conditions)
                extra_data[k] = group_query(q, k)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return [total, item, extra_data]


# @cache(db_result_key)
def get_item_by_conditions(mapper_class, order_field, *conditions, **kwargs):
    """Paged retrieval of items based on conditions
        Use for mapper class
    """
    page = kwargs.get('page', 0)
    sess = session()
    order_field = getattr(mapper_class, order_field)

    if kwargs.get('reverse', False) is True:
        order_field = order_field.desc()

    try:
        q = sess.query(mapper_class).filter(
            *conditions
        ).order_by(order_field)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    total = q.count()
    # Laci disabled: sometimes gives unpredictable result,
    # might be the first() which brokes it?
    # item = q.offset(page).limit(1).first()
    if not total:
        return [0, {}]

    item = q[page]

    return [total, item]


def get_item_by_conditions_table(table, order_field, *conditions, **kwargs):
    """Paged retrieval of items based on conditions
        Used for table
    """
    page = kwargs.get('page', 0)
    sess = session()
    order_field = getattr(table.c, order_field)

    if kwargs.get('reverse', False) is True:
        order_field = order_field.desc()

    try:
        q = sess.query(table).filter(
            *conditions
        ).order_by(order_field)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    total = q.count()
    # Laci disabled: sometimes gives unpredictable result,
    # might be the first() which brokes it?
    # item = q.offset(page).limit(1).first()
    if not total:
        return [0, {}]

    item = q[page]

    return [total, item]


# @cache(db_result_key)
def get_item_by_conditions_joined(
        mapper_class,
        klass_join,
        order_field,
        *conditions,
        **kwargs):
    # Paged retrieval of items based on conditions with joining two tables
    page = kwargs.get('page', 0)
    sess = session()
    order_field = getattr(mapper_class, order_field)
    try:
        q = sess.query(mapper_class).join(klass_join).filter(
            *conditions
        ).order_by(order_field)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    total = q.count()
    item = q.offset(page).limit(1).first()

    return [total, item]


def get_item_by_conditions_art_6(
        columns,
        klass_join,
        order_field,
        *conditions,
        **kwargs):
    # Paged retrieval of items based on conditions with joining two tables
    page = kwargs.get('page', 0)
    r_codes = kwargs.get('r_codes', [])
    sess = session()
    try:
        q = sess.query(*columns).join(klass_join).filter(
            *conditions
        ).order_by(order_field)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    q = [x for x in q]

    filtered_coops = []

    for row in q:
        if any(region in row.RegionsSubRegions for region in r_codes):
            filtered_coops.append(row)

    # item = q.offset(page).limit(1).first()
    item = filtered_coops[page]
    total = len(filtered_coops)

    return [total, item]


# @cache(db_result_key)
def get_table_records(columns, *conditions, **kwargs):
    order_by = kwargs.get('order_by')
    sess = session()
    try:
        q = sess.query(*columns).filter(*conditions)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    if order_by:
        q = q.order_by(order_by)

    total = q.count()

    return total, q


@cache(db_result_key)
def get_available_marine_unit_ids(marine_unit_ids, klass):
    """ Returns a list of which muid is available, of the ones provided
    """
    sess = session()
    try:
        q = sess.query(klass.MarineUnitID).filter(
            klass.MarineUnitID.in_(marine_unit_ids)
        ).order_by(klass.MarineUnitID).distinct()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    q = [x for x in q]
    total = len(q)

    return [total, q]


def count_items(primary, *conditions):
    """ Return number of records found with conditions
    """

    sess = session()
    fc = func.count(primary)
    try:
        count = sess.query(fc).filter(*conditions)[0][0]
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return count


@cache(db_result_key)
@use_db_session('2012')
def get_marine_unit_id_names(marine_unit_ids):
    """ Returns tuples of (id, label) based on the marine_unit_ids
    """

    sess = session()
    t = sql.t_MSFD4_GegraphicalAreasID

    try:
        q = sess.query(t.c.MarineUnitID, t.c.MarineUnits_ReportingAreas)\
            .filter(t.c.MarineUnitID.in_(marine_unit_ids))\
            .order_by(t.c.MarineUnits_ReportingAreas)\
            .distinct()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    q = [x for x in q]
    total = len(q)

    return [total, q]


# @cache(db_result_key)
def get_related_record(klass, column, rel_id):
    sess = session()

    try:
        q = sess.query(klass).filter(
            getattr(klass, column) == rel_id
        )
        item = q.first()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []


    return [q.count(), item]


# @cache(db_result_key)
def get_related_record_join(klass, klass_join, column, rel_id):
    sess = session()
    try:
        q = sess.query(klass).join(klass_join).filter(
            getattr(klass_join, column) == rel_id
        )
        item = q.first()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return [0, {}]

    return [q.count(), item]


@cache(db_result_key)
def get_all_records(mapper, *conditions, **kw):
    sess = session()

    try:
        if isinstance(mapper, (list, tuple)):
            q = sess.query(*mapper).filter(*conditions)
        else:
            q = sess.query(mapper).filter(*conditions)

        if 'order_by' in kw:
            order_by = kw.pop('order_by')
            q = q.order_by(order_by)

        q = [x for x in q]
        count = len(q)

    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return [0, []]

    return [count, q]


@cache(db_result_key)
def get_all_specific_columns(columns, *conditions, **kw):
    sess = session()
    try:
        q = sess.query(*columns).filter(*conditions).distinct()
        q = [x for x in q]
        count = len(q)
    except Exception as e:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return [0, []]

    return [count, q]


@cache(db_result_key)
def get_all_records_ordered(table, order_cols, *conditions):
    sess = session()

    order_by_mru = (hasattr(table.c, 'MarineReportingUnit')
                    and [table.c.MarineReportingUnit] or [])

    order_by = order_by_mru + [getattr(table.c, c)for c in order_cols]

    try:
        q = sess.query(table).filter(*conditions).\
            order_by(*order_by).distinct()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    # print q
    q = [x for x in q]
    count = len(q)

    return [count, q]


@cache(db_result_key)
def get_all_records_distinct_ordered(table, order_col, exclude, *conditions):
    sess = session()

    col = getattr(table.c, order_col)
    needed = set(table.columns.keys()) - set(exclude)
    col_needed = [getattr(table.c, c) for c in needed]

    try:
        # asd = sess.query(table).with_entities(*col_needed).distinct()

        q = sess.query(table).filter(*conditions).\
            order_by(table.c.MarineReportingUnit, col)

        q_unique = q.with_entities(*col_needed).distinct()
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    q_unique = [x for x in q_unique]

    exclude_data = {}

    for field in exclude:
        exclude_data[field] = ','.join(set([getattr(x, field) for x in q]))

    return [exclude_data, q_unique]


@cache(db_result_key)
def get_all_records_outerjoin(mapper_class, klass_join, *conditions, **kw):
    sess = session()
    try:
        res = sess.query(mapper_class).outerjoin(klass_join).filter(*conditions)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    res = [x for x in res]
    count = len(res)

    return [count, res]


@cache(db_result_key)
def get_all_records_join(columns, klass_join, *conditions, **kw):
    sess = session()
    try:
        q = sess.query(*columns).join(klass_join).filter(*conditions)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    q = [x for x in q]
    count = len(q)

    return [count, q]


def compliance_art8_join(columns, mc_join1, mc_join2, *conditions):
    sess = session()
    try:
        q = sess.query(*columns).outerjoin(mc_join1).outerjoin(mc_join2).filter(
            *conditions
        )
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []


    q = [x for x in q]
    count = len(q)

    return [count, q]


@cache(db_result_key)
def latest_import_ids_2018():
    mc = sql2018.ReportedInformation
    mc_v = sql2018.t_V_ReportedInformation

    conditions = [
        mc_v.c.EnvelopeStatus == 'End'
    ]

    sess = session()
    try:
        res = sess.query(mc).join(mc_v, mc.Id == mc_v.c.Id).filter(*conditions)
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    groups = defaultdict(int)

    for row in res:
        country_code = row.CountryCode
        schema = row.Schema
        rowid = row.Id
        k = (country_code, schema)

        if rowid >= groups[k]:
            groups[k] = rowid

    latest_ids = [v for k, v in groups.items()]

    return latest_ids


@cache(db_result_key)
def get_competent_auth_data(*conditions, **kw):
    mc = sql.t_MS_CompetentAuthorities
    sess = session()
    try:
        query = sess.query(mc).filter(*conditions).order_by(mc.c.C_CD)
        data = [x for x in query]
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    filtered_data = []
    last_rep_dates = {}

    # get the last reported date for each country
    for row in data:
        country = row.C_CD
        rep_date = row.ReportingDate

        # we do not have a max rep date yet so insert it
        if country not in last_rep_dates:
            last_rep_dates[country] = rep_date
            continue

        # update the reported date for the country if we have a newer rep date
        if rep_date > last_rep_dates[country]:
            last_rep_dates[country] = rep_date

    # filter the data
    for row in data:
        country = row.C_CD
        rep_date = row.ReportingDate

        if last_rep_dates[country] == rep_date:
            filtered_data.append(row)

    cnt = len(filtered_data)

    return cnt, filtered_data


# MSFD Search article 11 2020 specific queries
@use_db_session('2018')
def get_a11_regions_countries():
    try:
        t = sql2018.ART11ProgrammesMonitoringProgrammeMarineReportingUnit
        mp = sql2018.ART11ProgrammesMonitoringProgramme
        t_mru = sql2018.MarineReportingUnit
        rep = sql2018.ReportedInformation

        columns = [
            # t.MarineReportingUnit,
            t.IdMonitoringProgramme,
            t_mru.Region,
            t_mru.CountryCode,
            mp.ProgrammeCode,
        ]

        sess = session()

        q = sess.query(*columns) \
            .join(mp, mp.Id == t.IdMonitoringProgramme) \
            .join(rep, rep.Id == mp.IdReportedInformation) \
            .join(t_mru,
                  and_(t.MarineReportingUnit == t_mru.MarineReportingUnitId,
                       rep.CountryCode == t_mru.CountryCode)) \
            .distinct()

        res = [x for x in q]

    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return res


A11_REGIONS_COUNTRIES = get_a11_regions_countries()


@use_db_session('2018')
def get_a11_descr_prog_code():
    strat = sql2018.ART11StrategiesMonitoringStrategy
    strat_mp = sql2018.ART11StrategiesMonitoringStrategyMonitoringProgramme

    sess = session()
    columns = [strat.Descriptor, strat_mp.MonitoringProgrammes]
    try:
        q = sess.query(*columns).join(strat_mp)
        res = [x for x in q]
    except:
        sess.rollback()
        logger.exception("MSFD database is timed out")
        return []

    return res


A11_DESCR_PROG_CODES = get_a11_descr_prog_code()

@use_db_session('2018')
def get_all_data_from_view_Art8(country_code):
    sess = session()
    t = sql2018.t_V_ART8_GES_2018

    conditions = [
        t.c.CountryCode == country_code
    ]

    # Handle the case of Romania that submitted duplicate data,
    # where Element is empty, but Criteria has data
    if country_code != 'RO':
        conditions.append(
            or_(t.c.Element.isnot(None),
                t.c.Criteria.isnot(None))
        )
    else:
        conditions.append(
            t.c.Element.isnot(None)
        )

    # groupby IndicatorCode
    q = sess\
        .query(t)\
        .filter(*conditions)\
        .distinct()

    out = [x for x in q]

    return out


@use_db_session('2018')
def get_all_data_from_view_Art9(country_code):
    t = sql2018.t_V_ART9_GES_2018

    conditions = [
        t.c.CountryCode == country_code
    ]

    count, q = get_all_records_ordered(
        t,
        ('GESComponent', ),
        *conditions
    )

    out = [x for x in q]

    return out    


@use_db_session('2018')
def get_all_data_from_view_Art10(country_code):
    t = sql2018.t_V_ART10_Targets_2018

    conditions = [t.c.CountryCode == country_code]

    count, res = get_all_records_ordered(
        t,
        (),
        *conditions
    )

    out = [x for x in res]

    return out


@use_db_session('2018')
def get_all_data_from_view_art11(country_code):
    t = sql2018.t_V_ART11_Strategies_Programmes_2020

    conditions = [
        t.c.CountryCode == country_code
    ]

    count, q = get_all_records_ordered(
        t,
        (),
        *conditions
    )

    res = [x for x in q]

    return res    


@use_db_session('2018')
def get_all_data_from_view_art13(country_code):
    t = sql2018.t_V_ART13_Measures_2022

    conditions = [
        t.c.CountryCode == country_code
    ]

    count, q = get_all_records_ordered(
        t,
        (),
        *conditions
    )

    res = [x for x in q]

    return res    


@use_db_session('2018')
def get_all_data_from_view_art14(country_code):
    t = sql2018.t_V_ART14_Exceptions_2022

    conditions = [
        t.c.CountryCode == country_code
    ]

    count, q = get_all_records(
        t,
        *conditions
    )

    res = [x for x in q]

    return res    


@use_db_session('2018')
def is_art8_report_available_2018(region, country_code, descriptor):
    mapper = sql2018.t_V_ART8_GES_2018
    sess = session()

    conditions = [
        mapper.c.Region == region.upper(),
        mapper.c.CountryCode == country_code.upper(),
        mapper.c.GESComponent == descriptor.upper()
    ]

    q = sess.query(mapper).filter(*conditions).limit(1)

    return q.count() > 0


@use_db_session('2018')
def is_art9_report_available_2018(region, country_code, descriptor):
    mapper = sql2018.t_V_ART8_GES_2018
    sess = session()

    conditions = [
        or_(mapper.c.Region == region.upper(),
            mapper.c.Region == None),
        mapper.c.CountryCode == country_code.upper(),
        mapper.c.GESComponent == descriptor.upper()
    ]

    q = sess.query(mapper).filter(*conditions).limit(1)

    return q.count() > 0
