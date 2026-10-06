# pylint: skip-file
"""Registry of explorer data providers, keyed by article and reporting cycle."""
from __future__ import absolute_import

from wise.msfd.explorer.providers.article4_2024 import Article4Cycle2024Provider

PROVIDERS = (
    Article4Cycle2024Provider,
)

# block ``article_select`` slug -> article number
ARTICLE_ALIASES = {}

for _provider in PROVIDERS:
    if _provider.article_slug:
        ARTICLE_ALIASES[_provider.article_slug] = _provider.article

_BY_KEY = {
    (provider.article, provider.cycle): provider
    for provider in PROVIDERS
}


def normalize_article(article):
    if article is None:
        return None

    article = str(article)

    return ARTICLE_ALIASES.get(article, article)


def get_provider_class(article, cycle):
    if article is None or cycle is None:
        return None

    return _BY_KEY.get((normalize_article(article), str(cycle)))


def available_providers():
    """Introspection helper, useful for the frontend and for tests."""
    return [
        {
            'article': provider.article,
            'articleSlug': provider.article_slug,
            'cycle': provider.cycle,
            'cycleLabel': provider.cycle_label,
            'recordTitle': provider.record_title,
        }
        for provider in PROVIDERS
    ]
