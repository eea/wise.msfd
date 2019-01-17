import datetime
import logging
from collections import OrderedDict, defaultdict, namedtuple
from cPickle import dumps
from hashlib import md5
from inspect import getsource, isclass

from six import string_types
from sqlalchemy import inspect
from zope.component import getUtility
from zope.schema import Choice, List
from zope.schema.interfaces import IVocabularyFactory

from plone.api.portal import get_tool
from plone.intelligenttext.transforms import \
    convertWebIntelligentPlainTextToHtml
from plone.memoize import volatile
from Products.Five.browser.pagetemplatefile import PageTemplateFile

from .labels import COMMON_LABELS

# TODO: move this registration to search package
BLACKLIST = ['ID', 'Import', 'Id']

logger = logging.getLogger('wise.msfd')


def class_id(obj):
    if type(obj) is type:
        klass = obj
    else:
        klass = obj.__class__

    return klass.__name__.lower()


def scan(namespace):
    """ Scans the namespace for modules and imports them, to activate decorator
    """

    import importlib

    name = importlib._resolve_name(namespace, 'wise.msfd.search', 1)
    importlib.import_module(name)


def print_value(value):
    # TODO: this is only used in search package

    if not value:
        return value

    if isinstance(value, string_types):

        if value in COMMON_LABELS:
            tmpl = '<span title="{}">{}</span>'
            try:
                html = convertWebIntelligentPlainTextToHtml(
                    COMMON_LABELS[value]
                )
                ret = tmpl.format(value, html)
            except UnicodeEncodeError as e:
                ret = tmpl.format(value, COMMON_LABELS[value].encode('utf-8'))
            except Exception as e:
                logger.exception("Error print_value: %r", e)
                ret = tmpl.format(value, unicode(COMMON_LABELS[value]))

            return ret

        html = convertWebIntelligentPlainTextToHtml(value)

        return html

    base_values = string_types + (int, datetime.datetime, list)

    if not isinstance(value, base_values):

        # TODO: right now we're not showing complex, table-like values
        # Activate below to show tables
        # return self.value_template(item=value)

        return None
        # return '&lt;hidden&gt;'

    return value


def get_obj_fields(obj, use_blacklist=True, whitelist=None):
    whitelist = whitelist or []
    whitelist = getattr(obj, 'whitelist', whitelist)

    mapper = inspect(obj)

    fields = []
    keys = [c.key for c in mapper.attrs]        # forgo sorted use

    if use_blacklist:
        for key in keys:
            if key in whitelist:
                fields.append(key)

                continue
            flag = False

            for bit in BLACKLIST:
                if bit in key:
                    flag = True

            if not flag:
                fields.append(key)
    else:
        fields = keys

    # this is a hack to return a sorted list of fields, according to the order
    # of their definition. this is default behaviour in python 3.6+, but not in
    # python 2.7. there's no easy way to achieve this without a metaclass, so
    # we'll just hack it.

    res = []
    source = getsource(obj.__class__)

    for line in source.split('\n'):
        split = line.split(' = ')

        if len(split) == 2:
            name, value = split
            name = name.strip()

            if name in fields:
                res.append(name)

    # second strategy, go for the table

    if not res:
        tbl = obj.__table__

        return tbl.c.keys()

    return res


def db_objects_to_dict(data, excluded_columns=()):
    """
    Transform a list of sqlalchemy query objects into
    a list of dictionaries, needed for pivot_data()

    :param data: list of sqlalchemy query objects
    :return: list of dictionaries
    """
    out = []

    for row in data:
        columns = row.__table__.columns.keys()
        d = OrderedDict()

        for col in columns:
            # import pdb; pdb.set_trace()

            if col not in excluded_columns:
                d.update({col: getattr(row, col)})
        out.append(d)

    return out


def group_data(data, pivot):
    out = defaultdict(list)

    count_distinct_values = len(set(row.get(pivot, '') for row in data))

    for row in data:
        d = OrderedDict(row)
        p = d.pop(pivot) if count_distinct_values > 1 else d[pivot]

        if any(d.values()):
            out[p].append(d)

    return out


def group_query(query, pivot):
    """ Group results from a query over a table
    """

    cols = [x['name'] for x in query.column_descriptions]
    res = [dict(zip(cols, row)) for row in query]

    if len(cols) == 1:
        return {pivot: res}

    return group_data(res, pivot)


def default_value_from_field(context, field):
    """ Get the defaulf value for a choice field
    """

    if field.field.default:
        return field.field.default
    parent = context.context
    vocab = field.field.vocabulary

    if not vocab:
        name = field.field.vocabularyName
        vocab = getUtility(IVocabularyFactory, name=name)(parent)

    if not vocab._terms:
        return

    term = vocab._terms[0]

    # TODO: should we always return term.value?

    if isclass(term.value):
        return term.value

    return term.token


def all_values_from_field(context, field):
    if isinstance(field.field, Choice):
        return default_value_from_field(context, field)

    if not isinstance(field.field, List):
        # TODO: do we use other types of fields?

        return None

    # we use the parent for the vocabulary because parents usually have the
    # values that we want to filter in the current vocabulary

    parent = context.context

    vocab = field.field.value_type.vocabulary

    if not vocab:
        name = field.field.value_type.vocabularyName
        vocab = getUtility(IVocabularyFactory, name=name)(parent)

    return [term.token for term in vocab._terms]


def request_cache_key(func, self):
    form = sorted(self.request.form.items())
    bits = self.__class__.__name__ + dumps(form)
    key = md5(bits).hexdigest()

    return key


def db_result_key(func, *argss, **kwargs):
    if kwargs.get('raw', False):
        raise volatile.DontCache

    keys = [func.__name__]

    for arg in argss:
        if hasattr(arg, '__name__'):
            arg_key = arg.__name__
        elif hasattr(arg, 'compile'):
            arg_key = repr(arg.compile(compile_kwargs={"literal_binds": True}))
        else:
            arg_key = arg.__str__()

        keys.append(arg_key)

    bits = dumps(keys)

    key = md5(bits).hexdigest()

    return key


# To be used as data container when defining tabs for navigation
Tab = namedtuple('Tab', ['view', 'section', 'title', 'subtitle'])


def t2rt(text):
    """ Transform text to richtext using inteligent-text transform
    """

    portal_transforms = get_tool(name='portal_transforms')

    # Output here is a single <p> which contains <br /> for newline
    data = portal_transforms.convertTo('text/html',
                                       text,
                                       mimetype='text/x-web-intelligent')
    text = data.getData().strip()

    return text


class TemplateMixin:
    """ Reusable base class for reusable mini-template renderers
    """

    template = None

    def __call__(self):
        return self.template(**self.__dict__)


class ItemLabel(TemplateMixin):
    """ Render a <span title='...'>Bla</span> for a Label

    Also serves as a container (tuple) for name/title pairs
    """

    def __init__(self, name, title):
        self.name = name.strip()            # 'database short code', an id
        self.title = title.strip()          # human readable label

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
        # return "<ItemLabel '%s'>" % self.name

    def __cmp__(self, other):

        if hasattr(other, 'name'):
            return cmp(self.name, other.name)

        return cmp(self.name, other)        # this is not really ok

    def __hash__(self):
        return id(self)     # wonky but should work

    template = PageTemplateFile('pt/label.pt')


class ItemList(TemplateMixin):
    """ Render a python list of ItemLabels as an HTML list
    """

    template = PageTemplateFile('pt/list.pt')

    def __init__(self, rows):
        self.rows = sorted(rows, key=lambda r: r.title)

    def __repr__(self):
        v = ', '.join(map(unicode, self.rows))

        return v
        # return "<ItemList of %s children>" % len(self.rows)


class CompoundRow(TemplateMixin):
    multi_row = PageTemplateFile('pt/compound-row.pt')
    one_row = PageTemplateFile('pt/compound-one-row.pt')

    @property
    def template(self):
        if self.rowspan > 1:
            return self.multi_row

        return self.one_row

    def __init__(self, title, rows):
        self.title = title
        self.rows = rows
        self.rowspan = len(rows)


class Row(TemplateMixin):
    template = PageTemplateFile('pt/simple-row.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class RawRow(TemplateMixin):
    template = PageTemplateFile('pt/row.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class TableHeader(TemplateMixin):
    template = PageTemplateFile('pt/table-header.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class Item(OrderedDict):
    """ A generic data container for "columns"

    It is used in the 2012 report data tables.
    """


class Node(object):
    """ A wrapper over the lxml etree to simplify syntax
    """

    def __init__(self, node, nsmap):
        self.node = node
        self.namespaces = nsmap

    def __nonzero__(self):
        # make sure assertions over nodes always "detect" node

        return True

    def __getitem__(self, name):
        # flag = []
        #
        # for k in self.namespaces:
        #     s = "{}:".format(k)
        #
        #     if name.startswith(s):
        #         flag.append(True)
        #
        # # this is just a reminder for devel
        # assert True in flag, "Please remember to use the namespace aliases"

        # TODO: this used to be find(), now it's xpath. Check compatibility

        return self.node.xpath(name, namespaces=self.namespaces)

    def relax(self):
        return RelaxedNode(self.node)


class Empty(object):
    """ A "node" with empty text
    """

    @property
    def text(self):
        return ''


class RelaxedNode(Node):
    """ A "relaxed" version of the node getter.

    It never returns None from searches
    """

    def __getitem__(self, name):
        n = super(RelaxedNode, self).__getitem__(name)

        if n is None:
            return Empty()

        return n


def change_orientation(data, sorted_fields):
    """ From a set of results, create labeled list of rows

    :param data: a list of sql table rows results
    :param sorted_fields: a list of tuples (fieldname, label)

    Given a query result (a list of rows), it will return list of tuples like:

    (
        ("Features", "Features [GESComponent"),
        [v1, v2, v3, ...]
    )
    """

    res = []

    for fname, label in sorted_fields:
        values = [
            getattr(row, fname)
            # make_distinct(fname, getattr(row, fname))

            for row in data
        ]

        res.append([(fname, label), values])

    return res


def consolidate_data(data, group_by_fields):
    """ Reduce number of rows in data, by omitting rows with identical values

    TODO: explain why this is needed
    """

    if not data:
        return {}

    res = defaultdict(list)

    # Ignore the following fields when hashing the rows

    fieldnames = data[0]._fields
    indexes = [fieldnames.index(f) for f in group_by_fields]

    seen = []

    for row in data:
        # omitting the ignored fields, make a hash to identify duplicate rows

        hash = tuple([v
                      for (i, v) in enumerate(row)

                      if i not in indexes])

        if hash in seen:
            continue

        seen.append(hash)

        if not row.MarineReportingUnit:     # skip rows without muid
            continue

        res[row.MarineReportingUnit].append(row)

    return res
