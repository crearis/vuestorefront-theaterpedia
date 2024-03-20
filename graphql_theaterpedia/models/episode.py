from odoo import models, fields, api

class BlogPost(models.Model):
    _inherit = "blog.post"

    blocks = fields.Char('Content Blocks', required=True, translate=False, default='')