from plone.intelligenttext.transforms import \
    convertWebIntelligentPlainTextToHtml


def row_to_dict(table, row):
    cols = table.c.keys()
    res = {k: v for k, v in zip(cols, row)}

    return res


def to_html(text):
    if not text:
        return text

    if len(text.split(' ')) < 10:
        return text

    return convertWebIntelligentPlainTextToHtml(text)
