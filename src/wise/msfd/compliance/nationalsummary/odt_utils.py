from collections import defaultdict
import datetime

from lpod.heading import odf_create_heading
from lpod.paragraph import odf_create_paragraph
from lpod.style import (make_table_cell_border_string, odf_create_style,
                        odf_create_table_cell_style)
from lpod.table import odf_create_table, odf_create_row, odf_create_cell


COLORS = {
    0: (255, 255, 255),  # not relevant
    1: (177, 197, 135),  # very good
    2: (212, 223, 188),  # good
    4: (255, 174, 174),  # poor
    5: (253, 120, 120),  # very poor
    3: (221, 221, 221)   # not reported
}

TABLE_CELL_BASE = 'table_cell_base'
TABLE_CELL_AS_VALUE = 'table_cell_as_value_'
DOCUMENT_TITLE = 'document_title'

STYLES = defaultdict(object)


def setup_document_styles(document):
    """ Setup all styles used in the document, after the setup
    the style can be used by its 'name' as X.set_style(stylename)

    example: cell.set_style(STYLE[TABLE_CELL_BASE])
    """

    doc_title_style = odf_create_style('paragraph', size='18', bold=True)
    STYLES[DOCUMENT_TITLE] = document.insert_style(style=doc_title_style,
                                                   default=True)

    # Setup base cell style
    border = make_table_cell_border_string(
        thick='0.03cm', color='black'
    )
    style = {
        'color': 'black',
        'background_color': (255, 255, 255),
        'border_right': border,
        'border_left': border,
        'border_bottom': border,
        'border_top': border
    }

    base_style = odf_create_table_cell_style(**style)
    STYLES[TABLE_CELL_BASE] = document.insert_style(
        style=base_style, automatic=True
    )

    # Setup colored cell styles (based on score)
    for color_val, color_rgb in COLORS.items():
        style['background_color'] = color_rgb

        _style = odf_create_table_cell_style(**style)
        _stylename = "{}{}".format(TABLE_CELL_AS_VALUE, color_val)
        STYLES[_stylename] = document.insert_style(
            style=_style,
            automatic=True
        )


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

    # Insert headers and apply base cell style to the cells
    if headers:
        odt_row = odf_create_row()
        odt_row.set_values(headers)

        for cell in odt_row.traverse():
            cell.set_style(STYLES[TABLE_CELL_BASE])
            odt_row.set_cell(x=cell.x, cell=cell)

        table.set_row(0, odt_row)

    for indx, row in enumerate(data):
        odt_row = odf_create_row()

        values = []
        for val in row:
            if not val:
                values.append(u"")

            if isinstance(val, (basestring, unicode, int, float)):
                values.append(val)

            # In assessment summary table score is a tuple (conclusion, color)
            if isinstance(val, tuple):
                values.append(val[0])

        odt_row.set_values(values)

        # Color the cell, based on the score
        for j, cell in enumerate(odt_row.traverse()):
            # first column from row gets base cell style
            if j == 0:
                cell.set_style(STYLES[TABLE_CELL_BASE])
                odt_row.set_cell(x=cell.x, cell=cell)
                continue

            color_val = row[j][1]
            colored_style = "{}{}".format(TABLE_CELL_AS_VALUE, color_val)
            # other rows need too be colored
            cell.set_style(STYLES[colored_style])
            odt_row.set_cell(x=cell.x, cell=cell)

        table.set_row(indx + 1, odt_row)

    # apply_table_cell_base_style(document, table)

    return table


def create_table_descr(document, article_data):

    def set_table_cell_style(_row, color_val):
        for indx, cell in enumerate(_row.traverse()):
            if indx == 0:
                cell.set_style(STYLES[TABLE_CELL_BASE])
            else:
                colored_style = "{}{}".format(
                    TABLE_CELL_AS_VALUE, color_val
                )
                cell.set_style(STYLES[colored_style])

            _row.set_cell(x=cell.x, cell=cell)

    table = odf_create_table(u"Table")

    row = odf_create_row()
    row.set_values([
        u"Assessment summary: {}".format(
            article_data.assessment_summary or '-'
        ),
        u"Adequacy: {}".format(article_data.adequacy[0])
    ])
    set_table_cell_style(row, article_data.adequacy[1])
    table.set_row(0, row)

    row = odf_create_row()
    row.set_values([
        u"",
        u"Consistency: {}".format(article_data.consistency[0])
    ])
    set_table_cell_style(row, article_data.consistency[1])
    table.set_row(1, row)

    row = odf_create_row()
    row.set_values([
        u"Progress assessment: {}".format(
            article_data.progress_assessment or '-'
        ),
        u"Coherence: {}".format(article_data.coherence[0])
    ])
    set_table_cell_style(row, article_data.coherence[1])
    table.set_row(2, row)

    row = odf_create_row()
    row.set_values([
        u"",
        u"Overall score 2018: {}".format(article_data.overall_score_2018[0])
    ])
    set_table_cell_style(row, article_data.overall_score_2018[1])
    table.set_row(3, row)

    row = odf_create_row()
    row.set_values([
        u"Recommendations: {}".format(article_data.recommendations or '-'),
        u"Overall score 2012: {}".format(article_data.overall_score_2012[0])
    ])
    set_table_cell_style(row, article_data.overall_score_2012[1])
    table.set_row(4, row)

    row = odf_create_row()
    row.set_values([
        u"",
        u"Change since 2012: {}".format(article_data.change_since_2012)
    ])
    set_table_cell_style(row, 0)
    table.set_row(5, row)

    table.set_span((0, 0, 0, 1))
    table.set_span((0, 2, 0, 3))
    table.set_span((0, 4, 0, 5))

    # apply_table_cell_base_style(document, table)
    # apply_descriptors_table_style(document, table)

    return table


def create_paragraph(text, style=None):

    return odf_create_paragraph(text, style=style)


def create_heading(level, text, style=None):
    text = u" {}".format(text)

    return odf_create_heading(level, text)


def apply_table_cell_base_style(document, table):
    # apply basic styling to table

    all_rows = table.get_rows()
    for row in all_rows:
        for cell in row.traverse():
            cell.set_style(STYLES[TABLE_CELL_BASE])
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
