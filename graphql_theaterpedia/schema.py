# -*- coding: utf-8 -*-
# Copyright 2023 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo.addons.graphql_base import OdooObjectType
from odoo.addons.graphql_theaterpedia.schemas import (
    country, category, product, event, blog, post, order,
    invoice, contact_us, user_profile, sign,
    address, wishlist, shop, payment,
    mailing_list, website,
)


class Query(
    OdooObjectType,
    country.CountryQuery,
    category.CategoryQuery,
    product.ProductQuery,
    blog.BlogQuery,
    post.PostQuery,
    event.EventQuery,
    order.OrderQuery,
    invoice.InvoiceQuery,
    user_profile.UserProfileQuery,
    address.AddressQuery,
    wishlist.WishlistQuery,
    shop.ShoppingCartQuery,
    payment.PaymentQuery,
    mailing_list.MailingContactQuery,
    mailing_list.MailingListQuery,
    website.WebsiteQuery,
):
    pass


class Mutation(
    OdooObjectType,
    contact_us.ContactUsMutation,
    user_profile.UserProfileMutation,
    sign.SignMutation,
    address.AddressMutation,
    post.BlogPostMutation,
    event.EventMutation,
    wishlist.WishlistMutation,
    shop.ShopMutation,
    payment.PaymentMutation,
    payment.AdyenPaymentMutation,
    mailing_list.NewsletterSubscribeMutation,
    order.OrderMutation,
):
    pass


schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    types=[country.CountryList, category.CategoryList, blog.BlogList, post.PostList, event.EventList, product.ProductList, product.ProductVariantData, order.OrderList,
           invoice.InvoiceList, wishlist.WishlistData, shop.CartData, mailing_list.MailingContactList,
           mailing_list.MailingListList]
)
