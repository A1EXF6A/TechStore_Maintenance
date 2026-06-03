from odoo import models, fields, api


class TechStoreEquipmentState(models.Model):
    _name = 'techstore.equipment.state'
    _description = 'Estado de Equipo'
    _order = 'name'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True, translate=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', '¡El código del estado debe ser único!')
    ]

    @api.model
    def get_default_state(self):
        return self.search([('code', '=', 'nuevo')], limit=1)
