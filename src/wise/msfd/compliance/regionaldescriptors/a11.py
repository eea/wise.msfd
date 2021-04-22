
from wise.msfd.utils import national_compoundrow
from ..nationaldescriptors.a11 import Article11


class RegArticle11(Article11):
    is_regional = True

    @property
    def sort_order(self):
        order = ('MemberState', 'MonitoringProgrammeName',
                 'Q4g_SubProgrammeID')

        return order

    def items_to_rows(self, items):
        rep_fields = self.context.get_report_definition()
        country_codes = [
            item['MemberState']
            for item in items
        ]

        for field in rep_fields:
            field_name = field.name
            values = []

            for inner in items:
                values.append(inner[field_name])

            raw_values = []
            vals = []

            for i, v in enumerate(values):
                raw_values.append(v)

                vals.append(self.context.translate_value(
                    field_name, v, country_codes[i]))

            row = national_compoundrow(self.context, field, vals,
                                       raw_values)
            self.rows.append(row)
