# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.http import request

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    DomainUser
)

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    if not sorting:
        sorting = 'sequence ASC, id ASC'

    return sorting

class DomainUsers(graphene.Interface):
    domainusers = graphene.List(DomainUser)
    total_count = graphene.Int(required=True)


class DomainUserList(graphene.ObjectType):
    class Meta:
        interfaces = (DomainUsers,)


class DomainUserQuery(graphene.ObjectType):
    domainuser = graphene.Field(
        DomainUser,
        id=graphene.Int(),
        # slug=graphene.String(default_value=None),
    )
    domainusers = graphene.Field(
        DomainUsers,
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        # search=graphene.String(default_value=False),
    )

    @staticmethod
    def resolve_domainuser(self, info, id=None, slug=None):
        env = info.context['env']
        DomainUser = env['crearis.domainuser'].sudo()

        if id:
            domainuser = DomainUser.search([('id', '=', id)], limit=1)
        # elif slug:
        #    domainuser = DomainUser.search([('website_slug', '=', slug)], limit=1)
        else:
            domainuser = DomainUser

        if domainuser and not domainuser.can_access_from_current_website():
            website = env['website'].get_current_website()
            request.website = website
            if not domainuser.can_access_from_current_website():
                domainuser = DomainUser

        return domainuser

    @staticmethod
    def resolve_domainusers(self, info, current_page, page_size):
        env = info.context["env"]
        domain_id = env['website'].get_current_website().id

        DomainUsers = env['crearis.domainuser'].sudo()

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        if domain_id:
            domainusers = DomainUsers.search([('domain_id', '=', domain_id)], limit=page_size, offset=offset)

        return DomainUserList(domainusers=domainusers, total_count=20)
