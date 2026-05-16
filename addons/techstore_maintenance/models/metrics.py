# pyrefly: ignore [missing-import]
from odoo import models, fields, api

class TechStoreMaintenanceMetrics(models.Model):
    _name = 'techstore.maintenance.metrics'
    _description = 'Maintenance Metrics and Performance'
    _auto = False # Use a view or just a table that we populate

    # Actually, the user asked for a model with suggested fields and automatic calculations.
    # We can use a stored model or a database view. Let's use a stored model for simplicity 
    # and update it when maintenance is finished, or use a SQL view for real-time.
    # Given Odoo 18, a SQL view is very efficient for reporting.
    
    maintenance_id = fields.Many2one('techstore.maintenance', string='Maintenance', required=True, ondelete='cascade')
    technician_id = fields.Many2one('techstore.technician', string='Technician', related='maintenance_id.technician_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Client', related='maintenance_id.partner_id', store=True)
    maintenance_type = fields.Selection(related='maintenance_id.maintenance_type', store=True)
    
    attention_time = fields.Float(string='Time to Attention (Hours)', compute='_compute_metrics', store=True)
    resolution_time = fields.Float(string='Time to Resolution (Hours)', compute='_compute_metrics', store=True)
    sla_compliance = fields.Boolean(string='SLA Compliance', compute='_compute_metrics', store=True)
    delay = fields.Float(string='Delay (Hours)', compute='_compute_metrics', store=True)
    technician_efficiency = fields.Float(string='Technician Efficiency (%)', compute='_compute_metrics', store=True)
    state_changes_count = fields.Integer(string='State Changes', compute='_compute_metrics', store=True)
    quality_indicator = fields.Float(string='Quality Indicator', compute='_compute_metrics', store=True)

    @api.depends('maintenance_id.state', 'maintenance_id.start_date', 'maintenance_id.end_date', 'maintenance_id.request_date', 'maintenance_id.estimated_time', 'maintenance_id.real_time', 'maintenance_id.customer_satisfaction')
    def _compute_metrics(self):
        for rec in self:
            maint = rec.maintenance_id
            if not maint:
                continue
                
            # Time to Attention (Request to Start)
            if maint.start_date and maint.request_date:
                rec.attention_time = (maint.start_date - maint.request_date).total_seconds() / 3600.0
            else:
                rec.attention_time = 0.0
                
            # Time to Resolution (Start to End)
            rec.resolution_time = maint.real_time
            
            # SLA Compliance (Real time <= Estimated time)
            if maint.estimated_time > 0 and maint.real_time > 0:
                rec.sla_compliance = maint.real_time <= maint.estimated_time
                rec.delay = max(0.0, maint.real_time - maint.estimated_time)
                rec.technician_efficiency = (maint.estimated_time / maint.real_time) * 100 if maint.real_time > 0 else 0.0
            else:
                rec.sla_compliance = True
                rec.delay = 0.0
                rec.technician_efficiency = 100.0
                
            # State Changes Count
            rec.state_changes_count = self.env['techstore.maintenance.history'].search_count([('maintenance_id', '=', maint.id)])
            
            # Quality Indicator (Based on satisfaction)
            satisfaction = float(maint.customer_satisfaction or 0)
            rec.quality_indicator = (satisfaction / 4.0) * 100 if satisfaction > 0 else 0.0

    # We need a way to ensure a metric record exists for each maintenance
    # We can do this in the maintenance model or here with a cron or action.
    # Let's override maintenance.create to create metrics.
