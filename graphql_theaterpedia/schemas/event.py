# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Event
)

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        if field == 'date':
            sorting += 'date_begin %s' % val.value
        if field == 'stage':
            sorting += 'stage_id %s' % val.value            
        else:
            sorting += '%s %s' % (field, val.value)

    # Add id as last factor, so we can consistently get the same results
    if sorting:
        sorting += ', id ASC'
    else:
        sorting = 'date_begin ASC, id ASC'

    return sorting

class Events(graphene.Interface):
    events = graphene.List(Event)
    total_count = graphene.Int(required=True)
    # attribute_values = graphene.List(AttributeValue)
    min_date = graphene.String()
    max_date = graphene.String()


class EventList(graphene.ObjectType):
    class Meta:
        interfaces = (Events,)

class EventSortInput(graphene.InputObjectType):
    id = SortEnum()
    name = SortEnum()
    date = SortEnum()
    stage = SortEnum()

class EventQuery(graphene.ObjectType):
    event = graphene.Field(
        Event,
        id=graphene.Int(default_value=None),
        slug=graphene.String(default_value=None),
        barcode=graphene.String(default_value=None),
    )
    events = graphene.Field(
        Events,
        # filter=graphene.Argument(EventFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(EventSortInput, default_value={})
    )

    @staticmethod
    def resolve_event(self, info, id=None, slug=None, barcode=None):
        env = info.context["env"]
        Event = env["event.event"].sudo()

        if id:
            event = Event.search([('id', '=', id)], limit=1)
        #TODO _06 search by slug
        elif slug:  
            raise GraphQLError(_('Filter event.slug not yet implemented.'))
        #   event = Event.search([('website_slug', '=', slug)], limit=1)
        elif barcode:
            event = Event.search([('barcode', '=', barcode)], limit=1)
        else:
            event = Event

        if event:
            website = env['website'].get_current_website()
            request.website = website
            if not event.can_access_from_current_website():
                event = Event

        return event

    @staticmethod
    def resolve_events(self, info, current_page, page_size, search, sort):
        env = info.context["env"]
        domain = env['website'].get_current_website().website_domain()
        order = get_search_order(sort)

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        AllEvents = env["event.event"]
        total_count = AllEvents.search_count(domain)
        events = AllEvents.search(
            domain, limit=page_size, offset=offset, order=order)
        return EventList(events=events, total_count=total_count)          

