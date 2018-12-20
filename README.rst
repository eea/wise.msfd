============
wise.msfd
============

WISE Marine Directive Strategy Framework implementation

Features at end of Phase 2:

Search engine for MSFD reported data
------------------------------------

- Integrates with two MSSQL databases and allows searching and visualizing data
  from the various reporting exercises: Article 4, 7, 8, 9, 10, 11, 13, 14 from
  2012 and Art 8, 9 and 10 from 2018 reporting. The search engine is available
  at https://water.europa.eu/marine/data/msfd-data

- Implemented navigation between information. Main Sections:
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

**Article 4** shows the Geographical areas and regional cooperation
information. In addition to the main Geographical area information, it shows
the area description information and regional cooperation information, grouped
by region. Allows filtering information by region and subregion, countries and
area type.

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
Presents the monitoring programmes


Compliance Assessment module
----------------------------
