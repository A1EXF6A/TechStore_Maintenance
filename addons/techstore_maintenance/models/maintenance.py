# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
from datetime import datetime

class TechStoreMaintenance(models.Model):
    _name = 'techstore.maintenance'
    _description = 'TechStore Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'number'

    number = fields.Char(string='Maintenance Number', readonly=True, default=lambda self: _('New'), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    equipment_id = fields.Many2one('techstore.equipment', string='Equipment', required=True, tracking=True, domain="[('partner_id', '=', partner_id)]")
    technician_id = fields.Many2one('techstore.technician', string='Assigned Technician', tracking=True)
    
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, tracking=True)
    start_date = fields.Datetime(string='Start Date', tracking=True)
    end_date = fields.Datetime(string='End Date', tracking=True)
    
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('diagnostic', 'Diagnostic')
    ], string='Maintenance Type', default='preventive', required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True)
    
    state = fields.Selection([
        ('nuevo', 'New'),
        ('asignado', 'Assigned'),
        ('en_proceso', 'In Progress'),
        ('pendiente', 'Pending'),
        ('finalizado', 'Finished'),
        ('cancelado', 'Cancelled')
    ], string='Status', default='nuevo', tracking=True)
    
    description = fields.Text(string='Problem Description', required=True)
    diagnosis = fields.Text(string='Technical Diagnosis')
    solution = fields.Text(string='Applied Solution')
    
    estimated_cost = fields.Float(string='Estimated Cost')
    final_cost = fields.Float(string='Final Cost')
    
    estimated_time = fields.Float(string='Estimated Time (Hours)')
    real_time = fields.Float(string='Real Time Employed (Hours)', compute='_compute_real_time', store=True)
    
    customer_satisfaction = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Excellent')
    ], string='Customer Satisfaction')
    
    observations = fields.Text(string='Observations')
    active = fields.Boolean(default=True)
    history_ids = fields.One2many('techstore.maintenance.history', 'maintenance_id', string='Status History')

    @api.depends('start_date', 'end_date')
    def _compute_real_time(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                duration = rec.end_date - rec.start_date
                rec.real_time = duration.total_seconds() / 3600.0
            else:
                rec.real_time = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('New')) == _('New'):
                vals['number'] = self.env['ir.sequence'].next_by_code('techstore.maintenance') or _('New')
        records = super(TechStoreMaintenance, self).create(vals_list)
        for record in records:
            record._create_history_log('nuevo', 'Maintenance Created')
            self.env['techstore.maintenance.metrics'].create({'maintenance_id': record.id})
        return records

    def write(self, vals):
        if 'state' in vals:
            new_state = vals['state']
            for rec in self:
                if rec.state != new_state:
                    rec._create_history_log(new_state, f"Status changed from {rec.state} to {new_state}")
                    
                    if new_state == 'en_proceso' and not rec.start_date:
                        # We use super().write on individual records if we need per-record logic in vals
                        # or just set the field directly on the record if it's already created.
                        # Since we are in write, we can just update the record after super()
                        pass
                        
        res = super(TechStoreMaintenance, self).write(vals)
        
        if 'state' in vals:
            if vals['state'] == 'en_proceso':
                self.filtered(lambda r: not r.start_date).start_date = fields.Datetime.now()
            elif vals['state'] == 'finalizado':
                self.filtered(lambda r: not r.end_date).end_date = fields.Datetime.now()
                
        return res

    def _create_history_log(self, new_state, comment):
        self.env['techstore.maintenance.history'].create({
            'maintenance_id': self.id,
            'old_state': self.state if self.id else 'nuevo',
            'new_state': new_state,
            'user_id': self.env.user.id,
            'comment': comment
        })

    @api.onchange('priority')
    def _onchange_priority(self):
        if self.priority == '3':
            return {
                'warning': {
                    'title': _("Critical Priority"),
                    'message': _("You have selected a Critical priority. Please ensure immediate attention to this maintenance."),
                }
            }
