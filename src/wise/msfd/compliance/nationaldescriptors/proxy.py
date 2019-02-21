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

    def __init__(self, obj, article, extra=None):
        self.__o = obj       # the proxied object

        self.fields = REPORT_DEFS['2018'][article].get_fields()

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

            label_collection = field.label_collection
            converter = field.converter

            # assert (label_name or converter), 'Field should be dropped'

            if converter:
                assert '.' not in converter
                converter = getattr(convert, converter)
                value = converter(field, value)
            elif label_collection:
                title = GES_LABELS.get(label_collection, value)
                value = ItemLabel(value, title)

            setattr(self, name, value)

    def __getattr__(self, name):
        return getattr(self.__o, name, self.extra.get(name, None))

    def __iter__(self):
        """ Makes the proxy behave like a list of values
        """
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
