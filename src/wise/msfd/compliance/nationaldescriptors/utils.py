# pylint: skip-file
from __future__ import absolute_import
from collections import defaultdict
from itertools import chain
from operator import attrgetter

from Products.Five.browser import BrowserView
from wise.msfd.compliance import convert
from wise.msfd.labels import GES_LABELS
from wise.msfd.utils import (ItemLabel, ItemList, ItemListGroup,
                             LabeledItemList, timeit)


BLACKLIST = (       # used in templates to filter fields
    'CountryCode',
    'ReportingDate',
    'ReportedFileLink',
    'Region',
    'MarineReportingUnit'
)


def proxy_cmp(self, other, ignore_field='MarineReportingUnit'):
    """ Compare two proxy objects but only look at reported value, not MRU

    Could be implemented in Proxy2018, but take care, need to return integers
    """

    return self.hash(ignore_field) == other.hash(ignore_field)

    # fieldnames = [field.name for field in self.fields
    #               if field.name != ignore_field]
    #
    # for name in fieldnames:
    #     a = getattr(self, name)
    #     b = getattr(other, name)
    #
    #     if a != b:
    #         return False
    #
    # return True


def consolidate_date_by_mru(data):
    """ Takes data (proxies of data) organized by mru and groups them according
    to similarity of data (while ignoring the mru of that proxied row)

    This is used by the A9 2018 report.
    """

    groups = []

    # Rows without MRU reported
    # This case applies for Art9, when justification for delay is reported
    rows_without_mru = []

    for obj in chain(*list(data.values())):
        found = False

        for group in groups:
            # compare only with the first object from a group because
            # all objects from a group should contain the same data
            first_from_group = group[0]

            if proxy_cmp(obj, first_from_group):
                group.append(obj)
                found = True

        if not found:
            groups.append([obj])

    # regroup the data by mru, now that we found identical rows
    regroup = defaultdict(list)

    for batch in groups:
        # TODO: get a proper MarineUnitID object
        mrus = tuple(sorted(set([r.MarineReportingUnit for r in batch])))

        if mrus[0] is None:
            rows_without_mru.append(batch[0])

            continue

        regroup[mrus].append(batch[0])

    out = {}

    # rewrite the result keys to list of MRUs

    for mrus, rows in regroup.items():
        mrus_labeled = tuple([
            ItemLabel(row, u'{} ({})'.format(GES_LABELS.get('mrus', row), row))

            for row in mrus
        ])
        label = LabeledItemList(rows=mrus_labeled)

        # TODO how to explain better?
        # Skip rows from rows_without_mru if the GESComponent exists
        # in rows (we do not insert justification delay/non-use
        # if the GESComponent has reported data)
        # example: ges component D6C3, D6C4
        # .../fi/bal/d6/art9/@@view-report-data-2018

        ges_comps_with_data = set(x.GESComponent.id for x in rows)

        for row_extra in rows_without_mru:
            ges_comp = row_extra.GESComponent.id

            if ges_comp in ges_comps_with_data:
                continue

            rows.append(row_extra)

        # rows.extend(rows_without_mru)
        out[label] = rows

    if not regroup and rows_without_mru:
        rows = ItemLabel('No Marine unit ID reported',
                         'No Marine unit ID reported')
        label = LabeledItemList(rows=(rows, ))
        out[label] = rows_without_mru

    return out


@timeit
def consolidate_singlevalue_to_list(proxies, fieldname, order=None):
    """ Given a list of proxies where one of the fields needs to be a list, but
    is spread across different similar proxies, consolidate the single values
    to a list and return only one object for that list of similar objects
    """

    map_ = defaultdict(list)

    for o in proxies:
        map_[o.hash(fieldname)].append(o)

    res = []

    for set_ in map_.values():
        o = set_[0]
        values = [getattr(xo, fieldname) for xo in set_]

        if any(values):
            l = ItemList(rows=values)
            setattr(o, fieldname, l)

        res.append(o)

    # consolidate_singlevalue_to_list is used in regional descriptor too
    # where we do not order the results
    if order:
        res = list(sorted(res, key=attrgetter(*order)))

    return res


@timeit
def group_multiple_fields(proxies, main_fieldname, group_fields, order):
    """ Given a 'main_fieldname', get all unique values from that field and
        split these values into different rows. Also given the 'group_fields'
        we aggregate the data from these fields into a single value and display
        that value for the 'main_fieldname'

        To get a better understanding, check regional descriptors Art11 the
        following rows: features (split into multiple rows), element,
        gescriteria, parameters
    """

    main_field_vals = []
    seen = []

    proxy_hash_map = defaultdict(list)

    # create a map of unique proxies by creating a hash with
    # ignoring the main and the group fields
    for o in proxies:
        __k = o.hash_multi((main_fieldname, ) + group_fields)
        proxy_hash_map[__k].append(o)

    # get all unique main_field values
    for proxy in proxies:
        fvalue = getattr(proxy, main_fieldname)
        name = hasattr(fvalue, 'name') and fvalue.name or fvalue

        if name not in seen:
            seen.append(name)
            main_field_vals.append(fvalue)

    res = []

    # make the grouping of the field values
    for _, proxy_sets in proxy_hash_map.items():
        res_proxy = proxy_sets[0]
        values = defaultdict(lambda: defaultdict(list))

        # iterate over all proxy sets, and group the data
        # into the 'group_fields'
        for proxy in proxy_sets:
            for main_field in main_field_vals:
                name = (hasattr(main_field, 'name') and main_field.name
                        or main_field)

                if getattr(proxy, main_fieldname).name != name:
                    continue

                for gfield in group_fields:
                    v = getattr(proxy, gfield)

                    if isinstance(v, ItemList):
                        v = v.rows
                    else:
                        v = v and [v] or []

                    values[name][gfield].extend(v)

        for _field, vals in values.items():
            unique_vals = []

            for _gfield in group_fields:
                __vals = vals[_gfield]

                if __vals and isinstance(__vals[0], ItemLabel):
                    seen = set()

                    # This works because set.add returns None, so the
                    # expression in the list comprehension always yields obj,
                    # but only if obj.name has not already been added to seen
                    __vals = [
                        seen.add(obj.name) or obj
                        for obj in __vals
                        if obj.name not in seen
                    ]
                else:
                    __vals = sorted(set(__vals))

                unique_vals.append((_gfield, __vals))

            res_proxy.set_value(
                _field, ItemListGroup(unique_vals)
            )

        res.append(res_proxy)

    if order:
        res = list(sorted(res, key=attrgetter(*order)))

    return res, main_field_vals


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
        converter_name = field.converter
        filter_values = field.filter_values
        # separator used to split the value in a field, default is ','
        separator = field.separator

        # assert (label_name or converter), 'Field should be dropped'

        if filter_values:
            ok_values = getattr(self.report_class, filter_values)

            if ok_values:
                values = set(value.split(','))
                filtered = values.intersection(ok_values)
                value = u','.join(filtered)

        if converter_name:
            assert '.' not in converter_name
            converter = getattr(convert, converter_name)

            # special convert method, needs the report_class instance to get
            # additional info like url, article, descriptor, region etc.
            if converter_name.startswith('__'):
                value = converter(
                    field, value, self.report_class
                )
            else:
                if separator:
                    value = converter(
                        field, value, self.report_class.country_code, separator)
                else:
                    value = converter(
                        field, value, self.report_class.country_code)

        elif label_collection:
            title = GES_LABELS.get(label_collection, value)
            value = ItemLabel(value, title)
        setattr(self, fieldname, value)

    def __init__(self, obj, report_class, extra=None):
        self.__o = obj       # the proxied object
        self._hash = {}

        self.report_class = report_class
        self.article = report_class.article
        self.fields = report_class.get_report_definition()

        if not extra:
            extra = {}

        self.extra = extra

        for field in self.fields:
            if field.drop:
                continue

            name = field.name
            value = getattr(self.__o, name, extra.get(name, ''))

            if not value:
                continue

            self.set_value(name, value or '')

    def __getattr__(self, name):
        if name == '__o':
            return self.__o

        # return '' to make the Proxies sortable
        return getattr(self.__o, name, self.extra.get(name, '')) or ''

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
            setattr(obj, k, '')

        obj.__o = []
        obj.extra = {}      # compatibility with __getattr__ from above

        for k, v in kwargs.items():
            setattr(obj, k, v)

        return obj

    def hash(self, ignore=None):
        if ignore not in self._hash:
            keys = sorted([k for k in self.__o.keys() if k != ignore])
            vals = []

            for v in [getattr(self.__o, k) for k in keys]:
                if isinstance(v, list):
                    v = tuple(v)
                vals.append(v)
            self._hash[ignore] = hash(tuple(vals))

        return self._hash[ignore]

    def hash_multi(self, ignore=None):
        """ same as hash, but for multiple ignore fields """

        if ignore not in self._hash:
            keys = sorted([k for k in self.__o.keys() if k not in ignore])
            vals = []

            for v in [getattr(self.__o, k) for k in keys]:
                if isinstance(v, list):
                    v = tuple(v)
                vals.append(v)

            self._hash[ignore] = hash(tuple(vals))

        return self._hash[ignore]


class ViewSavedAssessmentData(BrowserView):
    """ Temporary class for viewing saved assessment data
    """

    def get_saved_assessment_data(self):
        catalog = self.context.portal_catalog

        brains = catalog.searchResults(
            portal_type='wise.msfd.nationaldescriptorassessment',
            path={
                "query": "/Plone/marine/assessment-module"
                         "/national-descriptors-assessments"
            }
        )

        res = []

        for brain in brains:
            obj = brain.getObject()
            if not hasattr(obj, 'saved_assessment_data'):
                continue

            sad = obj.saved_assessment_data

            if not sad:
                continue

            if len(sad) == 1:
                continue

            # import pdb; pdb.set_trace()
            res.append((obj, obj.saved_assessment_data))

        return res

    def fix_assessment_data(self):
        from wise.msfd.compliance.content import AssessmentData

        for obj, data in self.get_saved_assessment_data():
            last = data.last().copy()

            new_data = AssessmentData()
            new_data._append(last)

            obj.saved_assessment_data = new_data

    def __call__(self):
        if 'fix' in self.request.form:
            self.fix_assessment_data()

            return 'Done'

        return self.index()
