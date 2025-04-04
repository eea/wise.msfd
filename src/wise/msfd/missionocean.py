# from Products.Five.browser import BrowserView
from plone import api
# from plone.autoform import directives
from plone.namedfile.field import NamedFile
# from plone.supermodel import model
from z3c.form import button, field, form
# from zope import schema
from zope.interface import Interface
import csv
import io

# from wise.msfd.compliance.vocabulary import get_all_countries

# countries = dict(get_all_countries())

from wise.msfd.wisetheme.vocabulary import countries_vocabulary
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
