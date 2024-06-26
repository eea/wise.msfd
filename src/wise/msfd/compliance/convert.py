#pylint: skip-file
""" A collection of data transformers to be used to convert 2018 DB data in
some other useful formats. Used when displaying data.
"""

from __future__ import absolute_import
import re

from wise.msfd.compliance.vocabulary import REGIONAL_DESCRIPTORS_REGIONS
from wise.msfd.gescomponents import get_ges_component
from wise.msfd.labels import GES_LABELS
from wise.msfd.translation import get_translated
from wise.msfd.utils import ItemLabel, ItemList, SimpleTable

from .regionaldescriptors.utils import get_nat_desc_country_url

comma_separator_re = re.compile(r',(?=[^\s])')
art11_measure_separator = re.compile(r'(?<=\'),')


def simple_itemlist(field, value, lang, separator=","):
    vals = value.split(separator)
    vals = set([v.strip() for v in vals])

    return ItemList(rows=vals)


def simple_itemlist_re(field, value, lang):
    vals = re.split(comma_separator_re, value)

    return ItemList(rows=set(vals))


def simple_itemlist_art11_measures(field, value, lang):
    vals = re.split(art11_measure_separator, value)

    return ItemList(rows=set(vals))


def csv_ges_labels_list(field, value, lang, separator=','):
    vals = value.split(separator)
    vals = set([v.strip() for v in vals])

    res = []

    for v in vals:
        title = GES_LABELS.get(field.label_collection, v)
        i = ItemLabel(v, title)
        res.append(i)

    return ItemList(rows=res)


def ges_component(field, value, lang):
    criterion = get_ges_component(value)

    if criterion is None:
        return value

    return criterion


def inverse_label(field, value, lang):
    title = GES_LABELS.get(field.label_collection, value)
    item = ItemLabel(title, value)

    return item


def ges_component_list(field, value, lang, separator=','):
    values = value.split(separator)
    values = [v.strip() for v in values]
    rows = [ges_component(None, v, lang) for v in values]
    item_list = ItemList(rows=rows)

    return item_list


def csv_ges_labels_inverse_list(field, value, lang, separator=','):
    vals = value.split(separator)
    vals = set([v.strip() for v in vals])

    res = []

    for v in vals:
        title = GES_LABELS.get(field.label_collection, v)
        i = ItemLabel(title, v)
        res.append(i)

    return ItemList(rows=res)


def csv_ges_labels_inverse_list_indicators(field, value, lang, separator=','):
    vals = value.split(separator)
    vals = set([v.strip() for v in vals])

    res = []

    for v in vals:
        i = get_indicators(field, v, lang)
        res.append(i)

    return ItemList(rows=res)


def art11_indicators(field, value, lang):
    vals = re.split(comma_separator_re, value)

    res = []

    for v in vals:
        code = v.split(' - ')[0].strip()
        i = get_indicators(field, code, lang)
        res.append(i)

    return ItemList(rows=res)


def format_nr(field, value, lang):
    if value:
        return "%.2f" % value

    return value


def get_indicators(field, value, lang):
    value_orig = value
    title = GES_LABELS.get('indicators', value)
    url = GES_LABELS.get('indicators_url', value)
    tr = get_translated(title, lang)

    if tr:
        value = u"{} ({})".format(value, title)
        title = tr

    if url != value_orig:
        template = u'<a style="cursor: help;" target="_blank" href="{}">{}</a>'

        return ItemLabel(value, template.format(url, title))

    # if tr:
    #     value = u"{} ({})".format(value, title)
    #
    #     return ItemLabel(value, tr)
    else:
        return ItemLabel(value, title)


def format_area(field, value, lang):
    if value:
        return "{:.0f} km2".format(value)

    return value


def mrus_as_table(field, value, lang):

    return SimpleTable(field.name, value)


def anchor(field, value, lang):
    if value and value.startswith('http'):
        return u"<a href='{0}' target='_blank'>{0}</a>".format(value)

    return value


def public_consulation_date(field, value, lang):
    if value:
        v = value

        return "{}/{}/{} - {}/{}/{}".format(v[0:4], v[4:6], v[6:8],
                                            v[9:13], v[13:15], v[15:17])

    return value


def __link_to_nat_desc_art11(field, value, self):
    url = self.request['URL0']

    reg_main = self._countryregion_folder.id.upper()
    subregions = [r.subregions for r in REGIONAL_DESCRIPTORS_REGIONS
                  if reg_main in r.code]

    res = []
    template = u'<a style="cursor: pointer;" target="_blank" href="{}">{}</a>'

    c_code = value.split('/')[3].upper()
    regions = [r.code for r in REGIONAL_DESCRIPTORS_REGIONS
               if len(r.subregions) == 1 and c_code in r.countries
               and r.code in subregions[0]]

    for r in regions:
        report_url = get_nat_desc_country_url(url, reg_main, c_code, r)
        res.append(ItemLabel(r, template.format(report_url, r)))

    return ItemList(res)
