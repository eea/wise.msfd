# -*- coding: utf-8 -*-

""" Module to generate the feature list based on terms
"""

from zope.schema.vocabulary import SimpleVocabulary

from z3c.formwidget.optgroup.widget import OptgroupTerm

from .db import get_all_records, switch_session, threadlocals
from .sql2018 import LFeature


@switch_session
def get_feature_terms():
    # TODO: generate the vocabulary based on the context country, descriptor

    # TODO: next line needs to be included in the switch_session decorator
    threadlocals.session_name = 'session_2018'

    terms = []
    seen = []

    count, db_res = get_all_records(LFeature)

    for row in db_res:

        value = row.Code
        label = row.Feature
        group = row.Theme

        if value in seen:
            continue

        seen.append(value)

        term = OptgroupTerm(value=value,
                            token=value,
                            title=label,
                            optgroup=group or 'No theme')
        terms.append(term)

    return terms


features_vocabulary = SimpleVocabulary(get_feature_terms())
