""" mission ocean """
import csv
import io
import json
import logging
from collections import defaultdict
# import lxml
from plone import api
from plone.api.portal import get_tool
from plone.dexterity.content import Container
from plone.namedfile.field import NamedFile
from plone.restapi.deserializer.dxcontent import DeserializeFromJson
from plone.restapi.interfaces import IDeserializeFromJson
from plone.dexterity.interfaces import IDexterityContainer
from plone.restapi.deserializer import json_body
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button, field, form
from zope.component import adapter
from zope.interface import Interface, implementer

from collective.relationhelpers import api as relapi
from wise.msfd.wisetheme.vocabulary import countries_vocabulary


logger = logging.getLogger("wise.msfd")

countries_vocab = {
    code: vocab.title
    for code, vocab in countries_vocabulary('').by_value.items()
}


countries_vocab.update({
    "AL": "Albania",
    "AM": "Azerbaijan",
    "AR": "Armenia",
    "AT": "Austria",
    "BA": "Bosnia and Herzegovina",
    "BR": "Brazil",
    "CZ": "Czechia",
    "GE": "Georgia",
    "GR": "Greece",
    "HU": "Hungary",
    "IS": "Iceland",
    "IL": "Israel",
    "MA": "Morocco",
    "ME": "Montenegro",
    "MD": "Moldova",
    "NO": "Norway",
    "RS": "Serbia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "TU": "Tunisia",
    "TN": "Tunisia",
    "UA": "Ukraine",
})


def get_type_is_region(row):
    """get_type_is_region"""
    # type_is_region = row.get('Type', 'Demo site')
    type_ds = row.get('Type_DS', '')

    if type_ds != 'Associated region':
        return 'Demo site'

    return type_ds


class IDemoSiteContent(Interface):
    """ Interface for Demo site content type
    """


@implementer(IDemoSiteContent)
class DemoSiteContent(Container):
    """ Demo site content
    """


class DemoSitesImportSchema(Interface):
    """ DemoSitesImportSchema """

    csv_demo_sites = NamedFile(
        title="CSV File Demo sites",
        description="Upload a CSV file woth demo sites to import data.",
        required=True,
    )

    csv_objectives = NamedFile(
        title="CSV File objectives",
        description="Upload a CSV file with objectives to import data.",
        required=False,
    )


class DemoSitesImportView(form.Form):
    """ DemoSitesImportView """
    template = ViewPageTemplateFile("./pt/demo-sites-import.pt")
    fields = field.Fields(DemoSitesImportSchema)
    ignoreContext = True

    label = "Import Demo Sites Data"
    description = "Upload a CSV file to import data into Plone."

    def __init__(self, context, request):
        super().__init__(context, request)
        self.show_table = False
        self.matched_rows = {}
        self.matched = 0
        self.unmatched = 0
        self.new = 0
        self.unmatched_list = []

    @property
    def indicators_folder(self):
        """indicators_folder"""
        return self.context.aq_parent['mo-indicators']

    def demosite_matches_row(self, content, row):
        """Check if a demo site content item matches a CSV row"""
        # Check ID match
        _id = row.get('ID', row.get('Id'))
        if _id != content.id_ds:
            return False

        # Check country match
        _country = row.get('Country_DS', row.get('Country'))
        country_codes = _country.split(',') if _country else []
        countries = set([
            countries_vocab.get(c.strip(), c.strip())
            for c in country_codes
        ]) or None

        if ((countries or content.country_ds) and
                countries != content.country_ds):
            return False

        # One of these must match: name_ds or coordinates
        # Check coordinates match
        name_match = False
        # coords_match = False
        # latitude = row.get('Latitude') or ''
        # longitude = row.get('Longitude') or ''

        # if not latitude and not longitude:
        #     coords_match = False

        # if (latitude and longitude and content.latitude == latitude
        #         and content.longitude == longitude):
        #     coords_match = True

        name_ds = row.get('Name_DS', row.get('Region name'))
        if (name_ds == content.title or name_ds in content.title or
                content.title in name_ds):
            name_match = True

        return name_match  # or coords_match

    def demosite_exists(self, row):
        """ check if content exists and return it """

        for content in self.context.contentValues():
            # ID must match
            _id = row.get('ID', row.get('Id'))
            if _id != content.id_ds:
                continue

            # country must match
            _country = row.get('Country_DS', row.get('Country'))
            country_codes = _country.split(',') if _country else []
            countries = set([
                countries_vocab.get(c.strip(), c.strip())
                for c in country_codes
            ]) or None

            if ((countries or content.country_ds) and
                    countries != content.country_ds):
                continue

            # one of these must match: name_ds or coordinates
            name_ds = row.get('Name_DS', row.get('Region name'))
            if name_ds == content.title:
                return content

            # latitude and longitude
            latitude = row['Latitude'] or ''
            longitude = row['Longitude'] or ''

            if content.latitude != latitude:
                continue

            if content.longitude != longitude:
                continue

            return content

        return None

    def indicator_exists(self, title):
        """indicator_exists"""
        for content in self.indicators_folder.contentValues():
            if title != content.title:
                continue

            return content

        return None

    def add_objective_prefix(self, objective):
        """add_objective_prefix"""
        # _obj_map = {
        #     'Carbon-neutral and circular blue economy': 'Ob. 3:',
        #     'Digital twin of the ocean': 'En. 1: ',
        #     'Prevent and eliminate pollution of waters': 'Ob. 2:',
        #     'Protect and restore marine and freshwater ecosystems': 'Ob. 1:',
        #     'Public mobilisation and engagement': 'En. 2: ',
        # }
        return objective

    @button.buttonAndHandler('Import')
    def handleApply(self, action):
        """handleApply"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        csv_demo_sites = data['csv_demo_sites']
        csv_objectives = data['csv_objectives'] or {}
        self.process_csv(csv_demo_sites, csv_objectives, do_create=True)
        # self.process_csv(csv_demo_sites)
        message = (
            "Import successful! Matched: {}, "
            "Unmatched: {}, New: {}".format(
                self.matched, self.unmatched, self.new
            )
        )
        api.portal.show_message(message=message, request=self.request)
        self.show_table = True

    @button.buttonAndHandler('Show Matches')
    def handleShowMatches(self, action):
        """handleShowMatches"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        csv_demo_sites = data['csv_demo_sites']
        csv_objectives = data['csv_objectives'] or {}
        self.process_csv(csv_demo_sites, csv_objectives, do_create=False)
        message = (
            "Import successful! Matched: {}, "
            "Unmatched: {}, New: {}".format(
                self.matched, self.unmatched, self.new
            )
        )
        api.portal.show_message(message=message, request=self.request)
        self.show_table = True

    def process_csv(self, csv_demo_sites, csv_objectives, do_create=False):
        """process_csv"""
        # Access the file data correctly
        csv_data_demo_sites = csv_demo_sites.data
        csv_data_objectives = csv_objectives.data if csv_objectives else {}
        # Decode the data and remove the BOM if present
        csv_text_demo_sites = csv_data_demo_sites.decode('utf-8-sig')
        csv_reader_demo_sites = csv.DictReader(
            io.StringIO(csv_text_demo_sites))

        if csv_data_objectives:
            csv_text_objectives = csv_data_objectives.decode('utf-8-sig')
            csv_reader_objectives_reader = csv.DictReader(
                io.StringIO(csv_text_objectives))
            csv_reader_objectives = [x for x in csv_reader_objectives_reader]

        # Convert CSV rows to a list to allow multiple iterations
        csv_rows = [row for row in csv_reader_demo_sites]

        # Initialize counters
        self.matched = 0
        self.new = 0
        existing_sites = list(self.context.contentValues())
        total_existing = len(existing_sites)
        matched_contents = set()
        matched_rows = defaultdict(list)
        matched_csv_rows = set()

        # Iterate through existing demo sites and find matches in CSV
        for content in existing_sites:
            matching_rows = []
            for idx, row in enumerate(csv_rows):
                if self.demosite_matches_row(content, row):
                    matching_rows.append(row)
                    matched_csv_rows.add(idx)

            if matching_rows:
                self.matched += 1
                matched_contents.add(content)
                matched_rows[content] = matching_rows

                if do_create and matching_rows:
                    # Use the first matching row's objectives
                    first_row = matching_rows[0]
                    if csv_data_objectives:
                        objective = [
                            self.add_objective_prefix(x['Objective'])
                            for x in csv_reader_objectives
                            if (x['ID'] ==
                                first_row.get('ID', first_row.get('Id')))
                        ]
                    else:
                        objective = ''

                    self.update_content(content, first_row,
                                        objective[0] if objective else '')

        # Count new items from CSV that don't match any existing site
        self.new = len(csv_rows) - len(matched_csv_rows)

        self.unmatched = total_existing - self.matched
        self.matched_rows = dict(matched_rows)
        unmatched_sites = [
            c for c in existing_sites if c not in matched_contents]
        self.unmatched_list = [
            {
                'name_ds': c.title,
                'ID': getattr(c, 'id_ds', ''),
                'Country_DS': getattr(c, 'country_ds') or [],
                'latitude': getattr(c, 'latitude', ''),
                'longitude': getattr(c, 'longitude', ''),
                'type_is_region': getattr(c, 'type_is_region', '')
            }
            for c in unmatched_sites
        ]

        if do_create:
            # Retract unmatched content (set to private)
            for content in unmatched_sites:
                try:
                    api.content.transition(obj=content, to_state='private')
                    logger.info("Retracted demo site: %s", content.title)
                except Exception as e:
                    logger.warning(
                        "Failed to retract demo site %s: %s",
                        content.title, str(e))

            # Create new content from unmatched CSV rows
            for idx, row in enumerate(csv_rows):
                if idx not in matched_csv_rows:
                    if csv_data_objectives:
                        objective = [
                            self.add_objective_prefix(x['Objective'])
                            for x in csv_reader_objectives
                            if x['ID'] == row.get('ID', row.get('Id'))
                        ]
                    else:
                        objective = ''
                    self.create_content(row, objective[0] if objective else '')

    def update_content(self, content, row, objective_csv):
        """update_content - updates an existing demo site with CSV data"""
        if objective_csv:
            objectives = [objective_csv]
        else:
            objectives = row.get('Objectives/enablers', '').split(';')
            objectives = [x.strip() for x in objectives if x]

        targets = row.get('Targets', '').split(';')
        targets = [x.strip() for x in targets]

        content.objective_ds = objectives
        content.target_ds = targets
        content.project_ds = row['Project']
        content.project_link_ds = row.get('Project link', '')

        _country = row.get('Country_DS', row.get('Country'))
        if _country:
            country_ds = _country.split(',')
            content.country_ds = set([
                countries_vocab.get(c.strip(), c.strip())
                for c in country_ds
            ])

        if row.get('Type_DS'):
            type_ds = row['Type_DS'].replace(
                'Living Labs', 'Living labs').replace("&", "and").split(',')
            content.type_ds = [x.strip() for x in type_ds]

        _indicators_visited = []
        indicator_blacklist = ['0']

        for indicator in row['Indicator'].split(';'):
            indicator = indicator.strip()

            if indicator in indicator_blacklist:
                continue

            if not indicator or indicator in _indicators_visited:
                continue

            _indicators_visited.append(indicator)

            indicator_obj = self.indicator_exists(indicator)

            if not indicator_obj:
                indicator_obj = api.content.create(
                    container=self.indicators_folder,
                    type='indicator_mo',
                    title=indicator,
                )

                indicator_obj.target_ds = targets
                indicator_obj.objective_ds = objectives

            if not content.indicator_mo:
                continue

            rel_objects = [x.to_object for x in content.indicator_mo]

            if indicator_obj not in rel_objects:
                relapi.link_objects(
                    content, indicator_obj, 'indicator_mo')

        content.info_ds = row.get('Info_DS', row.get('More info'))
        content.website_ds = row.get('Website', '')
        content.level_of_impl = row.get('Level of implementation', None)
        content.latitude = row['Latitude'] or ''
        content.longitude = row['Longitude'] or ''
        type_is_region = get_type_is_region(row)
        content.type_is_region = type_is_region

        content.reindexObject()

    def create_content(self, row, objective_csv):
        """create_content"""
        name_ds = row.get('Name_DS', row.get('Region name'))

        if objective_csv:
            # print("Using objective from additional CSV!")
            objectives = [objective_csv]
        else:
            # print("Using objective from demo sites CSV!")
            objectives = row.get('Objectives/enablers', '').split(';')
            objectives = [x.strip() for x in objectives]

        targets = row.get('Targets', '').split(';')
        targets = [x.strip() for x in targets]

        if not name_ds or name_ds in ('to be confirmed', 'To be defined'):
            return

        # content = self.demosite_exists(row)
        content = None

        if not content:
            content = api.content.create(
                container=self.context,
                type='demo_site_mo',
                title=name_ds,
            )

        content.id_ds = row.get('ID', row.get('Id'))
        content.objective_ds = objectives
        content.target_ds = targets
        content.project_ds = row['Project']
        content.project_link_ds = row.get('Project link', '')

        _country = row.get('Country_DS', row.get('Country'))
        if _country:
            country_ds = _country.split(',')
            content.country_ds = set([
                countries_vocab.get(c.strip(), c.strip())
                for c in country_ds
            ])

        if row.get('Type_DS'):
            type_ds = row['Type_DS'].split(',')
            content.type_ds = [x.strip() for x in type_ds]

        _indicators_visited = []
        indicator_blacklist = ['0']

        for indicator in row['Indicator'].split(';'):
            indicator = indicator.strip()

            if indicator in indicator_blacklist:
                continue

            if not indicator or indicator in _indicators_visited:
                continue

            _indicators_visited.append(indicator)

            indicator_obj = self.indicator_exists(indicator)

            if not indicator_obj:
                indicator_obj = api.content.create(
                    container=self.indicators_folder,
                    type='indicator_mo',
                    title=indicator,
                )

            indicator_obj.target_ds = targets
            indicator_obj.objective_ds = objectives

            relapi.link_objects(
                content, indicator_obj, 'indicator_mo')

        content.info_ds = row.get('Info_DS', row.get('More info'))
        content.website_ds = row.get('Website', '')
        content.level_of_impl = row.get('Level of implementation', '')
        content.latitude = row['Latitude'] or ''
        content.longitude = row['Longitude'] or ''
        type_is_region = row.get('Type', 'Demo site')
        content.type_is_region = type_is_region

        content.reindexObject()


class DemoSiteItems(BrowserView):
    """ Return demo sites needed for the map """

    def __call__(self):
        """"""
        results = {
            "type": "FeatureCollection",
            "metadata": {
                "generated": 1615559750000,
                "url": "https://earthquake.usgs.gov/earthquakes"
                    "/feed/v1.0/summary/all_month.geojson",
                "title": "WISE Marine Demo Site arcgis items",
                "status": 200,
                "api": "1.10.3",
                "count": 10739,
            },
            "features": [],
        }

        catalog = get_tool("portal_catalog")
        brains = catalog.searchResults(
            {
                "portal_type": [
                    "demo_site_mo",
                ],
                # "path": "/",
                # "review_state": "published",
            }
        )

        for brain in brains:
            obj = brain.getObject()
            if not getattr(obj, "latitude", ""):
                continue

            # if obj.general:
            #     general_html = lxml.etree.fromstring(obj.general.raw)
            #     long_description = general_html.cssselect(
            #         'div .field--name-field-nwrm-cs-summary .field__item')
            #     long_description = (
            #         long_description[0].text if long_description else '')
            # else:
            #     long_description = ''
            # measures = []

            indicators = []

            if obj.indicator_mo:
                indicators = [
                    {"id": indicator.to_id,
                     "title": indicator.to_object.title,
                     "path": "/marine" +
                        indicator.to_path.replace("/Plone", "")}
                    for indicator in obj.indicator_mo if indicator.to_id
                ]

            # sectors = [
            #     measure.to_object.measure_sector
            #     for measure in obj.measures
            # ]

            results["features"].append(
                {
                    "properties": {
                        "portal_type": obj.portal_type,
                        "title": obj.title,
                        "project": obj.project_ds,
                        "project_link": obj.project_link_ds,
                        "country": list(obj.country_ds or []),
                        "type_is_region": obj.type_is_region,
                        "type": list(obj.type_ds or []),
                        "indicators": indicators,
                        "info": obj.info_ds,
                        "website": obj.website_ds,
                        "objective": list(obj.objective_ds or []),
                        "target": list(obj.target_ds or []),
                        # "description": long_description,
                        "url": brain.getURL(),
                        "path": "/marine" + "/".join(
                            obj.getPhysicalPath()).replace('/Plone', ''),
                        # "image": "",
                        # "measures": measures,  # nwrms_implemented
                        # "sectors": sorted(list(set(sectors)))
                    },
                    "geometry": {
                        "type": "Point",
                        # "coordinates": [geo.x, geo.y]
                        "svg": {"fill_color": "#009900"},
                        "color": "#009900",
                        "coordinates": [
                            # "6.0142918",
                            # "49.5057481"
                            # obj.latitude,
                            obj.longitude,
                            obj.latitude,
                        ],
                    },
                }
            )

        response = self.request.response
        response.setHeader("Content-type", "application/json")

        return json.dumps(results)


@implementer(IDeserializeFromJson)
@adapter(IDexterityContainer, Interface)
# @adapter(IDemoSiteContent, Interface)
class MissionOceanDeserializer(DeserializeFromJson):
    """ MissionOceanDeserializer """

    def __call__(self, validate_all=False, data=None,
                 create=False, mask_validation_errors=True):
        if data is None:
            data = json_body(self.request)

        if data and "indicator_mo" in data:
            logger.info("Fix path for indicator_mo relation!")
            for value in data["indicator_mo"]:
                if isinstance(value, dict) and "@id" in value:
                    path = value["@id"]
                    if path.startswith("/marine/"):
                        value["@id"] = path.replace("/marine/", "/", 1)

        return super(MissionOceanDeserializer, self).__call__(
            validate_all, data, create, mask_validation_errors)


# from OFS.SimpleItem import SimpleItem
# from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
# from plone.app.contentrules.browser.formhelper import NullAddForm


# class UpdateModifiedDateAddForm(NullAddForm):
#     """UpdateModifiedDateAddForm"""

#     def create(self):
#         return UpdateModifiedDateAction()


# class IUpdateModifiedDateAction(Interface):
#     """IUpdateModifiedDateAction"""


# @implementer(IUpdateModifiedDateAction, IRuleElementData)
# class UpdateModifiedDateAction(SimpleItem):
#     """UpdateModifiedDateAction"""

#     element = "missionocean.UpdateModifiedDate"
#     summary = str("Update indicator modified date")


# @implementer(IExecutable)
# class UpdateModifiedDateExecutor(object):
#     """Translate async executor"""

#     adapts(Interface, IUpdateModifiedDateAction, Interface)

#     def __init__(self, context, element, event):
#         self.context = context
#         self.element = element
#         self.event = event

#     def __call__(self):
#         # import pdb; pdb.set_trace()

#         logger.info("Update indicator modified date! %s", self.event.object)
#         return True
