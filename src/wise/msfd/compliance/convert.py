""" A collection of data transformers to be used to convert 2018 DB data in
some other useful formats. Used when displaying data.
"""

from wise.msfd.gescomponents import get_ges_component
from wise.msfd.labels import GES_LABELS
from wise.msfd.translation import get_translated
from wise.msfd.utils import ItemLabel, ItemList, SimpleTable


def simple_itemlist(field, value, lang):
    vals = set(value.split(','))

    return ItemList(rows=vals)


def csv_ges_labels_list(field, value, lang):
    vals = set(value.split(','))

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


def ges_component_list(field, value, lang):
    values = value.split(',')
    rows = [ges_component(None, v, lang) for v in values]

    return ItemList(rows=rows)


def csv_ges_labels_inverse_list(field, value, lang):
    vals = set(value.split(','))

    res = []

    for v in vals:
        title = GES_LABELS.get(field.label_collection, v)
        i = ItemLabel(title, v)
        res.append(i)

    return ItemList(rows=res)


def csv_ges_labels_inverse_list_indicators(field, value, lang):
    vals = set(value.split(','))

    res = []

    for v in vals:
        i = get_indicators(field, v, lang)
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
        return u"<a href='{0}'>{0}</a>".format(value)

    return value


def public_consulation_date(field, value, lang):
    if value:
        v = value

        return "{}/{}/{} - {}/{}/{}".format(v[0:4], v[4:6], v[6:8],
                                            v[9:13], v[13:15], v[15:17])

    return value
