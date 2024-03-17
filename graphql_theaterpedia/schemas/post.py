# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.http import request

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    Post
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

class Posts(graphene.Interface):
    posts = graphene.List(Post)
    total_count = graphene.Int(required=True)


class PostList(graphene.ObjectType):
    class Meta:
        interfaces = (Posts,)


class PostQuery(graphene.ObjectType):
    post = graphene.Field(
        Post,
        id=graphene.Int(),
        slug=graphene.String(default_value=None),
    )
    posts = graphene.Field(
        Posts,
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=20),
        search=graphene.String(default_value=False),
    )

    @staticmethod
    def resolve_post(self, info, id=None, slug=None):
        env = info.context['env']
        Post = env['blog.post'].sudo()

        if id:
            post = Post.search([('id', '=', id)], limit=1)
        elif slug:
            post = Post.search([('website_slug', '=', slug)], limit=1)
        else:
            post = Post

        if post:
            website = env['website'].get_current_website()
            request.website = website
            if not post.can_access_from_current_website():
                post = Post

        return post             

    @staticmethod
    def resolve_posts(self, info, current_page, page_size, search):
        env = info.context["env"]
        domain = env['website'].get_current_website().website_domain()

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        posts = Posts.search(
            domain, limit=page_size, offset=offset)
        return PostList(posts=posts, total_count=10)
