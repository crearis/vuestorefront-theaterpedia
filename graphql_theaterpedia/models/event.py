from odoo import models, fields, api

class EventEvent(models.Model):
    _inherit = "event.event"

    blocks = fields.Char('Content Blocks', required=True, translate=False, default='')