# pylint: skip-file
from __future__ import absolute_import
import csv

from pkg_resources import resource_filename
from six.moves import zip


def parse_csv(path, klass):
    wf = resource_filename('wise.msfd.wisetheme', path)

    reader = csv.reader(open(wf))
    cols = next(reader)
    stats = []

    for line in reader:
        d = dict(zip(cols, line))
        s = klass(**d)
        stats.append(s)

    return stats
