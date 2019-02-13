import lxml.etree


class ReportDefinition(object):
    """ Parser class for a XML report definition file.

    For 2018, use report_2018_def.xml, for 2012 use report_2012_def.xml
    """

    def __init__(self, fpath, article):
        self.article = article
        self.doc = lxml.etree.parse(fpath)
        self.nodes = self.doc.find(self.article).getchildren()

    def get_elements(self):
        return self.nodes

    def get_group_by_fields(self):
        res = [
            x.get('name')

            for x in self.nodes

            if x.attrib.get('exclude', 'false') == 'true'
        ]

        return res

    def get_translatable_fields(self):
        res = [
            x.get('name')

            for x in self.nodes

            if x.attrib.get('translate', 'false') == 'true'
        ]

        return res


def _get_sorted_fields(reportdef, fields):
    """ field = name from DB
        title = title/label showed in the template

    :param fields: ['Feature', 'GESComponents', 'Element', 'TargetCode', ...]
    :param article: 'Art8'
    :return: [('<fieldname>', <title'), ...
              ('Feature', 'Feature'), ('GESComponents', ''GESComponents),
        ... , ('TargetCode', 'RelatedTargets')]
    """
    elements = reportdef.get_elements()

    labels = [
        (x.get('name'), x.text.strip())

        for x in elements

        if x.attrib.get('skip', 'false') == 'false'
    ]

    if not labels:
        final = [(x, x) for x in fields]

        return final

    diff = set(fields) - set([x.get('name') for x in elements])
    final = [(x, x) for x in diff]

    final.extend(labels)

    return final
