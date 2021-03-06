
DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [1, 25],
    [0, 0],
]


CONCLUSIONS = [
    'Not relevant',
    'Very good',
    'Good',
    'Poor',
    'Very poor',
    'Not reported',
]


def get_range_index(percentage):
    p = int(percentage)

    for x, r in enumerate(reversed(DEFAULT_RANGES)):
        if (p >= r[0]) and (p <= r[1]):
            # return x + 1
            return x

    return len(DEFAULT_RANGES) + 1


def scoring_based(answers, scores):
    raw_scores = []
    for answ in answers:
        score = scores[answ]
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


class OverallScores(object):
    """ Class used to store the score for each phase
    """

    def __init__(self, article_weights):
        self.article_weights = article_weights
        _init = {
            'score': 0,
            'max_score': 0,
            'conclusion': 'Not reported',
            'color': 0,
        }

        for phase in article_weights.values()[0].keys():
            d = {}
            d.update(_init)
            setattr(self, phase, d)

    def get_overall_score(self, article):
        """ Overall conclusion art. XX: 2018

        :return: 80
        """
        if article in ('Art3', 'Art4'):
            return self.get_overall_score_secondary(article)

        overall_score = 0
        max_score = 0
        weights = self.article_weights[article]

        for phase in weights:
            score = self.get_score_for_phase(phase)
            overall_score += score * weights[phase]
            max_score += getattr(self, phase)['max_score'] * weights[phase]

        if max_score == 0:  # all phases not relevant
            return '-', '-'

        # check if adequacy and consistency scores are 0
        # and they are not 'Not relevant'
        # if both are 0, overall score is 0 regardless of coherence
        if (self.adequacy['score'] == 0 and self.consistency['score'] == 0
            and (self.adequacy['max_score'] > 0
                 or self.consistency['max_score'] > 0)
            ):
            overall_score = 0

        final_score = int(round(overall_score))

        # TODO this formula is not correct, why was it introduced
        # final_score = int(round((overall_score / max_score) * 100))

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

    def conclusion(self, phase):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """
        score_value = self.get_range_index_for_phase(phase)

        if score_value == 0 and phase == 'consistency':
            return 'Not consistent'

        concl = list(reversed(CONCLUSIONS))[score_value]

        return concl

    def get_score_for_phase(self, phase):
        # max_score ............. 100%
        # score ................. x%

        score = getattr(self, phase)['score']
        max_score = getattr(self, phase)['max_score']

        return int(round(max_score and (score * 100) / max_score or 0))

    def get_range_index_for_phase(self, phase):
        score = self.get_score_for_phase(phase)

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
            .format(score, max_score, final_score, phase)

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
        weights = self.article_weights[article]
        ad_wght = int(weights['adequacy'] * 100)
        cn_wght = int(weights['consistency'] * 100)
        co_wght = int(weights['coherence'] * 100)
        ad_score = self.get_score_for_phase('adequacy')
        cn_score = self.get_score_for_phase('consistency')
        co_score = self.get_score_for_phase('coherence')
        overall_color, overall_score_val = self.get_overall_score(article)

        text = "<b>Adequacy weight</b>: {}" \
               "</br><b>Consistency weight</b>: {}" \
               "</br><b>Coherence weight</b>: {}" \
               "</br></br><b>Final score</b>: {} (Adequacy score * " \
               "Adequacy weight + Consistency score * Consistency weight + " \
               "Coherence score * Coherence weight) / 100" \
               "</br>({}*{} + {}*{} + {}*{}) / 100" \
               .format(ad_wght, cn_wght, co_wght,
                       overall_score_val,
                       ad_score, ad_wght, cn_score, cn_wght, co_score, co_wght)

        return text


class Score(object):
    """ Class used to store scores for each question
    """

    def __init__(self, question, descriptor, values):
        """
        :param question: instance of AssessmentQuestionDefinition
        :param descriptor: 'D5'
        :param values: index of the options selected for the question
            ex. [3, 0, 5, 2]
        """
        self.descriptor = descriptor
        self.question = question
        self.weight = float(question.score_weights.get(descriptor, 10.0))
        self.values = values
        self.scores = question.scores

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
