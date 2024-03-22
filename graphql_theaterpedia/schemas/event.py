# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _
from odoo.osv import expression

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Event, EventStage, EventType, EventEditMode
)

def get_event(env, event_id):
    Event = env['event.event'].with_context().sudo()
    event = Event.browse(event_id)

    #TODO _07 check_access_rights('read') for event
    # Validate if the blog-post exists and if the user has access to this address
    if not event or not event.exists():
        raise GraphQLError(_('Event not found.'))
    
    return event

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

def get_search_domain(env, search, **kwargs):
    domains = [env['website'].get_current_website().website_domain()]

    # Filter with ids
    if kwargs.get('ids', False):
        domains.append([('id', 'in', kwargs['ids'])])

    # Filter by published-status
    if kwargs.get('published', False):
        domains.append([('is_published', '=', kwargs['published'])])

    # Filter with Event Type
    if kwargs.get('event_type', False):
        domains.append([('event_type_id', '=', kwargs['event_type'])])

    # Filter with Address ID
    if kwargs.get('address_ids', False):
        address_ids = [address for address in kwargs.get['address_ids']]
        domains.append([('address_id', 'in', address_ids)])        

    # Filter by stages or default to 2 or 3
    if kwargs.get('stages', False):
        stages = [stage.id for stage in kwargs.get['stages']]
        domains.append([('stage_id', 'in', stages)])
    else:
        domains.append([('stage_id', 'in', [2, 3])])

    # Filter With Name
    if kwargs.get('name', False):
        name = kwargs['name']
        for n in name.split(" "):
            domains.append([('name', 'ilike', n)])

    if search:
        for srch in search.split(" "):
            domains.append([
                '|', '|', ('name', 'ilike', srch), ('subtitle', 'like', srch), ('description', 'like', srch)])
            
    #TODO _06 adopt partial_domain from product.py

    return expression.AND(domains)

def get_event_list(env, current_page, page_size, search, sort, **kwargs):
    Event = env['event.event'].sudo()
    domain = get_search_domain(env, search, **kwargs)

    # First offset is 0 but first page is 1
    if current_page > 1:
        offset = (current_page - 1) * page_size
    else:
        offset = 0
    order = get_search_order(sort)
    events = Event.search(domain, order=order)

    dates = events.mapped('date_begin')

    total_count = len(events)
    events = events[offset:offset + page_size]
    if dates:
        return events, total_count, min(dates), max(dates)
    return events, total_count, "no min date", "no max date"

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

class EventFilterInput(graphene.InputObjectType):
    ids = graphene.List(graphene.Int)
    published = graphene.Boolean()
    event_type = graphene.Int()
    edit_mode = graphene.List(EventEditMode)
    address_id = graphene.List(graphene.Int)
    stages = graphene.List(graphene.Int)
    name = graphene.String()
    #TODO _06 build min_date and max_date-logic
    # need to implement date-conversions to get a meaningful mapping in get_event_list
    min_date = graphene.String()
    max_date = graphene.String()

class EventQuery(graphene.ObjectType):
    event = graphene.Field(
        Event,
        id=graphene.Int(default_value=None),
        slug=graphene.String(default_value=None),
        barcode=graphene.String(default_value=None),
    )
    events = graphene.Field(
        Events,
        filter=graphene.Argument(EventFilterInput, default_value={}),
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
    def resolve_events(self, info, filter, current_page, page_size, search, sort):
        env = info.context["env"]
        events, total_count, min_date, max_date = get_event_list(
            env, current_page, page_size, search, sort, **filter)
        return EventList(events=events, total_count=total_count, min_date=min_date, max_date=max_date)          

class UpdateEventInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    name = graphene.String()
    subtitle = graphene.String()
    description = graphene.String()
    blocks = graphene.String()
    note = graphene.String()
    meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()

class UpdateSyncIdInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    sync_id = graphene.Int()

    
class UpdateEvent(graphene.Mutation):
    class Arguments:
        event = UpdateEventInput(required=True)

    Output = Event

    @staticmethod
    def mutate(self, info, event):
        env = info.context["env"]
        EventEvent = get_event(env, event['id'])

        values = {
            'name': event.get('name'),
            'note': event.get('note'),
            'subtitle': event.get('subtitle'),
            'description': event.get('description'),
            'website_meta_title': event.get('meta_title'),
            'website_meta_keywords': event.get('meta_keywords'),
            'website_meta_description': event.get('meta_description'),                        
        }

        if event.get('name'):
            values.update({'name': event['name']})
        if event.get('note'):
            values.update({'note': event['note']})
        if event.get('subtitle'):
            values.update({'subtitle': event['subtitle']})
        if event.get('description'):
            values.update({'description': event['description']})
        if event.get('blocks'):
            values.update({'blocks': event['blocks']}) 
        if event.get('meta_title'):
            values.update({'website_meta_title': event['meta_title']})            
        if event.get('meta_keywords'):
            values.update({'website_meta_keywords': event['meta_keywords']})               
        if event.get('meta_description'):
            values.update({'website_meta_description': event['meta_description']}) 

        if values:
            EventEvent.write(values)

        return EventEvent
    
class UpdateSyncId(graphene.Mutation):
    class Arguments:
        event = UpdateSyncIdInput(required=True)

    Output = Event

    @staticmethod
    def mutate(self, info, event):
        env = info.context["env"]
        EventEvent = get_event(env, event['id'])

        values = {
            'sync_id': event.get('sync_id'),
        }

        if event.get('sync_id'):
            values.update({'sync_id': event['sync_id']})  

        if values:
            EventEvent.write(values)        

        return EventEvent
    
class EventMutation(graphene.ObjectType):
    update_sync_id = UpdateSyncId.Field(description="Update the SyncId of an Event.")
    update_event = UpdateEvent.Field(description="Update event content.")