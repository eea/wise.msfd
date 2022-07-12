from __future__ import absolute_import
import csv
import logging
import re
from collections import namedtuple
from eea.cache import cache
from sqlalchemy import desc, or_

from pkg_resources import resource_filename
from plone.api.portal import get_tool

from AccessControl import Unauthorized
from persistent.list import PersistentList
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
# from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from chameleon.zpt.template import PageTemplateFile

from wise.msfd import db, sql2018
from wise.msfd.compliance.content import AssessmentData
from wise.msfd.compliance.interfaces import (
    ICountryDescriptorsFolder, IDescriptorFolder, IEditAssessorsForm,
    INationalDescriptorAssessment, INationalDescriptorsFolder,
    INationalRegionDescriptorFolder, IRegionalDescriptorAssessment,
    IRegionalDescriptorRegionsFolder, IRegionalDescriptorsFolder
)
from wise.msfd.compliance.regionaldescriptors.base import BaseRegComplianceView
from wise.msfd.compliance.scoring import (CONCLUSIONS, get_range_index, 
                                          OverallScores)
from wise.msfd.compliance.utils import (get_assessors, set_assessors,
                                        ordered_regions_sortkey)
from wise.msfd.compliance.vocabulary import (REGIONAL_DESCRIPTORS_REGIONS,
                                             SUBREGIONS_TO_REGIONS)
from wise.msfd.gescomponents import get_descriptor  # get_descriptor_elements
from wise.msfd.utils import fixedorder_sortkey, t2rt, timeit

from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from zope.schema import Text

from .base import BaseComplianceView

logger = logging.getLogger('wise.msfd')


REGION_RE = re.compile('.+\s\((?P<region>.+)\)$')

ARTICLE_WEIGHTS = {
    'Art9': {
        'adequacy': 0.6,
        'consistency': 0.0,
        'coherence': 0.4
    },
    'Art8': {
        'adequacy': 0.6,
        'consistency': 0.2,
        'coherence': 0.2
    },
    'Art10': {
        'adequacy': 0.6,
        'consistency': 0.2,
        'coherence': 0.2
    },
    'Art3': {
        'adequacy': 1.0,
        'consistency': 1.0,
        'coherence': 1.0
    },
    'Art4': {
        'adequacy': 1.0,
        'consistency': 1.0,
        'coherence': 1.0
    },
    'Art7': {
        'adequacy': 1.0,
        'consistency': 0,
        'coherence': 0
    },
    'Art8esa': {
        'adequacy': 1.0,
        'consistency': 0,
        'coherence': 0
    },
    'Art8ESA': {
        'adequacy': 1.0,
        'consistency': 0,
        'coherence': 0
    },
    'Art11': {
        'adequacy': 1.0,
        'consistency': 0,
        'coherence': 0
    }
}

DESCRIPTOR_SUMMARY = namedtuple(
    'DescriptorSummary',
    ['assessment_summary', 'progress_assessment', 'recommendations',
     'adequacy', 'consistency', 'coherence', 'overall_score_2018',
     'overall_score_2012', 'change_since_2012', 'coherence_2012',
     'coherence_change_since_2012',]
)


# This somehow translates the real value in a color, to be able to compress the
# displayed information in the assessment table
# New color table with answer score as keys, color as value
ANSWERS_COLOR_TABLE = {
    '1': 1,      # very good
    '0.75': 2,   # good
    '0.5': 4,    # poor
    '0.25': 5,   # very poor
    '0': 3,      # not reported
    '0.250': 6,  # not clear
    '/': 7       # not relevant
}

# score_value as key, color as value
CONCLUSION_COLOR_TABLE = {
    5: 0,       # not relevant
    4: 1,       # very good
    3: 2,       # good
    2: 4,       # poor
    1: 5,       # very poor
    0: 3,       # not reported
    0.5: 0o5,
    1.5: 15,
    2.5: 25,
    3.5: 35,
}

CHANGE_COLOR_TABLE = {
    -2: 5,
    -1: 4,
    0: 6,
    1: 3,
    2: 2,
    3: 1,
}

Assessment2012 = namedtuple(
    'Assessment2012', [
        'gescomponents',
        'criteria',
        'summary',
        'concl_crit',
        'overall_ass',
        'score'
    ]
)

Criteria = namedtuple(
    'Criteria', ['crit_name', 'answer']
)


# TODO which question type belongs to which phase?
PHASES = {
    'phase1': ('adequacy', 'consistency'),
    'phase2': ('coherence', ),
    'phase3': (),
}

# mapping of title: field_name
additional_fields = {
    'Summary': u'Summary',
}

summary_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress since 2012'),
    ('recommendations', u'Recommendations for Member State'),
)

reg_summary_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress since 2012'),
    ('recommendations', u'Recommendations'),
)

# TODO not used
progress_fields = (
    ('assessment_summary', u'Assessment summary'),
    ('progress', u'Progress since 2012'),
    ('recommendations', u'Recommendations for Member State'),
)


COM_ASSESSMENT = namedtuple(
    'COM_ASSESSMENT',
    ('Country', 'Descriptor', 'AssessmentCriteria', 'MSFDArticle',
     'Assessment', 'Conclusions', 'Criteria', 'OverallScore',
     'OverallAssessment')
)


COM_ASSESSMENT_Art13_2016 = namedtuple(
    'COM_ASSESSMENT_Art13_2016',
    ('Country', 'Region', 'Article', 'Descriptor', 'AssessmentCriteria', 
     'Assessment', 'Summary', 'Score', 'Conclusion', 'SourceFile')
)


COM_RECOMMENDATION_Art13_2016 = namedtuple(
    'COM_RECOMMENDATION_Art13_2016',
    ('Title', 'RecCode', 'Recommendation', 'MSRegion', 'Descriptors', 
     'ReportURL', 'Comments')
)

COM_ASSESSMENT_Art13_2016_Overall = namedtuple(
    'COM_ASSESSMENT_Art13_2016_Overall',
    ('Country', 'Region', 'Article', 'Descriptors', 'AssessCrit', 'Summary')
)


def get_assessment_data_2012_db(*args):
    """ Returns the assessment for 2012, from COM_Assessments_2012.csv
    """

    articles = {
        'Art8': 'Initial assessment (Article 8)',
        'Art9': 'GES (Article 9)',
        'Art10': 'Targets (Article 10)',
    }

    country, descriptor, article = args
    art = articles.get(article)
    descriptor = descriptor.split('.')[0]

    res = []
    csv_f = resource_filename('wise.msfd', 'data/COM_Assessments_2012.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=';', quotechar='"')

        for row in csv_file:
            res.append(row)

    res_final = []

    for row in res[1:]:
        assess_row = COM_ASSESSMENT(*row)

        overall_text = assess_row.OverallAssessment
        _country = assess_row.Country

        if country not in _country:
            continue

        _desc = assess_row.Descriptor

        if descriptor != _desc:
            continue

        _article = assess_row.MSFDArticle or None

        if _article != art and _article is not None:
            continue

        if not overall_text:
            res_final.append(assess_row)

            continue

        res_final.append(assess_row)

    return res_final


def _get_csv_region(region):
    if region == "ANS":
        region = "ATL"

    if region in ("MAL", ):
        region = "MED"

    return region

def get_assessment_data_2016_art1314(*args):
    """ Returns the assessment for 2016, 
        from National_assessments_Art_1314_2016.csv
    """

    country, descriptor, article, region = args
    if descriptor == 'D1-P':
        descriptor = 'D1 Pelagic'

    region = _get_csv_region(region)

    res = []
    csv_f = resource_filename('wise.msfd', 
        'data/National_assessments_Art_1314_2016.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=';', quotechar='"')

        for row in csv_file:
            res.append(row)

    results = []

    for row in res[1:]:
        assess_row = COM_ASSESSMENT_Art13_2016(*row[:10])

        _country = assess_row.Country.strip()
        if country != _country:
            continue

        _desc = assess_row.Descriptor.strip()
        if descriptor != _desc:
            continue

        _region = assess_row.Region.strip()
        if region != _region:
            continue

        _article = assess_row.Article.strip()
        if article != _article:
            continue

        results.append(assess_row)

    return results


def _get_csv_descriptor(descriptor):
    descriptor_mapping = {
        "D1-B": ("D1, 4 – Birds",), # birds
        "D1-M": ("D1, 4 – Mammals and reptiles",), # mammals
        "D1-R": ("D1, 4 – Mammals and reptiles",), # reptiles
        "D1-F": ("D1, 4 – Fish and cephalopods",), # fish
        "D1-C": ("D1, 4 – Fish and cephalopods",), # cephalopods
        "D1-P": ("D1, 4 – Water column habitats", 
                 "D1, 4, 6 – Seabed habitats"), # pelagic habitats
    }

    if descriptor in descriptor_mapping:
        descriptor = descriptor_mapping[descriptor]

    return descriptor


def get_recommendation_data_2016_art1314(*args):
    """ Returns the recommendation for 2016, 
        from Recommendations_Art_13_2016.csv
    """

    country, descriptor = args

    descriptor_alt = _get_csv_descriptor(descriptor)

    res = []
    csv_f = resource_filename('wise.msfd', 
        'data/Recommendations_Art_13_2016.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=';', quotechar='"')

        for row in csv_file:
            res.append(row)

    results = []

    for row in res[1:]:
        row_title = row[3].strip()
        
        if row_title == 'General':
            _title = 'General recommendations'
        elif row_title == 'Exceptions':
            _title = 'Recommendations on exceptions'
        else:
            _title = 'Descriptor recommendations'

        _row = [_title] + row[:6]
        assess_row = COM_RECOMMENDATION_Art13_2016(*_row)

        _country = assess_row.MSRegion.strip()
        if country != _country:
            continue
        
        if '/' in assess_row.Descriptors:
            _desc = assess_row.Descriptors.strip().split('/')
        elif '–' in assess_row.Descriptors:
            _desc = [assess_row.Descriptors]
        else:
            _desc = assess_row.Descriptors.strip().split(', ')
        
        # this is too complicated
        if isinstance(descriptor_alt, (list, tuple)):
            if (not set(descriptor_alt).intersection(set(_desc)) and descriptor not in _desc):
                if 'General' not in _desc and 'Exceptions' not in _desc:
                    continue
        else:
            if descriptor not in _desc:
                if 'General' not in _desc and 'Exceptions' not in _desc:
                    continue

        results.append(assess_row)

    return results


def get_assessment_data_2016_art1314_overall(*args):
    """ Returns the overall asssesment for 2016, 
        from National_assessments_Art_13_2016_overall.csv
    """

    country, descriptor, region = args
    descriptor = _get_csv_descriptor(descriptor)
    region = _get_csv_region(region)

    res = []
    csv_f = resource_filename('wise.msfd', 
        'data/National_assessments_Art_13_2016_overall.csv')

    with open(csv_f, 'rt') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=';', quotechar='"')

        for row in csv_file:
            res.append(row)

    results = []

    for row in res[1:]:
        assess_row = COM_ASSESSMENT_Art13_2016_Overall(*row[:6])

        _country = assess_row.Country.strip()
        if country != _country:
            continue
        
        _region = assess_row.Region.strip()
        if region != _region:
            continue
        
        if '/' in assess_row.Descriptors:
            _desc = assess_row.Descriptors.strip().split('/')
        elif '–' in assess_row.Descriptors:
            _desc = [assess_row.Descriptors]
        else:
            _desc = assess_row.Descriptors.strip().split(', ')

        if isinstance(descriptor, (list, tuple)):
            if not set(descriptor).intersection(set(_desc)):
                continue
        else:
            if descriptor not in _desc:
                if 'General' not in _desc:
                    continue

        results.append(assess_row)

    return results


@db.use_db_session('2018')
def get_assessment_data_2012_db_old(*args):
    """ Returns the assessment for 2012, from COM_Assessments_2012 table
    """

    articles = {
        'Art8': 'Initial assessment (Article 8)',
        'Art9': 'GES (Article 9)',
        'Art10': 'Targets (Article 10)',
    }

    country, descriptor, article = args
    art = articles.get(article)
    descriptor = descriptor.split('.')[0]

    t = sql2018.t_COM_Assessments_2012
    count, res = db.get_all_records(
        t,
        t.c.Country.like('%{}%'.format(country)),
        t.c.Descriptor == descriptor,
        or_(t.c.MSFDArticle == art,
            t.c.MSFDArticle.is_(None))
    )

    # look for rows where OverallAssessment looks like 'see D1'
    # replace these rows with data for the descriptor mentioned in the
    # OverallAssessment
    res_final = []
    descr_reg = re.compile('see\s(d\d{1,2})', flags=re.I)

    for row in res:
        overall_text = row.OverallAssessment
        assess = row.Assessment

        if 'see' in overall_text.lower() or (not overall_text and
                                             'see d' in assess.lower()):
            descr_match = (descr_reg.match(overall_text)
                            or descr_reg.match(assess))
            descriptor = descr_match.groups()[0]

            _, r = db.get_all_records(
                t,
                t.c.Country == row.Country,
                t.c.Descriptor == descriptor,
                t.c.AssessmentCriteria == row.AssessmentCriteria,
                t.c.MSFDArticle == row.MSFDArticle
            )

            res_final.append(r[0])

            continue

        if not overall_text:
            res_final.append(row)

            continue

        res_final.append(row)

    return res_final


# TODO: use memoization for old data, needs to be called again to get the
# score, to allow delta compute for 2018
#
# @memoize
def filter_assessment_data_2012(data, region_code, descriptor_criterions):
    """ Filters and formats the raw db data for 2012 assessment data
    """
    gescomponents = [c.id for c in descriptor_criterions]

    assessments = {}
    criterias = []

    for row in data:
        fields = row._fields

        def col(col):
            return row[fields.index(col)]

        country = col('Country')

        # The 2012 assessment data have the region in the country name
        # For example: United Kingdom (North East Atlantic)
        # When we display the assessment data (which we do, right now, based on
        # subregion), we want to match the data according to the "big" region

        if '(' in country:
            region = REGION_RE.match(country).groupdict()['region']

            if region not in SUBREGIONS_TO_REGIONS[region_code]:
                continue

        summary = col('Conclusions')
        score = col('OverallScore')
        overall_ass = col('OverallAssessment')
        criteria = Criteria(
            col('AssessmentCriteria'),
            t2rt(col('Assessment'))
        )
        concl_crit = t2rt(col('Criteria'))

        # TODO test for other countries beside LV
        # Condition changed because of LV report, where score is 0

        # if not score:

        if score is None:
            criterias.append(criteria)
        elif country not in assessments:
            criterias.insert(0, criteria)

            if round(float(score)) == float(score):  # score is int like 2
                score = int(score)
            else:  # score is float like 1.5
                score = float(score)

            assessment = Assessment2012(
                gescomponents,
                criterias,
                summary,
                concl_crit,
                overall_ass,
                score,
            )
            assessments[country] = assessment
        else:
            assessments[country].criteria.append(criteria)

        # if country not in assessments:
        #     assessment = Assessment2012(
        #         gescomponents,
        #         [criteria],
        #         summary,
        #         overall_ass,
        #         score,
        #     )
        #     assessments[country] = assessment
        # else:
        #     assessments[country].criteria.append(criteria)

    if not assessments:
        assessment = Assessment2012(
            gescomponents,
            criterias,
            summary,
            concl_crit,
            overall_ass,
            score,
        )
        assessments[country] = assessment

    return assessments


class EditAssessorsForm(Form, BaseComplianceView):
    """ Assessment settings form, used to edit the assessors list

    /assessment-module/national-descriptors-assessments/edit-assessors
    """

    ignoreContext = True
    name = 'edit-assessors'
    section = 'compliance-admin'
    title = u'Edit assessed by'
    fields = Fields(IEditAssessorsForm)
    template = ViewPageTemplateFile('pt/edit-assessors.pt')

    @buttonAndHandler(u'Save', name='Save')
    def hande_save(self, action):
        data, errors = self.extractData()

        if not errors:
            value = data.get('assessed_by', '')
            value = ', '.join(value.split('\r\n'))
            set_assessors(value)

    def updateWidgets(self):
        super(EditAssessorsForm, self).updateWidgets()
        assessed_by_field = self.fields['assessed_by'].field
        default = assessed_by_field.default
        annot_assessors = get_assessors()
        annot_assessors = '\r\n'.join(annot_assessors.split(', '))

        if annot_assessors and default != annot_assessors:
            assessed_by_field.default = annot_assessors
            self.update()


class ViewAssessmentSummaryForm(BaseComplianceView):
    """ Render the assessment summary, progress assessment
    and recommendations for member state for view

    """

    template = ViewPageTemplateFile("pt/assessment-summary-form-view.pt")

    @property
    def summary_fields(self):
        return summary_fields

    @property
    def summary_data(self):
        saved_data = self.context.saved_assessment_data.last()

        _fields = []

        for name, title in self.summary_fields:
            _name = '{}_{}'.format(
                self.article, name
            )

            text = t2rt(saved_data.get(_name, None))

            _fields.append((title, text))

        return _fields

    def __call__(self):
        fields = self.summary_data

        return self.template(fields=fields)


class ViewAssessmentSummaryFormRegional(BaseRegComplianceView,
                                        ViewAssessmentSummaryForm):
    """ Render the assessment summary, progress assessment
    and recommendations for member state for view

        Wrapper class for regional descriptors
    """

    @property
    def summary_fields(self):
        return reg_summary_fields


class EditAssessmentSummaryForm(Form, BaseComplianceView):
    """ Edit the assessment summary

    Fields are: summary, recommendations, progress assessment
    """
    # TODO unused

    title = u"Edit progress assessment"
    template = ViewPageTemplateFile("pt/inline-form.pt")
    _saved = False

    @property
    def fields(self):
        saved_data = self.context.saved_assessment_data.last()

        _fields = []

        for name, title in progress_fields:
            _name = '{}_{}'.format(
                self.article, name
            )

            default = saved_data.get(_name, None)
            _field = Text(title=title,
                          __name__=_name, required=False, default=default)
            _fields.append(_field)

        return Fields(*_fields)

    @buttonAndHandler(u'Save', name='save')
    def handle_save(self, action):
        if self.read_only_access:
            raise Unauthorized

        data, errors = self.extractData()

        if errors:
            return

        context = self.context

        # BBB code, useful in development

        if not hasattr(context, 'saved_assessment_data') or \
                not isinstance(context.saved_assessment_data, PersistentList):
            context.saved_assessment_data = AssessmentData()

        saved_data = self.context.saved_assessment_data.last()

        if not saved_data:
            self.context.saved_assessment_data.append(data)
        else:
            saved_data.update(data)
        self.context.saved_assessment_data._p_changed = True

    def nextURL(self):
        return self.context.absolute_url()

    @property
    def action(self):
        return self.context.absolute_url() + '/@@edit-assessment-summary'

    def render(self):
        if self.request.method == 'POST':
            Form.render(self)

            return self.request.response.redirect(self.nextURL())

        return Form.render(self)


class EditAssessmentDataFormMain(Form):

    @property
    def criterias(self):
        return self.descriptor_obj.sorted_criterions()      # criterions

    @property
    def help(self):
        return render_assessment_help(self.criterias, self.descriptor)

    def is_disabled(self, question):
        """ Returns True if question is not editable
        """

        if self.read_only_access:
            return True

        # Is this still needed?
        state, _ = self.current_phase
        is_disabled = question.klass not in PHASES.get(state, ())

        return is_disabled

    @property
    def fields(self):
        if not self.subforms:
            self.subforms = self.get_subforms()

        fields = []

        for subform in self.subforms:
            fields.extend(subform.fields._data_values)

        return Fields(*fields)

    @property       # TODO: memoize
    def descriptor_obj(self):
        return get_descriptor(self.descriptor)

    # TODO: use memoize
    @property
    def questions(self):
        qs = self._questions[self.article]

        return qs

Cell = namedtuple('Cell', ['text', 'rowspan'])


help_template = PageTemplateFile(
    'src/wise.msfd/src/wise/msfd/compliance/pt/assessment-question-help.pt'
)


def render_assessment_help(criterias, descriptor):
    elements = []
    methods = []

    for c in criterias:
        elements.extend([e.id for e in c.elements])
        methods.append(c.methodological_standard.id)

    element_count = {}

    for k in elements:
        element_count[k] = elements.count(k)

    method_count = {}

    for k in methods:
        method_count[k] = methods.count(k)

    rows = []
    seen = []

    for c in criterias:
        row = []

        if not c.elements:
            logger.info("Skipping %r from help rendering", c)

            continue
        cel = c.elements[0]     # TODO: also support multiple elements

        if cel.id not in seen:
            seen.append(cel.id)
            rowspan = element_count[cel.id]
            cell = Cell(cel.definition, rowspan)
            row.append(cell)

        prim_label = c.is_primary(descriptor) and 'primary' or 'secondary'
        cdef = u"<strong>{} ({})</strong><br/>{}".format(
            c.id, prim_label, c.definition
        )

        cell = Cell(cdef, 1)
        row.append(cell)

        meth = c.methodological_standard

        if meth.id not in seen:
            seen.append(meth.id)
            rowspan = method_count[meth.id]
            cell = Cell(meth.definition, rowspan)
            row.append(cell)

        rows.append(row)

    return help_template(rows=rows)


class AssessmentDataMixin(object):
    """ Helper class for easier access to the assesment_data for
        national and regional descriptor assessments

        Currently used to get the coherence score from regional descriptors

        TODO: implement a method to get the adequacy and consistency scores
        from national descriptors assessment
    """
    overall_scores = {}

    def t2rt(self, text):
        return t2rt(text)

    @property
    def _nat_desc_folder(self):
        portal_catalog = get_tool('portal_catalog')
        brains = portal_catalog.unrestrictedSearchResults(
            object_provides=INationalDescriptorsFolder.__identifier__
        )
        nat_desc_folder = brains[0]._unrestrictedGetObject()

        return nat_desc_folder

    @property
    def _nat_desc_country_folders(self):
        return self.filter_contentvalues_by_iface(
            self._nat_desc_folder, ICountryDescriptorsFolder
        )

    @property
    def _reg_desc_folder(self):
        portal_catalog = get_tool('portal_catalog')
        brains = portal_catalog.unrestrictedSearchResults(
            object_provides=IRegionalDescriptorsFolder.__identifier__
        )
        nat_desc_folder = brains[0]._unrestrictedGetObject()

        return nat_desc_folder

    @property
    def _reg_desc_region_folders(self):
        return self.filter_contentvalues_by_iface(
            self._reg_desc_folder, IRegionalDescriptorRegionsFolder
        )

    @property
    def rdas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='wise.msfd.regionaldescriptorassessment',
        )

        for brain in brains:
            obj = brain._unrestrictedGetObject()

            if not IRegionalDescriptorAssessment.providedBy(obj):
                continue

            yield obj

    def get_color_for_score(self, score_value):
        return CONCLUSION_COLOR_TABLE.get(score_value, 0)

    def get_conclusion(self, score_value):
        try:
            concl = list(reversed(CONCLUSIONS))[score_value]
        except:
            concl = CONCLUSIONS[0]

        return concl

    def _get_assessment_data(self, article_folder):
        if not hasattr(article_folder, 'saved_assessment_data'):
            return {}

        return article_folder.saved_assessment_data.last()

    def get_main_region(self, region_code):
        """ Returns the main region (used in regional descriptors)
            for a sub region (used in national descriptors)
        """

        for region in REGIONAL_DESCRIPTORS_REGIONS:
            if not region.is_main:
                continue

            if region_code in region.subregions:
                return region.code

        return region_code

    @cache(lambda func, *args: '-'.join((func.__name__, args[1], args[2],
                                        args[3])), lifetime=1800)
    def get_coherence_data(self, region_code, descriptor, article):
        """ For year 2018
        :return: {'color': 5, 'score': 0, 'max_score': 0,
                'conclusion': (1, 'Very poor')
            }
        """

        article_folder = None

        for obj in self.rdas:
            descr = obj.aq_parent.id.upper()

            if descr != descriptor:
                continue

            region = obj.aq_parent.aq_parent.id.upper()

            if region != self.get_main_region(region_code):
                continue

            art = obj.title

            if art != article:
                continue

            article_folder = obj

            break

        assess_data = self._get_assessment_data(article_folder)

        res = {
            'score': 0,
            'max_score': 100,
            'color': 0,
            'conclusion': (0, 'Not reported')
        }

        for k, score in assess_data.items():
            if '_Score' not in k:
                continue

            if not score:
                continue

            is_not_relevant = getattr(score, 'is_not_relevant', False)
            weighted_score = getattr(score, 'final_score', 0)
            max_weighted_score = getattr(score, 'weight', 0)

            if is_not_relevant:
                res['max_score'] -= max_weighted_score
                continue

            res['score'] += weighted_score

        score_percent = int(round(res['max_score'] and (res['score'] * 100)
                                  / res['max_score'] or 0))

        # score_percent = res['score']
        score_val = get_range_index(score_percent)

        res['color'] = self.get_color_for_score(score_val)
        res['conclusion'] = (score_val, self.get_conclusion(score_val))

        if res['max_score'] == 0:
            res['conclusion'] = ('-', 'Not relevant')
            res['color'] = 0

        return res

    @cache(lambda func, *args: '-'.join((func.__name__, args[1], args[2],
                                        args[3], args[4])), lifetime=1800)
    def get_assessment_data_2012(self, region_code, country_name,
                                 descriptor, article):
        """ Returns the score and conclusion of the 2012 national assessment
        """

        try:
            db_data_2012 = get_assessment_data_2012_db(
                country_name,
                descriptor,
                article
            )
            assessments_2012 = filter_assessment_data_2012(
                db_data_2012,
                region_code,
                []  # descriptor_criterions,
            )

            if assessments_2012.get(country_name):
                score_2012 = assessments_2012[country_name].score
                conclusion_2012 = assessments_2012[country_name].overall_ass
            else:       # fallback
                ctry = list(assessments_2012.keys())[0]
                score_2012 = assessments_2012[ctry].score
                conclusion_2012 = assessments_2012[ctry].overall_ass

        except:
            logger.exception("Could not get assessment data for 2012")
            score_2012 = 0
            conclusion_2012 = 'Not found'

        # __score = int(round(score_2012 or 0))

        return score_2012, conclusion_2012 or 'Not found'

    def get_reg_assessments_data_2012(self, article=None, region_code=None,
                                      descriptor_code=None):
        """ Get the regional descriptor assessment 2012 data """
        from .regionaldescriptors.assessment import ASSESSMENTS_2012

        if not article:
            article = self.article

        if not region_code:
            region_code = self.country_region_code

        if not descriptor_code:
            descriptor_code = self.descriptor_obj.id

        # region_code = self.get_main_region(region_code)

        res = []

        for x in ASSESSMENTS_2012:
            if x.region.strip() != region_code:
                continue

            if x.descriptor.strip() != descriptor_code.split('.')[0]:
                continue

            art = x.article.replace(" ", "")

            if not art.startswith(article):
                continue

            res.append(x)

        sorted_res = sorted(
            res, key=lambda i: int(i.overall_score), reverse=True
        )

        return sorted_res

    def _setup_phase_overall_scores(self, phase_overall_scores, assess_data,
                                    article):
        """ National Descriptors Assessments
            Given an assessment data calculates the adequacy, consistency
            and coherence scores

        :param phase_overall_scores: an instance of OverallScores class, with
            empty adequacy, consistency, coherence score values
        :param assess_data: saved_assessment_data (dictionary) attribute
            from an assessment object like .../fi/bal/d1.1/art8
        :param article: 'Art9'
        :return: instance of OverallScores with calculated adequacy,
            consistency and coherence score values
        """
        phases = list(phase_overall_scores.article_weights[article].keys())
        phases_answered = set()

        for k, score in assess_data.items():
            if '_Score' not in k:
                continue

            if not score:
                continue

            is_not_relevant = getattr(score, 'is_not_relevant', False)
            q_klass = score.question.klass
            phases_answered.add(q_klass)
            weighted_score = getattr(score, 'final_score', 0)
            max_weighted_score = getattr(score, 'weight', 0)

            if not is_not_relevant:
                p_score = getattr(phase_overall_scores, q_klass)
                p_score['score'] += weighted_score
                p_score['max_score'] += max_weighted_score

        # set the max score to 100 for phases which do not have
        # answered questions
        for phase in phases:
            if phase == 'consistency' and article == 'Art9':
                continue

            if phase in phases_answered:
                continue

            phase_scores = getattr(phase_overall_scores, phase)
            phase_scores['max_score'] = 100

        for phase in phases:
            # set the conclusion and color based on the score for each phase
            phase_scores = getattr(phase_overall_scores, phase)
            score_val = phase_overall_scores.get_range_index_for_phase(phase)

            if (phase == 'consistency' and article == 'Art9'
                    or phase_scores['max_score'] == 0):
                phase_scores['conclusion'] = ('-', 'Not relevant')
                phase_scores['color'] = 0
                phase_scores['score'] = '/'
            elif phase == 'consistency' and phase_scores['score'] == 0:
                phase_scores['conclusion'] = (0, 'Not consistent')
                phase_scores['color'] = 3
            else:
                phase_scores['conclusion'] = (score_val,
                                              self.get_conclusion(score_val))
                phase_scores['color'] = self.get_color_for_score(score_val)

        return phase_overall_scores

    def _get_article_data(self, region_code, country_name, descriptor,
                          assess_data, article):
        """ Given the result from '_setup_phase_overall_scores' method
            return a DESCRIPTOR_SUMMARY namedtuple with summaries,
            adequacy/consistency/coherence scores, 2012 scores, conclusions,
            score changes

        :param region_code: 'BAL'
        :param country_name: 'Finland'
        :param descriptor: 'D1.1'
        :param assess_data: saved_assessment_data dictionary
        :param article: Art9
        :return: DESCRIPTOR_SUMMARY namedtuple
        """

        phase_overall_scores = OverallScores(ARTICLE_WEIGHTS)

        # Get the adequacy, consistency scores from national descriptors
        phase_overall_scores = self._setup_phase_overall_scores(
            phase_overall_scores, assess_data, article)

        # Get the coherence scores from regional descriptors
        phase_overall_scores.coherence = self.get_coherence_data(
            region_code, descriptor, article
        )

        adequacy_score_val, conclusion = \
            phase_overall_scores.adequacy['conclusion']
        # score = phase_overall_scores.get_score_for_phase('adequacy')
        adequacy = ("{} ({})".format(conclusion, adequacy_score_val),
                    phase_overall_scores.adequacy['color'])

        score_val, conclusion = phase_overall_scores.consistency['conclusion']
        # score = phase_overall_scores.get_score_for_phase('consistency')
        consistency = ("{} ({})".format(conclusion, score_val),
                       phase_overall_scores.consistency['color'])

        cscore_val, conclusion = phase_overall_scores.coherence['conclusion']
        # score = phase_overall_scores.get_score_for_phase('coherence')
        coherence = ("{} ({})".format(conclusion, cscore_val),
                     phase_overall_scores.coherence['color'])

        overallscore_val, score = phase_overall_scores.get_overall_score(
            article
        )
        conclusion = self.get_conclusion(overallscore_val)
        overall_score_2018 = (
            "{} ({})".format(conclusion, overallscore_val),
            self.get_color_for_score(overallscore_val)
        )

        assessment_summary = t2rt(
            assess_data.get('{}_assessment_summary'.format(article)) or '-'
        )
        progress_assessment = t2rt(
            assess_data.get('{}_progress'.format(article)) or '-'
        )
        recommendations = t2rt(
            assess_data.get('{}_recommendations'.format(article)) or '-'
        )

        score_2012, conclusion_2012 = self.get_assessment_data_2012(
            region_code, country_name, descriptor, article
        )
        overall_score_2012 = ("{} ({})".format(conclusion_2012, score_2012),
                              self.get_color_for_score(score_2012))

        __key_2018 = (region_code, descriptor, article, '2018')
        __key_2012 = (region_code, descriptor, article, '2012')
        self.overall_scores[__key_2012] = overall_score_2012
        self.overall_scores[__key_2018] = overall_score_2018

        if adequacy_score_val == '-':  # if adequacy is not relevant
            change_since_2012 = 'Not relevant (-)'
        else:
            change_since_2012 = int(adequacy_score_val - score_2012)

        reg_assess_2012 = self.get_reg_assessments_data_2012(
            article, region_code, descriptor
        )
        coherence_2012 = ('Not scored', '0')
        coherence_change_since_2012 = 'Not relevant (-)'

        if reg_assess_2012:
            __score = float(reg_assess_2012[0].overall_score)
            coherence_2012 = ("{} ({})".format(reg_assess_2012[0].conclusion,
                                              int(__score)),
                              self.get_color_for_score(__score))
            if cscore_val == '-':
                cscore_val = 0

            coherence_change_since_2012 = int(cscore_val - __score)

        res = DESCRIPTOR_SUMMARY(
            assessment_summary, progress_assessment, recommendations,
            adequacy, consistency, coherence, overall_score_2018,
            overall_score_2012, change_since_2012,
            coherence_2012, coherence_change_since_2012
        )

        return res

    @timeit
    def setup_descriptor_level_assessment_data(self, country_code=None):
        """ Setup the national assessments data for a single country,


        :return: res =  [("Baltic Sea", [
                    ("D7 - Hydrographical changes", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                    ("D1.4 - Birds", [
                            ("Art8", DESCRIPTOR_SUMMARY),
                            ("Art9", DESCRIPTOR_SUMMARY),
                            ("Art10", DESCRIPTOR_SUMMARY),
                        ]
                    ),
                ]
            )]
        """
        self.overall_scores = {}

        if not country_code:
            country_code = self.country_code

        res = []

        country_folder = [
            country
            for country in self._nat_desc_folder.contentValues()
            if country.id == country_code.lower()
        ][0]

        self.nat_desc_country_folder = country_folder
        region_folders = self.filter_contentvalues_by_iface(
            country_folder, INationalRegionDescriptorFolder
        )

        region_folders_sorted = sorted(
            region_folders, key=lambda i: ordered_regions_sortkey(i.id.upper())
        )

        for region_folder in region_folders_sorted:
            region_code = region_folder.id
            region_name = region_folder.title
            descriptor_data = []
            descriptor_folders = self.filter_contentvalues_by_iface(
                region_folder, IDescriptorFolder
            )

            for descriptor_folder in descriptor_folders:
                desc_id = descriptor_folder.id.upper()
                desc_name = descriptor_folder.title
                articles = []
                article_folders = self.filter_contentvalues_by_iface(
                    descriptor_folder, INationalDescriptorAssessment
                )

                for article_folder in article_folders:
                    article = article_folder.title

                    if article in ('Art11', ):
                        continue

                    assess_data = self._get_assessment_data(article_folder)
                    article_data = self._get_article_data(
                        region_code.upper(), country_folder.title,
                        desc_id, assess_data, article
                    )
                    articles.append((article, article_data))

                articles = sorted(
                    articles,
                    key=lambda i: fixedorder_sortkey(i[0], self.ARTICLE_ORDER)
                )

                descriptor_data.append(
                    ((desc_id, desc_name), articles)
                )

            res.append((region_name, descriptor_data))

        return res