# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphql import GraphQLError
from odoo.http import request
from odoo import _
from odoo.osv import expression

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Event, EventStage, EventTypeEnum
)


def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        if field == 'date':
            sorting += 'date_begin %s' % val.value
        else:
            sorting += '%s %s' % (field, val.value)

    # Add id as last factor, so we can consistently get the same results
    if sorting:
        sorting += ', id ASC'
    else:
        sorting = 'id ASC'

    return sorting


def get_search_domain(env, search, **kwargs):
    domains = []

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
    if kwargs.get('address_id', False):
        domains.append([('address_id', '=', kwargs['address_id'])])

    # Filter by stages or default to 2 or 3
    if kwargs.get('stages', False):
        stages = [stage.value for stage in kwargs.get['stages']]
        domain += [('stage_id', 'in', stages)]
    else:
        domain += [('stage_id', 'in', [2, 3])]

    # Filter With Name
    if kwargs.get('name', False):
        name = kwargs['name']
        for n in name.split(" "):
            domains.append([('name', 'ilike', n)])

    if search:
        for srch in search.split(" "):
            domains.append([
                '|', '|', ('name', 'ilike', srch), ('description_sale', 'like', srch), ('default_code', 'like', srch)])

    """  partial_domain = domains.copy()

    # Product Price Filter
    if kwargs.get('min_price', False):
        domains.append([('list_price', '>=', float(kwargs['min_price']))])
    if kwargs.get('max_price', False):
        domains.append([('list_price', '<=', float(kwargs['max_price']))])

    # Deprecated: filter with Attribute Value
    if kwargs.get('attribute_value_id', False):
        domains.append([('attribute_line_ids.value_ids', 'in', kwargs['attribute_value_id'])])

    # Filter with Attribute Value
    if kwargs.get('attrib_values', False):
        attributes = {}
        attributes_domain = []

        for value in kwargs['attrib_values']:
            try:
                value = value.split('-')
                if len(value) != 2:
                    continue

                attribute_id = int(value[0])
                attribute_value_id = int(value[1])
            except ValueError:
                continue

            if attribute_id not in attributes:
                attributes[attribute_id] = []

            attributes[attribute_id].append(attribute_value_id)

        for key, value in attributes.items():
            attributes_domain.append([('attribute_line_ids.value_ids', 'in', value)])

        attributes_domain = expression.AND(attributes_domain)
        domains.append(attributes_domain)

    return expression.AND(domains), expression.AND(partial_domain) """
    return domains

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
    return events, total_count


class Events(graphene.Interface):
    events = graphene.List(Event)
    total_count = graphene.Int(required=True)
    # attribute_values = graphene.List(AttributeValue)
    min_date = graphene.String()
    max_date = graphene.String()


class EventList(graphene.ObjectType):
    class Meta:
        interfaces = (Events,)


class EventFilterInput(graphene.InputObjectType):
    ids = graphene.List(graphene.Int)
    published = graphene.Boolean()
    #TODO _06 remove Enum and get EventType from table event_type
    event_type = graphene.Field(EventTypeEnum)
    address_id = graphene.List(graphene.Int)
    stages = graphene.List(EventStage)
    name = graphene.String()
    #TODO _06 build min_date and max_date-logic
    # need to implement date-conversions to get a meaningful mapping in get_event_list
    min_date = graphene.String()
    max_date = graphene.String()


class EventSortInput(graphene.InputObjectType):
    id = SortEnum()
    name = SortEnum()
    date = SortEnum()


""" class EventVariant(graphene.Interface):
    event = graphene.Field(Event)
    product = graphene.Field(Event)
    product_template_id = graphene.Int()
    display_name = graphene.String()
    display_image = graphene.Boolean()
    price = graphene.Float()
    list_price = graphene.String()
    has_discounted_price = graphene.Boolean()
    is_combination_possible = graphene.Boolean()


class EventVariantData(graphene.ObjectType):
    class Meta:
        interfaces = (EventVariant,) """


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
    # attribute = graphene.Field(
    #    Attribute,
    #    required=True,
    #    id=graphene.Int(),
    #)
    #event_variant = graphene.Field(
    #    EventVariant,
    #    required=True,
    #    product_template_id=graphene.Int(),
    #    combination_id=graphene.List(graphene.Int)
    #)

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
        return EventList(events=events, total_count=total_count,
                           min_date=min_date, max_date=max_date)

    # @staticmethod
    # def resolve_attribute(self, info, id):
    #    return info.context["env"]["product.attribute"].search([('id', '=', id)], limit=1)

"""     @staticmethod
    def resolve_product_variant(self, info, product_template_id, combination_id):
        env = info.context["env"]

        website = env['website'].get_current_website()
        request.website = website
        pricelist = website.get_current_pricelist()

        product_template = env['product.template'].browse(product_template_id)
        combination = env['product.template.attribute.value'].browse(combination_id)

        variant_info = product_template._get_combination_info(combination, pricelist)

        product = env['product.product'].browse(variant_info['product_id'])

        # Condition to verify if Product exist
        if not product:
            raise GraphQLError(_('Product does not exist'))

        is_combination_possible = product_template._is_combination_possible(combination)

        # Condition to Verify if Product is active or if combination exist
        if not product.active or not is_combination_possible:
            variant_info['is_combination_possible'] = False
        else:
            variant_info['is_combination_possible'] = True

        return ProductVariantData(
            product=product,
            product_template_id=variant_info['product_template_id'],
            display_name=variant_info['display_name'],
            display_image=variant_info['display_image'],
            price=variant_info['price'],
            list_price=variant_info['list_price'],
            has_discounted_price=variant_info['has_discounted_price'],
            is_combination_possible=variant_info['is_combination_possible']
        ) """
