import datetime
import logging
import os
import re
import time
from collections import OrderedDict, defaultdict, namedtuple
from cPickle import dumps
from hashlib import md5
from inspect import getsource, isclass

from pkg_resources import resource_filename
from six import string_types
from sqlalchemy import inspect
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.schema import Choice, List
from zope.schema.interfaces import IVocabularyFactory

from plone.api.portal import get_tool, getSite
from plone.intelligenttext.transforms import \
    convertWebIntelligentPlainTextToHtml
from plone.memoize import volatile
from Products.Five.browser.pagetemplatefile import (PageTemplateFile,
                                                    ViewPageTemplateFile)


# TODO: move this registration to search package
BLACKLIST = ['ID', 'Import', 'Id']

logger = logging.getLogger('wise.msfd')

WEIGHTS_ANNOT_KEY = 'wise.msfd.weights'


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


def __setup_common_labels():
    from .labels import COMMON_LABELS, GES_LABELS

    common_labels = {}
    common_labels.update(COMMON_LABELS)
    common_labels.update(getattr(GES_LABELS, 'indicators'))
    common_labels.update(getattr(GES_LABELS, 'targets'))
    common_labels.update(getattr(GES_LABELS, 'mrus'))
    common_labels.update(getattr(GES_LABELS, 'ktms'))

    return common_labels


def print_value(value):
    # TODO: this is only used in search package

    common_labels = __setup_common_labels()

    if not value:
        return value

    if isinstance(value, string_types):
        value = value.strip()

        if value in common_labels:
            tmpl = '<span title="{}">{}</span>'
            try:
                html = convertWebIntelligentPlainTextToHtml(
                    common_labels[value]
                )
                ret = tmpl.format(value, html)
            except UnicodeEncodeError as e:
                try:
                    ret = tmpl.format(value,
                                      common_labels[value].encode('utf-8'))
                except UnicodeEncodeError as e:
                    ret = tmpl.format(value.encode('utf-8'),
                                      common_labels[value].encode('utf-8'))
            except Exception as e:
                logger.exception("Error print_value: %r", e)
                ret = tmpl.format(value, unicode(common_labels[value]))

            return ret

        html = convertWebIntelligentPlainTextToHtml(value)

        return html

    if isinstance(value, ItemList):
        return value()

    base_values = string_types + (int, float, datetime.datetime, list)

    if not isinstance(value, base_values):

        # TODO: right now we're not showing complex, table-like values
        # Activate below to show tables
        # return self.value_template(item=value)

        return None
        # return '&lt;hidden&gt;'

    return value


def print_value_xls(value, fieldname):
    # TODO: this is only used in search package

    if fieldname in TRANSFORMS:
        transformer = TRANSFORMS.get(fieldname)

        return transformer(value)

    common_labels = __setup_common_labels()

    if not value:
        return value

    if isinstance(value, string_types):
        value = value.strip()

        if value in common_labels:
            tmpl = u'{}'
            try:
                html = common_labels[value]
                ret = tmpl.format(html)
            except UnicodeEncodeError as e:
                ret = tmpl.format(common_labels[value].encode('utf-8'))
            except Exception as e:
                logger.exception("Error print_value_xls: %r", e)
                ret = tmpl.format(common_labels[value].decode('utf-8'))

            return ret

        return value

    if isinstance(value, ItemList):
        return value()

    base_values = string_types + (int, float, datetime.datetime, list)

    if not isinstance(value, base_values):
        return None

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
        if hasattr(row, '__table__'):
            columns = row.__table__.columns.keys()
        else:
            columns = row._fields

        d = OrderedDict()

        for col in columns:
            if col not in excluded_columns:
                d.update({col: getattr(row, col)})
        out.append(d)

    return out


def change_orientation(data):
    """ Change the orientation of data, from rows to columns
    """
    out = []
    max = 0

    for row in data:
        nr_of_keys = len(row.keys())

        if nr_of_keys > max:
            max = nr_of_keys
            fields = row.keys()

    for field in fields:
        field_data = []

        for row in data:
            field_data.append(row.get(field, ''))

        out.append((field, field_data))

    return out


def group_data(data, pivot, remove_pivot=True):
    out = defaultdict(list)

    # count_distinct_values = len(set(row.get(pivot, '') for row in data))

    for row in data:
        d = OrderedDict(row)

        # Remove the pivot column from the rows, so it will not be showed
        # In some edge cases (Art10 2018) we don't want to remove the pivot

        if remove_pivot:
            p = d.pop(pivot)  # if count_distinct_values > 1 else d[pivot]
        else:
            p = d.get(pivot)

        if any(d.values()):
            out[p].append(d)

    return out


def group_query(query, pivot, remove_pivot=True):
    """ Group results from a query over a table
    """

    cols = [x['name'] for x in query.column_descriptions]
    res = [dict(zip(cols, row)) for row in query]

    if len(cols) == 1:
        return {pivot: res}

    return group_data(res, pivot, remove_pivot)


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

    keys = [current_date(), func.__name__]

    for arg in argss:
        if hasattr(arg, '__name__'):
            arg_key = arg.__name__
        elif hasattr(arg, 'compile'):
            if hasattr(arg, 'fullname'):  # meaning its a table
                arg_key = arg.fullname
            else:
                arg_key = str(
                    arg.compile(compile_kwargs={"literal_binds": True})
                )

        else:
            arg_key = arg.__str__()

        keys.append(arg_key)

    bits = dumps(keys)
    key = md5(bits).hexdigest()

    return key


# To be used as data container when defining tabs for navigation
Tab = namedtuple('Tab', [
    'path',
    'section',
    'title',
    'subtitle',
    'description',
    'cssclass',
    'condition',
])


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


def _parse_files_in_location(location, check_filename, parser):
    dirpath = resource_filename('wise.msfd', location)
    out = {}

    for fname in os.listdir(dirpath):
        if check_filename(fname):
            fpath = os.path.join(dirpath, fname)
            logger.info("Parsing file: %s", fname)
            try:
                res = parser(fpath)
            except:
                logger.exception('Could not parse file: %s', fpath)

                continue

            if res:
                desc, elements = res
                out[desc] = elements

    return out


def get_element_by_id(root, id):
    if id.startswith('#'):
        id = id[1:]

    el = root.xpath('//*[@id = "' + id + '"]')[0]

    return el


class TemplateMixin:
    """ Reusable base class for reusable mini-template renderers
    """

    template = None

    def __call__(self):
        # sometimes the values come from properties, so we need a way to map
        # them

        if hasattr(self, "template_vars"):
            values = self.template_vars
        else:
            values = self.__dict__

        return self.template(**values)


class NationalCompoundRow(TemplateMixin):
    template = ViewPageTemplateFile('pt/national-compound-row.pt')

    def __init__(self, context, request, field, vals, raw_values):
        self.context = context
        self.request = request
        self.field = field
        self.title = field.title
        self.vals = vals
        self.raw_values = raw_values


def national_compoundrow(self, field, vals, raw_values):
    # FIELD = namedtuple("Field", ["group_name", "name", "title"])
    # field = FIELD(title, title, title)

    return NationalCompoundRow(self, self.request, field, vals, raw_values)


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

    def __cmp__(self, other):
        # see https://rszalski.github.io/magicmethods/

        if hasattr(other, 'name'):
            return cmp(self.name, other.name)

        if self.name == other:        # this is not really ok
            return 0

        return -1

    def __hash__(self):
        return id(self)     # wonky but should work

    def __call__(self):
        # sometimes the values come from properties, so we need a way to map
        # them

        if hasattr(self, "template_vars"):
            values = self.template_vars
        else:
            values = self.__dict__

        out = {}

        for k, v in values.items():
            if isinstance(v, unicode):
                pass
            elif v is None:
                v = u''
            elif isinstance(v, str):
                v = v.decode('utf-8')
            else:
                v = repr(v).decode('utf-8')     # support ItemLabels

            out[k] = v

        return self.template(**out)

    template = PageTemplateFile('pt/label.pt')


class ItemList(TemplateMixin):
    """ Render a python list of ItemLabels as an HTML list
    """

    template = PageTemplateFile('pt/list.pt')

    def __init__(self, rows, sort=True):
        rows = list(rows)

        # the rows may be ItemLabel instances

        if sort and rows and (not isinstance(rows[0], basestring)):
            self.rows = sorted(rows,
                               key=lambda r: (r is not None) and r.title or '')
        elif sort:
            self.rows = sorted(rows)
        else:
            self.rows = rows

    def __repr__(self):
        v = ', '.join(map(unicode, self.rows))

        return v
        # return "<ItemList of %s children>" % len(self.rows)

    def __cmp__(self, other):

        if len(self.rows) != len(other.rows):
            return -1

        for v1, v2 in zip(self.rows, other.rows):
            if v1 != v2:
                return -1

        return 0

    def __hash__(self):
        # this is needed to be able to set a list of marineunitids as group
        # for Art9 2018

        return id(self)     # wonky but should work


class ItemListFiltered(ItemList):
    """ Filter out empty values """

    def __init__(self, rows, sort=True):
        ItemList.__init__(self, rows, sort)

        _rows = [x.replace('\n', '').replace('\t', '') for x in self.rows]
        _rows = [x for x in _rows if x]
        self.rows = _rows


class LabeledItemList(ItemList):
    """ List that renders using <div> instead of <ul>
    """
    template = PageTemplateFile('pt/labeled-list.pt')

    def __init__(self, rows):
        self.rows = rows

    def __call__(self):

        return self.template(rows=self.rows)


class ItemListGroup(LabeledItemList):
    template = PageTemplateFile('pt/grouped-list.pt')


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
        self.raw_values = values


class RawRow(TemplateMixin):
    template = PageTemplateFile('pt/row.pt')

    def __init__(self, title, values, raw_values=None):
        self.title = title
        self.cells = values
        self.raw_values = raw_values


class TableHeader(TemplateMixin):
    template = PageTemplateFile('pt/table-header.pt')

    def __init__(self, title, values):
        self.title = title
        self.cells = values


class SimpleTable(TemplateMixin):
    template = PageTemplateFile('pt/table.pt')

    def __init__(self, title, values):
        self.title = title
        self.item_labels = []

        for row in values:
            self.item_labels = row.keys()

            break

        self.item_values = values


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


class RelaxedNodeEmpty(RelaxedNode):
    """ If no results, return empty list instead of empty string
    """

    def __getitem__(self, name):
        val = super(RelaxedNodeEmpty, self).__getitem__(name)

        if not val:
            return ['']

        return val


def current_date():
    """ Return the current date as string, included in cache keys
    """

    return datetime.datetime.now().date().isoformat()


def items_to_rows(data, fields):
    """ From a set of results, create labeled list of rows

    :param data: a list of sql table rows results
    :param fields: a list of ``ReportField`` objects

    Given a query result (a list of rows), it will return list of tuples like:

    (
        ("Features", "Features [GESComponent"),
        [v1, v2, v3, ...]
    )
    """

    res = []

    for field in fields:        # this guarantees sorting of data
        if field.drop:
            continue

        values = [
            getattr(row, field.name)

            for row in data     # make_distinct(fname, getattr(row, fname))
        ]

        res.append([field, values])

    return res


def to_html(text):
    if not text:
        return text

    if len(text.split(' ')) < 10:
        return text

    return convertWebIntelligentPlainTextToHtml(text)


def row_to_dict(table, row):
    # TODO: couldn't we use row.keys(), so that we don't need table?
    cols = table.c.keys()
    res = {k: v for k, v in zip(cols, row)}

    return res


def timeit(func):
    """ A decorator to log time spend in a function

    Use it as @timeit
    """
    func_name = "{}.{}".format(func.__module__, func.__name__)

    def wrapped(*args, **kw):
        ts = time.time()
        res = func(*args, **kw)
        te = time.time()

        logger.info("%r %2.2f ms" % (func_name, (te - ts) * 1000))

        return res

    return wrapped


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """ Natural sorting key, used for alphanumeric sorting

    usage: sorted(list, key=natural_sort_key)
    """

    return [text.isdigit() and int(text) or text.lower()
            for text in _nsre.split(s)]


def fixedorder_sortkey(value, order):
    """ Used to sort a list by a specific order of values
    If the value is not in the order list, it will be added to the end of
    the list

    :param value: 'Not good'
    :param order: ['Good', 'Not good', 'Unknown', 'not reported']
    :return: index on the value from the order list
    """

    key = value in order and order.index(value) + 1 or len(order) + 2

    return key


def get_annot():
    site = getSite()
    annot = IAnnotations(site, {})

    return annot


def get_weight_from_annot(q_id, descr):
    annot = get_annot()
    aw = annot.get(WEIGHTS_ANNOT_KEY, {})

    try:
        x = aw[str(q_id)].get(descr, '')
    except:
        x = ''

    return x


def area_transform(value):
    new_val = "{:.2f}".format(value)

    return new_val


def mrus_transform(value):
    from .labels import GES_LABELS

    mru_labels = getattr(GES_LABELS, 'mrus')
    label = mru_labels.get(value, 'No name available')
    template = u"{} ({})".format(label, value)

    return template


TRANSFORMS = {
    'Area': area_transform,
    'Marine Unit(s)': mrus_transform,
    'MarineUnitID': mrus_transform,
    'MarineReportingUnit': mrus_transform
}
