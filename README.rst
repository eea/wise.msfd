=========
wise.msfd
=========

WISE Marine Directive Strategy Framework implementation

Features at end of Phase 2:

Search engine for MSFD reported data
------------------------------------

Integrates with two MSSQL databases and allows searching and visualizing data
from the various reporting exercises: Article 4, 7, 8, 9, 10, 11, 13, 14 from
2012 and Art 8, 9 and 10 from 2018 reporting. The search engine is available
at https://water.europa.eu/marine/data/msfd-data

Allows navigation between types of information. Main Sections:

  - Article 7 (Competent authorities)
  - Articles 4, 8, 9, 10 - 2012
  - Article 11 - 2014
  - Articles 13 & 14 - 2015
  - Article 8, 9 & 10 - 2018

Generic features when displaying the records:

  - because the member states used ad-hoc text formats to input their reports,
    we have to interpret that text and try to re-format it for HTML (blank
    lines to be converted to paragraphs, autodetect links, etc).
  - there are 2 types of filtering widgets: single selection and
    multiselection. The single selection widget allows searching for text,
    while the multi-selection widget allows searching for text, clearing the
    selection, invert selection, select all, apply filters button.
  - persistent search filters: when navigating to a different page and coming
    back to the search engine, the filters are preserved, using the browser's
    local storage.
  - AJAX based loading of information, to avoid hard refreshes of browser pages
  - Caching of information at the server level, to optimize page load speed
  - Download a collection of filtered records as Excel, where they are
    presented grouped in worksheets, per type of included feature.
  - Present human readable labels for the short codes stored as values in the
    database

Article 7 section
~~~~~~~~~~~~~~~~~

Show the competent authorities records. Offers pagination and filtering based
on countries.

Articles 4, 8, 9, 10 - 2012
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Article 4** shows the Geographical areas primary information, the area
description and related regional cooperation information. Allows filtering
information by region and subregion, countries and area type.

**Article 8.1a** shows the Analysis of the Environment information. The
information here can be filtered, in addition to the usual Region and
subregion, Countries, Area type, MarineUnitID, also by the theme (a total of 7
themes): Ecosystem, Habitats, etc, and the displayed information has the
related records of information displayed there.

**Article 8.1b** shows the Analysis of the pressure impacts. The information
here can be filtered, in addition to the usual Region and subregion, Countries,
Area type, MarineUnitID, also by the theme (a total of 13 themes):
Acidification, Marine litter, etc, and the displayed information has the
related records of information displayed there.

**Article 8.1c** shows the Economic and social analysis records. The
information here can be filtered by Region and subregion, Countries,
Area type, MarineUnitID and displays related information of "Pressures produced
by the activities"

**Article 9** shows GES determination information. The information here can be
filtered by the usual filters and offers additional Feature Types information.

**Article 10** shows targets information, with Feature Types and Criteria
Indicators as additional information.

Article 11
~~~~~~~~~~
Presents the monitoring programmes information, with various related elements
and concerned marine unit ids. It allows filtering for Monitoring Programme
Type, and Information Type (monitoring programm or subprogram), in addition to
the regular region, countries and marine unit ids filters.

Articles 13 & 14
~~~~~~~~~~~~~~~~
This is where the reported information can be viewed, where we can filter by
Report Type, Regions, Countries, MarineUnitIds and Unique Codes of the reports.
The reports are presented with related information about the report type,
report URL, Relevant Environment Targets, Links to existing policies, Spatial
Scope Geographic Zones, KTM, Relevant GES Descriptors and Relevant Features
from Annex 3.

Articles 8, 9, 10 - 2018 version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here we display the recorded information from 2018 reports. We have Article 10
(Targets), the Article 8.1ab (GES Assessments), Article 8.1c (ESA assessments),
Article 9 (GES Determination) and the Indicators pages. Each page allows
filtering and displays relevant information.

Article 8.1ab
~~~~~~~~~~~~~
Displays the GES Assessments information with related pressure and target
codes, element and criteria statuses, criteria values and criteria value
indicators. Allows filtering information by MarineUnitID, Country Code,
Features and GES Component.

Artiticle 8.1c
~~~~~~~~~~~~~~
Display the ESA assessments information. Filtering can be done by MarineUnitID,
Country Code, Features and GES Component.

Article 9
~~~~~~~~~
Displays GES determination information, GES description, the determination
date, update type. The information here can be filtered by MarineUnitID,
Country Code, GES Component, and Features.

Article 10
~~~~~~~~~~
Displays the targets and associated indicators, target codes, description, time
scale, update date, update type and parameters. The information can be filtered
by MarineUnitID, Country Code, Features and GES Component.


Compliance Assessment module
----------------------------

This module facilitates the assessment of MSFD reported information.

Features:

Bootstrap process
~~~~~~~~~~~~~~~~~
We have a bootstrap process that creates the necessary Plone content:
compliance modules folders (national descriptors, regional descriptors, etc),
the country folders (one for each participating member state), inside the
country folders there are folders for each region, then we have a folder for
each descriptor, with children folders for each assessed article and finally
two folders per article assessment, that hold the tracks of comments. During
bootstraping the proper security access is also setup, with integration to
dedicated Eionet groups.

Navigation
~~~~~~~~~~
- navigation to sections: Start page, National Descriptors assessment section,
  Regional descriptors section, National overviews, Regional overviews.


National descriptors section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- In the National descriptors section, we can navigate to each country and see
  the color coded overview of the assessment phase of that country's assessment.

- In the member state's national descriptor assessment overview page, we have
  the Proces state overview, with security-based workflow state change, and
  a descriptor-based access and status overview of all articles (Art8, Art9,
  Art10), all grouped by regions.

National descriptor Article assessment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Article assessment overview page we have navigation links to all the
relevant pages for that assessment:

  - 2012 Report Data,
  - 2018 Report Data,
  - Edit the Assessment
  - and finally a security-based workflow state change dropdown.

The assessment overview shows two overview sections:

  - one for the 2012 assessment and
  - one for the 2018 assessment.

In the 2018 assessment overview we have an overview of each question, with 
color-coded values for each involved criterion and calculates a score based on 
descriptor-appropriate weighting tables. It also shows:

  - the assessment summary
  - the recommendations
  - and allows the editing of the progress assessment field.

It calculates the overall score on all the questions in this descriptor
assessment and a difference to the previous assessment score.

The 2012 assessment overview is similar, but doesn't have individual questions
attached to the criterions.

At the bottom we have the two discussion tracks: one for the Compliance Module
reviewers (Milieu) to the assigned Topic Lead, and another for the Milieu with
EC. Each type of user can add comments only in its available comments section.

The Edit Assessment page allows the Topic Leads to enter their assessment
answers: for each assessment question they are asked to choose answers from
a series of dropdowns, one for each available criterion for that question. They
can also enter a summary text for each question and an overall assessment
summary and recommendations for that Member state. The form also makes
available a popup window with the criteria definition relevant to that
descriptor and also shows tooltips with criteria definitions next to each
dropdown in the questions form.

The questions for each article are defined in a separate XML file, with all
possible answers, information about the scoring method used and weighting for
each descriptor.

The 2018 report data page uses several backend implementation to adjust its
displayed data according to the type of article (8a, 8b, 9, 10) and the desired
descriptor. It shows an overview of the reported data, as extracted from the
database, with links to the original report and the HTML Factsheet offered by
the CDR converters. It also offers a link to download the report data in Excel
format.

The report tables on the 2018 page are separated by the MarineUnitIDs for
Article 8 and 10. A "simplify table" toggle is available to allow easier
understanding of the extracted information and works by merging identical
values in adjacent table cells. The database values are "translated" to human
readable labels and the original value is available as a tooltip. The left-most
column is fixed, while the rest of the columns are horizonal scrollable.

Specific data cells are available to be automatically translated by Milieu,
using a special online service provided by EC (with special security
permissions). Once translated, it is possible to toggle between the two texts
with small buttons inside the cell. It is also possible to edit the
translation.

The 2012 report data shows its information in a similar format, but needs to be
able to map the 2012 reported information using the concept of descriptors,
which were not available at that time, so it needs to map old indicators and
descriptors to the 2018 data format.
