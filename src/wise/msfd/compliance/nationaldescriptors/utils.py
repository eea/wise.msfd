import lxml.etree
from pkg_resources import resource_filename


def row_to_dict(table, row):
    cols = table.c.keys()
    res = {k: v for k, v in zip(cols, row)}

    return res


def get_sorted_fields_2018(fields, article):
    """ Return field/title by parsing report_2018_def.xml
        field = name from DB
        title = title/label showed in the template

    :param fields: ['Feature', 'GESComponents', 'Element', 'TargetCode', ...]
    :param article: 'Art8'
    :return: [('<fieldname>', <title'), ...
              ('Feature', 'Feature'), ('GESComponents', ''GESComponents),
        ... , ('TargetCode', 'RelatedTargets')]
    """

    labels_file = resource_filename(
        'wise.msfd',
        'data/report_2018_def.xml'
    )
    doc = lxml.etree.parse(labels_file)
    elements = doc.find(article).getchildren()

    labels = [
        (x.tag, x.text)

        for x in elements

        if x.attrib.get('skip', 'false') == 'false'
    ]

    if not labels:
        final = [(x, x) for x in fields]

        return final

    diff = set(fields) - set([x.tag for x in elements])
    final = [(x, x) for x in diff]

    final.extend(labels)

    return final
