# pyrefly: ignore [missing-import]
from odoo import models, fields, api

class TechStoreMaintenanceHistory(models.Model):
    _name = 'techstore.maintenance.history'
    _description = 'Historial de Estados del Mantenimiento'
    _order = 'change_date desc'

    maintenance_id = fields.Many2one('techstore.maintenance', string='Mantenimiento', ondelete='cascade', required=True)
    old_state = fields.Char(string='Estado Anterior')
    new_state = fields.Char(string='Nuevo Estado')
    user_id = fields.Many2one('res.users', string='Usuario Responsable', default=lambda self: self.env.user)
    change_date = fields.Datetime(string='Fecha de Cambio', default=fields.Datetime.now)
    comment = fields.Text(string='Comentario')
