""" A collection of data transformers to be used to convert 2018 DB data in
some other useful formats. Used when displaying data.
"""

from wise.msfd.gescomponents import GES_LABELS, get_ges_component
from wise.msfd.utils import ItemLabel, ItemList


def ges_labels_list(node, value):
    vals = set(value.split(','))
    label_name = node.get('label')

    res = [
        ItemLabel(
            v,
            GES_LABELS.get(label_name, v),
        )

        for v in vals
    ]

    return ItemList(rows=res)


def ges_component(node, value):
    criterion = get_ges_component(value)

    if criterion is None:
        return value

    return criterion


def target_code_to_description(node, value):
    """
    """

    # TODO: this doesn't work properly, to fix
    title = GES_LABELS.get('targets', value)

    return ItemLabel(title, value)
