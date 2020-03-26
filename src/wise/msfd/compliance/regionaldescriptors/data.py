from pkg_resources import resource_filename

from wise.msfd.compliance.utils import ReportDefinition


definition_files = {
    '2018': 'data/report_2018_def.xml',
    # '2012': 'data/report_2012_def.xml',
}

# f_2012 = resource_filename(__package__, definition_files['2012'])
f_2018 = resource_filename(__package__, definition_files['2018'])


REPORT_DEFS = {
    '2018': {
        'Art8': ReportDefinition(f_2018, 'Art8'),
        'Art9': ReportDefinition(f_2018, 'Art9'),
        'Art10': ReportDefinition(f_2018, 'Art10'),
    },
    '2012': {
        #     'Art8a': ReportDefinition(f_2012, 'Art8a'),
        #     'Art8b': ReportDefinition(f_2012, 'Art8b'),
        #     'Art9': ReportDefinition(f_2012, 'Art9'),
        #     'Art10': ReportDefinition(f_2012, 'Art10'),
    }
}


def get_report_definition(year, article):
    return REPORT_DEFS[year][article]
