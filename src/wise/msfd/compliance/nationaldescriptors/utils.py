from collections import defaultdict

from sqlalchemy import and_, or_

from wise.msfd import db, sql, sql2018


def row_to_dict(table, row):
    cols = table.c.keys()
    res = {k: v for k, v in zip(cols, row)}

    return res


@db.use_db_session('2012')
def get_indicator_descriptors(muids, available_indicators):
    """ Get data based on Marine Units and available indicators

    :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
    :param available_indicators: ['5.2.2-indicator 5.2C',
                                  '5.2.1- indicator 5.2B']
    :return: table result
    """
    # TODO: sort the results based on ascending muid?
    count, res = db.get_all_records(
        sql.MSFD9Descriptor,
        sql.MSFD9Descriptor.MarineUnitID.in_(muids),
        sql.MSFD9Descriptor.ReportingFeature.in_(available_indicators)
    )

    return res


@db.use_db_session('2012')
def get_indicators_with_feature_pressures(muids, criterions):
    """ Get a dict with all indicators and their corresponding features

    :param muids: ['BAL- LV- AA- 001', 'BAL- LV- AA- 002', ...]
    :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    :return: {'5.2.2-indicator 5.2C': ['Transparency', 'InputN_Psubst'],
             {'5.2.1- indicator 5.2B': ['InputN_Psubst',
                                        'FunctionalGroupOther'],
              ...}
    """

    t = sql.t_MSFD9_Features
    count, res = db.get_all_records(
        t,
        t.c.MarineUnitID.in_(muids),
    )
    res = [row_to_dict(t, r) for r in res]

    indicators = defaultdict(set)

    for row in res:
        rf = row['ReportingFeature']
        indicators[rf].add(row['FeaturesPressuresImpacts'])

    res = {}

    for k, v in indicators.items():
        flag = False

        for crit in criterions:
            if k.startswith(crit):
                flag = True

        if flag:
            res[k] = v

    return res


@db.use_db_session('2012')
def get_all_criterions(descriptor):
    """ Get all criterions(indicators) + descriptor, for a descriptor

    :return: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    """
    nr = descriptor[1:]
    m = sql.MSFDFeaturesOverview
    res = db.get_unique_from_mapper(
        m,
        'RFCode',
        or_(
            and_(m.RFCode.like('{}.%'.format(nr)),
                 m.FeatureType == 'GES criterion',),
            and_(m.RFCode.like('{}'.format(descriptor)),
                 m.FeatureType == 'GES descriptor')
        ),
        m.FeatureRelevant == 'Y',
        m.FeatureReported == 'Y',
    )

    return res


@db.use_db_session('2012')
def get_criterion_labels(criterions, descriptor, descriptor_label):
    """ Get all labels for the criterions

    :param criterions: ['D5', '5.1', '5.2', ..., '5.1.2', '5.2.4', ...]
    :return: [('5.1', '5.1: Nutrients levels'),
              ('5.1.2', '5.1.2: Nutrient ratios (silica'),
              (...)]
    """

    count, res = db.get_all_records(
        sql.MSFD11CommonLabel,
        sql.MSFD11CommonLabel.value.in_(criterions),
        sql.MSFD11CommonLabel.group.in_(('list-GESIndicator',
                                         'list-GESCriteria')),
    )

    criterion_labels = dict([(x.value, x.Text) for x in res])
    # add D5 criterion to the criterion lists too
    criterion_labels[descriptor] = descriptor_label

    return criterion_labels


def get_sorted_fields_2018(fields, article):
    sorted_fields = {
        'Art10': ('TargetCode', 'Description', 'GESComponents',
                  'TimeScale', 'UpdateDate', 'UpdateType', 'Measures',
                  'Element', 'Element2', 'Parameter', 'ParameterOther',
                  'TargetValue', 'ValueAchievedUpper', 'ValueAchievedLower',
                  'ValueUnit', 'ValueUnitOther', 'TargetStatus',
                  'AssessmentPeriod', 'ProgressDescription', 'Indicators'),
        'Art9': ('GESComponent', 'GESDescription', 'JustificationNonUse',
                 'JustificationDelay', 'DeterminationDate', 'UpdateType'),
        'Art8': ('Element', 'ElementCode', 'ElementCodeSource',
                 'Element2', 'Element2Code', 'Element2CodeSource',
                 'ElementSource', 'Criteria', 'Parameter', 'ParameterOther',
                 'ThresholdValueUpper', 'ThresholdValueLower',
                 'ThresholdQualitative', 'ThresholdValueSource',
                 'ThresholdValueSourceOther',
                 'ValueAchievedUpper', 'ValueAchievedLower', 'ValueUnit',
                 'ValueUnitOther', 'ProportionThresholdValue',
                 'ProportionValueAchieved', 'ProportionThresholdValueUnit',
                 'Trend', 'ParameterAchieved', 'DescriptionParameter',
                 'IndicatorCode', 'CriteriaStatus', 'DescriptionCriteria',
                 'ElementStatus', 'DescriptionElement',
                 'IntegrationRuleTypeParameter',
                 'IntegrationRuleDescriptionParameter',
                 'IntegrationRuleDescriptionReferenceParameter',
                 'IntegrationRuleTypeCriteria',
                 'IntegrationRuleDescriptionCriteria',
                 'IntegrationRuleDescriptionReferenceCriteria',
                 'GESExtentThreshold', 'GESExtentAchieved', 'GESExtentUnit',
                 'GESAchieved', 'DescriptionOverallStatus',
                 'AssessmentsPeriod',
                 'PressureCode',  # RelatedPressures
                 # Related activities, Does not have field in DB view
                 'TargetCode',  # RelatedTargets

                 # NOT used fields
                 # 'GESComponent',
                 # 'Feature',
                 )
    }

    sf = sorted_fields.get(article, None)
    if not sf:
        return fields

    diff = set(fields) - set(sf)
    final = list(diff) + list(sf)

    return final
