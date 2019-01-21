import csv
import logging

from lxml.etree import parse
from pkg_resources import resource_filename

COMMON_LABELS = {}                        # vocabulary of labels


logger = logging.getLogger('wise.msfd')


def _extract_from_csv():
    labels = {}
    csv_f = resource_filename('wise.msfd',
                              'data/MSFDreporting_TermLists.csv')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='|')

        for row in csv_file:
            if row[0] in labels.keys():
                logger.debug("Duplicate label in csv file: %s", row[0])

            labels[row[0]] = row[1]

    return labels


def _extract_from_xsd(fpath):
    labels = {}

    # """ Read XSD files and populates a vocabulary of term->label

    # Note: there labels are pretty ad-hoc defined in the xsd file as
    # documentation tags, so this method is imprecise.
    # """

    lines = []
    xsd_f = resource_filename('wise.msfd', fpath)

    e = parse(xsd_f)

    for node in e.xpath('//xs:documentation',
                        namespaces={'xs': "http://www.w3.org/2001/XMLSchema"}):
        text = node.text.strip()
        lines.extend(text.split('\n'))

    for line in lines:

        line = line.strip()

        for splitter in ['=', '\t']:
            eqpos = line.find(splitter)

            if eqpos == -1:
                continue

            if ' ' in line[:eqpos]:
                continue

            label, title = line.split(splitter, 1)

            # if label in COMMON_LABELS:
            #     logger = logging.getLogger('tcpserver')
            #     logger.warning("Duplicate label in xsd file: %s", label)

            labels[label] = title

    return labels


def get_common_labels():
    labels = {}
    labels.update(_extract_from_csv())
    labels.update(_extract_from_xsd('data/MSCommon_1p0.xsd'))
    labels.update(_extract_from_xsd('data/MSCommon_1p1.xsd'))

    return labels


COMMON_LABELS = get_common_labels()
