# wise.msfd - Agent Guide

## Project Overview

Plone package implementing WISE Marine Directive Strategy Framework. Version: 7.6-dev0

**Two main modules:**
1. **Search engine** (`src/wise/msfd/search/`) - MSSQL data integration for MSFD reported data (Articles 4, 7, 8, 9, 10, 11, 13, 14, 18, 19)
2. **Compliance Assessment** (`src/wise/msfd/compliance/`) - Assessment workflow for MSFD reported information with country/region/descriptor structure

## Architecture

```
src/wise/msfd/
├── search/           # MSSQL integration, Article-specific views
│   ├── article4/     # Article 4 (Marine Units) per-year files
│   ├── article8/     # Art 8.1a, 8.1b, 8.1ab/8.1c (2018+)
│   ├── article9/     # Art 9 (GES determination) 2012 & 2018
│   ├── article10/    # Art 10 (Targets) 2012 & 2018
│   ├── article11/    # Art 11 (Monitoring programmes) 2014 & 2020
│   ├── article13/    # Art 13 (Measures) + StartArticle18Form
│   ├── article14/    # Art 14 (Exceptions)
│   ├── article18/    # Art 18 (PoM progress)
│   ├── article19/    # Art 19.3 (Datasets used)
│   ├── main.py       # Start forms, reporting cycle wrappers, scan() calls
│   └── base.py       # ItemDisplayForm, MainForm, RegionForm, MemberStatesForm, AreaTypesForm
├── compliance/       # Assessment module with workflow, scoring, national/regional descriptors
├── wisetheme/        # Theme, blocks, React-based search UI
│   └── search/       # React app (pnpm, @eeacms/search)
├── sql*.py           # Generated SQLAlchemy models (large auto-generated files)
└── profiles/         # GenericSetup profiles
```

## CI/CD (Jenkins)

**Lint stages** (docker-based, run in parallel):
- JSHint: `eeacms/jshint` (excludes: `static/*`)
- PEP8: `eeacms/pep8` (excludes: `sql2024.py,sql2018.py,sql.py,sql_extra.py,db.py,data.py,utils.py,search,compliance,translation`)
- PyLint: `eeacms/pylint`
- ZPT Lint: `eeacms/plone-test:4`
- PyFlakes: `eeacms/pyflakes`

**Branch workflow:**
- PRs must be from `develop` or `hotfix/*` branches to `master`
- Release from `master` triggers PyPI publish via `eeacms/gitflow`
- SonarQube reporting on master branch

## Key Dependencies

**Python:** Plone 4.3/5, Python 2.7, SQLAlchemy 1.4.46, pymssql 2.3.0, plone.api

**Frontend:** React 17, pnpm, @eeacms/search, Elasticsearch integration

## Development Notes

- Large auto-generated SQL files (`sql.py`, `sql2018.py`, `sql2018.py`) are excluded from PEP8 checks
- MSSQL databases: Integration with two external MSSQL databases for reported data
- Compliance module uses Eionet groups for security/workflow
- Assessment questions defined in XML files with scoring/weighting per descriptor

## Frontend Build (React)

Located in `src/wise/msfd/wisetheme/search/`:
```bash
pnpm install
pnpm start          # Dev server with ES proxy
pnpm build          # Production build
pnpm watch          # Watch mode
```

Uses `mrs.developer` for searchlib dependency from `https://github.com/eea/searchlib.git`

## Compliance Module Deep Dive

The compliance module (`src/wise/msfd/compliance/`) is a complex assessment workflow system for evaluating MSFD reported data. It is organized into several sub-packages:

### Sub-packages

- **`nationaldescriptors/`** - National descriptor assessments (country > region > descriptor > article)
- **`regionaldescriptors/`** - Regional descriptor assessments (region > descriptor > article)  
- **`nationalsummary/`** - National summary/overview pages (Art 12/16 assessments)
- **`regionalsummary/`** - Regional summary/overview pages
- **`admin/`** - Bootstrap, admin views, scoring utilities, migrations

### Content Hierarchy

The module creates a deep Plone content hierarchy:

```
/assessment-module/                          (IComplianceModuleFolder)
├── national-descriptors-assessments/         (INationalDescriptorsFolder)
│   ├── <country-code>/                       (ICountryDescriptorsFolder)
│   │   ├── <region-code>/                    (INationalRegionDescriptorFolder)
│   │   │   ├── <descriptor-code>/            (IDescriptorFolder)
│   │   │   │   ├── <article>/                (INationalDescriptorAssessment)
│   │   │   │   │   ├── tl/                   (ICommentsFolder - Topic Leads)
│   │   │   │   │   └── ec/                   (ICommentsFolder - EC)
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── <secondary-article>/              (INationalDescriptorAssessmentSecondary)
│   │       ├── tl/
│   │       └── ec/
│   └── ...
├── regional-descriptors-assessments/         (IRegionalDescriptorsFolder)
│   ├── <region-code>/                        (IRegionalDescriptorRegionsFolder)
│   │   ├── <descriptor-code>/
│   │   │   ├── <article>/                    (IRegionalDescriptorAssessment)
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── national-summaries/                       (INationalSummaryFolder)
│   ├── <country-code>/                       (INationalSummaryCountryFolder)
│   │   ├── assessment-summary/               (INationalSummaryOverviewFolder)
│   │   └── assessment-summary-2022/          (INationalSummary2022Folder)
│   └── ...
├── regional-summaries/                       (IRegionalSummaryFolder)
│   └── ...
└── ms-recommendations/                       (IMSRecommendationsFeedback)
```

### Bootstrap Process

The compliance module is bootstrapped via admin views that create the entire content tree:

- **`@@bootstrap-compliance?setup=nationaldesc&production=1`** - Creates national descriptors structure
- **`@@bootstrap-assessment-landingpages`** - Creates landing pages  
- **`@@bootstrap-ms-recommendations`** - Creates recommendations structure

In debug mode (no `production` param), only a subset of countries (LV, NL, DE) and descriptors (D1.1, D4, D5, D6) are created.

Bootstrap sets up:
- Placeful workflow policies (`compliance_section_policy`)
- Eionet security groups per descriptor (`contributor-<descriptor>`, `reviewer-<descriptor>`, `editor-<descriptor>`)
- Comments folders (tl = Topic Leads track, ec = EC track)

### Assessment Data Flow

**Assessment content types** (`compliance/content.py`):
- `NationalDescriptorAssessment` / `RegionalDescriptorAssessment` - Store assessment data in `_data` attribute (persistent dict)
- `AssessmentData` - PersistentList subclass for tracking edit history with assessor info

**Key assessment views** (registered in `configure.zcml` files):
- `@@nat-desc-art-view` / `@@reg-desc-art-view` - Main assessment overview page
- `@@edit-assessment-data-2018` / `@@edit-assessment-data-2024` - Edit assessment answers
- `@@edit-assessment-summary` - Edit assessment summary text
- `@@view-report-data-2018` / `@@view-report-data-2012` - View raw reported data
- `@@view-edit-history` - Track changes over time

### Scoring System

**Scoring** (`compliance/scoring.py`):
- Default score ranges: `[76-100]`, `[51-75]`, `[26-50]`, `[1-25]`, `[0]`
- 2022 ranges: `[81-100]`, `[61-80]`, `[41-60]`, `[21-40]`, `[0-20]`
- Conclusions: `Not relevant`, `Very good`, `Good`, `Poor`, `Very poor`, `Not reported`
- Per-question weights can vary by country and descriptor (`COUNTRY_WEIGHTS` dict)
- `OverallScores` class computes aggregated scores across assessment phases

**Article weights** (`compliance/assessment.py` `ARTICLE_WEIGHTS`):
- Art8/Art9/Art10: `adequacy=0.6, consistency=0.2, coherence=0.2`
- Art13: `adequacy=0.6, completeness=0.4`
- Art3/Art4/Art7/Art8esa/Art11: full weight on single criterion

### Workflow & Security

- Uses custom permissions: `wise.ViewAssessmentData`, `wise.EditAssessment`, `wise.ViewAssessmentEditPage`, `wise.ManageCompliance`
- Workflow states: `not_started` -> `in_work` -> `in_draft_review_tl` -> `in_draft_review` -> `in_draft_review_com` -> `in_final_review_tl` -> `in_final_review` -> `in_final_review_com` -> `approved`
- Colors map to workflow states via `STATUS_COLORS` and `PROCESS_STATUS_COLORS` dicts in `compliance/base.py`
- Eionet LDAP groups control access per descriptor
- Bulk workflow transitions available via `@@process-state-change-bulk`

### Report Data Views

Report data is displayed by year-specific views that query MSSQL:
- **2012 data** (`reportdata2012.py`) - Legacy reports, sometimes mapped to 2018 format
- **2018/2020/2022/2024 data** (`reportdata2018.py`, `reportdata2024.py`) - Modern reports with "simplify table" toggle
- Regional variants in `regionaldescriptors/reportdata.py`

Key feature: "simplify table" merges adjacent identical cells for readability.

### Admin Utilities

Available at `@@compliance-admin` (requires `wise.ManageCompliance`):
- `@@admin-scoring` - View/adjust scoring configuration
- `@@export-scores-xml` - Export scores to XML
- `@@recalculate-scores-by-article` - Batch recalculate
- `@@translate-indicators` - Batch translate indicator labels
- `@@migrate-translations` / `@@migrate-eionet-groups` - Data migrations
- `@@cleanup-compliance` - Clear caches

### Questions & Configuration

Assessment questions are loaded from XML files (referenced via `pkg_resources.resource_filename`). Questions define:
- Available answers per criterion
- Scoring method
- Descriptor-specific weights
- Cross-cutting sections (socio-economic, climate change, funding, etc.)

Question IDs may have display overrides via `QUESTION_DISPLAY_IDS` in `compliance/base.py`.

### Important Conventions

- Most compliance Python files start with `# pylint: skip-file`
- Database sessions are managed via `@db.use_db_session('2018')` decorator
- Assessment data is stored as raw dicts on content objects, not in catalog
- Comments are stored as sub-objects in `tl/` and `ec/` folders
- PDF export uses `pdfkit` for assessment summaries
- Excel export uses `pyexcel-xlsx` / `xlsxwriter`

## Search Module Deep Dive

The search module (`src/wise/msfd/search/`) is a multi-step form wizard for querying and displaying MSFD reported data from MSSQL databases. It supports multiple reporting cycles (2012, 2018, 2020, 2022, 2024) and articles (Art 4, 7, 8, 9, 10, 11, 13, 14, 18, 19).

### Architecture

**Form hierarchy** (each level is a nested `EmbeddedForm`):
```
MainForm (article selection)
  └── EmbeddedForm (reporting period / theme)
        └── EmbeddedForm (region/country/filters)
              └── ItemDisplayForm (record display with pagination)
                    └── ItemDisplay (inline related records)
```

**Key base classes** (`search/base.py`):
- `ItemDisplayForm` - Generic paginated record display with prev/next buttons
- `ItemDisplayForm2018` - 2018-variant with `reported_date_info` dict for import tracking
- `MultiItemDisplayForm` - Groups multiple items with sections via `register_form_section`
- `MainForm` - Top-level article form that delegates to subforms via `get_subform()`

### Form Registration System

Forms are registered via decorators in `search/utils.py`:
- `@register_form_art4` / `@register_form_art8` / `@register_form_art9` / `@register_form_art10` / `@register_form_art11` / `@register_form_art13` / `@register_form_art14` / `@register_form_art18` / `@register_form_art19` - Register top-level reporting period forms
- `@register_form_a8_2012` / `@register_form_a8_2018` - Register 2012/2018 Art 8 variants
- `@register_subform(MainForm)` - Register theme/subform choices
- `@register_form_section(ParentDisplay)` - Register inline sections within a display form

Registration populates global dicts (`FORMS_ART4`, `FORMS_ART8`, etc.) that drive vocabulary factories in `search/vocabulary.py`.

### Database Layer

**Session management** (`db.py`):
- Three databases: `2012` → `MarineDB_public`, `2018` → `MSFD2018_public`, `2024` → `MSFD2024_public`
- Session switched via `db.threadlocals.session_name` or `@db.use_db_session('2018')` decorator
- Connection uses `mssql+pymssql` with CrestedDuck credentials from env vars: `CRESTEDDUCK_HOST`, `CRESTEDDUCK_DOMAIN`, `CRESTEDDUCK_USER`, `CRESTEDDUCK_PASSWORD`
- Fallback `MockSession` when DB is offline (controlled by `USE_MOCKSESSION` env var)
- SQLAlchemy models are auto-generated in `sql.py` (2012), `sql2018.py` (2018), `sql2024.py` (2024)

**Key DB functions** (`db.py`):
- `get_all_records(mapper, *conditions)` - Standard filtered query
- `get_all_records_join(columns, join_table, *conditions)` - Join query
- `get_related_record(mapper, col, value)` - Single relation lookup
- `get_unique_from_mapper(mapper, column, *conditions)` - Distinct values
- `latest_import_ids_2018()` - Returns latest import IDs per country/region

### Article-Specific File Mapping (Subpackages)

Files are organized under `search/<articleN>/` with per-year variants. `main.py` imports from these subpackages and calls `scan('<subpackage>')` to register decorated forms.

| Subpackage | Files | Purpose |
|------------|-------|---------|
| `article4/` | `a4_2012.py`, `a4_2018.py`, `a4_2024.py` | Article 4 (Marine Units) 2012, 2018-2024, 2024-2030 cycles |
| `article8/` | `a8_2012_ac.py`, `a8_2012_b.py`, `a8_2018.py` | Art 8.1a (env status), 8.1b (pressures), 8.1ab/8.1c (2018+) |
| `article9/` | `a9_2012.py`, `a9_2018.py` | Art 9 (GES determination) 2012 & 2018 |
| `article10/` | `a10_2012.py`, `a10_2018.py` | Art 10 (Targets) 2012 & 2018 |
| `article11/` | `a11_2014.py`, `a11_2020.py` | Art 11 (Monitoring programmes/strategies) 2014 & 2020 |
| `article13/` | `a13_2016.py`, `a18_2019.py` | Art 13 (Measures) 2016 & 2022; also holds `StartArticle18Form` |
| `article14/` | `a14_2016.py` | Art 14 (Exceptions) 2016 & 2022 |
| `article18/` | `a18_2019.py` | Art 18 (PoM progress) 2019 |
| `article19/` | `a19_2012.py`, `a19_2018.py` | Art 19.3 (Datasets used) 2012 & 2018 |

### Shared Forms (moved to `base.py`)

`RegionForm`, `MemberStatesForm`, `AreaTypesForm`, and `MarineUnitIDsForm` were extracted from `main.py` into `search/base.py` to avoid circular imports between article subpackages. `AreaTypesForm` uses lazy imports (`from .article4 import A4Form`, `from .article10 import A10Form`) inside `get_subform()`.

### Display & Export Conventions

**Templates** (`search/pt/`):
- `item-display-form.pt` - Main paginated record wrapper
- `item-display.pt` - Single record field rendering
- `extra-data.pt` / `extra-data-pivot.pt` - Related/child records display
- `multi-item-display.pt` - Multi-section grouped display

**Field display**:
- `blacklist` - Columns to hide from display
- `blacklist_labels` - Columns to show without label transformation
- `name_as_title()` in `base.py` converts CamelCase DB columns to readable labels using `DISPLAY_LABELS` dict
- `print_value()` translates coded values to human-readable labels

**Excel export**:
- `download_results()` returns list of `(worksheet_title, data)` tuples
- `data_to_xls()` in `search/utils.py` converts to xlsx stream
- Raw vs processed: `raw=True` in DB queries returns ORM objects; without it returns dicts

### Important Conventions

- Most search Python files start with `# pylint: skip-file`
- `session_name` class attribute (e.g., `'2012'`, `'2018'`) determines which DB is used
- `mapper_class` attribute specifies the SQLAlchemy model for queries
- `order_field` specifies pagination ordering column
- `reported_date_info` dict maps import tables to reporting dates for 2018+ data
- `get_import_id()` / `get_current_country()` / `get_reported_date()` methods are overridden per article to handle different data schemas
- Related data is fetched via explicit SQLAlchemy queries, not ORM relationships
- `DB_INFO.txt` documents which DB tables are used per article
- Files in subpackages use `from .. import ...` to reach `search/` level modules (`base`, `utils`, `interfaces`) and `../pt/` for template paths
