import re

translations = {
    "Client": "Cliente",
    "Equipment": "Equipos",
    "Equipments": "Equipos",
    "Maintenance": "Mantenimiento",
    "Maintenances": "Mantenimientos",
    "Technician": "Técnico",
    "Technicians": "Técnicos",
    "Priority": "Prioridad",
    "Status": "Estado",
    "New": "Nuevo",
    "Assigned": "Asignado",
    "In Progress": "En Proceso",
    "Pending": "Pendiente",
    "Finished": "Finalizado",
    "Cancelled": "Cancelado",
    "Received": "Recibido",
    "Repaired": "Reparado",
    "Delivered": "Entregado",
    "Desktop": "Escritorio",
    "Laptop": "Portátil",
    "Printer": "Impresora",
    "Server": "Servidor",
    "Smartphone": "Teléfono Inteligente",
    "Hardware": "Hardware",
    "Software": "Software",
    "Networking": "Redes",
    "Low": "Baja",
    "Medium": "Media",
    "High": "Alta",
    "Critical": "Crítica",
    "Corrective": "Correctivo",
    "Preventive": "Preventivo",
    "Diagnostic": "Diagnóstico",
    "Excellent": "Excelente",
    "Good": "Bueno",
    "Fair": "Regular",
    "Poor": "Malo",
    "TechStore Maintenance": "Mantenimiento TechStore",
    "Dashboard": "Tablero",
    "Metrics": "Métricas",
    "Configuration": "Configuración",
    "Maintenance Number": "Número de Mantenimiento",
    "Problem Description": "Descripción del Problema",
    "Maintenance Request": "Solicitud de Mantenimiento",
    "Assign Technician": "Asignar Técnico",
    "Assigned Technician": "Técnico Asignado",
    "Costs": "Costos",
    "Costs & Times": "Costos y Tiempos",
    "Create your first maintenance request!": "¡Crea tu primera solicitud de mantenimiento!",
    "Customer Satisfaction": "Satisfacción del Cliente",
    "Delay (Hours)": "Retraso (Horas)",
    "Description of the issue...": "Descripción del problema...",
    "End Date": "Fecha de Fin",
    "Estimated Cost": "Costo Estimado",
    "Estimated Time (Hours)": "Tiempo Estimado (Horas)",
    "Execution Time": "Tiempo de Ejecución",
    "Final Cost": "Costo Final",
    "Full Name": "Nombre Completo",
    "Has Warranty": "Tiene Garantía",
    "Observations": "Observaciones",
    "Real Time Employed (Hours)": "Tiempo Real Empleado (Horas)",
    "Receipt Date": "Fecha de Recepción",
    "Register a new equipment!": "¡Registra un nuevo equipo!",
    "Register your first technician!": "¡Registra tu primer técnico!",
    "Request Date": "Fecha de Solicitud",
    "SLA Compliance": "Cumplimiento SLA",
    "Search Equipment": "Buscar Equipos",
    "Search Maintenance": "Buscar Mantenimientos",
    "Search Technicians": "Buscar Técnicos",
    "Active": "Activo",
    "Inactive": "Inactivo",
    "Group By": "Agrupar Por",
    "Client & Equipment": "Cliente y Equipo",
    "Planning": "Planificación",
    "Problem & Diagnosis": "Problema y Diagnóstico",
    "Satisfaction & History": "Satisfacción e Historial",
    "Quality Indicator": "Indicador de Calidad",
    "Maintenance Metrics": "Métricas de Mantenimiento",
    "Maintenance Metrics Analysis": "Análisis de Métricas de Mantenimiento"
}

pot_file = "addons/techstore_maintenance/i18n/techstore_maintenance.pot"
po_file = "addons/techstore_maintenance/i18n/es.po"

with open(pot_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # Check if the line is msgid "Something"
    match = re.match(r'^msgid "(.*)"$', line)
    if match and i + 1 < len(lines) and lines[i+1].startswith('msgstr ""'):
        msgid = match.group(1)
        if msgid in translations:
            new_lines.append(f'msgstr "{translations[msgid]}"\n')
            i += 1 # skip the original msgstr ""
            i += 1
            continue
    i += 1

with open(po_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Translation es.po generated successfully.")
