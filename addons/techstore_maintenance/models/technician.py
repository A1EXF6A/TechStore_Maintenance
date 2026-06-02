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
    specialty_id = fields.Many2one('techstore.specialty', string='Especialidad', tracking=True)
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

    @api.constrains('identification')
    def _check_identification(self):
        for rec in self:
            if not rec.identification:
                continue
            cedula = rec.identification.strip()
            if len(cedula) != 10 or not cedula.isdigit():
                raise ValidationError(_("La identificación (cédula) debe tener exactamente 10 dígitos."))
            
            province = int(cedula[:2])
            if not (1 <= province <= 24 or province == 30):
                raise ValidationError(_("La identificación no corresponde a una provincia ecuatoriana válida (primeros dos dígitos de 01 a 24, o 30)."))
            
            third_digit = int(cedula[2])
            if third_digit >= 6:
                raise ValidationError(_("El tercer dígito de la cédula debe ser menor a 6."))
            
            coefs = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            for i in range(9):
                val = int(cedula[i]) * coefs[i]
                if val >= 10:
                    val -= 9
                total += val
            
            check_digit = int(cedula[9])
            calculated_check = 10 - (total % 10)
            if calculated_check == 10:
                calculated_check = 0
                
            if check_digit != calculated_check:
                raise ValidationError(_("La identificación ingresada no es una cédula ecuatoriana válida por algoritmo de módulo 10."))

    @api.constrains('phone')
    def _check_phone(self):
        for rec in self:
            if not rec.phone:
                raise ValidationError(_("El número de teléfono es obligatorio."))
            # Extract digits only to check exact length of 10
            digits_phone = ''.join(c for c in rec.phone if c.isdigit())
            if len(digits_phone) != 10:
                raise ValidationError(_("El número de teléfono debe contener exactamente 10 dígitos (por ejemplo, 0999999999)."))


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
