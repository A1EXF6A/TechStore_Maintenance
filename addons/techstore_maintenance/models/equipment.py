# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TechStoreEquipment(models.Model):
    _name = 'techstore.equipment'
    _description = 'Equipo TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'

    code = fields.Char(string='Código de Equipo', readonly=True, default=lambda self: _('Nuevo'), tracking=True)
    client_id = fields.Many2one('techstore.client', string='Cliente', required=True, tracking=True)
    equipment_type_id = fields.Many2one('techstore.equipment.type', string='Tipo de Equipo', required=True, tracking=True)
    brand = fields.Char(string='Marca', tracking=True)
    model = fields.Char(string='Modelo', tracking=True)
    serial_number = fields.Char(string='Número de Serie', required=True, tracking=True)
    receipt_date = fields.Date(string='Fecha de Recepción', default=fields.Date.context_today, tracking=True)
    has_warranty = fields.Boolean(string='Tiene Garantía', default=False)
    problem_description = fields.Text(string='Descripción del Problema', required=True, tracking=True)
    observations = fields.Text(string='Observaciones')
    # Keep a selection for workflow/statusbar compatibility but provide a Many2one model
    state = fields.Selection([
        ('received', 'Ingresado'),
        ('under_repair', 'En Reparación'),
        ('repaired', 'Reparado'),
        ('delivered', 'Entregado')
    ], string='Estado', default='received', tracking=True)

    state_id = fields.Many2one('techstore.equipment.state', string='Estado (registro)', default=lambda self: self.env['techstore.equipment.state'].get_default_state(), tracking=True)

    # relacionar mantenimientos al equipo para mostrar historial
    maintenance_ids = fields.One2many('techstore.maintenance', 'equipment_id', string='Mantenimientos')

    _sql_constraints = [
        ('unique_serial_number', 'unique(serial_number)', '¡El número de serie debe ser único!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('Nuevo')) == _('Nuevo'):
                vals['code'] = self.env['ir.sequence'].next_by_code('techstore.equipment') or _('Nuevo')
        return super(TechStoreEquipment, self).create(vals_list)

    @api.constrains('problem_description', 'serial_number')
    def _check_problem_description(self):
        for rec in self:
            if not rec.problem_description or not rec.problem_description.strip():
                raise ValidationError(_("Por favor, ingrese una descripción detallada del problema antes de registrar el equipo."))

