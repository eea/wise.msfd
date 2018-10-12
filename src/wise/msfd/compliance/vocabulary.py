# -*- coding: utf-8 -*-

import csv

from pkg_resources import resource_filename
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from .base import Leaf as L

ASSESSED_ARTICLES = (
    ('Art3', 'Art. 3(1) Marine waters',),
    ('Art4', 'Art. 4/2017 Decision: Marine regions, subregions, '
     'and subdivisions '),
    ('Art5', '(MRUs)', ),
    ('Art6', 'Art. 6 Regional cooperation', ),
    ('Art7', 'Art. 7 Competent authorities', ),
    ('Art8', 'Art. 8 Initial assessment (and Art. 17 updates)', ),
    ('Art9', 'Art. 9 Determination of GES (and Art. 17 updates) ', ),
    ('Art10', 'Art. 10 Environmental targets (and Art. 17 updates)', ),
    ('Art11', 'Art. 11 Monitoring programmes (and Art. 17 updates)', ),
    ('Art13', 'Art. 13 Programme of measures (and Art. 17 updates)', ),
    ('Art14', 'Art. 14 Exceptions (and Art. 17 updates)', ),
    ('Art18', 'Art. 18 Interim report on programme of measures', ),
    ('Art19_3', 'Art. 19(3) Access to data', ),
)


def parse_forms_file():
    csv_f = resource_filename('wise.msfd',
                              'data/forms.tsv')
    # hierarchy = [
    #     'MSFD article', 'AssessmentCriteria', 'AssessedInformation',
    #     'Evidence'
    # ]

    res = L('articles')

    with open(csv_f, 'rb') as csvfile:
        csv_file = csv.reader(csvfile, delimiter='\t')

        l1, l2, l3, l4 = None, None, None, None     # the 4 columns

        for row in csv_file:
            if not row:
                continue
            article, criteria, information, evidence = row
            evidence = unicode(evidence, 'utf-8')

            l4 = L(evidence)    # always last level, we can safely create it

            if (l3 is None) or (l3.name != information):
                l3 = L(information)
            l3.add(l4)

            if (l2 is None) or (l2.name != criteria):
                l2 = L(criteria)
            l2.add(l3)

            if (l1 is None) or (l1.name != article):
                l1 = L(article)
                res.add(l1)
            l1.add(l2)

    return res


form_structure = parse_forms_file()


# TODO: sort this vocabulary (somehow)
GES_DESCRIPTORS = (
    ('D1', 'D1 Biodiversity'),
    ('D1 Birds', 'D1 Biodiversity – birds'),
    ('D1 Cephalopods', 'D1 Biodiversity –  cephalopods'),
    ('D1 Fish', 'D1 Biodiversity – fish'),
    ('D1 Mammals', 'D1 Biodiversity – mammals'),
    ('D1 Pelagic habitats', 'D1 Biodiversity – pelagic habitats'),
    ('D1 Reptiles', 'D1 Biodiversity – reptiles'),
    ('D2', 'D2 Non-indigenous species'),
    ('D3', 'D3 Commercial fish and shellfish'),
    ('D4/D1', 'D4 Food webs/D1 Biodiversity - ecosystems'),
    ('D5', 'D5 Eutrophication'),
    ('D6/D1', 'D6 Sea-floor integrity/D1 Biodiversity - benthic habitats'),
    ('D7', 'D7 Hydrographical changes'),
    ('D8', 'D8 Contaminants'),
    ('D9', 'D9 Contaminants in seafood'),
    ('D10', 'D10 Marine litter'),
    ('D11', 'D11 Energy, incl. underwater noise'),
)


def vocab_from_pairs(pairs):
    """ Build a zope.schema vocabulary from pairs of (value(token), title)
    """
    terms = []

    for val, title in pairs:
        term = SimpleTerm(val, val, title)
        terms.append(term)

    return SimpleVocabulary(terms)


def vocab_from_list(values):
    return SimpleVocabulary([SimpleTerm(x, x, x) for x in values])


descriptors_vocabulary = vocab_from_pairs(GES_DESCRIPTORS)
articles_vocabulary = vocab_from_pairs(ASSESSED_ARTICLES)
