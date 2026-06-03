from odoo import models, fields, api, _

class TechStoreMaintenanceStateWizard(models.TransientModel):
    _name = 'techstore.maintenance.state.wizard'
    _description = 'Historial de Estados'

    maintenance_id = fields.Many2one('techstore.maintenance', string='Mantenimiento', readonly=True, required=True)
    old_state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('en_proceso', 'En Proceso'),
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado')
    ], string='Estado Anterior', readonly=True)
    new_state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('en_proceso', 'En Proceso'),
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado')
    ], string='Nuevo Estado', readonly=True)
    change_date = fields.Datetime(string='Fecha de Cambio', default=fields.Datetime.now, readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario Responsable', default=lambda self: self.env.user, readonly=True)
    comment = fields.Text(string='Comentario', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.maintenance_id.with_context(custom_comment=self.comment).write({
            'state': self.new_state
        })
        return {'type': 'ir.actions.act_window_close'}
