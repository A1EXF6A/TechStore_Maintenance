# pyrefly: ignore [missing-import]
from odoo import models, fields

class TechStoreSpecialty(models.Model):
    _name = 'techstore.specialty'
    _description = 'Especialidad Técnica'
    _order = 'name'

    name = fields.Char(string='Nombre de Especialidad', required=True, translate=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', '¡El nombre de la especialidad debe ser único!')
    ]
