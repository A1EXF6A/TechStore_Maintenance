# pyrefly: ignore [missing-import]
from odoo import models, fields, api

class TechStoreMaintenanceMetrics(models.Model):
    _name = 'techstore.maintenance.metrics'
    _description = 'Métricas y Rendimiento de Mantenimiento'

    # Modelo almacenado que se actualiza cuando cambia el mantenimiento.
    # Provee métricas en tiempo real de calidad y rendimiento del servicio técnico.

    maintenance_id = fields.Many2one('techstore.maintenance', string='Mantenimiento', required=True, ondelete='cascade')
    technician_id = fields.Many2one('techstore.technician', string='Técnico', related='maintenance_id.technician_id', store=True)
    client_id = fields.Many2one('techstore.client', string='Cliente', related='maintenance_id.client_id', store=True)
    maintenance_type = fields.Selection(related='maintenance_id.maintenance_type', store=True, string='Tipo de Mantenimiento')

    attention_time = fields.Float(string='Tiempo de Atención (Horas)', compute='_compute_metrics', store=True)
    resolution_time = fields.Float(string='Tiempo de Resolución (Horas)', compute='_compute_metrics', store=True)
    sla_compliance = fields.Boolean(string='Cumplimiento SLA', compute='_compute_metrics', store=True)
    delay = fields.Float(string='Retraso (Horas)', compute='_compute_metrics', store=True)
    technician_efficiency = fields.Float(string='Eficiencia del Técnico (%)', compute='_compute_metrics', store=True)
    state_changes_count = fields.Integer(string='Cambios de Estado', compute='_compute_metrics', store=True)
    quality_indicator = fields.Float(string='Indicador de Calidad', compute='_compute_metrics', store=True)

    @api.depends(
        'maintenance_id.state',
        'maintenance_id.start_date',
        'maintenance_id.end_date',
        'maintenance_id.request_date',
        'maintenance_id.estimated_time',
        'maintenance_id.real_time',
        'maintenance_id.customer_satisfaction',
    )
    def _compute_metrics(self):
        for rec in self:
            maint = rec.maintenance_id
            if not maint:
                continue

            # Tiempo de Atención (desde solicitud hasta inicio)
            if maint.start_date and maint.request_date:
                rec.attention_time = (maint.start_date - maint.request_date).total_seconds() / 3600.0
            else:
                rec.attention_time = 0.0

            # Tiempo de Resolución (desde inicio hasta fin)
            rec.resolution_time = maint.real_time

            # Cumplimiento SLA (tiempo real <= tiempo estimado)
            if maint.estimated_time > 0 and maint.real_time > 0:
                rec.sla_compliance = maint.real_time <= maint.estimated_time
                rec.delay = max(0.0, maint.real_time - maint.estimated_time)
                rec.technician_efficiency = (maint.estimated_time / maint.real_time) * 100 if maint.real_time > 0 else 0.0
            else:
                rec.sla_compliance = True
                rec.delay = 0.0
                rec.technician_efficiency = 100.0

            # Cantidad de cambios de estado
            rec.state_changes_count = self.env['techstore.maintenance.history'].search_count([
                ('maintenance_id', '=', maint.id)
            ])

            # Indicador de calidad basado en satisfacción del cliente
            satisfaction = float(maint.customer_satisfaction or 0)
            rec.quality_indicator = (satisfaction / 4.0) * 100 if satisfaction > 0 else 0.0
