# -*- coding: utf-8 -*-
# Copyright 2024 theaterpedia.org + ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene
from graphene.types.generic import GenericScalar
from odoo.http import request
from graphql import GraphQLError
from odoo import _
from odoo.addons.graphql_theaterpedia.schemas.objects import (
    SortEnum, Post, Blog
)

def get_post(env, post_id):
    BlogPost = env['blog.post'].with_context().sudo()
    post = BlogPost.browse(post_id)

    #TODO _07 check_access_rights('read') for post
    # Validate if the blog-post exists and if the user has access to this address
    if not post or not post.exists():
        raise GraphQLError(_('BlogPost not found.'))

    return post

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
        domain = [] # env['website'].get_current_website().website_domain()
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
    
class AddBlogPostInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    """ partner-id """
    author_id = graphene.Int(required=True)
    blog_id = graphene.Int()
    subtitle = graphene.String()
    teasertext = graphene.String()
    blocks = GenericScalar()
    meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()    

class UpdatePostInput(graphene.InputObjectType):
    id = graphene.Int(required=True)
    headline = graphene.String()
    """ partner-id """
    author_id = graphene.Int()
    overline = graphene.String()
    teasertext = graphene.String()
    blocks = GenericScalar()
    meta_title = graphene.String()
    meta_keywords = graphene.String()
    meta_description = graphene.String()

class AddPost(graphene.Mutation):
    class Arguments:
        post = AddBlogPostInput()

    Output = Post

    @staticmethod
    def mutate(self, info, post):
        env = info.context["env"]
        BlogPost = env['blog.post'].sudo().with_context(tracking_disable=True)

        values = {
            'name': post.get('headline'),
            'author_id': post.get('author_id'),
            'blog_id': post.get('blog_id'),
            'subtitle': post.get('overline'),
            'description': post.get('teasertext'),
            'blocks': post.get('blocks'),
            'website_meta_title': post.get('meta_title'),
            'website_meta_keywords': post.get('meta_keywords'),
            'website_meta_description': post.get('meta_description'),               
        }

        # Create post entry
        post = BlogPost.create(values)

        return post
    
class UpdatePost(graphene.Mutation):
    class Arguments:
        post = UpdatePostInput(required=True)

    Output = Post

    @staticmethod
    def mutate(self, info, post):
        env = info.context["env"]
        BlogPost = get_post(env, post['id'])

        values = {
            'name': post.get('headline'),
            'author_id': post.get('author_id'),
            'subtitle': post.get('overline'),
            'description': post.get('teasertext'),
            'blocks': post.get('blocks'),
            'website_meta_title': post.get('meta_title'),
            'website_meta_keywords': post.get('meta_keywords'),
            'website_meta_description': post.get('meta_description'),            
        }

        if post.get('headline'):
            values.update({'name': post['headline']})
        if post.get('author_id'):
            values.update({'author_id': post['author_id']})
        if post.get('overline'):
            values.update({'subtitle': post['overline']})
        if post.get('teasertext'):
            values.update({'description': post['teasertext']})
        if post.get('blocks'):
            values.update({'blocks': post['blocks']})
        if post.get('meta_title'):
            values.update({'website_meta_title': post['meta_title']})            
        if post.get('meta_keywords'):
            values.update({'website_meta_keywords': post['meta_keywords']})               
        if post.get('meta_description'):
            values.update({'website_meta_description': post['meta_description']})                 

        if values:
            BlogPost.write(values)

        return BlogPost
    
class BlogPostMutation(graphene.ObjectType):
    add_post = AddPost.Field(description='Add new blogpost and make it active.')
    update_post = UpdatePost.Field(description="Update a blogpost and make it active.")
