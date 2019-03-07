from wise.msfd.utils import FlatItemList
from .proxy import proxy_cmp
from collections import defaultdict


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
