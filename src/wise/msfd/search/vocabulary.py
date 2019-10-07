# TODO: move rest of vocabularies from wise.msfd.vocabulary, they're not ok
# in that location
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from .utils import (FORMS, FORMS_2018, FORMS_ART11, FORMS_ART18, SUBFORMS,
                    article_sort_helper)


@provider(IVocabularyFactory)
def monitoring_programme_info_types(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART11.items()]
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
def articles_vocabulary_factory_2018(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_2018.items()]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab


@provider(IVocabularyFactory)
def articles_vocabulary_factory(context):
    terms = [SimpleTerm(k, k, v.title) for k, v in FORMS.items()]
    terms.sort(key=article_sort_helper)
    vocab = SimpleVocabulary(terms)

    return vocab


# Article 18
@provider(IVocabularyFactory)
def a18_data_type(context):
    terms = [SimpleTerm(v, k, v.title) for k, v in FORMS_ART18.items()]
    terms.sort(key=lambda t: t.title)
    vocab = SimpleVocabulary(terms)

    return vocab
