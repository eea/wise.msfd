from wise.msfd.gescomponents import get_all_descriptors

from .base import BaseView


class Management(BaseView):
    """"""

    name = 'management'
    section = 'national-descriptors'

    @property
    def get_descriptors(self):
        descriptors = get_all_descriptors()

        return descriptors

    def get_groups_for_desc(self, descriptor):
        descriptor = descriptor.split('.')[0]
        group_id = 'extranet-wisemarine-msfd-tl-{}'.format(descriptor.lower())

        from Products.CMFCore.utils import getToolByName
        acl_users = getToolByName(self.context, 'acl_users')
        groups_tool = getToolByName(self.context, 'portal_groups')
        groups = acl_users.source_groups.getGroupIds()

        g = groups_tool.getGroupById(group_id)
        g_members = g.getGroupMembers()

        if not g_members:
            return '-'

        res = [x.getProperty('fullname') for x in g_members]

        return ', '.join(res)


