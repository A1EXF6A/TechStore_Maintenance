from odoo import models, fields, api, _
from odoo.exceptions import UserError

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

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and not self.env.user.has_group('techstore_maintenance.group_techstore_admin'):
            raise UserError(_("No tienes acceso para crear registros en el Historial de Estados del Mantenimiento. Esta operación está reservada para el Administrador Técnico."))
        return super(TechStoreMaintenanceHistory, self).create(vals_list)

    def write(self, vals):
        if not self.env.su and not self.env.user.has_group('techstore_maintenance.group_techstore_admin'):
            raise UserError(_("No tienes acceso para modificar registros en el Historial de Estados del Mantenimiento. Esta operación está reservada para el Administrador Técnico."))
        return super(TechStoreMaintenanceHistory, self).write(vals)

    def unlink(self):
        if not self.env.su and not self.env.user.has_group('techstore_maintenance.group_techstore_admin'):
            raise UserError(_("No tienes acceso para eliminar registros en el Historial de Estados del Mantenimiento. Esta operación está reservada para el Administrador Técnico."))
        return super(TechStoreMaintenanceHistory, self).unlink()

