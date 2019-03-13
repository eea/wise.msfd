from wise.msfd.compliance import convert
from wise.msfd.gescomponents import GES_LABELS
from wise.msfd.utils import ItemLabel

from .data import REPORT_DEFS

BLACKLIST = (       # used in templates to filter fields
    'CountryCode',
    'ReportingDate',
    'ReportedFileLink',
    'Region',
    'MarineReportingUnit'
)


class Proxy2018(object):
    """ A proxy wrapper that uses XML definition files to 'translate' elements
    """

    def set_value(self, fieldname, value):
        """ Set the field to a specific value, according to set policies
        """

        field = None

        for f in self.fields:
            if f.name == fieldname:
                field = f

                break

        if not field:
            # field definition was not found, fallback
            setattr(self, fieldname, value)

            return

        label_collection = field.label_collection
        converter = field.converter
        filter_values = field.filter_values

        # assert (label_name or converter), 'Field should be dropped'

        if filter_values:
            ok_values = getattr(self.report_class, filter_values)

            if ok_values:
                values = set(value.split(','))
                filtered = values.intersection(ok_values)
                value = u','.join(filtered)

        if converter:
            assert '.' not in converter
            converter = getattr(convert, converter)
            value = converter(field, value)
        elif label_collection:
            title = GES_LABELS.get(label_collection, value)
            value = ItemLabel(value, title)

        setattr(self, fieldname, value)

    def __init__(self, obj, report_class, extra=None):
        self.__o = obj       # the proxied object

        self.report_class = report_class
        self.article = report_class.article
        self.fields = REPORT_DEFS['2018'][self.article].get_fields()

        if not extra:
            extra = {}

        self.extra = extra

        for field in self.fields:
            if field.drop:
                continue

            name = field.name
            value = getattr(self.__o, name, extra.get(name, None))

            if not value:
                continue

            self.set_value(name, value)

    def __getattr__(self, name):
        return getattr(self.__o, name, self.extra.get(name, None))

    def __iter__(self):
        """ Makes the proxy behave like a list of values
        """
        # TODO: is this needed?
        keys = [k for k in self.__o.keys() if k not in BLACKLIST]
        res = [getattr(self.__o, k) for k in keys]

        return iter(res)      # self.__o

    def clone(self, **kwargs):
        cls = self.__class__
        obj = cls.__new__(cls)

        for k, v in vars(self).items():
            setattr(obj, k, None)

        obj.__o = []
        obj.extra = {}      # compatibility with __getattr__ from above

        for k, v in kwargs.items():
            setattr(obj, k, v)

        return obj


def proxy_cmp(self, other, ignore_field='MarineReportingUnit'):
    """ Compare two proxy objects but only look at reported value, not MRU

    Could be implemented in Proxy2018, but take care, need to return integers
    """

    fieldnames = [field.name for field in self.fields
                  if field.name != ignore_field]

    for name in fieldnames:
        a = getattr(self, name)
        b = getattr(other, name)

        if a != b:
            return False

    return True
