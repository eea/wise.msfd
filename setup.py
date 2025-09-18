# -*- coding: utf-8 -*-
"""Installer for the wise.content package."""

import os
from os.path import join
from setuptools import setup, find_packages

NAME = 'wise.msfd'
PATH = ['src'] + NAME.split('.') + ['version.txt']
VERSION = open(join(*PATH)).read().strip()

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
    open(os.path.join("docs", "HISTORY.txt")).read()
])

setup(
    name=NAME,
    version=VERSION,
    description="WISE MSFD",
    long_description_content_type="text/x-rst",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone',
    author='"EEA: IDM2 S-Team"',
    author_email='Christian.Prosperini@eea.europa.eu',
    url='https://pypi.python.org/pypi/wise.msfd',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['wise'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'plone.api',
        'plone.app.contenttypes',
        'zope.sqlalchemy==2.0',
        'pymssql==2.2.8',
        'SQLAlchemy==1.4.46',
        'sparql-client',
        # 'pyodbc',
        'langdetect',  # used in translations
        # 'pyexcel-xlsx',
        'z3c.formwidget.optgroup',  # used in compliance select lists
        'eea.cache',        # generic caching solution
        'Products.CMFPlacefulWorkflow',
        # from wise.theme
        'Products.GenericSetup>=1.8.2',
        'z3c.jbot',
        'plone.app.theming',
        # 'plone.app.themingplugins',
        # 'plone.app.robotframework',
        'plone.app.testing',
        'eea.api.dataconnector',
        # 'webcouturier.dropdownmenu',
        'robotsuite',
        'pyexcel==0.6.7',
        'pyexcel-xlsx==0.6.0',
        'openpyxl==3.0.10',
        'pdfkit',
        'dnspython===2.7.0'

    ],
    extras_require={
        'test': [
            'plone.app.testing',
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            'plone.testing>=5.0.0',
            'plone.app.contenttypes',
            # 'plone.app.robotframework[debug]',

        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
