# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from odoo.http import request

from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Post, Blog
)

def get_search_order(sort):
    sorting = ''
    for field, val in sort.items():
        if sorting:
            sorting += ', '
        sorting += '%s %s' % (field, val.value)

    return sorting
    
class PostFilterInput(graphene.InputObjectType):
    blogs = graphene.List(graphene.Int)
    is_published = graphene.Boolean()

class Posts(graphene.Interface):
    posts = graphene.List(Post)
    total_count = graphene.Int(required=True)

class PostSortInput(graphene.InputObjectType):
    id = SortEnum()

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
        filter=graphene.Argument(PostFilterInput, default_value={}),
        current_page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
        search=graphene.String(default_value=False),
        sort=graphene.Argument(PostSortInput, default_value={})        
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
    def resolve_posts(self, info, filter, current_page, page_size, sort, search):
        env = info.context["env"]
        domain = env['website'].get_current_website().website_domain()
        order = get_search_order(sort)

        # Filter by blogs or default to all
        if filter.get('blogs', False):
            blog_ids = [blog_id for blog_id in filter['blogs']]
            domain += [('blog_id', 'in', blog_ids)]

        # Filter by is_published
        if filter.get('is_published', False):
            domain += [('is_published', '=', 'true')]

        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]

        # First offset is 0 but first page is 1
        if current_page > 1:
            offset = (current_page - 1) * page_size
        else:
            offset = 0

        BlogPosts = env["blog.post"]
        total_count = BlogPosts.search_count(domain)
        posts = BlogPosts.search(
            domain, limit=page_size, offset=offset, order=order)
        return PostList(posts=posts, total_count=total_count)        
