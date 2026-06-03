from odoo import models, fields


class TechStoreEquipmentType(models.Model):
    _name = 'techstore.equipment.type'
    _description = 'Tipo de Equipo'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True, translate=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', '¡El nombre del tipo de equipo debe ser único!')
    ]
