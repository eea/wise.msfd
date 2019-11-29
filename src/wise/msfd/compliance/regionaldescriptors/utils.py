from collections import namedtuple

from plone.intelligenttext.transforms import \
    convertWebIntelligentPlainTextToHtml as convertWIPT

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd import db, sql, utils
from wise.msfd.data import countries_in_region, muids_by_country
from wise.msfd.utils import TemplateMixin

from ..base import BaseComplianceView

# TODO: AreaType for each record can be AA_AssessmentArea, SR_SubRegion and
# so on. Which one we use?


def _separated_itemlist(values, separator, sort):
    _sorted = values

    if sort:
        _sorted = sorted(set(values))

    return convertWIPT(separator.join(_sorted))


def newline_separated_itemlist(values, sort=True):
    separator = u"\n"

    return _separated_itemlist(values, separator, sort)


def emptyline_separated_itemlist(values, sort=True):
    separator = u"\n\n\n"

    return _separated_itemlist(values, separator, sort)


def compoundrow(func):
    """ Decorator to return a compound row for 2018 reports"""

    def inner(*args, **kwargs):
        rows = func(*args, **kwargs)
        self = args[0]

        return RegionalCompoundRow(self, self.request,
                                   self.field, rows)

    return inner


def compoundrow2012(self, title, rows):
    """ Function to return a compound row for 2012 report"""

    FIELD = namedtuple("Field", ["name", "title"])
    field = FIELD(title, title)

    return RegionalCompoundRow(self, self.request, field, rows)


def get_percentage(values):
    """ Compute percentage of true-ish values in the list
    """
    # TODO: check if x is 0, consider it True
    trues = len([x for x in values if x])

    return (trues * 100.0) / len(values)


class RegionalCompoundRow(TemplateMixin):
    template = ViewPageTemplateFile('pt/regional-compound-row.pt')

    def __init__(self, context, request, field, rows):
        self.context = context
        self.request = request
        self.field = field
        self.rows = rows
        self.rowspan = len(rows)


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
        return utils.TableHeader('Member state', self.countries)

    def get_elements_monitored(self):
        # MONSub = sql_extra.MSFD11MONSub
        all_elements = get_monitored_elements(self.countries)

        for el in all_elements:
            print el.Q9a_ElementMonitored

        rows = []

        return utils.CompoundRow(
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


def get_nat_desc_country_url(url, reg_main, c_code, r_code):
    href = url.replace(
        'regional-descriptors-assessments/{}'.format(reg_main.lower()),
        'national-descriptors-assessments/{}/{}'.format(
            c_code.lower(), r_code.lower())
    )

    return "<a target='_blank' href='{}'>{}</a>".format(href, r_code)
