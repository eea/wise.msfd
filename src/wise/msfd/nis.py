""" Non-indigenous species """
import datetime
import csv
import io
import six
import xlsxwriter

from plone import api
from plone.api.portal import get_tool
from plone.dexterity.content import Container
from plone.namedfile.field import NamedFile
from zope.interface import Interface, implementer
from z3c.form import button, field, form
from Products.Five import BrowserView
from zope.schema.interfaces import IVocabularyFactory
from Products.CMFCore.utils import getToolByName
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.interface import provider

nis_fields = {
    "Species_name_original": "nis_species_name_original",
    "Species_name_accepted": "nis_species_name_accepted",
    "ScientificName_accepted": "nis_scientificname_accepted",
    "List": "nis_list",
    "Subregion": "nis_subregion",
    "Region": "nis_region",
    "Status comment": "nis_status_comment",
    "STATUS": "nis_status",
    "Group": "nis_group",
    "VER-INV-PP": "nis_ver_inv_pp",
    "Taxonomy": "nis_taxonomy",
    "NS stand": "nis_ns_stand",
    "Year": "nis_year",
    "Period": "nis_period",
    "Country": "nis_country",
    "Area": "nis_area",
    "REL": "nis_rel",
    "EC": "nis_ec",
    "TC": "nis_tc",
    "TS-0ther": "nis_ts_other",
    "TS-ball": "nis_ts_ball",
    "TS-hull": "nis_ts_hull",
    "COR": "nis_cor",
    "UNA": "nis_una",
    "UNK": "nis_unk",
    "Total": "nis_total",
    "Pathway_Probability": "nis_pathway_probability",
    "Comment": "nis_comment",
    "Source": "nis_source",
    "Remarks": "nis_remarks",
    "Taxon_comment": "nis_taxon_comment",
    "checked_by": "nis_checked_by",
    "checked_on": "nis_checked_on",
    "check_comment": "nis_check_comment"
}

def get_catalog_values(context, index):
    """get_catalog_values"""

    catalog = getToolByName(context, "portal_catalog")

    return catalog.uniqueValuesFor(index)


@provider(IVocabularyFactory)
def nis_region_vocabulary(context):
    """nis_region_vocabulary"""

    catalog_values = get_catalog_values(
        context, "nis_region"
    )

    terms = []
    for key in catalog_values:
        terms.append(
            SimpleTerm(
                key, key, key.encode("ascii", "ignore").decode("ascii")
            )
        )

    terms.sort(key=lambda t: t.title)

    return SimpleVocabulary(terms)


@provider(IVocabularyFactory)
def nis_subregion_vocabulary(context):
    """nis_subregion_vocabulary"""

    catalog_values = get_catalog_values(
        context, "nis_subregion"
    )

    terms = []
    for key in catalog_values:
        terms.append(
            SimpleTerm(
                key, key, key.encode("ascii", "ignore").decode("ascii")
            )
        )

    terms.sort(key=lambda t: t.title)

    return SimpleVocabulary(terms)


@provider(IVocabularyFactory)
def nis_group_vocabulary(context):
    """nis_group_vocabulary"""

    catalog_values = get_catalog_values(
        context, "nis_group"
    )

    terms = []
    for key in catalog_values:
        terms.append(
            SimpleTerm(
                key, key, key.encode("ascii", "ignore").decode("ascii")
            )
        )

    terms.sort(key=lambda t: t.title)

    return SimpleVocabulary(terms)


class INonIndigenousSpeciesContent(Interface):
    """ Interface for Non indigenous species content type
    """


@implementer(INonIndigenousSpeciesContent)
class NonIndigenousSpeciesContent(Container):
    """NonIndigenousSpeciesContent"""


class NonIndigenousSpeciesImportSchema(Interface):
    """ NonIndigenousSpeciesImportSchema """

    csv_nis = NamedFile(
        title="CSV File NonIndigenousSpecies",
        description="Upload a CSV file with NIS to import data.",
        required=True,
    )


class NonIndigenousSpeciesImportView(form.Form):
    """ NonIndigenousSpeciesImportView """

    fields = field.Fields(NonIndigenousSpeciesImportSchema)
    ignoreContext = True

    label = "Import NIS Data"
    description = "Upload a CSV file to import data into Plone."

    @button.buttonAndHandler('Import')
    def handleApply(self, action):
        """handleApply"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        csv_nis = data['csv_nis']
        self.process_csv(csv_nis)
        api.portal.show_message(message="Import successfull!",
                                request=self.request)

    def process_csv(self, csv_nis):
        """process_csv"""
        csv_data_nis = csv_nis.data
        csv_text_nis = csv_data_nis.decode('utf-8-sig')
        csv_reader_nis = csv.DictReader(
            io.StringIO(csv_text_nis))

        for row in csv_reader_nis:
            self.create_content(row)

    def create_content(self, row):
        """create_content"""
        nis_species_name_original = row.get('Species_name_original')

        if not nis_species_name_original:
            return

        content = api.content.create(
            container=self.context,
            type='non_indigenous_species',
            title=nis_species_name_original,
        )

        for title, field_name in nis_fields.items():
            setattr(content, field_name, row.get(title))

        content.reindexObject()


class NISExport(BrowserView):
    """ Export NIS data to xlsx """

    def __call__(self):
        """"""
        catalog = get_tool("portal_catalog")
        brains = catalog.searchResults(
            {
                "portal_type": [
                    "non_indigenous_species",
                ],
                "sort_on": 'id',
                "sort_order": 'ascending'
            }
        )

        out = io.BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        # add worksheet with report header data
        worksheet = workbook.add_worksheet(six.text_type('Data'))

        for i, (title, field_name) in enumerate(nis_fields.items()):
            worksheet.write(0, i, title)

        for i, brain in enumerate(brains):
            obj = brain.getObject()

            for j, (title, field_name) in enumerate(nis_fields.items()):
                value = getattr(obj, field_name, '')
                worksheet.write(i + 1, j, value)

        workbook.close()
        out.seek(0)

        sh = self.request.response.setHeader

        sh('Content-Type', 'application/vnd.openxmlformats-officedocument.'
           'spreadsheetml.sheet')
        fname = "-".join(('Marine Non Indigenous Species Data - ',
                          datetime.datetime.now().strftime('%Y-%m-%d')))
        sh('Content-Disposition',
           'attachment; filename=%s.xlsx' % fname)

        return out.read()

# from plone.restapi.deserializer.dxcontent import DeserializeFromJson
# from plone.restapi.interfaces import IDeserializeFromJson
# from plone.dexterity.interfaces import IDexterityContainer
# from plone.restapi.deserializer import json_body
# from zope.component import adapter
# from zope.interface import Interface, implementer

# @implementer(IDeserializeFromJson)
# @adapter(IDexterityContainer, Interface)
# class NISDeserializer(DeserializeFromJson):
#     """ NISDeserializer """
#     def __call__(self, validate_all=False, data=None,
#                  create=False, mask_validation_errors=True):
#         if data is None:
#             data = json_body(self.request)

#         if data and "non_indigenous_species" in data:
#             for value in data["non_indigenous_species"]:
#                 import pdb; pdb.set_trace()
#                 if isinstance(value, dict) and "@id" in value:
#                     path = value["@id"]
#                     if path.startswith("/marine/"):
#                         value["@id"] = path.replace("/marine/", "/", 1)

#         return super(NISDeserializer, self).__call__(
#             validate_all, data, create, mask_validation_errors)
