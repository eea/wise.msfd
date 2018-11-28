from collections import defaultdict

from sqlalchemy import and_, or_

from Products.Five.browser.pagetemplatefile import \
    ViewPageTemplateFile as Template
from wise.msfd import db, sql, sql2018, sql_extra
from wise.msfd.gescomponents import get_ges_criterions
from wise.msfd.utils import Row, TableHeader

from ..base import BaseArticle2012
from .utils import get_all_criterions, get_indicator_descriptors, row_to_dict


class Article10(BaseArticle2012):
    """ Article 10 implementation for nation descriptors data

    klass(self, self.request, self.country_code, self.descriptor,
          self.article, self.muids, self.colspan)
    """

    template = Template('pt/report-data-a10.pt')

    def get_gescomponents(self):
        return Row('[GEScomponent]', [x[1] for x in self.labeled_criterias])

    def get_marine_unit_ids(self):
        return Row('MarineUnitID', [', '.join(self.muids)])

    def get_indicator_descriptors(self):
        values = get_indicator_descriptors(self.muids,
                                           self.indicators_map.keys())

        return Row('GES description [DescriptionGES]', values)

    def __call__(self):

        self.labeled_criterias = self.context.get_criterias_list(
            self.descriptor
        )
        criterions = get_all_criterions(self.descriptor)

        self.indicators_map = get_indicators_with_feature_pressures(
            criterions
        )

        self.rows = [
            self.get_marine_unit_ids(),
            self.get_gescomponents(),
            self.get_indicator_descriptors(),
        ]

        return self.template()
