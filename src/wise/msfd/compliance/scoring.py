
DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [0, 25],
    # [0, 0]
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
            return x + 1

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
            'conclusion': '',
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

        overall_score = 0
        weights = self.article_weights[article]

        for phase in weights:
            score = self.get_score_for_phase(phase)
            overall_score += score * weights[phase]

        overall_score = int(overall_score)

        return get_range_index(overall_score), overall_score

    def conclusion(self, phase):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """
        score_value = self.get_range_index_for_phase(phase)
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
        """ TODO not used """

        score = getattr(self, phase)['score']
        max_score = getattr(self, phase)['max_score']
        final_score = self.get_score_for_phase(phase)

        text = \
            "<b>Score achieved</b>: {} (Sum of the final scores " \
            "from each questions)" \
            "</br><b>Max score</b>: {} (Maximum possible score)" \
            "</br><b>Final score</b>: {} (Final calculated score " \
            "(<b>Score achieved</b> / <b>Max score</b>) * 100)" \
            .format(score, max_score, final_score)

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
            '</br><b>Max weighted score</b>: {} (Maximum possible weighted ' \
            'score <b>Weight</b> * <b>Max score</b>)' \
            '</br><b>Weighted score</b>: {} (Final calculated score ' \
            '<b>Score achieved</b> * <b>Weight</b>)' \
            .format(self.weight, self.max_score, self.score_achieved,
                    raw_score, self.max_weighted_score, self.weighted_score)

        return text

# A10Ad1 A0810Cy1 A08Ad4 A09Ad1 A09Ad2
