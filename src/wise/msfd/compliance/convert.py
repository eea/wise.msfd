""" A collection of data transformers to be used to convert 2018 DB data in
some other useful formats. Used when displaying data.
"""

from wise.msfd.gescomponents import GES_LABELS, get_ges_component
from wise.msfd.translation import get_translated
from wise.msfd.utils import ItemLabel, ItemList


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


def ges_component_list(field, value):
    values = value.split(',')
    rows = [ges_component(None, v) for v in values]

    return ItemList(rows=rows)


def csv_ges_labels_inverse_list(field, value, lang):
    vals = set(value.split(','))

    res = []

    for v in vals:
        title = GES_LABELS.get(field.label_collection, v)
        i = ItemLabel(title, v)
        res.append(i)

    return ItemList(rows=res)


def format_nr(field, value, lang):
    if value:
        return "%.2f" % value

    return value

def get_indicators(field, value, lang):
    title = GES_LABELS.get('indicators', value)
    tr = get_translated(title, lang)

    if tr:
        value = u"{} ({})".format(value, title)

        return ItemLabel(value, tr)
    else:
        return ItemLabel(value, title)
