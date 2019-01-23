import logging

from lxml.etree import fromstring

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql
from wise.msfd.data import country_ges_components, get_report_data
from wise.msfd.gescomponents import (get_criterion, get_descriptor,
                                     is_descriptor, sorted_by_criterion)
from wise.msfd.labels import COMMON_LABELS
from wise.msfd.translation import retrieve_translation
from wise.msfd.utils import Item, ItemLabel, ItemList, Node, RawRow

from ..base import BaseArticle2012
from .a9 import Article9
from .utils import to_html

logger = logging.getLogger('wise.msfd')


NSMAP = {"w": "http://water.eionet.europa.eu/schemas/dir200856ec"}


class A10Item(Item):

    def __init__(self, context,
                 criterion, targets_indicators, country_code, region_code,
                 muids):
        super(A10Item, self).__init__([])

        self.context = context
        self.criterion = criterion
        self.targets_indicators = targets_indicators
        self.country_code = country_code
        self.region_code = region_code

        self.targets = []

        # Note: the handling of D1.x indicators is not ideal

        if self.is_descriptor:
            for ti in targets_indicators:
                targets = ti.targets_for_descriptor(self.criterion)
                self.targets.extend(targets)
            print self.targets
        else:
            for ti in targets_indicators:
                targets = ti.targets_for_criterion(self.criterion)
                self.targets.extend(targets)

        pick = self.pick

        attrs = [
            ('GES descriptor, criterion or indicator [GEScomponent]',
             self.ges_component()),
            ('MarineUnitID', muids),
            ('Method used', 'Row not implemented'),
            ('Feature [Target or Indicator code]', self.criterion),
            # ('Feature [Target code]', self.target_code()),
            ('Description [Targets]', self.description()),
            ('Threshold value [TargetValue]', self.threshold_value_a9()),
            ('Reference point type', pick('w:ReferencePointType/text()')),
            ('Baseline', pick('w:Baseline/text()')),
            ('Proportion', pick('w:Proportion/text()')),
            ('AssessmentMethod', pick('w:AssessmentMethod/text()')),
            ('Development status', pick('w:DevelopmentStatus/text()')),
            ('Type of target/indicator', pick('w:Type/text()')),
            ('Timescale', pick('w:TimeScale/text()')),
            ('Interim or GES target', pick('w:InterimGESTarget/text()')),
            ('Compatibility with existing targets/indicators',
             pick('w:CompatibilityExistingTargets/text()')),

        ]

        feature_pressures = self.get_feature_pressures()

        for name in [
                'Physical/chemical features',
                'Predominant habitats',
                'Functional group',
                'Pressures'
        ]:
            labels = [ItemLabel(k, COMMON_LABELS.get(k, k))
                      for k in feature_pressures[name]]
            attrs.append((name, ItemList(labels)))

        for title, value in attrs:
            self[title] = value

    def ges_component(self):
        crit = self.criterion.split('-', 1)[0]      # TODO: get title

        if is_descriptor(crit):
            return get_descriptor(crit).title

        crit = get_criterion(crit)

        if crit is None:
            logger.warning("Criterion not found: %s", self.criterion)

            return ''

        return crit.title

    @property
    def is_descriptor(self):
        return self.criterion.startswith('D')

    @db.use_db_session('2012')
    def _get_ges_description(self):
        # TODO: cache this info
        t = sql.t_MSFD_16a_9Detailed
        count, res = db.get_all_records(
            t.c.DescriptionGES,
            t.c.MemberState == self.country_code,
            t.c.ListOfGES == self.criterion,
        )

        for row in res:
            return row[0]       # there are multiple records, one for each MUID

    def target_code(self):
        # TODO: this needs to be redone, as there are multiple features
        # the problem is that the records should be shown for the descriptor,
        # not for the individual targets

        return self.pick('w:Feature/text()')

    @db.use_db_session('2012')
    def get_feature_pressures(self):
        t = sql.t_MSFD_19b_10PhysicalChemicalFeatures
        target = self.pick('w:Feature/text()')

        count, res = db.get_all_records(
            t,
            t.c.MemberState == self.country_code,
            t.c.Targets == target,
            t.c['Marine region/subregion'] == self.region_code
        )

        cols = t.c.keys()
        recs = [
            {k: v for k, v in zip(cols, row)}

            for row in res
        ]

        _types = {
            'Functional group': set(),
            'Pressures': set(),
            'Predominant habitats': set(),
            'Physical/chemical features': set(),
            'Species group': set(),
            'None': set(),
        }

        for rec in recs:
            t = rec['FeatureType']

            if t is None:
                continue

            s = _types[t]

            if rec['FeaturesPressures'] == 'FunctionalGroupOther':
                s.add('FunctionalGroupOther')
                s.add(rec['OtherExplanation'])
            else:
                s.add(rec['FeaturesPressures'])

        return _types

    def description(self):
        if not self.criterion.startswith('D'):
            return self._get_ges_description()

        for ti in self.targets_indicators:
            for target in ti.targets_for_descriptor(self.criterion):
                desc = target['w:Description/text()']

                if desc:
                    return desc[0]

        return ""

    def threshold_value_a9(self):
        """ Reimplementation of threshold values by looking them up
        in the A9 report view.

        From Article 9 get the table rows. Identify the needed
        Threshold Value by criterion

        :return: empty ItemList instance, or ItemList instance from
        Article 9
        """

        crit = self.criterion

        column = None

        for _c in self.context.article9_cols:
            if _c['GES Component [Reporting feature]'] == crit:
                column = _c

                break

        if column is None:
            return ''

        return column['Threshold value(s)']

    def threshold_value(self):
        values = {}

        for target in self.targets:
            muid = target.marine_unit_id
            values[muid] = target['w:ThresholdValue/text()'][0]

        rows = []
        count, mres = db.get_marine_unit_id_names(values.keys())
        muid_labels = dict(mres)

        for muid in sorted(values.keys()):
            name = u'{} = {}'.format(muid, values[muid])
            title = u'{} = {}'.format(muid_labels[muid], values[muid])

            label = ItemLabel(name, title)
            rows.append(label)

        return ItemList(rows=rows)

    def pick(self, xpath):
        """ For values which are repeated across all targets nodes, try to find
        one with a positive value
        """

        for target in self.targets:
            v = target[xpath]

            if v:
                return to_html(v[0])

        return ''

    def set_pick(self, xpath):
        """ Just like pick, but return all distinct values
        """

        if not self.is_descriptor:
            return ''

        res = []

        for target in self.targets:
            res.extend(target[xpath])

        return set(res) or ''

    def reference_point_type(self):
        # for which MarineUnitID do we show information?

        return self.pick('')


class Target(Node):
    """ Wraps a <Targets> node
    """

    def __init__(self, marine_unit_id, node, nsmap):
        super(Target, self).__init__(node, nsmap)
        self.marine_unit_id = marine_unit_id

    @property
    def descriptor(self):
        for dci in self['w:DesriptorCriterionIndicators/'
                        'w:DesriptorCriterionIndicator/text()']:

            if dci.startswith('D'):
                return dci

            if '.' in dci:      # this returns D1 for D1.x descriptors
                return 'D' + dci.split('.', 1)[0]

    @property
    def criterions(self):
        crits = set(self['w:DesriptorCriterionIndicators/'
                         'w:DesriptorCriterionIndicator/text()'])
        crits = set([x.split('-', 1)[0] for x in crits])

        if self.descriptor:
            crits.add(self.descriptor)

        return list(crits)


class TargetsIndicators(Node):
    """ A <TargetsIndicators> wrapper.

    There is one TargetsIndicators node for each MarineUnitID.
    It has multiple <Targets> nodes, one for each set of "descriptors"
    """

    def __init__(self, node):
        super(TargetsIndicators, self).__init__(node, NSMAP)
        self.id = self['w:MarineUnitID/text()'][0]
        self.targets = [Target(self.id, n, NSMAP)
                        for n in self['w:Targets']]

    def targets_for_descriptor(self, descriptor):
        if descriptor.startswith('D1.'):
            descriptor = 'D1'       # fallback

        return [t for t in self.targets if t.descriptor == descriptor]

    def targets_for_criterion(self, criterion):
        criterion = criterion.split('-', 1)[0]

        return [t for t in self.targets if criterion in t.criterions]


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)

    TODO: we should also extract DescriptorCriterionIndicators from the file

    How do we show data?

    """

    help_text = """
    - we identify the filename for the original XML file, by looking at the
      MSFD10_Imports table. This is the same file that you can find in the
      report table header on this page.

    - we download this file from CDR and parse it.

    - we lookup all the "<DescriptorCriterionIndicator>" tags in the file and
      filter them according to the current descriptor. See

      https://raw.githubusercontent.com/eea/wise.msfd/master/src/wise/msfd/data/ges_terms.csv

      for the hierarchical definition table of descriptors to indicators and
      criterias. To achieve this we do the following:

        - we get the assigned country criterion indicators from the MarineDB
          2012 database (we use the MSFD_19a_10DescriptiorsCriteriaIndicators
          view)

        - we use the first part of the criterion indicator to match the
          available criterion ids for the current descriptor. This is because
          some DescriptorCriterionIndicator are in a format like:
          1.2.1-indicator 5.2B

    - for each of these DescriptorCriterionIndicator we build a column in the
      result table

    Notes, problems:
    ----------------

    - the threshold values are not included in the report XML in
    the form that they appear in the specification. We take them from the 2012
    A9 report, by matching the criterion id.

    - the Functional/Pressures/Habitats rows cannot be matched per criterion,
      as they are in the spreadsheet, neither by using the database MarineDB or
      the XML files. We read the database view
      MSFD_19b_10PhysicalChemicalFeatures where we match the target id, country
      and region and get a list of ids which we split by type (functional
      group, pressure, habitat, etc), but there's no way of matching to the
      criterion.
    """

    template = Template('pt/report-data-a10.pt')

    def get_article9_columns(self):
        """ Get the view for Article 9 2012, which contains the
        table with the data. This is needed because we show
        the Threshold values from article 9

        :return: article 9 view
        """
        ctx = self.context
        art = 'Art9'
        filename = ctx.get_report_filename(art)
        view = Article9(ctx, ctx.request, ctx.country_code,
                        ctx.country_region_code,
                        ctx.descriptor, art, ctx.muids)
        view.setup_data(filename)

        return view.cols

    def filtered_ges_components(self, seed):
        """ Returns a list of valid ges criterion indicator targets

        Can be something like "1.6.2-indicator 5.2B" or "3.1" or "D1"
        """
        descriptor = get_descriptor(self.descriptor)
        country_criterions = country_ges_components(self.country_code)

        res = set([self.descriptor])

        for d_id in descriptor.all_ids():
            if d_id in country_criterions:
                res.add(d_id)

        for crit in set(country_criterions + seed):
            crit_id = crit.split('-', 1)[0]

            if crit_id in descriptor.all_ids():
                res.add(crit)

        return sorted_by_criterion(res)

    def setup_data(self):
        self.article9_cols = self.get_article9_columns()
        filename = self.context.get_report_filename()
        text = get_report_data(filename)

        if not text:
            self.rows = []

            return self.template()

        root = fromstring(text)

        def xp(xpath, node=root):
            return node.xpath(xpath, namespaces=NSMAP)

        muids = xp('//w:MarineUnitID/text()')
        count, res = db.get_marine_unit_id_names(list(set(muids)))

        labels = [ItemLabel(m, u'{} ({})'.format(t, m)) for m, t in res]
        muids = ItemList(labels)

        descriptor = get_descriptor(self.descriptor)
        self.descriptor_label = descriptor.title

        reported = xp("//w:DesriptorCriterionIndicator/text()")
        gcs = self.filtered_ges_components(reported)

        self.rows = []

        # wrap the target per MarineUnitID
        all_target_indicators = [TargetsIndicators(node)
                                 for node in xp('w:TargetsIndicators')]
        self.cols = cols = [A10Item(self,
                                    gc,
                                    all_target_indicators,
                                    self.country_code,
                                    self.region_code,
                                    muids)

                            for gc in gcs]

        # unwrap the columns into rows

        for col in cols:
            for name in col.keys():
                values = []

                for inner in cols:
                    values.append(inner[name])
                values = [self.context.translate_value(name, value=v)
                          for v in values]
                row = RawRow(name, values)
                self.rows.append(row)

            break       # only need the "first" row

    def __call__(self):
        self.setup_data()

        return self.template()

    def auto_translate(self):
        # report_def = REPORT_DEFS[self.year][self.article]
        # translatables = report_def.get_translatable_fields()

        self.setup_data()

        translatables = self.context.TRANSLATABLES
        seen = set()

        for item in self.cols:
            for k in translatables:
                value = item[k]
                if not isinstance(value, basestring):
                    continue

                if value not in seen:
                    retrieve_translation(self.country_code, value)
                    seen.add(value)

        return ''
