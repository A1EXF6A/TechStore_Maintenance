from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, time
import io
import xlsxwriter
import base64

class TechStoreMaintenanceReportWizard(models.TransientModel):
    _name = 'techstore.maintenance.report.wizard'
    _description = 'Asistente de Reportes de Mantenimiento'

    report_type = fields.Selection([
        ('mantenimiento', 'Mantenimientos (Detallado)'),
        ('general', 'General del Sistema (Consolidado)')
    ], string='Tipo de Reporte', default='mantenimiento', required=True)

    start_date = fields.Date(string='Fecha Inicio')
    end_date = fields.Date(string='Fecha Fin')
    technician_id = fields.Many2one('techstore.technician', string='Técnico')
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('asignado', 'Asignado'),
        ('en_proceso', 'En Proceso'),
        ('pendiente', 'Pendiente'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado')
    ], string='Estado')

    is_technician_user = fields.Boolean(compute='_compute_is_technician_user')
    excel_file = fields.Binary(string='Archivo Excel', readonly=True)
    excel_filename = fields.Char(string='Nombre Archivo Excel', readonly=True)

    @api.depends_context('uid')
    def _compute_is_technician_user(self):
        user = self.env.user
        is_tech = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
        for rec in self:
            rec.is_technician_user = is_tech and not (is_admin or is_sup)

    @api.constrains('report_type')
    def _check_report_type_permission(self):
        user = self.env.user
        is_tech = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
        for rec in self:
            if is_tech and not (is_admin or is_sup) and rec.report_type == 'general':
                raise ValidationError(_("Los técnicos no tienen permiso para generar el reporte general del sistema."))

    @api.model
    def default_get(self, fields_list):
        res = super(TechStoreMaintenanceReportWizard, self).default_get(fields_list)
        user = self.env.user
        is_tech = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
        if is_tech and not (is_admin or is_sup):
            res['report_type'] = 'mantenimiento'
            tech = self.env['techstore.technician'].search([('user_id', '=', user.id)], limit=1)
            if tech:
                res['technician_id'] = tech.id
        return res

    def _get_maintenance_domain(self):
        self.ensure_one()
        domain = []
        if self.start_date:
            domain.append(('request_date', '>=', fields.Datetime.to_string(datetime.combine(self.start_date, datetime.min.time()))))
        if self.end_date:
            domain.append(('request_date', '<=', fields.Datetime.to_string(datetime.combine(self.end_date, datetime.max.time()))))
        
        user = self.env.user
        is_tech = user.has_group('techstore_maintenance.group_techstore_technician')
        is_admin = user.has_group('techstore_maintenance.group_techstore_admin')
        is_sup = user.has_group('techstore_maintenance.group_techstore_supervisor')
        
        if is_tech and not (is_admin or is_sup):
            tech = self.env['techstore.technician'].search([('user_id', '=', user.id)], limit=1)
            domain.append(('technician_id', '=', tech.id if tech else False))
        elif self.technician_id:
            domain.append(('technician_id', '=', self.technician_id.id))

        if self.state:
            domain.append(('state', '=', self.state))
            
        return domain

    def action_generate_pdf(self):
        self.ensure_one()
        return self.env.ref('techstore_maintenance.action_report_techstore_maintenance').report_action(self)

    def action_generate_excel(self):
        self.ensure_one()
        domain = self._get_maintenance_domain()
        records = self.env['techstore.maintenance'].search(domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Styling formats
        title_format = workbook.add_format({
            'bold': True, 'size': 15, 'align': 'center', 'valign': 'vcenter',
            'font_color': '#FFFFFF', 'bg_color': '#1f4e79',
        })
        filter_header_format = workbook.add_format({
            'bold': True, 'size': 10, 'font_color': '#1f4e79',
            'bottom': 1, 'bottom_color': '#1f4e79',
        })
        filter_val_format = workbook.add_format({
            'size': 10, 'bottom': 1, 'bottom_color': '#1f4e79',
        })
        header_format = workbook.add_format({
            'bold': True, 'size': 11, 'font_color': '#FFFFFF', 'bg_color': '#2f5597',
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#d9d9d9',
        })
        data_center_format = workbook.add_format({
            'size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': '#e0e0e0',
        })
        data_left_format = workbook.add_format({
            'size': 10, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'border_color': '#e0e0e0',
        })
        data_currency_format = workbook.add_format({
            'size': 10, 'align': 'right', 'valign': 'vcenter',
            'num_format': '$#,##0.00', 'border': 1, 'border_color': '#e0e0e0',
        })
        kpi_title_format = workbook.add_format({
            'bold': True, 'size': 9, 'font_color': '#595959', 'align': 'center',
            'bg_color': '#f2f2f2', 'border': 1, 'border_color': '#d9d9d9',
        })
        kpi_val_format = workbook.add_format({
            'bold': True, 'size': 12, 'font_color': '#1f4e79', 'align': 'center',
            'bg_color': '#f2f2f2', 'border': 1, 'border_color': '#d9d9d9',
        })
        kpi_val_currency_format = workbook.add_format({
            'bold': True, 'size': 12, 'font_color': '#2e7d32', 'align': 'center',
            'bg_color': '#f2f2f2', 'num_format': '$#,##0.00', 'border': 1, 'border_color': '#d9d9d9',
        })
        sub_section_format = workbook.add_format({
            'bold': True, 'size': 12, 'font_color': '#1f4e79', 'bottom': 2, 'bottom_color': '#1f4e79',
        })

        if self.report_type == 'mantenimiento':
            # --- SINGLE TAB: MANTENIMIENTO ---
            worksheet = workbook.add_worksheet('Mantenimientos')
            worksheet.hide_gridlines(0)
            worksheet.set_row(0, 35)
            worksheet.set_row(4, 25)

            worksheet.merge_range('A1:L1', 'REPORTE DETALLADO DE MANTENIMIENTOS', title_format)

            worksheet.write('A3', 'Fecha Generación:', filter_header_format)
            worksheet.write('B3', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filter_val_format)
            worksheet.write('C3', 'Usuario:', filter_header_format)
            worksheet.write('D3', self.env.user.name, filter_val_format)

            filters = []
            if self.start_date: filters.append(f"Desde: {self.start_date}")
            if self.end_date: filters.append(f"Hasta: {self.end_date}")
            if self.technician_id: filters.append(f"Técnico: {self.technician_id.name}")
            if self.state: filters.append(f"Estado: {self.state.upper()}")
            worksheet.write('E3', 'Filtros:', filter_header_format)
            worksheet.write('F3', ', '.join(filters) if filters else 'Ninguno', filter_val_format)
            for c in range(6, 12): worksheet.write(2, c, '', filter_val_format)

            total_count = len(records)
            total_final_cost = sum(records.mapped('final_cost'))
            avg_real_time = sum(records.mapped('real_time')) / total_count if total_count > 0 else 0.0

            worksheet.merge_range('A5:B5', 'TOTAL MANTENIMIENTOS', kpi_title_format)
            worksheet.merge_range('A6:B6', total_count, kpi_val_format)
            worksheet.merge_range('C5:D5', 'COSTO FINAL ACUMULADO', kpi_title_format)
            worksheet.merge_range('C6:D6', total_final_cost, kpi_val_currency_format)
            worksheet.merge_range('E5:F5', 'PROMEDIO TIEMPO REAL', kpi_title_format)
            worksheet.merge_range('E6:F6', f"{avg_real_time:.2f} hrs", kpi_val_format)

            headers = [
                'Número', 'Cliente', 'Equipo', 'Técnico Asignado', 
                'Fecha Solicitud', 'Fecha Fin', 'Tipo', 
                'Prioridad', 'Estado', 'Costo Estimado', 'Costo Final', 'Tiempo Real (Hrs)'
            ]
            for col, h in enumerate(headers): worksheet.write(7, col, h, header_format)

            row = 8
            for m in records:
                worksheet.write(row, 0, m.number or '', data_center_format)
                worksheet.write(row, 1, m.client_id.name or '', data_left_format)
                worksheet.write(row, 2, f"{m.equipment_id.brand} {m.equipment_id.model}" if m.equipment_id else '', data_left_format)
                worksheet.write(row, 3, m.technician_id.name or 'No Asignado', data_left_format)
                worksheet.write(row, 4, m.request_date.strftime('%Y-%m-%d %H:%M') if m.request_date else '', data_center_format)
                worksheet.write(row, 5, m.end_date.strftime('%Y-%m-%d %H:%M') if m.end_date else '', data_center_format)
                worksheet.write(row, 6, dict(m._fields['maintenance_type'].selection).get(m.maintenance_type, m.maintenance_type), data_center_format)
                worksheet.write(row, 7, dict(m._fields['priority'].selection).get(m.priority, m.priority), data_center_format)
                worksheet.write(row, 8, dict(m._fields['state'].selection).get(m.state, m.state), data_center_format)
                worksheet.write(row, 9, m.estimated_cost or 0.0, data_currency_format)
                worksheet.write(row, 10, m.final_cost or 0.0, data_currency_format)
                worksheet.write(row, 11, m.real_time or 0.0, data_center_format)
                row += 1

            for col_idx in range(len(headers)):
                max_len = len(headers[col_idx])
                for r in range(8, row):
                    cell_val = str(records[r-8].number if col_idx == 0 else records[r-8].client_id.name if col_idx == 1 else '')
                    max_len = max(max_len, len(cell_val))
                worksheet.set_column(col_idx, col_idx, max_len + 3)

        else:
            # --- MULTI-TAB: GENERAL SYSTEM REPORT ---
            # TAB 1: Resumen General
            ws_summary = workbook.add_worksheet('Resumen General')
            ws_summary.hide_gridlines(0)
            ws_summary.set_row(0, 35)
            ws_summary.merge_range('A1:G1', 'REPORTE GENERAL DEL SISTEMA - CONSOLIDADO', title_format)

            ws_summary.write('A3', 'Fecha Generación:', filter_header_format)
            ws_summary.write('B3', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filter_val_format)
            ws_summary.write('C3', 'Usuario:', filter_header_format)
            ws_summary.write('D3', self.env.user.name, filter_val_format)
            for c in range(4, 7): ws_summary.write(2, c, '', filter_val_format)

            # System totals
            total_m = len(records)
            total_eq = self.env['techstore.equipment'].search_count([])
            total_tech = self.env['techstore.technician'].search_count([])
            total_final_cost = sum(records.mapped('final_cost'))

            ws_summary.merge_range('A5:B5', 'MANTENIMIENTOS FILTRADOS', kpi_title_format)
            ws_summary.merge_range('A6:B6', total_m, kpi_val_format)
            ws_summary.merge_range('C5:D5', 'COSTO ACUMULADO', kpi_title_format)
            ws_summary.merge_range('C6:D6', total_final_cost, kpi_val_currency_format)
            ws_summary.merge_range('E5:F5', 'EQUIPOS REGISTRADOS', kpi_title_format)
            ws_summary.merge_range('E6:F6', total_eq, kpi_val_format)
            ws_summary.write('G5', 'TÉCNICOS ACT.', kpi_title_format)
            ws_summary.write('G6', total_tech, kpi_val_format)

            # Maintenance State Distribution
            ws_summary.write('A8', 'Distribución de Mantenimientos por Estado', sub_section_format)
            ws_summary.write(9, 0, 'Estado', header_format)
            ws_summary.write(9, 1, 'Cantidad', header_format)
            ws_summary.write(9, 2, 'Porcentaje', header_format)
            
            states_m = {}
            for state_code, state_name in self.env['techstore.maintenance']._fields['state'].selection:
                states_m[state_code] = 0
            for r_m in records:
                states_m[r_m.state] = states_m.get(r_m.state, 0) + 1

            r_idx = 10
            state_selection_dict = dict(self.env['techstore.maintenance']._fields['state'].selection)
            for state_code, count in states_m.items():
                pct = (count / total_m) if total_m > 0 else 0.0
                ws_summary.write(r_idx, 0, state_selection_dict.get(state_code, state_code), data_left_format)
                ws_summary.write(r_idx, 1, count, data_center_format)
                ws_summary.write_number(r_idx, 2, pct, workbook.add_format({'size': 10, 'num_format': '0.0%', 'border': 1, 'border_color': '#e0e0e0', 'align': 'center'}))
                r_idx += 1

            # Equipment State Distribution
            ws_summary.write('E8', 'Distribución de Equipos por Estado', sub_section_format)
            ws_summary.write(9, 4, 'Estado de Proceso', header_format)
            ws_summary.write(9, 5, 'Cantidad', header_format)
            ws_summary.write(9, 6, 'Porcentaje', header_format)

            all_equipments = self.env['techstore.equipment'].search([])
            total_equipments = len(all_equipments)
            states_eq = {}
            for state_code, state_name in self.env['techstore.equipment']._fields['state'].selection:
                states_eq[state_code] = 0
            for eq in all_equipments:
                states_eq[eq.state] = states_eq.get(eq.state, 0) + 1

            r_eq_idx = 10
            eq_selection_dict = dict(self.env['techstore.equipment']._fields['state'].selection)
            for state_code, count in states_eq.items():
                pct = (count / total_equipments) if total_equipments > 0 else 0.0
                ws_summary.write(r_eq_idx, 4, eq_selection_dict.get(state_code, state_code), data_left_format)
                ws_summary.write(r_eq_idx, 5, count, data_center_format)
                ws_summary.write_number(r_eq_idx, 6, pct, workbook.add_format({'size': 10, 'num_format': '0.0%', 'border': 1, 'border_color': '#e0e0e0', 'align': 'center'}))
                r_eq_idx += 1

            ws_summary.set_column('A:A', 22)
            ws_summary.set_column('B:C', 12)
            ws_summary.set_column('D:D', 5)
            ws_summary.set_column('E:E', 22)
            ws_summary.set_column('F:G', 12)

            # TAB 2: Mantenimientos
            ws_maint = workbook.add_worksheet('Mantenimientos')
            ws_maint.hide_gridlines(0)
            ws_maint.set_row(0, 30)
            ws_maint.merge_range('A1:L1', 'LISTADO COMPLETO DE MANTENIMIENTOS', title_format)
            
            headers_m = [
                'Número', 'Cliente', 'Equipo', 'Técnico Asignado', 
                'Fecha Solicitud', 'Fecha Fin', 'Tipo', 
                'Prioridad', 'Estado', 'Costo Estimado', 'Costo Final', 'Tiempo Real (Hrs)'
            ]
            for col, h in enumerate(headers_m): ws_maint.write(2, col, h, header_format)
            ws_maint.set_row(2, 22)

            row_m = 3
            for m in records:
                ws_maint.write(row_m, 0, m.number or '', data_center_format)
                ws_maint.write(row_m, 1, m.client_id.name or '', data_left_format)
                ws_maint.write(row_m, 2, f"{m.equipment_id.brand} {m.equipment_id.model}" if m.equipment_id else '', data_left_format)
                ws_maint.write(row_m, 3, m.technician_id.name or 'No Asignado', data_left_format)
                ws_maint.write(row_m, 4, m.request_date.strftime('%Y-%m-%d %H:%M') if m.request_date else '', data_center_format)
                ws_maint.write(row_m, 5, m.end_date.strftime('%Y-%m-%d %H:%M') if m.end_date else '', data_center_format)
                ws_maint.write(row_m, 6, dict(m._fields['maintenance_type'].selection).get(m.maintenance_type, m.maintenance_type), data_center_format)
                ws_maint.write(row_m, 7, dict(m._fields['priority'].selection).get(m.priority, m.priority), data_center_format)
                ws_maint.write(row_m, 8, dict(m._fields['state'].selection).get(m.state, m.state), data_center_format)
                ws_maint.write(row_m, 9, m.estimated_cost or 0.0, data_currency_format)
                ws_maint.write(row_m, 10, m.final_cost or 0.0, data_currency_format)
                ws_maint.write(row_m, 11, m.real_time or 0.0, data_center_format)
                row_m += 1

            for col_idx in range(len(headers_m)):
                ws_maint.set_column(col_idx, col_idx, 16)

            # TAB 3: Equipos
            ws_equip = workbook.add_worksheet('Equipos')
            ws_equip.hide_gridlines(0)
            ws_equip.set_row(0, 30)
            ws_equip.merge_range('A1:J1', 'LISTADO DE EQUIPOS EN EL SISTEMA', title_format)

            headers_eq = [
                'Código', 'Cliente', 'Tipo de Equipo', 'Marca', 
                'Modelo', 'Número de Serie', 'Fecha Recepción', 
                'Garantía', 'Estado Proceso', 'Estado Físico'
            ]
            for col, h in enumerate(headers_eq): ws_equip.write(2, col, h, header_format)
            ws_equip.set_row(2, 22)

            row_eq = 3
            for eq in all_equipments:
                ws_equip.write(row_eq, 0, eq.code or '', data_center_format)
                ws_equip.write(row_eq, 1, eq.client_id.name or '', data_left_format)
                ws_equip.write(row_eq, 2, eq.equipment_type_id.name or '', data_left_format)
                ws_equip.write(row_eq, 3, eq.brand or '', data_left_format)
                ws_equip.write(row_eq, 4, eq.model or '', data_left_format)
                ws_equip.write(row_eq, 5, eq.serial_number or '', data_center_format)
                ws_equip.write(row_eq, 6, eq.receipt_date.strftime('%Y-%m-%d') if eq.receipt_date else '', data_center_format)
                ws_equip.write(row_eq, 7, 'SÍ' if eq.has_warranty else 'NO', data_center_format)
                ws_equip.write(row_eq, 8, dict(eq._fields['state'].selection).get(eq.state, eq.state), data_center_format)
                ws_equip.write(row_eq, 9, eq.state_id.name or '', data_center_format)
                row_eq += 1

            for col_idx in range(len(headers_eq)):
                ws_equip.set_column(col_idx, col_idx, 16)

            # TAB 4: Técnicos
            ws_tech = workbook.add_worksheet('Técnicos')
            ws_tech.hide_gridlines(0)
            ws_tech.set_row(0, 30)
            ws_tech.merge_range('A1:G1', 'REGISTRO DE TÉCNICOS Y CARGA LABORAL', title_format)

            headers_tech = [
                'Nombre', 'Identificación', 'Teléfono', 'Email', 
                'Especialidad', 'Mantenimientos Activos', 'Nivel de Carga'
            ]
            for col, h in enumerate(headers_tech): ws_tech.write(2, col, h, header_format)
            ws_tech.set_row(2, 22)

            all_technicians = self.env['techstore.technician'].search([])
            row_tech = 3
            for t in all_technicians:
                ws_tech.write(row_tech, 0, t.name or '', data_left_format)
                ws_tech.write(row_tech, 1, t.identification or '', data_center_format)
                ws_tech.write(row_tech, 2, t.phone or '', data_center_format)
                ws_tech.write(row_tech, 3, t.email or '', data_left_format)
                ws_tech.write(row_tech, 4, t.specialty_id.name or '', data_left_format)
                ws_tech.write(row_tech, 5, t.maintenance_count or 0, data_center_format)
                ws_tech.write(row_tech, 6, dict(t._fields['workload_level'].selection).get(t.workload_level, t.workload_level) if t.workload_level else '', data_center_format)
                row_tech += 1

            for col_idx in range(len(headers_tech)):
                ws_tech.set_column(col_idx, col_idx, 18)

        workbook.close()
        output.seek(0)
        excel_data = output.read()
        output.close()

        # Save binary
        self.write({
            'excel_file': base64.b64encode(excel_data),
            'excel_filename': f'Reporte_Mantenimientos_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=techstore.maintenance.report.wizard&id={self.id}&field=excel_file&filename_field=excel_filename&download=true',
            'target': 'self',
        }


class MaintenanceReportAbstract(models.AbstractModel):
    _name = 'report.techstore_maintenance.report_maintenance_template'
    _description = 'Modelo Abstracto para Reporte de Mantenimiento PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['techstore.maintenance.report.wizard'].browse(docids)
        report_data = []
        for wizard in docs:
            domain = wizard._get_maintenance_domain()
            records = self.env['techstore.maintenance'].search(domain)
            
            # Compute stats
            total_count = len(records)
            total_final_cost = sum(records.mapped('final_cost'))
            total_estimated_cost = sum(records.mapped('estimated_cost'))
            avg_real_time = sum(records.mapped('real_time')) / total_count if total_count > 0 else 0.0
            
            # Count by state
            states_count = {}
            for state_code, state_name in self.env['techstore.maintenance']._fields['state'].selection:
                states_count[state_code] = 0
            for m in records:
                states_count[m.state] = states_count.get(m.state, 0) + 1
            
            # Selection label dicts
            state_selection = dict(self.env['techstore.maintenance']._fields['state'].selection)
            priority_selection = dict(self.env['techstore.maintenance']._fields['priority'].selection)
            type_selection = dict(self.env['techstore.maintenance']._fields['maintenance_type'].selection)

            # Gather general stats if general report type
            general_stats = {}
            if wizard.report_type == 'general':
                all_technicians = self.env['techstore.technician'].search([])
                all_equipments = self.env['techstore.equipment'].search([])
                
                # Equipment stats
                eq_count = len(all_equipments)
                eq_states_count = {}
                for state_code, state_name in self.env['techstore.equipment']._fields['state'].selection:
                    eq_states_count[state_code] = 0
                for eq in all_equipments:
                    eq_states_count[eq.state] = eq_states_count.get(eq.state, 0) + 1
                
                eq_selection = dict(self.env['techstore.equipment']._fields['state'].selection)
                workload_selection = dict(self.env['techstore.technician']._fields['workload_level'].selection)

                general_stats = {
                    'total_technicians': len(all_technicians),
                    'total_equipments': eq_count,
                    'technicians': all_technicians,
                    'eq_states_count': eq_states_count,
                    'eq_selection': eq_selection,
                    'workload_selection': workload_selection,
                }

            report_data.append({
                'wizard': wizard,
                'records': records,
                'total_count': total_count,
                'total_final_cost': total_final_cost,
                'total_estimated_cost': total_estimated_cost,
                'avg_real_time': avg_real_time,
                'states_count': states_count,
                'state_selection': state_selection,
                'priority_selection': priority_selection,
                'type_selection': type_selection,
                'general_stats': general_stats,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'techstore.maintenance.report.wizard',
            'docs': docs,
            'report_data': report_data,
        }
