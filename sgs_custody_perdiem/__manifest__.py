{
    'name': 'SGS Control de Viáticos y Custodias',
    'version': '19.0.1.0.1',
    'category': 'Operations/Logistics',
    'summary': 'Gestión de custodios, rutas, viáticos, comprobación de gastos y portal público por token.',
    'description': '''
SGS Control de Viáticos y Custodias
===================================

Módulo para administrar custodios de vehículos pesados, depósitos de viáticos, servicios de custodia en rutas, comprobación de gastos, casetas, facturas fiscales y validación administrativa. Incluye portal público por token para que los custodios reporten gastos sin usuario interno.
    ''',
    'author': 'Manus AI',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'portal',
        'hr', # Añadido para la integración con empleados
        'fleet', # Añadido para la integración con vehículos
        'contacts', # Añadido para la integración con clientes
        #'web_editor', # Necesario para algunas vistas de Odoo
    ],
    'external_dependencies': {
        'python': ['pdfminer.six'], # Añadido para la extracción de texto de PDF
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/assets.xml',
        'views/menu.xml',
        'views/custody_views.xml',
        'views/deposit_batch_views.xml', # Nueva vista para el asistente de carga masiva
        'views/portal_templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'sgs_custody_perdiem/static/src/scss/sgs_portal.scss',
        ],
    },
    'application': True,
    'installable': True,
}
