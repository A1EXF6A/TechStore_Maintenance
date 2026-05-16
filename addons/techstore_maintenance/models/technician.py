from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class TechStoreTechnician(models.Model):
    _name = 'techstore.technician'
    _description = 'TechStore Technician'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Full Name', required=True, tracking=True)
    identification = fields.Char(string='Identification', required=True, tracking=True)
    phone = fields.Char(string='Phone', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    specialty = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('networking', 'Networking'),
        ('general', 'General Technical Support')
    ], string='Specialty', default='general', tracking=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Related User', tracking=True)
    maintenance_ids = fields.One2many('techstore.maintenance', 'technician_id', string='Maintenances')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Maintenance Count', store=True)
    workload_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], compute='_compute_workload_level', string='Workload Level', store=True)
    observations = fields.Text(string='Observations')

    _sql_constraints = [
        ('unique_identification', 'unique(identification)', 'The identification must be unique!')
    ]

    @api.depends('maintenance_ids.state')
    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids.filtered(lambda m: m.state not in ('finalizado', 'cancelado')))

    @api.depends('maintenance_count')
    def _compute_workload_level(self):
        for rec in self:
            if rec.maintenance_count <= 2:
                rec.workload_level = 'low'
            elif rec.maintenance_count <= 5:
                rec.workload_level = 'medium'
            elif rec.maintenance_count <= 8:
                rec.workload_level = 'high'
            else:
                rec.workload_level = 'critical'

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and not re.match(r"[^@]+@[^@]+\.[^@]+", rec.email):
                raise ValidationError(_("Please enter a valid email address."))

    @api.constrains('phone')
    def _check_phone(self):
        for rec in self:
            if not rec.phone:
                raise ValidationError(_("Phone number is mandatory."))
