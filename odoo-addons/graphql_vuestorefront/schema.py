# Copyright 2021 ODOOGAP/PROMPTEQUATION LDA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# disable undefined variable error, which erroneously triggers
# on forward declarations of classes in lambdas
# pylint: disable=E0602

import graphene

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.graphql_base import OdooObjectType


class Country(OdooObjectType):
    code = graphene.String(required=True)
    name = graphene.String(required=True)


class Partner(OdooObjectType):
    name = graphene.String(required=True)
    street = graphene.String()
    street2 = graphene.String()
    city = graphene.String()
    zip = graphene.String()
    country = graphene.Field(Country)
    email = graphene.String()
    phone = graphene.String()
    is_company = graphene.Boolean(required=True)
    contacts = graphene.List(graphene.NonNull(lambda: Partner), required=True)

    @staticmethod
    def resolve_country(root, info):
        return root.country_id or None

    @staticmethod
    def resolve_contacts(root, info):
        return root.child_ids


class Category(OdooObjectType):
    id = graphene.ID()
    name = graphene.String(required=True)
    slug = name
    items = graphene.List(graphene.NonNull(lambda: Category), required=True)

    @staticmethod
    def resolve_slug(root, info):
        return root.name

    @staticmethod
    def resolve_items(root, info):
        return root.child_id


class Product(OdooObjectType):
    id = graphene.ID()
    name = graphene.String()
    default_code = graphene.String()
    list_price = graphene.Float()
    categ_id = graphene.Field(Category)

    @staticmethod
    def resolve_categ_id(root, info):
        return root.categ_id or None


class Query(graphene.ObjectType):
    all_partners = graphene.List(
        graphene.NonNull(Partner),
        required=True,
        companies_only=graphene.Boolean(),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    all_categories = graphene.List(
        graphene.NonNull(Category),
        required=True,
        id=graphene.ID(),
        name=graphene.String(),
        parents_only=graphene.Boolean(),
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    all_products = graphene.List(
        graphene.NonNull(Product),
        required=True,
        limit=graphene.Int(),
        offset=graphene.Int(),
    )

    reverse = graphene.String(
        required=True,
        description="Reverse a string",
        word=graphene.String(required=True),
    )

    error_example = graphene.String()

    @staticmethod
    def resolve_all_partners(root, info, companies_only=False, limit=None, offset=None):
        domain = []
        if companies_only:
            domain.append(("is_company", "=", True))
        return info.context["env"]["res.partner"].search(
            domain, limit=limit, offset=offset
        )

    @staticmethod
    def resolve_all_categories(root, info, id=None, name=False, parents_only=False, limit=None, offset=None):
        domain = []
        if id:
            domain.append(("id", '=', id))
        if name:
            domain.append(("name", '=', name))
        if parents_only:
            domain.append(("parent_id", "=", None))
        return info.context["env"]["product.category"].search(
            domain, limit=limit, offset=offset
        )

    @staticmethod
    def resolve_all_products(root, info, limit=None, offset=None):
        domain = []
        return info.context["env"]["product.product"].search(
            domain, limit=limit, offset=offset
        )

    @staticmethod
    def resolve_reverse(root, info, word):
        return word[::-1]

    @staticmethod
    def resolve_error_example(root, info):
        raise UserError(_("UserError example"))


class CreatePartner(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        is_company = graphene.Boolean()
        raise_after_create = graphene.Boolean()

    Output = Partner

    @staticmethod
    def mutate(self, info, name, email, is_company=False, raise_after_create=False):
        env = info.context["env"]
        partner = env["res.partner"].create(
            {"name": name, "email": email, "is_company": is_company}
        )
        if raise_after_create:
            raise UserError(_("as requested"))
        return partner


class Mutation(graphene.ObjectType):
    create_partner = CreatePartner.Field(description="Documentation of CreatePartner")


schema = graphene.Schema(query=Query, mutation=Mutation)
