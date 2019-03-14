from collections import defaultdict

from wise.msfd.utils import FlatItemList, ItemList

from .proxy import proxy_cmp


def consolidate_date_by_mru(data):
    """ Takes data (proxies of data) organized by mru and groups them according
    to similarity of data (while ignoring the mru of that proxied row)

    This is used by the A9 2018 report.
    """

    groups = []
    # Rows without MRU reported
    # This case applies for Art9, when justification for delay is reported
    rows_without_mru = []

    for dataset in data.values():

        for row in dataset:
            found = False

            for group in groups:
                for g_row in group[:]:
                    if proxy_cmp(g_row, row):
                        group.append(row)
                        found = True

            if not found:   # create a new group
                groups.append([row])

    # regroup the data by mru, now that we found identical rows
    regroup = defaultdict(list)

    for batch in groups:
        # TODO: get a proper MarineUnitID object
        mrus = tuple(sorted(set([r.MarineReportingUnit for r in batch])))

        if mrus[0] is None:
            rows_without_mru.append(batch[0])

            continue

        regroup[mrus].append(batch[0])

    out = {}

    # rewrite the result keys to list of MRUs

    for mrus, rows in regroup.items():
        label = FlatItemList(rows=mrus)
        rows.extend(rows_without_mru)
        out[label] = rows

    if not regroup and rows_without_mru:
        label = 'No Marine unit ID reported'
        out[label] = rows_without_mru

    return out


def consolidate_singlevalue_to_list(proxies, fieldname):
    """ Given a list of proxies where one of the fields needs to be a list, but
    is spread across different similar proxies, consolidate the single values
    to a list and return only one object for that list of similar objects
    """
    map_ = []

    for o in proxies:
        if not map_:
            map_.append([o])

            continue

        found = False

        for set_ in map_:
            if proxy_cmp(set_[0], o, fieldname):
                set_.append(o)
                found = True

                break

        if not found:
            map_.append([o])

    res = []

    for set_ in map_:
        o = set_[0]
        values = [getattr(xo, fieldname) for xo in set_]

        if any(values):
            l = ItemList(rows=values)
            setattr(o, fieldname, l)

        res.append(o)

    return res
