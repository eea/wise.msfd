#pylint: skip-file
from __future__ import absolute_import
from zope.interface import provider
from zope.security import checkPermission
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from .. import db, sql, sql2018
from ..vocabulary import values_to_vocab
from .utils import (FORMS_ART4, FORMS_ART8, FORMS_ART8_2012, FORMS_ART8_2018,
                    FORMS_ART9_2012, FORMS_ART9,
                    FORMS_ART10_2012, FORMS_ART10,
                    FORMS_ART11, FORMS_ART18, FORMS_ART19, SUBFORMS,
                    article_sort_helper, article_sort_helper_2018)


@provider(IVocabularyFactory)
def monitoring_programme_info_types(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART11.items()]
    # terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


def _reporting_period(context, forms):
    terms = []

    for k, v in forms.items():
        term = SimpleTerm(v, k, v.title)
        permission = v.permission
        can_view = checkPermission(permission, context)

        if can_view:
            terms.append(term)

    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a8_reporting_period(context):
    forms = FORMS_ART8

    return _reporting_period(context, forms)


@provider(IVocabularyFactory)
def a9_reporting_period(context):
    forms = FORMS_ART9

    return _reporting_period(context, forms)


@provider(IVocabularyFactory)
def report_type_art9(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART9_2012.items()]
    terms.sort(key=lambda t: t.title, reverse=True)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def report_type_art10(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART10_2012.items()]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a10_reporting_period(context):
    forms = FORMS_ART10

    return _reporting_period(context, forms)


@provider(IVocabularyFactory)
def a19_reporting_period(context):
    terms = []
    for k, v in FORMS_ART19.items():
        term = SimpleTerm(v, k, v.title)
        terms.append(term)

    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a81_forms_vocab_factory(context):
    klass = context.subform.__class__

    terms = []

    forms = SUBFORMS[klass]

    for k in forms:
        terms.append(SimpleTerm(k, k.title, k.title))

    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


# Articles 8, 9, 10
# reporting year 2018
@provider(IVocabularyFactory)
def articles_vocabulary_factory_a8_2018(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART8_2018.items()]
    terms.sort(key=article_sort_helper_2018)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def articles_vocabulary_factory_a8(context):
    terms = [SimpleTerm(k, k, v.title) for k, v in FORMS_ART8_2012.items()]
    terms.sort(key=article_sort_helper)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a4_mru_reporting_cycle_factory(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART4.items()]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


# Article 18
@provider(IVocabularyFactory)
def a18_data_type(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART18.items()]
    terms.sort(key=lambda t: t.title, reverse=True)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def a19_region_subregions(context):
    conditions = []

    mc = sql.MetadataArt193

    count, rows = db.get_all_records(
        mc,
        *conditions
    )

    return values_to_vocab(set(x.Region for x in rows))


@provider(IVocabularyFactory)
def a19_member_states(context):
    conditions = []

    mc = sql.MetadataArt193

    if hasattr(context, 'get_selected_region_subregions'):
        regions = context.get_selected_region_subregions()

        if regions:
            conditions.append(mc.Region.in_(regions))

    count, rows = db.get_all_records(
        mc,
        *conditions
    )

    return values_to_vocab(set(x.Country for x in rows))
