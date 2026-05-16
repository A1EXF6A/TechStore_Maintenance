# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _

class TechStoreEquipment(models.Model):
    _name = 'techstore.equipment'
    _description = 'TechStore Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'

    code = fields.Char(string='Equipment Code', readonly=True, default=lambda self: _('New'), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    equipment_type = fields.Selection([
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('tablet', 'Tablet'),
        ('smartphone', 'Smartphone'),
        ('printer', 'Printer'),
        ('server', 'Server'),
        ('other', 'Other')
    ], string='Equipment Type', required=True, tracking=True)
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    serial_number = fields.Char(string='Serial Number', required=True, tracking=True)
    receipt_date = fields.Date(string='Receipt Date', default=fields.Date.context_today, tracking=True)
    has_warranty = fields.Boolean(string='Has Warranty', default=False)
    problem_description = fields.Text(string='Problem Description', tracking=True)
    observations = fields.Text(string='Observations')
    state = fields.Selection([
        ('received', 'Received'),
        ('under_repair', 'Under Repair'),
        ('repaired', 'Repaired'),
        ('delivered', 'Delivered')
    ], string='Status', default='received', tracking=True)

    _sql_constraints = [
        ('unique_serial_number', 'unique(serial_number)', 'The serial number must be unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('techstore.equipment') or _('New')
        return super(TechStoreEquipment, self).create(vals_list)
