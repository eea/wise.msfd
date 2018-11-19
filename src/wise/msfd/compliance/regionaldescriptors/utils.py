from collections import defaultdict

from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)
from wise.msfd import db, sql, sql_extra

from ..base import BaseComplianceView

# TODO: AreaType for each record can be AA_AssessmentArea, SR_SubRegion and
# so on. Which one we use?


def get_percentage(values):
    """ Compute percentage of true-ish values in the list
    """
    # TODO: check if x is 0, consider it True
    trues = len([x for x in values if x])

    return (trues * 100.0) / len(values)


class TemplateMixin:
    template = None

    def __call__(self):
        return self.template(**self.__dict__)


class List(TemplateMixin):
    template = PageTemplateFile('pt/list.pt')

    def __init__(self, rows):
        self.rows = rows


class CompoundRow(TemplateMixin):
    multi_row = PageTemplateFile('pt/compound-row.pt')
    one_row = PageTemplateFile('pt/compound-one-row.pt')

    @property
    def template(self):
        if self.rowspan > 1:
            return self.multi_row

        return self.one_row

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows
        self.rowspan = len(rows)


class Row(TemplateMixin):
    template = PageTemplateFile('pt/simple-row.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class TableHeader(TemplateMixin):
    template = PageTemplateFile('pt/table-header.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


def get_key(func, self):
    return self.descriptor + ':' + self.region


@db.use_db_session('2012')
def all_regions():
    """ Return a list of region ids
    """

    return db.get_unique_from_mapper(
        sql_extra.MSFD4GeographicalAreaID,
        'RegionSubRegions'
    )


@db.use_db_session('2012')
def countries_in_region(regionid):
    """ Return a list of (<countryid>, <marineunitids>) pairs
    """
    t = sql_extra.MSFD4GeographicalAreaID

    return db.get_unique_from_mapper(
        t,
        'MemberState',
        t.RegionSubRegions == regionid
     )


@db.use_db_session('2012')
def muids_by_country():
    t = sql_extra.MSFD4GeographicalAreaID
    count, records = db.get_all_records(t)
    res = defaultdict(list)

    for rec in records:
        res[rec.MemberState].append(rec.MarineUnitID)

    return dict(**res)


class RegDescA11(BaseComplianceView):
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
        self.muids_in_region = []

        for c in self.countries:
            self.muids_in_region.extend(self.all_countries[c])

        allrows = [
            self.get_countries_row(),
            self.get_elements_monitored(),
        ]

        return self.template(rows=allrows)

    def get_countries_row(self):
        return TableHeader('Member state', self.countries)

    def get_elements_monitored(self):
        # MONSub = sql_extra.MSFD11MONSub
        all_elements = get_monitored_elements(self.countries)

        for el in all_elements:
            print el.Q9a_ElementMonitored

        rows = []

        return CompoundRow(
            'Elements monitored',
            rows
        )


@db.use_db_session('2012')
def get_monitored_elements(countryids):
    MS = sql.MSFD11MONSub
    EM = sql.MSFD11Q9aElementMonitored
    SP = sql.MSFD11SubProgramme

    sess = db.session()
    q = sess.query(EM)\
        .filter(EM.SubProgramme == SP.ID)\
        .filter(SP.ID == MS.SubProgramme)\
        .filter(MS.MemberState.in_(countryids))

    return q.all()
