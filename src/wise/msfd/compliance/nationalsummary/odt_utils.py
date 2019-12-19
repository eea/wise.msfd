import datetime

from lpod.heading import odf_create_heading
from lpod.paragraph import odf_create_paragraph
from lpod.style import (make_table_cell_border_string, odf_create_style,
                        odf_create_table_cell_style)
from lpod.table import odf_create_table, odf_create_row, odf_create_cell


def create_table(document, data, headers=None, style=None):
    table = odf_create_table(u"Table")

    if headers:
        odt_row = odf_create_row()
        odt_row.set_values(headers)
        table.set_row(0, odt_row)

    for indx, row in enumerate(data):
        odt_row = odf_create_row()

        values = []
        for val in row:
            if not val:
                values.append(u"")
                continue

            if isinstance(val, (datetime.date, datetime.datetime)):
                values.append(val.strftime('%Y %b %d'))
                continue

            if isinstance(val, (basestring, unicode, int, float)):
                values.append(val)
                continue

            # In assessment summary table score is a tuple (conclusion, color)
            if isinstance(val, tuple):
                values.append(val[0])
                continue

            # ItemList type
            values.append(', '.join(val.rows))

        odt_row.set_values(values)
        table.set_row(indx + 1, odt_row)

    apply_table_cell_base_style(document, table)

    return table


def create_table_summary(document, data, headers=None, style=None):
    table = odf_create_table(u"Table")

    if headers:
        odt_row = odf_create_row()
        odt_row.set_values(headers)
        table.set_row(0, odt_row)

    for indx, row in enumerate(data):
        odt_row = odf_create_row()

        values = []
        for val in row:
            if not val:
                values.append(u"")
                continue

            if isinstance(val, (datetime.date, datetime.datetime)):
                values.append(val.strftime('%Y %b %d'))
                continue

            if isinstance(val, (basestring, unicode, int, float)):
                values.append(val)
                continue

            # In assessment summary table score is a tuple (conclusion, color)
            if isinstance(val, tuple):
                values.append(val[0])
                continue

            # ItemList type
            values.append(', '.join(val.rows))

        odt_row.set_values(values)
        table.set_row(indx + 1, odt_row)

    apply_table_cell_base_style(document, table)

    return table


def create_table_descr(document, article_data):
    table = odf_create_table(u"Table")

    row = odf_create_row()
    row.set_values([
        article_data.assessment_summary,
        "Adequacy: {}".format(article_data.adequacy[0])
    ])
    table.set_row(0, row)

    row = odf_create_row()
    row.set_values([
        u"",
        "Consistency: {}".format(article_data.consistency[0])
    ])
    table.set_row(1, row)

    row = odf_create_row()
    row.set_values([
        article_data.progress_assessment,
        "Coherence: {}".format(article_data.coherence[0])
    ])
    table.set_row(2, row)

    row = odf_create_row()
    row.set_values([
        u"",
        "Overall score 2018: {}".format(article_data.overall_score_2018[0])
    ])
    table.set_row(3, row)

    row = odf_create_row()
    row.set_values([
        article_data.recommendations,
        "Overall score 2012: {}".format(article_data.overall_score_2012[0])
    ])
    table.set_row(4, row)

    row = odf_create_row()
    row.set_values([
        article_data.recommendations,
        "Change since 2012: {}".format(article_data.change_since_2012)
    ])
    table.set_row(5, row)

    table.set_span((0, 0, 0, 1))
    table.set_span((0, 2, 0, 3))
    table.set_span((0, 4, 0, 5))

    apply_table_cell_base_style(document, table)
    apply_descriptors_table_style(document, table)

    return table


def create_paragraph(text, style=None):

    return odf_create_paragraph(text)


def create_heading(level, text, style=None):
    text = u" {}".format(text)

    return odf_create_heading(level, text)


def apply_table_cell_base_style(document, table):
    # apply basic styling to table

    border = make_table_cell_border_string(thick='0.03cm', color='black')
    table_cell_base_style = odf_create_table_cell_style(
        color='black',
        border_right=border,
        border_left=border,
        border_bottom=border,
        border_top=border,
    )
    style = document.insert_style(style=table_cell_base_style, automatic=True)

    all_rows = table.get_rows()
    for row in all_rows:
        for cell in row.traverse():
            cell.set_style(style)
            row.set_cell(x=cell.x, cell=cell)
        table.set_row(row.y, row)


def apply_descriptors_table_style(document, table):
    # adjust last column width
    col_style = odf_create_style('table-column', width='3cm')
    style = document.insert_style(style=col_style, automatic=True)

    columns = table.get_columns()

    for indx, column in enumerate(columns):
        if indx != len(columns) - 1:
            continue

        column.set_style(col_style)
        table.set_column(column.x, column)
