{
    'name': 'SGS Viáticos Custodios',
    'version': '19.0.1.0.0',
    'category': 'Operations',
    'summary': 'Gestión de viáticos SGS',
    'depends': ['base', 'portal', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/viatico_views.xml',
        'views/portal_templates.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
