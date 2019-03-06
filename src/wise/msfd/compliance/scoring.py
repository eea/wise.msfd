
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


DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [0, 25],
]


def calculate_percentage(raw_score, max_score):
    # max_score ... 100%
    # raw_score ... x

    percentage = (raw_score * 100) / max_score

    return float(percentage)


def get_range_index(percentage):
    p = percentage

    for x, r in enumerate(reversed(DEFAULT_RANGES)):
        if (p >= r[0]) and (p <= r[1]):
            return x + 1

    return len(DEFAULT_RANGES) + 1


def scoring_based(answers, scores):
    raw_score = 0.0
    max_score = 0
    for answ in answers:
        score = scores[answ]
        if score == '/':
            continue

        raw_score += float(score)
        max_score += 1

    return raw_score, max_score


CONCLUSIONS = [
    'Very good',
    'Good',
    'Poor',
    'Very poor',
    'Not reported',
]


OVERALL_CONCLUSIONS = [
    'Good practice',
    'Adequate',
    'Partially adequate',
    'Inadequate',
    'Not reported',
]


def get_overall_conclusion(concl_score):
    score = get_range_index(concl_score)

    conclusion = list(reversed(OVERALL_CONCLUSIONS))[score]

    return score, conclusion


def compute_score(question, descriptor, values):
    scores = question.scores
    raw_score, max_score = question.score_method(values, scores)

    percentage = calculate_percentage(raw_score, max_score)
    score_value = get_range_index(percentage)

    weight = float(question.score_weights.get(descriptor, 10.0))
    # TODO find a proper algorithm to calculate wighted score
    weighted_score = score_value * weight / 4
    conclusion = list(reversed(CONCLUSIONS))[score_value]

    return conclusion, score_value, weighted_score
