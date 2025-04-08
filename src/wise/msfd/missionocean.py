from plone import api
from plone.api.portal import get_tool
from Products.Five import BrowserView
from plone.namedfile.field import NamedFile
from z3c.form import button, field, form
from zope.interface import Interface
import csv
import io
import json
import logging
# import lxml
from wise.msfd.wisetheme.vocabulary import countries_vocabulary


logger = logging.getLogger("wise.msfd")

countries = {code: vocab.title
                for code, vocab in countries_vocabulary('').by_value.items()}


countries.update({
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
    csv_file = NamedFile(
        title="CSV File",
        description="Upload a CSV file to import data.",
        required=True,
    )


class DemoSitesImportView(form.Form):
    fields = field.Fields(DemoSitesImportSchema)
    ignoreContext = True

    label = "Import Demo Sites Data"
    description = "Upload a CSV file to import data into Plone."

    @button.buttonAndHandler('Import')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        csv_file = data['csv_file']
        self.process_csv(csv_file)
        api.portal.show_message(message="CSV file imported successfully!",
                                request=self.request)

    def process_csv(self, csv_file):
        # Access the file data correctly
        csv_data = csv_file.data
        # Decode the data and remove the BOM if present
        csv_text = csv_data.decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        for row in csv_reader:
            self.create_content(row)

    def create_content(self, row):
        name_ds = row['Name_DS']

        if not name_ds or name_ds in ('To be defined',):
            return

        # content_id = row['Name_DS']
        content = api.content.create(
            container=self.context,
            type='demo_site_mo',
            # id=content_id,
            title=row['Name_DS'],
            # description=row['Info_DS'],
        )

        content.project_ds = row['Project']
        content.project_link_ds = row['Project link']

        if row['Country_DS']:
            country_ds = row['Country_DS'].split(',')
            content.country_ds = [
                countries.get(c.strip(), c.strip())
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
                        "objective": '',
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
