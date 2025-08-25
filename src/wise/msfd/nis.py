""" Non-indigenous species """

import json
import datetime
import csv
import io
import six
import xlsxwriter

from zExceptions import BadRequest
from plone import api
from plone.api.portal import get_tool
from plone.dexterity.content import Container
from plone.namedfile.field import NamedFile
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zope.component import adapter, queryAdapter
from zope.interface import Interface, implementer, provider, alsoProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.publisher.interfaces import IPublishTraverse
from z3c.form import button, field, form
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.CMFPlone.interfaces import IPloneSiteRoot

from eea.progress.workflow.interfaces import IWorkflowProgress


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
def nis_experts_vocabulary(context):
    """nis_experts_vocabulary"""

    terms = []
    group_id = "extranet-wisemarine-nisexternalexperts"

    group = api.group.get(group_id)

    if group:
        for user in group.getGroupMembers():
            title = "{} ({})".format(
                user.getProperty("fullname") or user.id,
                user.id
            )
            terms.append(
                SimpleTerm(
                    value=title,
                    token=title,
                    title=title
                )
            )

        terms.append(
            SimpleTerm(
                value="laszlo-reader",
                token="laszlo-reader",
                title="laszlo-reader"
            )
        )

    return SimpleVocabulary(terms)


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
        """call"""
        filters = {
            "portal_type": ["non_indigenous_species"],
            "sort_on": "id",
            "sort_order": "ascending"
        }

        # setup filters from request
        for f in json.loads(self.request.form.get("query", "{}")):
            filters[f['i']] = f['v']

        catalog = get_tool("portal_catalog")
        brains = catalog.unrestrictedSearchResults(
            filters
        )

        out = io.BytesIO()
        workbook = xlsxwriter.Workbook(out, {'in_memory': True})

        # add worksheet with report header data
        worksheet = workbook.add_worksheet(six.text_type('Data'))

        for i, (title, field_name) in enumerate(nis_fields.items()):
            worksheet.write(0, i, title)

        for i, brain in enumerate(brains):
            # obj = brain.getObject()
            obj = brain._unrestrictedGetObject()

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


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class WorkflowProgress(object):
    """ Get workflow progress
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {
            "workflow.progress": {
                "@id": "{}/@workflow.progress.nis".format(
                    self.context.absolute_url())
            }
        }
        if not expand:
            return result

        if IPloneSiteRoot.providedBy(self.context):
            return result

        progress = queryAdapter(self.context, IWorkflowProgress)
        if progress:
            result["workflow.progress"]['steps'] = json_compatible(
                progress.steps)
            result["workflow.progress"]['done'] = json_compatible(
                progress.done)
            result["workflow.progress"]['transitions'] = json_compatible(
                progress.transitions)
        return result


class WorkflowProgressGet(Service):
    """Get workflow progress information"""

    def reply(self):
        """ Reply
        """
        info = WorkflowProgress(self.context, self.request)
        return info(expand=True)["workflow.progress"]


@implementer(IPublishTraverse)
class BulkAssign(Service):
    """Bulk assign content items to a user."""

    def __init__(self, context, request):
        super(BulkAssign, self).__init__(context, request)
        self.params = []

    def publishTraverse(self, request, name):
        """publishTraverse"""
        self.params.append(name)
        return self

    def _send_email(self, email, subject, body):
        """_send_email"""
        try:
            api.portal.send_email(
                recipient=email,
                sender="wise-marine@eea.europa.eu",
                subject=subject,
                body=body,
            )
        except Exception as e:
            api.portal.show_message(
                message="Failed to notify user: {}".format(str(e)),
                request=self.request,
                type="error"
            )

    def _notify_user(self, username, items):
        """Send an email notification to the assigned user."""
        user = api.user.get(username=username)
        if not user:
            return

        email = user.getProperty("email", "")
        fullname = user.getProperty("fullname", username)

        if not email:
            return

        subject = "[water.europa.eu - NIS] You have been assigned " \
            "{} new item(s)".format(len(items))
        body = (
            "Dear {},\n\n".format(fullname) +
            "You have been assigned the following items:\n" +
            "\n".join(items)
        )

        self._send_email(email, subject, body)

    def _notify_eea_group(self, username, items):
        """Send an email notification to the assigned user."""
        user = api.user.get(username=username)
        if not user:
            return

        email = "extranet-wisemarine-nisreviewers@roles.eea.eionet.europa.eu"
        fullname = user.getProperty("fullname", username)

        subject = "[water.europa.eu - NIS] {} have been assigned {}" \
                  "new item(s)".format(fullname, len(items))
        body = (
            "Dear NIS Database Reviewers,\n\n" +
            "{} have been assigned the following items:\n".format(fullname) +
            "\n".join(items)
        )

        self._send_email(email, subject, body)

    def reply(self):
        """reply"""
        alsoProvides(self.request, IDisableCSRFProtection)
        data = json.loads(self.request.get("BODY", "{}"))

        items = data.get("items", [])
        assignee = data.get("assigned_to", None)

        if not items or not assignee:
            raise BadRequest("Missing items or assigned_to")

        updated = []

        try:
            username = assignee.split(" (")[1].replace(")", "")
        except Exception:
            username = assignee

        for path in items:
            obj = api.content.get(path=path)
            if not obj:
                continue
            setattr(obj, "nis_assigned_to", assignee)
            api.user.grant_roles(username=username, roles=["Editor"], obj=obj)
            obj.reindexObject()
            updated.append(obj.absolute_url())

        self._notify_user(username, updated)
        self._notify_eea_group(username, updated)

        return {
            "success": True,
            "updated": updated,
            "assigned_to": assignee,
        }


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
