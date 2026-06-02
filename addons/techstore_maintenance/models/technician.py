from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re

class TechStoreTechnician(models.Model):
    _name = 'techstore.technician'
    _description = 'Técnico de TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre Completo', required=True, tracking=True)
    identification = fields.Char(string='Identificación', required=True, tracking=True)
    phone = fields.Char(string='Teléfono', required=True, tracking=True)
    email = fields.Char(string='Correo Electrónico', tracking=True)
    specialty = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('networking', 'Redes'),
        ('general', 'Soporte Técnico General')
    ], string='Especialidad', default='general', tracking=True)
    active = fields.Boolean(default=True, string='Activo')
    user_id = fields.Many2one('res.users', string='Usuario Odoo Vinculado', tracking=True)
    maintenance_ids = fields.One2many('techstore.maintenance', 'technician_id', string='Mantenimientos')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Cantidad de Mantenimientos', store=True)
    workload_level = fields.Selection([
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica')
    ], compute='_compute_workload_level', string='Nivel de Carga', store=True)
    observations = fields.Text(string='Observaciones')

    _sql_constraints = [
        ('unique_identification', 'unique(identification)', '¡La identificación debe ser única!')
    ]

    @api.depends('maintenance_ids.state')
    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids.filtered(lambda m: m.state not in ('finalizado', 'cancelado')))

    @api.depends('maintenance_count')
    def _compute_workload_level(self):
        for rec in self:
            if rec.maintenance_count <= 2:
                rec.workload_level = 'low'
            elif rec.maintenance_count <= 5:
                rec.workload_level = 'medium'
            elif rec.maintenance_count <= 8:
                rec.workload_level = 'high'
            else:
                rec.workload_level = 'critical'

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and not re.match(r"[^@]+@[^@]+\.[^@]+", rec.email):
                raise ValidationError(_("Por favor ingrese una dirección de correo electrónico válida."))

    @api.constrains('phone')
    def _check_phone(self):
        for rec in self:
            if not rec.phone:
                raise ValidationError(_("El número de teléfono es obligatorio."))

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Sincroniza el correo electrónico desde el usuario Odoo vinculado."""
        if self.user_id and self.user_id.email and not self.email:
            self.email = self.user_id.email

    def action_create_or_link_user(self):
        """Crea o vincula un usuario Odoo al técnico.

        - Si ya existe un usuario con el correo del técnico, lo vincula.
        - Si no existe, crea uno nuevo y lo asigna al grupo Técnico.
        """
        self.ensure_one()

        if not self.email:
            raise UserError(_("El técnico debe tener un correo electrónico antes de crear o vincular un usuario."))

        # Buscar el grupo de técnicos
        tech_group = self.env.ref('techstore_maintenance.group_techstore_technician', raise_if_not_found=False)

        # Buscar si ya existe un usuario con ese email
        existing_user = self.env['res.users'].search([
            '|',
            ('login', '=', self.email),
            ('email', '=', self.email),
        ], limit=1)

        if existing_user:
            # Vincular el usuario existente
            self.user_id = existing_user
            # Agregar al grupo técnico si no lo tiene
            if tech_group and tech_group not in existing_user.groups_id:
                existing_user.write({'groups_id': [(4, tech_group.id)]})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Usuario Vinculado'),
                    'message': _('El usuario "%s" ha sido vinculado exitosamente al técnico.') % existing_user.name,
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            # Crear un nuevo usuario Odoo para este técnico
            new_user = self.env['res.users'].with_context(no_reset_password=True).create({
                'name': self.name,
                'login': self.email,
                'email': self.email,
                'password': 'TechStore2024!',
                'groups_id': [(6, 0, [tech_group.id])] if tech_group else [],
            })
            self.user_id = new_user
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Usuario Creado'),
                    'message': _(
                        'Se creó el usuario "%s" con correo "%s". '
                        'Contraseña temporal: TechStore2024!'
                    ) % (new_user.name, new_user.login),
                    'sticky': True,
                    'type': 'success',
                }
            }
