import lxml.etree
from pkg_resources import resource_filename


def row_to_dict(table, row):
    cols = table.c.keys()
    res = {k: v for k, v in zip(cols, row)}

    return res


class Report2018Def(object):
    """ Parser class for report_2018_def.xml
    """

    def __init__(self):
        labels_file = resource_filename(
            'wise.msfd',
            'data/report_2018_def.xml'
        )
        self.doc = lxml.etree.parse(labels_file)

    def get_article_childrens(self, article):
        node = self.doc.find(article).getchildren()

        return node


REPORT_2018 = Report2018Def()


def get_sorted_fields_2018(fields, article):
    """ field = name from DB
        title = title/label showed in the template

    :param fields: ['Feature', 'GESComponents', 'Element', 'TargetCode', ...]
    :param article: 'Art8'
    :return: [('<fieldname>', <title'), ...
              ('Feature', 'Feature'), ('GESComponents', ''GESComponents),
        ... , ('TargetCode', 'RelatedTargets')]
    """

    elements = REPORT_2018.get_article_childrens(article)

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
