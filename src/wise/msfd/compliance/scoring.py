DEFAULT_RANGES = [
    [76, 100],
    [51, 75],
    [26, 50],
    [1, 25],
    [0, 1],
]


def get_percentage(values):
    """ Compute percentage of True values in the list
    """
    trues = len([x for x in values if x is True])

    return (trues * 100.0) / len(values)


def get_range_index(percentage):
    p = percentage
    
    for x, r in enumerate(reversed(DEFAULT_RANGES)):
        if (p >= r[0]) and (p <= r[1]):
            return x
        
    return len(DEFAULT_RANGES) + 1
        

def alternative_based(args):
    true_values = map(int, filter(None, args.strip().split(' ')))

    def calculate(values):
        acc = []

        for v in values:
            if v in true_values:
                acc.append(True)
            else:
                acc.append(False)

        p = get_percentage(acc)

        range_index = get_range_index(p)
        
        return range_index

    return calculate


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
    raw_score = question.score_method(values)

    weight = float(question.score_weights.get(descriptor, 10.0))
    score = raw_score * weight / 4
    conclusion = list(reversed(CONCLUSIONS))[raw_score]

    return conclusion, raw_score, score
