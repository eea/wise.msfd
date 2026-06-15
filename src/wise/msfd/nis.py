""" Non-indigenous species """
from urllib.parse import urlparse, parse_qs

import logging
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
from zope.interface import (
    Interface, implementer, provider, alsoProvides
)
from zope.lifecycleevent.interfaces import (
    IObjectModifiedEvent, IObjectAddedEvent
)
from zope.schema import ValidationError
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.publisher.interfaces import IPublishTraverse
from z3c.form import button, field, form
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.CMFPlone.interfaces import IPloneSiteRoot
from eea.progress.workflow.interfaces import IWorkflowProgress


logger = logging.getLogger('wise.msfd')


nis_fields = {
    "Species_name_original": "nis_species_name_original",
    "Species_name_accepted": "nis_species_name_accepted",
    "ScientificName_accepted": "nis_scientificname_accepted",
    "List": "nis_list",
    "Subregion": "nis_subregion",
    "Region": "nis_region",
    "Country": "nis_country",
    "Status comment": "nis_status_comment",
    "STATUS": "nis_status",
    "Group": "nis_group",
    "VER-INV-PP": "nis_ver_inv_pp",
    "Taxonomy": "nis_taxonomy",
    "NS stand": "nis_ns_stand",
    "Year": "nis_year",
    "Period": "nis_period",
    "Area": "nis_area",
    "REL": "nis_rel",
    "Pathway_Probability REL": "nis_pathway_probability_rel",
    "EC": "nis_ec",
    "Pathway_Probability EC": "nis_pathway_probability_ec",
    "TC": "nis_tc",
    "Pathway_Probability TC": "nis_pathway_probability_tc",
    "TS-0ther": "nis_ts_other",
    "Pathway_Probability TS-Other": "nis_pathway_probability_ts_other",
    "TS-ball": "nis_ts_ball",
    "Pathway_Probability TS-ball": "nis_pathway_probability_ts_ball",
    "TS-hull": "nis_ts_hull",
    "Pathway_Probability TS-hull": "nis_pathway_probability_ts_hull",
    "COR": "nis_cor",
    "Pathway_Probability COR": "nis_pathway_probability_cor",
    "UNA": "nis_una",
    "Pathway_Probability UNA": "nis_pathway_probability_una",
    "UNK": "nis_unk",
    "Pathway_Probability UNK": "nis_pathway_probability_unk",
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
def nis_country_vocabulary(context):
    """nis_country_vocabulary"""

    catalog_values = get_catalog_values(
        context, "nis_country"
    )

    terms = []
    for key in catalog_values:
        if isinstance(key, (list, tuple)):
            for k in key:
                terms.append(
                    SimpleTerm(
                        k, k, k.encode("ascii", "ignore").decode("ascii")
                    )
                )
        else:
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


PERIOD_RANGES = [
    (None, 1970, "<1970"),
    (1970, 1976, "1970-1975"),
    (1976, 1982, "1976-1981"),
    (1982, 1988, "1982-1987"),
    (1988, 1994, "1988-1993"),
    (1994, 2000, "1994-1999"),
    (2000, 2006, "2000-2005"),
    (2006, 2012, "2006-2011"),
    (2012, 2018, "2012-2017"),
    (2018, 2024, "2018-2023"),
    (2024, None, "2024-"),
]


def _year_to_period(year):
    """Map a year to its reporting period range."""
    try:
        year = int(year)
    except (ValueError, TypeError):
        return None

    for start, end, period in PERIOD_RANGES:
        if (start is None or year >= start) and (end is None or year < end):
            return period
    return None


class INonIndigenousSpeciesContent(Interface):
    """ Interface for Non indigenous species content type
    """


@adapter(INonIndigenousSpeciesContent, IObjectAddedEvent)
def validate_total_on_add(obj, event):
    """validate_total_on_add"""
    _validate_total(obj)


@adapter(INonIndigenousSpeciesContent, IObjectModifiedEvent)
def validate_total_on_edit(obj, event):
    """validate_total_on_edit"""
    _validate_total(obj)


@adapter(INonIndigenousSpeciesContent, IObjectModifiedEvent)
def set_period_from_year_on_edit(obj, event):
    """Auto-set Period from Year on edit."""
    if getattr(obj, 'nis_year', None):
        period = _year_to_period(obj.nis_year)
        if period:
            obj.nis_period = period


@adapter(INonIndigenousSpeciesContent, IObjectAddedEvent)
def set_period_from_year_on_add(obj, event):
    """Auto-set Period from Year on add."""
    if getattr(obj, 'nis_year', None):
        period = _year_to_period(obj.nis_year)
        if period:
            obj.nis_period = period


def _calculate_total(obj):
    """_calculate_total"""
    total = (
        float(obj.nis_rel or 0) +
        float(obj.nis_ec or 0) +
        float(obj.nis_tc or 0) +
        float(obj.nis_ts_other or 0) +
        float(obj.nis_ts_ball or 0) +
        float(obj.nis_ts_hull or 0) +
        float(obj.nis_cor or 0) +
        float(obj.nis_una or 0) +
        float(obj.nis_unk or 0)
    )

    return total


def _validate_total(obj):
    """_validate_total"""
    total = _calculate_total(obj)

    if round(total, 6) != 1.0:
        raise BadRequest(
            "SUM of each pathway must be 1. Currently: {}".format(total)
        )
        # raise TotalValidationMessage(
        #     "SUM of each pathway must be 1. Currently: %s" % total
        # )


class TotalValidationMessage(ValidationError):
    """TotalValidationMessage"""
    __doc__ = "SUM of each pathway must be 1"


@implementer(INonIndigenousSpeciesContent)
class NonIndigenousSpeciesContent(Container):
    """NonIndigenousSpeciesContent"""

    @property
    def nis_total(self):
        """nis_total"""
        total = _calculate_total(self)

        return total


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
        if not email:
            return

        fullname = user.getProperty("fullname") or username

        subject = " You have been assigned " \
            "{} new item(s)".format(len(items))
        body = (
            "Dear {},\n\n".format(fullname) +
            "You have been assigned the following items:\n" +
            "\n".join(items)
        )

        logger.info("Subject: %s", subject)
        logger.info("Body: %s", body)

        self._send_email(email, subject, body)

    def _notify_eea_group(self, username, items):
        """Send an email notification to the assigned user."""
        user = api.user.get(username=username)
        if not user:
            return

        email = "extranet-wisemarine-nisreviewers@roles.eea.eionet.europa.eu"
        fullname = user.getProperty("fullname") or username

        subject = " {} have been assigned {}" \
                  " new item(s)".format(fullname, len(items))
        body = (
            "Dear NIS Database Reviewers,\n\n" +
            "{} have been assigned the following items:\n".format(fullname) +
            "\n".join(items)
        )

        logger.info("Subject: %s", subject)
        logger.info("Body: %s", body)

        self._send_email(email, subject, body)

    def reply(self):
        """reply"""
        alsoProvides(self.request, IDisableCSRFProtection)
        data = json.loads(self.request.get("BODY", "{}"))

        items = data.get("items", [])
        assignee = data.get("assigned_to", None)
        search = getattr(urlparse(data.get("search", "{}")), "query", "{}")
        # import pdb; pdb.set_trace()

        if items and items[0] == 'All' and search:
            filters = {
                "portal_type": ["non_indigenous_species"],
                "sort_on": "id",
                "sort_order": "ascending"
            }

            # setup filters from request
            for f in json.loads(parse_qs(search).get("query", [None])[0]):
                filters[f['i']] = f['v']

            catalog = get_tool("portal_catalog")
            brains = catalog.unrestrictedSearchResults(
                filters
            )
            items = [x.getObject().absolute_url_path() for x in brains]

        if not items or not assignee:
            raise BadRequest("Missing items or assigned_to")

        updated = []

        try:
            username = assignee.split(" (")[1].replace(")", "")
        except Exception:
            username = assignee

        for path in items:
            path = path.replace("/marine/", "/")
            obj = api.content.get(path=path)
            if not obj:
                continue
            setattr(obj, "nis_assigned_to", assignee)

            local_roles = obj.__ac_local_roles__ or {}

            for userid, roles in list(local_roles.items()):
                if userid == username:
                    continue

                if "Editor" in roles:
                    del obj.__ac_local_roles__[userid]

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


class CopyNISRecord(Service):
    """Copy an NIS record to a new item in the same folder."""

    def reply(self):
        """reply"""
        alsoProvides(self.request, IDisableCSRFProtection)

        data = {}
        for field_name in nis_fields.values():
            value = getattr(self.context, field_name, None)
            if value is not None:
                data[field_name] = value

        original_title = self.context.title
        copy_title = "{} (copy)".format(original_title)

        container = self.context.__parent__
        new_obj = api.content.create(
            container=container,
            type='non_indigenous_species',
            title=copy_title,
            **data
        )

        new_obj.nis_assigned_to = None
        new_obj.reindexObject()

        return {
            "success": True,
            "@id": new_obj.absolute_url(),
            "title": copy_title,
        }


class CheckNISDuplicates(Service):
    """Find duplicate NIS records grouped by name, region, subregion,
    country, year."""

    @staticmethod
    def _country_value(obj):
        """_country_value"""
        value = getattr(obj, 'nis_country', None) or ''
        if isinstance(value, (list, tuple)):
            return value[0] if value else ''
        return value

    def reply(self):
        """reply"""
        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog.unrestrictedSearchResults(
            portal_type='non_indigenous_species'
        )

        groups = {}
        path_to_obj = {}
        for brain in brains:
            obj = brain._unrestrictedGetObject()
            key = (
                getattr(obj, 'nis_species_name_original', None) or '',
                getattr(obj, 'nis_species_name_accepted', None) or '',
                getattr(obj, 'nis_scientificname_accepted', None) or '',
                getattr(obj, 'nis_region', None) or '',
                getattr(obj, 'nis_subregion', None) or '',
                self._country_value(obj),
                getattr(obj, 'nis_year', None) or '',
            )
            path = obj.absolute_url_path()
            groups.setdefault(key, []).append(path)
            path_to_obj[path] = obj

        workflow_tool = getToolByName(self.context, 'portal_workflow')

        duplicate_ids = []
        duplicate_groups = []
        for key, paths in groups.items():
            if len(paths) > 1:
                duplicate_ids.extend(paths)
                ser_items = []
                for path in paths:
                    obj = path_to_obj[path]
                    review_state = workflow_tool.getInfoFor(
                        obj, 'review_state', ''
                    )
                    ser_items.append({
                        '@id': path,
                        'review_state': review_state or '',
                        'nis_species_name_original': key[0],
                        'nis_species_name_accepted': key[1],
                        'nis_scientificname_accepted': key[2],
                        'nis_region': key[3],
                        'nis_subregion': key[4],
                        'nis_country': key[5],
                        'nis_status':
                            getattr(obj, 'nis_status', '') or '',
                        'nis_group':
                            getattr(obj, 'nis_group', '') or '',
                        'nis_year': key[6],
                        'nis_assigned_to':
                            getattr(obj, 'nis_assigned_to', '') or '',
                    })
                duplicate_groups.append({
                    'species_name_original': key[0],
                    'species_name_accepted': key[1],
                    'scientificname_accepted': key[2],
                    'region': key[3],
                    'subregion': key[4],
                    'country': key[5],
                    'year': key[6],
                    'items': ser_items,
                })

        return {
            'duplicate_ids': duplicate_ids,
            'groups': duplicate_groups,
        }
