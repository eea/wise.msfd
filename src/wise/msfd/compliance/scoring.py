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

    return (len(trues) * 100) / len(values)


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

        for x, r in enumerate(reversed(DEFAULT_RANGES)):
            if (p >= r[0]) and (p <= r[1]):
                return x

        # TODO: offer default value here as return?

    return calculate


def compute_score(definition, method, args, values):
    # all scores are percentage based, so we can rely on

    raw_score = method(args)

    score = definition[raw_score]
    # this is an option score, with text and score attribute

    return score
