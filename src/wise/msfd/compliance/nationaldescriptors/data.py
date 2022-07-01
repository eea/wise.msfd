from __future__ import absolute_import
from pkg_resources import resource_filename

from wise.msfd.compliance.utils import ReportDefinition


definition_files = {
    '2020': 'data/report_2020_def.xml',
    '2018': 'data/report_2018_def.xml',
    '2016': 'data/report_2016_def.xml',
    '2014': 'data/report_2014_def.xml',
    '2012': 'data/report_2012_def.xml',
}

f_2012 = resource_filename(__package__, definition_files['2012'])
f_2014 = resource_filename(__package__, definition_files['2014'])
f_2016 = resource_filename(__package__, definition_files['2016'])
f_2018 = resource_filename(__package__, definition_files['2018'])
f_2020 = resource_filename(__package__, definition_files['2020'])


REPORT_DEFS = {
    '2020': {
        'Art11': ReportDefinition(f_2020, 'Art11'),
        'Art11Overview': ReportDefinition(f_2020, 'Art11Overview')
    },
    '2018': {
        'Art8': ReportDefinition(f_2018, 'Art8'),
        'Art9': ReportDefinition(f_2018, 'Art9'),
        'Art10': ReportDefinition(f_2018, 'Art10'),
        'Art3': ReportDefinition(f_2018, 'Art3'),
        'Art4': ReportDefinition(f_2018, 'Art3'),
        'Art7': ReportDefinition(f_2018, 'Art7'),
        'Art8esa': ReportDefinition(f_2018, 'Art8esa'),
    },
    '2016': {
        'Art13': ReportDefinition(f_2016, 'Art13'),
        'Art14': ReportDefinition(f_2016, 'Art14'),
    },
    '2014': {
        'Art11': ReportDefinition(f_2014, 'Art11'),
        'Art11Overview': ReportDefinition(f_2014, 'Art11Overview')
    },
    '2012': {
        'Art8a': ReportDefinition(f_2012, 'Art8a'),
        'Art8b': ReportDefinition(f_2012, 'Art8b'),
        'Art9': ReportDefinition(f_2012, 'Art9'),
        'Art10': ReportDefinition(f_2012, 'Art10'),
        'Art3': ReportDefinition(f_2012, 'Art3'),
        'Art4': ReportDefinition(f_2012, 'Art3'),
        'Art7': ReportDefinition(f_2012, 'Art7'),
        'Art8esa': ReportDefinition(f_2012, 'Art8esa'),
    }
}


def get_report_definition(year, article):
    try:
        rep_def = REPORT_DEFS[year][article]

        return rep_def

    except KeyError:
        return None
