from __future__ import absolute_import
import re
from collections import defaultdict
from datetime import datetime
from io import BytesIO

from six import string_types

import xlsxwriter
from wise.msfd.utils import class_id, get_obj_fields, print_value_xls
from six.moves import range

FORMS_ART4 = {}
FORMS_ART8 = {}
FORMS_ART8_2012 = {}
FORMS_ART8_2018 = {}
FORMS_ART9 = {}
FORMS_ART9_2012 = {}
FORMS_ART10 = {}
FORMS_ART10_2012 = {}
FORMS_ART11 = {}
FORMS_ART13 = {}
FORMS_ART14 = {}
FORMS_ART1318 = {}
FORMS_ART18 = {}
FORMS_ART19 = {}
SUBFORMS = defaultdict(set)        # store subform references
ITEM_DISPLAYS = defaultdict(set)   # store registration for item displays


def register_form_art19(klass):
    """ Register form classes for article 19
    2018 reporting year and 2012 reporting year
    """

    FORMS_ART19[class_id(klass)] = klass

    return klass


def register_form_art8(klass):
    """ Register form classes for article 8
    """

    FORMS_ART8[class_id(klass)] = klass

    return klass


def register_form_art9(klass):
    """ Register form classes for article 9
    """

    FORMS_ART9[class_id(klass)] = klass

    return klass


def register_form_art10(klass):
    """ Register form classes for article 10
    """

    FORMS_ART10[class_id(klass)] = klass

    return klass


def register_form_a8_2018(klass):
    """ Register form classes for articles 8, 9, 10

    for reporting year 2018
    """

    FORMS_ART8_2018[class_id(klass)] = klass

    return klass


def register_form_art4(klass):
    """ Registers a form for article 4

    """

    FORMS_ART4[class_id(klass)] = klass

    return klass


def register_form_art11(klass):
    """ Registers a 'secondary' form class for article 11

    """

    FORMS_ART11[class_id(klass)] = klass

    return klass


def register_form_art13(klass):
    FORMS_ART13[class_id(klass)] = klass

    return klass


def register_form_art14(klass):
    FORMS_ART14[class_id(klass)] = klass

    return klass


def register_form_art1318(klass):

    FORMS_ART1318[class_id(klass)] = klass

    return klass


def register_form_art18(klass):
    """ Registers a form class for article 18

    """

    FORMS_ART18[class_id(klass)] = klass

    return klass


def get_form(name):
    if name:
        return FORMS_ART8_2012[name]


def register_subform(mainform):
    """ Registers a 'subform' as a possible choice for displaying data

    These are the 'pages', such as 'Ecosystem(s)', 'Functional group(s)' in the
    'Article 8.1a (Analysis of the environmental status)'
    """

    def wrapper(klass):
        SUBFORMS[mainform].add(klass)

        return klass

    return wrapper


def get_registered_subform(form, name):
    """ Get the subform for a "main" form. For ex: A81a selects Ecosystem
    """

    if name:
        return SUBFORMS.get((class_id(form), name))


def register_form_section(parent_klass):
    """ Registers a 'section' in a page with data.

    These are the 'sections' such as 'Pressures and impacts' or
    'Status assessment' in subform 'Ecosystem(s)' in 'Article 8.1a (Analysis of
    the environmental status)'
    """

    def wrapper(klass):
        ITEM_DISPLAYS[parent_klass].add(klass)

        return klass

    return wrapper


def get_registered_form_sections(form):
    return ITEM_DISPLAYS[form.__class__]


def register_form_a8_2012(klass):
    """ Registers a 'secondary' form class

    These are the forms implementing the 'Article 9 (GES determination)',
    'Article 10 (Targets)' and so on, for one of the 'chapters'.
    """

    FORMS_ART8_2012[class_id(klass)] = klass

    return klass


def register_form_a9_2012(klass):
    """ Registers a 'Report type' form class for Article 9 year 2012
    """

    FORMS_ART9_2012[class_id(klass)] = klass

    return klass


def register_form_a10_2012(klass):
    """ Registers a 'Report type' form class for Article 10 year 2012
    """

    FORMS_ART10_2012[class_id(klass)] = klass

    return klass


def data_to_xls(data, blacklist_labels=None):
    """ Convert python export data to XLS stream of data

    blacklist_labels: a list of column names for which we do not get label

    NOTE: this is very specific to MSFD search. Too bad
    """
    if not blacklist_labels:
        blacklist_labels = []

    # Create a workbook and add a worksheet.
    out = BytesIO()
    workbook = xlsxwriter.Workbook(out, {'in_memory': True})

    for wtitle, wdata in data:
        # check data length, we do not create empty sheets

        if isinstance(wdata, list):
            count_data = len(wdata)
        else:
            count_data = wdata.count()

        if not count_data:
            continue

        worksheet = workbook.add_worksheet(wtitle)

        row0 = wdata[0]
        is_tuple = isinstance(row0, tuple)

        if not is_tuple:
            fields = get_obj_fields(row0, False)
        else:
            fields = row0._fields

        # write titles, filter fields
        # exclude relationship type fields
        fields_needed = list()

        for i, f in enumerate(fields):
            field_needed = True

            for j in range(count_data):
                field_val = getattr(wdata[j], f)

                if not isinstance(field_val,
                                  string_types + (datetime, float,
                                                  int, type(None))):
                    field_needed = False

                    break

            if field_needed:
                fields_needed.append(f)
                worksheet.write(0, fields_needed.index(f), f)

        for j, row in enumerate(wdata):
            for i, f in enumerate(fields_needed):
                if not is_tuple:
                    value = getattr(row, f)
                else:
                    value = row[i]

                if isinstance(value, datetime):
                    value = value.isoformat()

                label = value

                if f not in blacklist_labels:
                    label = print_value_xls(value, f)

                try:
                    worksheet.write(j + 1, i, label)
                except TypeError:
                    worksheet.write(j + 1, i, str(label))

    workbook.close()
    out.seek(0)

    return out


ART_RE = re.compile('\s(\d+\.*\d?\w?)\s')
ART_RE_2018 = re.compile('\s\d+((\.\d\w+)|(\s&\s\d+))?')


def article_sort_helper(term):
    """ Returns a float number for an article, to help with sorting
    """
    title = term.title
    # make Article 6 last in order
    if 'Article 6' in title:
        return 99.9

    text = ART_RE.search(title).group().strip()
    chars = []

    for c in text:
        if c.isdigit() or c is '.':
            chars.append(c)
        else:
            chars.append(str(ord(c)))

    f = ''.join(chars)

    return float(f)


def article_sort_helper_2018(term):
    title = term.title
    text = ART_RE_2018.search(title).group().strip()
    chars = []

    for c in text:
        if c.isdigit() or c is '.':
            chars.append(c)
        else:
            chars.append(str(ord(c)))

    f = ''.join(chars)

    return float(f)
