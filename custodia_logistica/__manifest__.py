# -*- coding: utf-8 -*-
{
    'name': 'Custodia Logística',
    'version': '19.0.1.1',
    'summary': 'Gestión de servicios de custodia con portal, asignaciones y seguimiento',
    'category': 'Operations',
    'author': 'Xentinell',
    'license': 'OEEL-1',
    'depends': [
        'base',
        'mail',
        'bus',
        'website',
        'portal',
        'hr',
        'fleet',
        'purchase',
        'account',
        'planning',
    ],
    'data': [
        # Datos
        'data/sequence.xml',

        # Seguridad
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        # Menús (¡MOVIDO AQUÍ ARRIBA!)
        # Esto asegura que el menú raíz 'menu_custodia_root' exista antes de que cualquier vista intente usarlo.
        'views/custodia_menus.xml',

        # Catálogos
        'views/custodia_catalogos_views.xml',        
        'views/custodia_carrier_views.xml',
        'views/custodia_ruta_views.xml',

        # Servicio principal
        'views/custodia_service_views.xml',
        'views/custodia_service_list_view.xml',

        # Asignaciones (Ahora sí encontrará su menú padre sin problemas)
        'views/custodia_asignacion_views.xml',

        # Portal
        'views/portal_templates.xml',
        'views/portal_service_form.xml',
        #'views/portal_service_detail.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Aquí puedes agregar CSS/JS para personalizar el portal
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'custodia_logistica/static/src/css/portal_security_levels.css',
            'custodia_logistica/static/src/js/route_map.js', # Sin el "/" inicial
        ],
    },
    'application': True,
    'installable': True,
}





















