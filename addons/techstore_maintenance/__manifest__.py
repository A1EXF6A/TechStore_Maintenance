{
    'name': 'TechStore Maintenance',
    'version': '1.0',
    'category': 'Operations/Maintenance',
    'summary': 'Technical Maintenance Management System for TechStore',
    'description': """
        Complete module for managing technical maintenance, technicians, equipment and metrics.
    """,
    'author': 'TechStore',
    'website': 'https://www.techstore.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/techstore_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
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
