{
    'name': 'SGS Viáticos Custodios',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Gestión de viáticos y gastos para custodios SGS - Interfaz Portal',
    'author': 'SGS',
    'depends': ['base', 'portal', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/viatico_views.xml',
        'views/portal_templates.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
