import logging
from collections import namedtuple

from plone.api.portal import get_tool

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from wise.msfd.compliance.interfaces import (IDescriptorFolder,
                                             INationalDescriptorAssessment,
                                             INationalDescriptorsFolder,
                                             INationalRegionDescriptorFolder)
from wise.msfd.compliance.scoring import (CONCLUSIONS, get_range_index,
                                          OverallScores)
from wise.msfd.utils import (ItemList, TemplateMixin, db_objects_to_dict,
                             fixedorder_sortkey, timeit)

from ..nationaldescriptors.main import (ARTICLE_WEIGHTS,
                                        CONCLUSION_COLOR_TABLE,
                                        get_assessment_data_2012_db,
                                        filter_assessment_data_2012)
from .base import BaseNatSummaryView

logger = logging.getLogger('wise.msfd')

DESCRIPTOR_SUMMARY = namedtuple(
    'DescriptorSummary',
    ['assessment_summary', 'progress_assessment', 'recommendations',
     'adequacy', 'consistency', 'coherence', 'overall_score_2018',
     'overall_score_2012', 'change_since_2012']
)


class DescriptorLevelAssessments(BaseNatSummaryView):

    template = ViewPageTemplateFile('pt/descriptor-level-assessments.pt')

    overall_scores = {}

    descriptor_types = [
        ("Pressure-based descriptors", ['D2', 'D5', 'D7', 'D9', 'D10', 'D11']),
        ("State-based descriptors", ['D1.1', 'D1.2', 'D1.3', 'D1.4', 'D1.5',
                                     'D3', 'D1.6', 'D6', 'D4'])
    ]

    @property
    def rdas(self):
        catalog = get_tool('portal_catalog')
        brains = catalog.searchResults(
            portal_type='wise.msfd.regionaldescriptorassessment',
        )

        for brain in brains:
            obj = brain.getObject()

            yield obj

    def get_coherence_data(self, region_code, descriptor, article):
        """
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

            if region != region_code:
                continue

            art = obj.title

            if art != article:
                continue

            article_folder = obj

            break

        assess_data = self._get_assessment_data(article_folder)

        res = {
            'score': 0,
            'max_score': 0,
            'color': 0,
            'conclusion': (1, 'Very poor')
        }

        for k, score in assess_data.items():
            if '_Score' not in k:
                continue

            if not score:
                continue

            is_not_relevant = getattr(score, 'is_not_relevant', False)
            weighted_score = getattr(score, 'weighted_score', 0)
            max_weighted_score = getattr(score, 'max_weighted_score', 0)

            if not is_not_relevant:
                res['score'] += weighted_score
                res['max_score'] += max_weighted_score

        score_percent = int(round(res['max_score'] and (res['score'] * 100)
                                  / res['max_score'] or 0))
        score_val = get_range_index(score_percent)
        res['color'] = self.get_color_for_score(score_val)
        res['conclusion'] = (score_val, self.get_conclusion(score_val))

        return res

    def get_assessment_data_2012(self, region_code, country_name,
                                 descriptor, article):
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
                ctry = assessments_2012.keys()[0]
                score_2012 = assessments_2012[ctry].score
                conclusion_2012 = assessments_2012[ctry].overall_ass

        except:
            logger.exception("Could not get assessment data for 2012")
            score_2012 = 0
            conclusion_2012 = 'Not found'

        return int(round(score_2012)), conclusion_2012

    def get_color_for_score(self, score_value):
        return CONCLUSION_COLOR_TABLE[score_value]

    def get_conclusion(self, score_value):
        concl = list(reversed(CONCLUSIONS))[score_value]

        return concl

    def _get_assessment_data(self, article_folder):
        if not hasattr(article_folder, 'saved_assessment_data'):
            return {}

        return article_folder.saved_assessment_data.last()

    def _setup_phase_overall_scores(self, phase_overall_scores, assess_data,
                                    article):

        for k, score in assess_data.items():
            if '_Score' not in k:
                continue

            if not score:
                continue

            is_not_relevant = getattr(score, 'is_not_relevant', False)
            q_klass = score.question.klass
            weighted_score = getattr(score, 'weighted_score', 0)
            max_weighted_score = getattr(score, 'max_weighted_score', 0)

            if not is_not_relevant:
                p_score = getattr(phase_overall_scores, q_klass)
                p_score['score'] += weighted_score
                p_score['max_score'] += max_weighted_score

        phases = phase_overall_scores.article_weights[article].keys()

        for phase in phases:
            # set the conclusion and color based on the score for each phase
            phase_scores = getattr(phase_overall_scores, phase)
            score_val = phase_overall_scores.get_range_index_for_phase(phase)

            if phase == 'consistency' and article == 'Art9':
                phase_scores['conclusion'] = ('-', 'Not relevant')
                phase_scores['color'] = 0
            else:
                phase_scores['conclusion'] = (score_val,
                                              self.get_conclusion(score_val))
                phase_scores['color'] = self.get_color_for_score(score_val)

        return phase_overall_scores

    def _get_article_data(self, region_code, country_name, descriptor,
                          assess_data, article):
        phase_overall_scores = OverallScores(ARTICLE_WEIGHTS)

        # Get the adequacy, consistency scores from national descriptors
        phase_overall_scores = self._setup_phase_overall_scores(
            phase_overall_scores, assess_data, article)

        # Get the coherence scores from regional descriptors
        phase_overall_scores.coherence = self.get_coherence_data(
            region_code, descriptor, article
        )

        # if assess_data:
        #     import pdb; pdb.set_trace()

        adequacy_score_val, conclusion = \
            phase_overall_scores.adequacy['conclusion']
        score = phase_overall_scores.get_score_for_phase('adequacy')
        adequacy = ("{} ({}) {}%".format(conclusion, adequacy_score_val, score),
                    phase_overall_scores.adequacy['color'])

        score_val, conclusion = phase_overall_scores.consistency['conclusion']
        score = phase_overall_scores.get_score_for_phase('consistency')
        consistency = ("{} ({}) {}%".format(conclusion, score_val, score),
                       phase_overall_scores.consistency['color'])

        score_val, conclusion = phase_overall_scores.coherence['conclusion']
        score = phase_overall_scores.get_score_for_phase('coherence')
        coherence = ("{} ({}) {}%".format(conclusion, score_val, score),
                     phase_overall_scores.coherence['color'])

        overallscore_val, score = phase_overall_scores.get_overall_score(
            article
        )
        conclusion = self.get_conclusion(overallscore_val)
        overall_score_2018 = (
            "{} ({}) {}%".format(conclusion, overallscore_val, score),
            self.get_color_for_score(overallscore_val)
        )

        assessment_summary = assess_data.get(
            '{}_assessment_summary'.format(article)
        )
        progress_assessment = assess_data.get('{}_progress'.format(article))
        recommendations = assess_data.get('{}_recommendations'.format(article))

        score_2012, conclusion_2012 = self.get_assessment_data_2012(
            region_code, country_name, descriptor, article
        )
        overall_score_2012 = ("{} ({})".format(conclusion_2012, score_2012),
                              self.get_color_for_score(score_2012))

        __key = (region_code, descriptor, article)
        self.overall_scores[__key] = overall_score_2018

        change_since_2012 = int(overallscore_val - score_2012)

        res = DESCRIPTOR_SUMMARY(
            assessment_summary, progress_assessment, recommendations,
            adequacy, consistency, coherence, overall_score_2018,
            overall_score_2012, change_since_2012
        )

        return res

    @timeit
    def setup_descriptor_level_assessment_data(self):
        """
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

        res = []

        portal_catalog = self.context.context.portal_catalog
        brains = portal_catalog.searchResults(
            object_provides=INationalDescriptorsFolder.__identifier__
        )
        nat_desc_folder = brains[0].getObject()
        country_folder = [
            country
            for country in nat_desc_folder.contentValues()
            if country.id == self.country_code.lower()
        ][0]

        self.nat_desc_country_folder = country_folder
        region_folders = self.filter_contentvalues_by_iface(
            country_folder, INationalRegionDescriptorFolder
        )

        for region_folder in region_folders:
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

    def __call__(self):
        data = self.setup_descriptor_level_assessment_data()

        return self.template(data=data)