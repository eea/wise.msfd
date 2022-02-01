from __future__ import absolute_import
from z3c.form.browser.select import SelectWidget
from z3c.form.interfaces import NO_VALUE
from z3c.form.widget import FieldWidget


class MarineUnitIDSelectWidget(SelectWidget):
    """ Special marine widget that, if there's no selection already made,
    always returns at least one value from its possible choices.
    """
    prompt = False

    def isSelected(self, term):
        return term.token in self.value

    def extract(self, default=None):
        value = super(MarineUnitIDSelectWidget, self).extract()

        if value is NO_VALUE:
            items = self.items

            if callable(self.items):
                items = list(self.items())

            available = [x['value'] for x in items]

            if available:
                return available[:1]

        return value


def MarineUnitIDSelectFieldWidget(field, source, request=None):

    if request is None:
        real_request = source
    else:
        real_request = request

    return FieldWidget(field, MarineUnitIDSelectWidget(real_request))
