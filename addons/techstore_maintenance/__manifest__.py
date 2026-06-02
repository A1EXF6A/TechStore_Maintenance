{
    'name': 'TechStore Mantenimiento',
    'version': '1.0',
    'category': 'Operaciones/Mantenimiento',
    'summary': 'Sistema de Gestión de Mantenimientos Técnicos para TechStore',
    'description': """
        Módulo completo para la gestión de mantenimientos técnicos, técnicos,
        equipos y métricas de calidad del servicio de TechStore.

        Funcionalidades principales:
        - Gestión de solicitudes de mantenimiento
        - Asignación y seguimiento de técnicos
        - Registro y control de equipos
        - Historial de estados
        - Prioridades de atención
        - Métricas de calidad y rendimiento
        - Vinculación de técnicos con usuarios Odoo
    """,
    'author': 'TechStore',
    'website': 'https://www.techstore.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/techstore_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/techstore.specialty.csv',
        'data/techstore.client.csv',
        'data/techstore.technician.csv',
        'data/techstore.equipment.type.csv',
        'data/techstore.equipment.state.csv',
        'data/techstore.equipment.csv',
        'data/techstore.maintenance.csv',
        'data/res_users_technicians.xml',
        'views/technician_views.xml',
        'views/equipment_views.xml',
        'views/maintenance_views.xml',
        'views/metrics_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
