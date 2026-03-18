# pylint: skip-file
from __future__ import absolute_import
from __future__ import print_function
import re
import logging
import html
from collections import namedtuple
from dateutil import parser
from six import text_type, string_types

from zope.security import checkPermission

from plone.memoize import volatile
from wise.msfd.utils import current_date

logger = logging.getLogger("wise.msfd")

NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}
RE_REGION_NORM = re.compile(r"^[A-Z]{3}\s")
FILENAME_FIX = re.compile(r"^[0-9]\-")


ReportingInformation = namedtuple(
    "ReportingInformation", ["report_date", "reporters"])

ReportingInformation2018 = namedtuple(
    "ReportingInformation", ["ReportedFileLink",
                             "ContactOrganisation", "ReportingDate"]
)


ORDER_COLS_ART11 = (
    "CountryCode",
    "Descriptor",
    "MonitoringProgrammes",
    "P_ProgrammeCode",
    "GESCriteria",
    "Feature",
)


def date_format(date):
    date_placeholder = "-"

    if not date:
        return date_placeholder

    try:
        return parser.parse(date).date().isoformat()
    except ValueError:
        return date_placeholder


def get_reportdata_key(func, self, *args, **kwargs):
    """Reportdata template rendering cache key generation"""

    if "nocache" in self.request.form:
        raise volatile.DontCache

    can_edit = checkPermission("wise.EditTranslations", self.context)
    muids = ",".join([m.id for m in self.muids])
    region = getattr(self, "country_region_code", "".join(self.regions))
    focus_muid = getattr(self, "focus_muid", "")

    cache_key_extra = getattr(self, "cache_key_extra", "")

    res = "_cache_" + "_".join(
        [
            func.__name__,
            self.report_year,
            cache_key_extra,
            self.country_code,
            region,
            self.descriptor,
            self.article,
            muids,
            focus_muid,
            current_date(),
            text_type(can_edit),
        ]
    )
    # TODO why replace '.', makes D1.1 the same as D11
    # res = res.replace('.', '').replace('-', '')
    logger.info("Report data cache key: %s", res)

    return res


def serialize_rows(rows):
    """Return a cacheable result of rows, this is used when
    downloading the report data as excel

    :param rows: view.rows
    :return: dict in format {mru : data, ...} where
        'mru': marine unit id, representing the worksheet title
        'data': list of tuples in format [(row_title, raw_data), ...]
        'raw_data' list of unicode values [u'GES 5.1', u'GES 5.2', ...]
    """

    if isinstance(rows, list):
        rows = {"Report data": rows}

    res = {}

    for mru, data in rows.items():
        raw_data = []

        for row in data:
            title = row.title
            raw_values = []

            for v in row.raw_values:
                if isinstance(v, str):
                    v = html.unescape(v)  # .decode('utf-8'))

                if not isinstance(v, string_types):
                    if not v:
                        v = ""
                    else:
                        v = v.__repr__()

                        if isinstance(v, str):
                            v = v  # .decode('utf-8')

                raw_values.append(text_type(v))

            raw_data.append((title, raw_values))

        res[mru] = raw_data

    return res
