""" A collection of data transformers to be used to convert 2018 DB data in
some other useful formats. Used when displaying data.
"""

from wise.msfd.gescomponents import GES_LABELS, get_ges_component
from wise.msfd.utils import ItemLabel, ItemList


def ges_labels_list(node, value):
    vals = set(value.split(','))
    label_name = node.get('label')

    res = []

    for v in vals:
        title = GES_LABELS.get(label_name, v)
        i = ItemLabel(v, title)
        res.append(i)

    return ItemList(rows=res)


def ges_component(node, value):
    criterion = get_ges_component(value)

    if criterion is None:
        return value

    return criterion


def ges_labels_inverse_list(node, value):
    vals = set(value.split(','))
    label_name = node.get('label')

    res = []

    for v in vals:
        title = GES_LABELS.get(label_name, v)
        i = ItemLabel(title, v)
        res.append(i)

    return ItemList(rows=res)


# def target_code_to_description(node, value):
#     """
#     """
#
#     # TODO: this doesn't work properly, to fix
#     title = GES_LABELS.get('targets', value)
#
#     return ItemLabel(title, value)
