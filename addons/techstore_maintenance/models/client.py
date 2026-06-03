# pyrefly: ignore [missing-import]
from odoo import models, fields

class TechStoreClient(models.Model):
    _name = 'techstore.client'
    _description = 'Cliente TechStore'
    _order = 'name'

    name = fields.Char(string='Nombre o Razón Social', required=True, tracking=True)
    identification = fields.Char(string='Identificación / RUC', tracking=True)
    phone = fields.Char(string='Teléfono', tracking=True)
    email = fields.Char(string='Correo Electrónico', tracking=True)
    observations = fields.Text(string='Observaciones')

    _sql_constraints = [
        ('unique_identification', 'unique(identification)', '¡La identificación del cliente debe ser única!')
    ]
