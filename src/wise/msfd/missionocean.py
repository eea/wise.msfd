""" mission ocean """
import csv
import io
import json
import logging
# import lxml
from plone import api
from plone.api.portal import get_tool
from plone.namedfile.field import NamedFile
from Products.Five import BrowserView
from z3c.form import button, field, form
from zope.interface import Interface

from wise.msfd.wisetheme.vocabulary import countries_vocabulary


logger = logging.getLogger("wise.msfd")

countries_vocab = {code: vocab.title
                   for code, vocab in countries_vocabulary('').by_value.items()}


countries_vocab.update({
    "AR": "Armenia",
    "AT": "Austria",
    "BR": "Brazil",
    "CZ": "Czechia",
    "HU": "Hungary",
    "IS": "Iceland",
    "IL": "Israel",
    "MA": "Morocco",
    "ME": "Montenegro",
    "NO": "Norway",
    "RS": "Serbia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "UA": "Ukraine",
})


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
        required=True,
    )


class DemoSitesImportView(form.Form):
    """ DemoSitesImportView """

    fields = field.Fields(DemoSitesImportSchema)
    ignoreContext = True

    label = "Import Demo Sites Data"
    description = "Upload a CSV file to import data into Plone."

    def content_exists(self, row):
        """ check if content exists and return it """

        for content in self.context.contentValues():
            if row['Name_DS'] != content.title:
                return None

            if row['ID'] != content.id_ds:
                return None

            country_codes = row['Country_DS'].split(',')
            countries = [
                countries_vocab.get(c.strip(), c.strip())
                for c in country_codes
            ]

            if countries != content.country_ds:
                return None

            return content

        return None

    @button.buttonAndHandler('Import')
    def handleApply(self, action):
        """handleApply"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        csv_demo_sites = data['csv_demo_sites']
        csv_objectives = data['csv_objectives']
        self.process_csv(csv_demo_sites, csv_objectives)
        api.portal.show_message(message="Import successfull!",
                                request=self.request)

    def process_csv(self, csv_demo_sites, csv_objectives):
        """process_csv"""
        # Access the file data correctly
        csv_data_demo_sites = csv_demo_sites.data
        csv_data_objectives = csv_objectives.data
        # Decode the data and remove the BOM if present
        csv_text_demo_sites = csv_data_demo_sites.decode('utf-8-sig')
        csv_reader_demo_sites = csv.DictReader(
            io.StringIO(csv_text_demo_sites))
        csv_text_objectives = csv_data_objectives.decode('utf-8-sig')
        csv_reader_objectives_reader = csv.DictReader(
            io.StringIO(csv_text_objectives))
        csv_reader_objectives = [x for x in csv_reader_objectives_reader]

        for row in csv_reader_demo_sites:
            objective = [
                x['Objective']
                for x in csv_reader_objectives
                if x['ID'] == row['ID']
                ]

            self.create_content(row, objective[0] if objective else '')

    def create_content(self, row, objective):
        """create_content"""
        name_ds = row['Name_DS']

        if not name_ds:
            return

        content = self.content_exists(row)

        if not content:
            content = api.content.create(
                container=self.context,
                type='demo_site_mo',
                title=row['Name_DS'],
            )

        content.id_ds = row['ID']
        content.objective_ds = objective
        content.project_ds = row['Project']
        content.project_link_ds = row['Project link']

        if row['Country_DS']:
            country_ds = row['Country_DS'].split(',')
            content.country_ds = [
                countries_vocab.get(c.strip(), c.strip())
                for c in country_ds
            ]

        if row['Type_DS']:
            type_ds = row['Type_DS'].split(',')
            content.type_ds = [x.strip() for x in type_ds]

        # content.indicator = row['Indicator']
        content.info_ds = row['Info_DS']
        content.website_ds = row['Website']
        content.latitude = row['Latitude']
        content.longitude = row['Longitude']

        type_is_region = row['Type']
        if type_is_region == 'Associated region':
            content.type_is_region = "Associated region"
        else:
            content.type_is_region = "Demo site"

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

            # if obj.measures:
            #     measures = [
            #         {"id": measure.to_id,
            #          "title": measure.to_object.title,
            #          "path": "/freshwater" +
            #             measure.to_path.replace("/Plone", "")}
            #         for measure in obj.measures
            #     ]

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
                        "country": obj.country_ds,
                        "type_is_region": obj.type_is_region,
                        "type": obj.type_ds,
                        "indicators": obj.indicator_mo,
                        "info": obj.info_ds,
                        "website": obj.website_ds,
                        "objective": obj.objective_ds,
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
