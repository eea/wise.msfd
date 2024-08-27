# pylint: skip-file
DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [1, 25],
    [0, 0],
]


DEFAULT_RANGES_2022 = [
    [81, 100],
    [61, 80],
    [41, 60],
    [21, 40],
    [0, 20]
]


CONCLUSIONS = [
    'Not relevant',
    'Very good',
    'Good',
    'Poor',
    'Very poor',
    'Not reported',
]


CONCLUSIONS_2022 = [
    'Not relevant',
    'Very good',
    'Good',
    'Moderate',
    'Poor',
    'Very poor',
]


# specific weights for some qestions/countries/descriptor
COUNTRY_WEIGHTS = {
    "Ad02B": {
        "CY": {
            "D5": 3,
            "D8": 3,
            "D9": 3
        },
        "IE": {
            "D2": 3,
            "D5": 3,
            "D7": 3,
            "D8": 3,
            "D9": 3
        },
        "LV": {
            "D9": 3,
        },
        "NL": {
            "D2": 3,
            "D7": 3,
            "D9": 3
        },
        "RO": {
            "D9": 3,
        },
        "IT": {
            "D7": 3,
            "D9": 3,
        },
        "PT": {
            "D5": 3,
            "D7": 3,
        },
        "SI": {
            "D9": 3,
        },
    }
}


def get_range_index(percentage):
    p = int(percentage)

    for x, r in enumerate(reversed(DEFAULT_RANGES)):
        if (p >= r[0]) and (p <= r[1]):
            # return x + 1
            return x

    return len(DEFAULT_RANGES) + 1


def get_range_index_2022(percentage):
    p = int(percentage)

    for x, r in enumerate(reversed(DEFAULT_RANGES_2022)):
        if (p >= r[0]) and (p <= r[1]):
            # return x + 1
            return x

    return len(DEFAULT_RANGES_2022) + 1


def scoring_based(answers, scores):
    raw_scores = []
    for answ in answers:
        # if the answer is not available
        # eg. 'Not relevant' was removed, get the score from the last option
        try:
            score = scores[answ]
        except:
            score = scores[-1]

        if score == '/':
            continue

        raw_scores.append(float(score))

    return raw_scores


def get_overall_conclusion(concl_score):
    if concl_score == '-':  # not relevant
        return '-', CONCLUSIONS[0]

    if concl_score > 100:
        return 1, 'Error'

    score = get_range_index(concl_score)
    conclusion = list(reversed(CONCLUSIONS))[score]

    return score, conclusion


def get_overall_conclusion_2022(concl_score):
    if concl_score == '-':  # not relevant
        return '-', CONCLUSIONS_2022[0]

    if concl_score > 100:
        return 1, 'Error'

    score = get_range_index_2022(concl_score)
    conclusion = list(reversed(CONCLUSIONS_2022))[score]

    return score, conclusion


class OverallScores(object):
    """ Class used to store the score for each phase
    """

    def __init__(self, article_weights, article=None):
        self.article_weights = article_weights
        _init = {
            'score': 0,
            'max_score': 0,
            'conclusion': 'Not reported',
            'color': 0,
        }
        if not article:
            phases = list(article_weights.values())[0].keys()
        else:
            phases = article_weights[article].keys()

        for phase in phases:
            d = {}
            d.update(_init)
            setattr(self, phase, d)

    def get_overall_score(self, article, is_national=True):
        """ Overall conclusion art. XX: 2018

        :return: 80
        """
        if article in ('Art3', 'Art4'):
            return self.get_overall_score_secondary(article)

        if article in ('Art13', 'Art14', 'Art13Completeness',
                       'Art14Completeness', 'Art1314CrossCutting'):
            return self.get_overall_score_2022(article)

        overall_score = 0
        max_score = 0
        overall_max = 0
        weights = self.article_weights[article]

        for phase in weights:
            score = self.get_score_for_phase(phase)
            max_phase_score = getattr(self, phase)['max_score']
            overall_score += score * weights[phase]
            max_score += max_phase_score * weights[phase]
            if max_phase_score > 0:
                overall_max += weights[phase] * 100

        if max_score == 0:  # all phases not relevant
            return '-', '-'

        # adequacy and consistency are not relevant -> overall is not relevant
        # ONLY for National scores, for Regional this rule is not used
        if (is_national
            and self.adequacy['score'] == 0 and self.consistency['score'] == 0
            and self.adequacy['max_score'] == 0
                and self.consistency['max_score'] == 0):

            return '-', '-'

        # check if adequacy and consistency scores are 0
        # and they are not 'Not relevant'
        # if both are 0, overall score is 0 regardless of coherence
        if (self.adequacy['score'] == 0 and self.consistency['score'] == 0
            and (self.adequacy['max_score'] > 0
                 or self.consistency['max_score'] > 0)):

            overall_score = 0

        # in cases when adequacy/consistency or coherence is not relevant
        # final_score = int(round(overall_score))
        final_score = int(round((overall_score / overall_max) * 100))

        return get_range_index(final_score), final_score

    def get_overall_score_secondary(self, article):
        """ Overall conclusion art. XX: 2018

        :return: 80
        """

        score_achieved = 0
        max_score = 0
        weights = self.article_weights[article]

        for phase in weights:
            _score = getattr(self, phase)['score']
            _max_score = getattr(self, phase)['max_score']

            score_achieved += _score
            max_score += _max_score

        overall_score = int(round(
            max_score and (score_achieved * 100) / max_score or 0
        ))

        return get_range_index(overall_score), overall_score

    def get_overall_score_2022(self, article):
        """ Overall conclusion art. XX: 2018

        :return: 80
        """

        score_achieved = 0
        max_score = 0
        weights = self.article_weights[article]

        for phase in weights:
            _score = getattr(self, phase)['score']
            _max_score = getattr(self, phase)['max_score']

            try:
                score_achieved += _score
            except:
                pass

            max_score += _max_score

        overall_score = int(round(
            max_score and (score_achieved * 100) / max_score or 0
        ))

        if max_score == 0:  # all phases not relevant
            return 5, '-'
        
        return get_range_index_2022(overall_score), overall_score

    def conclusion(self, phase):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """
        if self.question.article in ('Art13', 'Art14', 'Art13Completeness',
                                'Art14Completeness', 'Art1314CrossCutting'):
            return self.conclusion_2022(phase)

        score_value = self.get_range_index_for_phase(phase)

        if score_value == 0 and phase == 'consistency':
            return 'Not consistent'

        concl = list(reversed(CONCLUSIONS))[score_value]

        return concl

    def conclusion_2022(self, phase):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """
        score_value = self.get_range_index_for_phase(phase)

        concl = list(reversed(CONCLUSIONS_2022))[score_value]

        return concl

    def get_score_for_phase(self, phase):
        # max_score ............. 100%
        # score ................. x%

        score = getattr(self, phase)['score']
        max_score = getattr(self, phase)['max_score']

        return int(round(max_score and (score * 100) / max_score or 0))

    def get_range_index_for_phase(self, phase, article=None):
        score = self.get_score_for_phase(phase)

        if article and article in ('Art13', 'Art14', 'Art13Completeness',
                                   'Art14Completeness', 'Art1314CrossCutting'):
            return get_range_index_2022(score)

        return get_range_index(score)

    def score_tooltip(self, phase):
        score = getattr(self, phase)['score']
        max_score = getattr(self, phase)['max_score']
        final_score = self.get_score_for_phase(phase)

        text = \
            "<b>Score achieved</b>: {} (Sum of the scores from each question)"\
            "</br><b>Max score</b>: {} (Maximum possible score: sum of the " \
            "weights from each question, excluding <b>Not relevant</b> " \
            "questions)" \
            "</br><b>Final score</b>: {} (<b>Score achieved</b> * 100 / " \
            "<b>Max score<b/>)" \
            .format(score, max_score, final_score)

        return text

    def score_tooltip_overall_secondary(self, article):
        weights = self.article_weights[article]
        overall_color, overall_score_val = self.get_overall_score(article)

        score_achieved = 0
        max_score = 0

        for phase in weights:
            _score = getattr(self, phase)['score']
            _max_score = getattr(self, phase)['max_score']

            score_achieved += _score
            max_score += _max_score

        text = \
            "<b>Score achieved</b>: {} (Sum of the scores from each question)"\
            "</br><b>Max score</b>: {} (Maximum possible score: sum of " \
            "the weights from each question, excluding " \
            "<b>Not relevant</b> questions)" \
            "</br><b>Final score</b>: {} (<b>Score achieved</b> * 100 / " \
            "<b>Max score</b>)" \
            .format(score_achieved, max_score, overall_score_val)

        return text

    def score_tooltip_overall_regional(self, article):
        weights = self.article_weights[article]
        co_wght = int(weights['coherence'] * 100)
        overall_color, overall_score_val = self.get_overall_score(article)

        text = "<b>Coherence weight</b>: {}" \
               "</br><b>Final score</b>: {} (<b>Coherence</b> score)" \
               .format(co_wght,
                       overall_score_val)

        return text

    def score_tooltip_overall(self, article):
        overall_max = 0
        weights = self.article_weights[article]
        ad_wght = int(weights['adequacy'] * 100)
        cn_wght = int(weights['consistency'] * 100)
        co_wght = int(weights['coherence'] * 100)
        ad_score = self.get_score_for_phase('adequacy')
        cn_score = self.get_score_for_phase('consistency')
        co_score = self.get_score_for_phase('coherence')
        ad_max = getattr(self, 'adequacy')['max_score']
        cn_max = getattr(self, 'consistency')['max_score']
        co_max = getattr(self, 'coherence')['max_score']
        overall_max += ad_max and weights['adequacy'] * 100 or 0
        overall_max += cn_max and weights['consistency'] * 100 or 0
        overall_max += co_max and weights['coherence'] * 100 or 0
        overall_color, overall_score_val = self.get_overall_score(article)

        text = "<b>Adequacy weight</b>: {0}" \
               "</br><b>Consistency weight</b>: {1}" \
               "</br><b>Coherence weight</b>: {2}" \
               "</br> <b>Overall max score</b>: {10}" \
               "</br></br><b>Final score</b>: {3} (Adequacy score * " \
               "Adequacy weight + Consistency score * Consistency weight + " \
               "Coherence score * Coherence weight) / {10}" \
               "</br>({4}*{5} + {6}*{7} + {8}*{9}) / {10}" \
               .format(ad_wght, cn_wght, co_wght,
                       overall_score_val,
                       ad_score, ad_wght, cn_score, cn_wght, co_score, co_wght,
                       int(overall_max))

        return text

    def score_tooltip_overall_2022(self, article):
        overall_max = 0
        weights = self.article_weights[article]
        ad_wght = int(weights['adequacy'] * 100)
        cn_wght = int(weights['completeness'] * 100)
        co_wght = int(weights['coherence'] * 100)
        ad_score = self.get_score_for_phase('adequacy')
        cn_score = self.get_score_for_phase('completeness')
        co_score = self.get_score_for_phase('coherence')
        ad_max = getattr(self, 'adequacy')['max_score']
        cn_max = getattr(self, 'completeness')['max_score']
        co_max = getattr(self, 'coherence')['max_score']
        overall_max += ad_max and weights['adequacy'] * 100 or 0
        overall_max += cn_max and weights['completeness'] * 100 or 0
        overall_max += co_max and weights['coherence'] * 100 or 0
        overall_color, overall_score_val = self.get_overall_score(article)

        text = "<b>Adequacy weight</b>: {0}" \
               "</br><b>Completeness weight</b>: {1}" \
               "</br><b>Coherence weight</b>: {2}" \
               "</br> <b>Overall max score</b>: {10}" \
               "</br></br><b>Final score</b>: {3} (Adequacy score * " \
               "Adequacy weight + Completeness score * Completeness weight + " \
               "Coherence score * Coherence weight) / {10}" \
               "</br>({4}*{5} + {6}*{7} + {8}*{9}) / {10}" \
               .format(ad_wght, cn_wght, co_wght,
                       overall_score_val,
                       ad_score, ad_wght, cn_score, cn_wght, co_score, co_wght,
                       int(overall_max))

        return text


class Score(object):
    """ Class used to store scores for each question
    """

    # set specific weights for some of the countries
    country_weights = COUNTRY_WEIGHTS

    def __init__(self, question, descriptor, values, country_code=None):
        """
        :param question: instance of AssessmentQuestionDefinition
        :param descriptor: 'D5'
        :param values: index of the options selected for the question
            ex. [3, 0, 5, 2]
        """
        self.descriptor = descriptor
        self.question = question
        self.weight = self.get_weight(question, descriptor, country_code)
        self.values = values
        self.scores = question.scores

    def get_weight(self, question, descriptor, country_code):
        """ Get the weight for the question"""
        weight_from_xml = float(question.score_weights.get(descriptor, 10.0))
        weight_for_country = self.country_weights.get(question.id, {}).get(
            country_code, {}).get(descriptor, None)

        try:
            weight_for_country = float(weight_for_country)
        except (TypeError, ValueError):
            weight_for_country = None

        return (weight_for_country if weight_for_country is not None 
                else weight_from_xml)

    @property
    def is_not_relevant(self):
        """ If all options selected are 'Not relevant' return True

        :return: True or False
        """
        if not self.values:
            return False

        answers = [self.scores[answ] for answ in self.values]

        return answers.count('/') == len(self.values)

    @property
    def raw_scores(self):
        """ Currently calls scoring_based function, and returns the raw scores
        based on the options selected for the question

        :return: list of floats [1.0, 0.25, 0, 0.75]
        """
        rs = self.question.score_method(self.values, self.scores)

        return rs

    @property
    def score_achieved(self):
        """ Sum of all raw scores

        :return: 1.5
        """

        return sum(self.raw_scores)

    @property
    def max_score(self):
        """ Maximum possible score

        :return: 5
        """

        return len(self.raw_scores)

    @property
    def percentage(self):
        """ Calculate the percentage from raw scores

        # max_score ... 100%
        # raw_score ... x

        :return: float 53.25
        """

        # All answers are 'Not relevant'
        if self.max_score == 0:
            return '-'

        percentage = (self.score_achieved * 100) / self.max_score

        return float("{0:.1f}".format(percentage))

    @property
    def score_value(self):
        """ Get the score value from percentage, only used to get conclusion

        :return: integer from range 1-4
        """

        # All answers are 'Not relevant'
        if self.percentage == '-':
            return 5

        sv = get_range_index(self.percentage)

        return sv

    @property
    def conclusion(self):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """

        if self.question.article in ('Art13', 'Art14', 'Art13Completeness',
                                'Art14Completeness', 'Art1314CrossCutting'):
            concl = list(reversed(CONCLUSIONS_2022))[self.score_value]
        else:
            concl = list(reversed(CONCLUSIONS))[self.score_value]

        return concl

    @property
    def weighted_score(self):
        """ Calculate the weighted score

        :return: float 7.5
        """
        ws = self.score_achieved * self.weight

        return ws

    @property
    def max_weighted_score(self):
        """ Calculate the maximum possible weighted score

        :return: float 7.5
        """
        ws = len(self.raw_scores) * self.weight

        return ws

    @property
    def final_score(self):
        if self.max_score == 0:
            return 0

        ws = (self.percentage * self.weight) / 100

        return ws

    @property
    def score_tooltip(self):
        if self.is_not_relevant:
            return "All selected options are 'Not relevant', therefore " \
                   "the question is not accounted when calculating the " \
                   "overall scores"

        raw_score = ' + '.join(str(x) for x in self.raw_scores)

        text = \
            '<b>Weight</b>: {}' \
            '</br><b>Max score</b>: {} (number of answered criterias/targets ' \
            'excluding answers where option selected is "Not relevant")' \
            '</br><b>Score achieved</b>: {} (Sum of the scores {})' \
            '</br><b>Percentage</b>: {} (<b>Score achieved</b> * 100 / ' \
            '<b>Max score</b>)' \
            '</br><b>Weighted score</b>: {} (Final score ' \
            '<b>Percentage</b> * <b>Weight</b> / 100)' \
            .format(self.weight, self.max_score, self.score_achieved,
                    raw_score, self.percentage, self.final_score)

        # '</br><b>Max weighted score</b>: {} (Maximum possible weighted ' \
        # 'score <b>Weight</b> * <b>Max score</b>)' \

        return text
