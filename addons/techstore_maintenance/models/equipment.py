# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _

class TechStoreEquipment(models.Model):
    _name = 'techstore.equipment'
    _description = 'Equipo TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'

    code = fields.Char(string='Código de Equipo', readonly=True, default=lambda self: _('Nuevo'), tracking=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    equipment_type = fields.Selection([
        ('laptop', 'Portátil'),
        ('desktop', 'Escritorio'),
        ('tablet', 'Tableta'),
        ('smartphone', 'Smartphone'),
        ('printer', 'Impresora'),
        ('server', 'Servidor'),
        ('other', 'Otro')
    ], string='Tipo de Equipo', required=True, tracking=True)
    brand = fields.Char(string='Marca', tracking=True)
    model = fields.Char(string='Modelo', tracking=True)
    serial_number = fields.Char(string='Número de Serie', required=True, tracking=True)
    receipt_date = fields.Date(string='Fecha de Recepción', default=fields.Date.context_today, tracking=True)
    has_warranty = fields.Boolean(string='Tiene Garantía', default=False)
    problem_description = fields.Text(string='Descripción del Problema', tracking=True)
    observations = fields.Text(string='Observaciones')
    state = fields.Selection([
        ('received', 'Recibido'),
        ('under_repair', 'En Reparación'),
        ('repaired', 'Reparado'),
        ('delivered', 'Entregado')
    ], string='Estado', default='received', tracking=True)

    _sql_constraints = [
        ('unique_serial_number', 'unique(serial_number)', '¡El número de serie debe ser único!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('Nuevo')) == _('Nuevo'):
                vals['code'] = self.env['ir.sequence'].next_by_code('techstore.equipment') or _('Nuevo')
        return super(TechStoreEquipment, self).create(vals_list)
