""" Non-indigenous species """
import csv
import io

from plone import api
from plone.dexterity.content import Container
from plone.namedfile.field import NamedFile
from zope.interface import Interface, implementer
from z3c.form import button, field, form


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

        content = api.content.create(
            container=self.context,
            type='non_indigenous_species',
            title=nis_species_name_original,
        )

        # Set only the attributes that exist in your XML/model_source
        content.nis_species_name_original = nis_species_name_original
        content.nis_species_name_accepted = row.get('Species_name_accepted')
        content.nis_scientificname_accepted = row.get(
            'ScientificName_accepted')
        # content.nis_list = ''
        content.nis_subregion = row.get('Subregion')
        content.nis_region = row.get('Region')

        content.nis_status_comment = row.get('Status comment')
        content.nis_status = row.get('STATUS')
        content.nis_group = row.get('Group')
        content.nis_ver_inv_pp = row.get('VER-INV-PP')
        # content.nis_taxonomy = ''
        # content.nis_ns_stand = ''
        content.nis_year = row.get('Year')
        content.nis_period = row.get('Period')
        # content.nis_country = ''
        # content.nis_area = ''

        content.nis_rel = row.get('REL')
        content.nis_ec = row.get('EC')
        content.nis_tc = row.get('TC')
        content.nis_ts_other = row.get('TS-Other')
        content.nis_ts_ball = row.get('TS-ball')
        content.nis_ts_hull = row.get('TS-hull')
        content.nis_cor = row.get('COR')
        content.nis_una = row.get('UNA')
        content.nis_unk = row.get('UNK')
        content.nis_total = row.get('Total')
        content.nis_pathway_probability = row.get('Pathway_Probability')
        content.nis_comment = row.get('Comment')

        content.reindexObject()
