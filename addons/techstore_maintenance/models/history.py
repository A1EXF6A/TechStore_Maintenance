# pyrefly: ignore [missing-import]
from odoo import models, fields, api

class TechStoreMaintenanceHistory(models.Model):
    _name = 'techstore.maintenance.history'
    _description = 'Maintenance Status History'
    _order = 'change_date desc'

    maintenance_id = fields.Many2one('techstore.maintenance', string='Maintenance', ondelete='cascade', required=True)
    old_state = fields.Char(string='Previous Status')
    new_state = fields.Char(string='New Status')
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)
    comment = fields.Text(string='Comment')
