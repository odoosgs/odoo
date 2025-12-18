# -*- coding: utf-8 -*-
{
    'name': 'Custodia Logística',
    'version': '19.0.1.0',
    'summary': 'Gestión de servicios de custodia con portal, asignaciones y seguimiento',
    'category': 'Operations',
    'author': 'Xentinell',
    'license': 'OEEL-1',
    'depends': [
        'base',
        'mail',
        'website',
        'portal',
        'hr',
        'fleet',
        'purchase',
        'account',
        'planning',
    ],
    'data': [
        # Datos primero (secuencias, seguridad, menus base)
        'data/sequence.xml',
        'security/ir_model_access.xml',
        'security/ir_rule.xml',
        'views/custodia_menus.xml',

        # Catálogos existentes
        'views/custodia_carrier_views.xml',
        'views/custodia_ruta_views.xml',

        # Servicio principal
        'views/custodia_service_views.xml',

        # Portal
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Si necesitas CSS/JS para el portal, agrégalo aquí
        ],
    },
    'application': True,
    'installable': True,
}
