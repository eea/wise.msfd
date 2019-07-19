
# def alternative_based(args):
#     true_values = map(int, filter(None, args.strip().split(' ')))
#
#     def calculate(values):
#         acc = []
#
#         for v in values:
#             if v in true_values:
#                 acc.append(True)
#             else:
#                 acc.append(False)
#
#         p = get_percentage(acc)
#
#         range_index = get_range_index(p)
#
#         return range_index
#
#     return calculate

# scores = [4, 3, 2, 1, 0]

# def percentage_based(args):
#     def calculate(value):
#         if value:
#             max_score = len(value) * scores[0]
#             current_score = sum([scores[x] for x in value])
#
#             # max ...... 100%
#             # curent ... x%
#
#             p = (current_score * 100) / max_score
#
#             range_index = get_range_index(p)
#
#             return range_index
#
#         return len(DEFAULT_RANGES) + 1
#
#     return calculate

# def get_percentage(values):
#     """ Compute percentage of True values in the list
#     """
#
#     if not values:
#         return 0
#
#     trues = len([x for x in values if x is True])
#
#     return (trues * 100.0) / len(values)

# def compute_score(question, descriptor, values):
#     weight = float(question.score_weights.get(descriptor, 10.0))
#     scores = question.scores
#     raw_scores = question.score_method(values, scores)
#
#     if not raw_scores:
#         score_value = 4
#     else:
#         percentage = calculate_percentage(raw_scores)
#         score_value = get_range_index(percentage)
#
#     # TODO find a proper algorithm to calculate wighted score
#     weighted_score = score_value * weight / 4
#     conclusion = list(reversed(CONCLUSIONS))[score_value]
#
#     return conclusion, score_value, weighted_score

# 2012 old conclusions, not used
# OVERALL_CONCLUSIONS = [
#     'Good practice',
#     'Adequate',
#     'Partially adequate',
#     'Inadequate',
#     'Not reported',
# ]

# def calculate_percentage(raw_scores):
#     # max_score ... 100%
#     # raw_score ... x
#
#     raw_score = sum(raw_scores)
#     max_score = len(raw_scores)
#
#     percentage = (raw_score * 100) / max_score
#
#     return float(percentage)

# from wise.msfd.compliance.base import BaseComplianceView


DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [0, 25],
]


CONCLUSIONS = [
    'Very good (4)',
    'Good (3)',
    'Poor (2)',
    'Very poor (1)',
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


class Score(object):
    def __init__(self, question, descriptor, values):
        self.descriptor = descriptor
        self.question = question
        self.weight = float(question.score_weights.get(descriptor, 10.0))
        self.values = values
        self.scores = question.scores

    @property
    def raw_scores(self):
        """ Currently calls scoring_based function, and returns the raw scores
        based on the options selected for the question

        :return: list of floats [1.0, 0.25, 0, 0.75]
        """
        rs = self.question.score_method(self.values, self.scores)

        return rs

    @property
    def max_score(self):
        return len(self.raw_scores)

    @property
    def percentage(self):
        """ Calculate the percentage from raw scores

        # max_score ... 100%
        # raw_score ... x

        :return: float 53.25
        """
        if self.max_score == 0:
            return 100

        raw_score = sum(self.raw_scores)
        percentage = (raw_score * 100) / self.max_score

        return float("{0:.1f}".format(percentage))

    @property
    def score_value(self):
        """ Get the score value from percentage

        :return: integer from range 1-4
        """
        sv = get_range_index(self.percentage)

        return sv

    @property
    def conclusion(self):
        """ Get the conclusion text from score_value

        :return: string 'Very good'
        """
        concl = list(reversed(CONCLUSIONS))[self.score_value]

        return concl

    # TODO find a proper algorithm to calculate wighted score
    @property
    def weighted_score(self):
        """ Calculate the weighted score

        :return: float 7.5
        """
        ws = self.score_value * self.weight / 4

        return ws

    @property
    def score_tooltip(self):
        raw_score = ' + '.join(str(x) for x in self.raw_scores)

        percentage = '(sum of raw_scores / max_score) * 100</br>' \
                     '(({}) / {}) * 100 = {}%' \
            .format(raw_score, self.max_score, self.percentage)

        if self.max_score == 0:
            percentage = "All selected options are 'Not relevant', therefore "\
                         "100% percentage is accorded"

        score_value = '{}% percentage translates to score value {} (out of 4)'\
                      ' meaning "{}"'\
            .format(self.percentage, self.score_value, self.conclusion)

        weighted_score = '({} * {}) / 4 = {}'\
            .format(self.score_value, self.weight, self.weighted_score)

        return '<b>Percentage calculation</b></br>' \
               '{}</br></br>' \
               '{}</br></br>' \
               '<b>Weighted score calculation</b></br>' \
               '(score_value * weight) / 4<br>' \
               '{}' \
            .format(percentage, score_value, weighted_score)