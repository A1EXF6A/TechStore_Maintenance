# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError
from datetime import datetime

class TechStoreMaintenance(models.Model):
    _name = 'techstore.maintenance'
    _description = 'Solicitud de Mantenimiento TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'number'

    number = fields.Char(string='Número de Mantenimiento', readonly=True, default=lambda self: _('Nuevo'), tracking=True)
    client_id = fields.Many2one('techstore.client', string='Cliente', required=True, tracking=True)
    equipment_id = fields.Many2one('techstore.equipment', string='Equipo', required=True, tracking=True, domain="[('client_id', '=', client_id)]")
    technician_id = fields.Many2one('techstore.technician', string='Técnico Asignado', tracking=True)

    request_date = fields.Datetime(string='Fecha de Solicitud', default=fields.Datetime.now, tracking=True)
    start_date = fields.Datetime(string='Fecha de Inicio', tracking=True)
    end_date = fields.Datetime(string='Fecha de Fin', tracking=True)

    maintenance_type = fields.Selection([
        ('preventive', 'Preventivo'),
        ('corrective', 'Correctivo'),
        ('diagnostic', 'Diagnóstico')
    ], string='Tipo de Mantenimiento', default='preventive', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Media'),
        ('2', 'Alta'),
        ('3', 'Crítica')
    ], string='Prioridad', default='1', tracking=True)

    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('en_proceso', 'En Proceso'),
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='nuevo', tracking=True)

    description = fields.Text(string='Descripción del Problema', required=True)
    diagnosis = fields.Text(string='Diagnóstico Técnico')
    solution = fields.Text(string='Solución Aplicada')

    estimated_cost = fields.Float(string='Costo Estimado')
    final_cost = fields.Float(string='Costo Final')

    estimated_time = fields.Float(string='Tiempo Estimado (Horas)')
    real_time = fields.Float(string='Tiempo Real Empleado (Horas)', compute='_compute_real_time', store=True)

    customer_satisfaction = fields.Selection([
        ('1', 'Malo'),
        ('2', 'Regular'),
        ('3', 'Bueno'),
        ('4', 'Excelente')
    ], string='Satisfacción del Cliente')

    observations = fields.Text(string='Observaciones')
    active = fields.Boolean(default=True, string='Activo')
    history_ids = fields.One2many('techstore.maintenance.history', 'maintenance_id', string='Historial de Estados')

    @api.depends('start_date', 'end_date')
    def _compute_real_time(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                duration = rec.end_date - rec.start_date
                rec.real_time = duration.total_seconds() / 3600.0
            else:
                rec.real_time = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', _('Nuevo')) == _('Nuevo'):
                vals['number'] = self.env['ir.sequence'].next_by_code('techstore.maintenance') or _('Nuevo')
        # Antes de crear, si el usuario es técnico (y no admin/supervisor), asignarlo automáticamente
        user = self.env.user
        is_tech_user = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
        # buscar técnico asociado al usuario
        tech_rec = self.env['techstore.technician'].search([('user_id', '=', user.id)], limit=1)

        for vals in vals_list:
            if is_tech_user and not (is_admin or is_sup):
                # siempre asignar al técnico vinculado del user si existe
                if tech_rec:
                    vals['technician_id'] = tech_rec.id
                else:
                    # si no hay técnico vinculado, dejamos el valor tal cual (se validará después)
                    pass

        records = super(TechStoreMaintenance, self).create(vals_list)
        for record in records:
            record._create_history_log('nuevo', 'Mantenimiento Creado')
            self.env['techstore.maintenance.metrics'].sudo().create({'maintenance_id': record.id})
            if record.equipment_id:
                record.equipment_id.state = 'received'
        return records

    def write(self, vals):
        for rec in self:
            if rec.state in ('finalizado', 'cancelado') and not self.env.su:
                user_fields = {
                    'client_id', 'equipment_id', 'technician_id', 'maintenance_type', 'priority',
                    'description', 'diagnosis', 'solution', 'estimated_cost', 'final_cost',
                    'estimated_time', 'customer_satisfaction', 'observations', 'active'
                }
                if any(field in vals for field in user_fields):
                    raise ValidationError(_("No se puede modificar un mantenimiento que se encuentra en estado Finalizado o Cancelado."))

        user = self.env.user
        is_tech_user = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')

        # Restricción: si usuario es técnico (no admin/sup) no puede reasignar técnicos a otros
        if 'technician_id' in vals and is_tech_user and not (is_admin or is_sup):
            # permitir solo asignarse a sí mismo
            tech_rec = self.env['techstore.technician'].search([('user_id', '=', user.id)], limit=1)
            if not tech_rec or vals.get('technician_id') != tech_rec.id:
                raise ValidationError(_('Solo el administrador o supervisor puede asignar o cambiar técnicos.'))

        if 'state' in vals:
            new_state = vals['state']
            for rec in self:
                if rec.state != new_state:
                    rec._create_history_log(new_state, f"Estado cambiado de {rec.state} a {new_state}")

                    if new_state == 'en_proceso' and not rec.start_date:
                        pass

        res = super(TechStoreMaintenance, self).write(vals)

        if 'state' in vals:
            new_state = vals['state']
            if new_state == 'en_proceso':
                self.filtered(lambda r: not r.start_date).start_date = fields.Datetime.now()
            elif new_state == 'finalizado':
                self.filtered(lambda r: not r.end_date).end_date = fields.Datetime.now()

            for rec in self:
                if rec.equipment_id:
                    if new_state in ('nuevo', 'asignado'):
                        rec.equipment_id.state = 'received'
                    elif new_state in ('en_proceso', 'pendiente'):
                        rec.equipment_id.state = 'under_repair'
                    elif new_state == 'finalizado':
                        rec.equipment_id.state = 'repaired'

        return res

    def _create_history_log(self, new_state, comment):
        custom_comment = self.env.context.get('custom_comment')
        self.env['techstore.maintenance.history'].sudo().create({
            'maintenance_id': self.id,
            'old_state': self.state if self.id else 'nuevo',
            'new_state': new_state,
            'user_id': self.env.user.id,
            'comment': custom_comment or comment
        })

    @api.onchange('priority')
    def _onchange_priority(self):
        if self.priority == '3':
            return {
                'warning': {
                    'title': _("Prioridad Crítica"),
                    'message': _("Ha seleccionado prioridad Crítica. Por favor asegure atención inmediata a este mantenimiento."),
                }
            }

    @api.constrains('equipment_id')
    def _check_equipment_received(self):
        for rec in self:
            if rec.equipment_id and rec.equipment_id.state != 'received':
                user = self.env.user
                is_tech = user.has_group('techstore_maintenance.group_techstore_technician')
                is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
                is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
                if is_tech and not (is_admin or is_sup):
                    raise ValidationError(_("El técnico solo puede registrar mantenimientos para equipos que estén en estado 'Recibido'."))

    def action_to_asignado(self):
        return self._open_state_wizard('asignado', _('Mantenimiento Asignado'))

    def action_to_en_proceso(self):
        return self._open_state_wizard('en_proceso', _('Mantenimiento En Proceso'))

    def action_to_pendiente(self):
        return self._open_state_wizard('pendiente', _('Mantenimiento Pendiente'))

    def action_to_finalizado(self):
        return self._open_state_wizard('finalizado', _('Mantenimiento Finalizado'))

    def action_to_cancelado(self):
        return self._open_state_wizard('cancelado', _('Mantenimiento Cancelado'))

    def _open_state_wizard(self, target_state, default_comment):
        self.ensure_one()
        wizard = self.env['techstore.maintenance.state.wizard'].create({
            'maintenance_id': self.id,
            'old_state': self.state,
            'new_state': target_state,
            'comment': default_comment
        })
        return {
            'name': _('Historial de Estados'),
            'type': 'ir.actions.act_window',
            'res_model': 'techstore.maintenance.state.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }


