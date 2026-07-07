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
        # 1. Configuración inicial y Datos básicos
        'data/sequence.xml',

        # 2. Seguridad (Siempre va primero para mapear accesos a modelos)
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        # 3. Archivos de Negocio que contienen las Acciones (act_window)
        # Cargamos las rutas primero para que 'action_custodia_ruta_maestra' ya exista
        'views/custodia_ruta_views.xml', 
        'views/custodia_catalogos_views.xml',        
        'views/custodia_carrier_views.xml',
        'views/custodia_service_views.xml',
        'views/custodia_service_list_view.xml',

        # 4. Declaración de Menús 
        # Aquí ya existen todas las acciones de arriba y sigue estando antes de asignaciones
        'views/custodia_menus.xml',

        # 5. Archivos secundarios que dependen de los menús cargados
        'views/custodia_asignacion_views.xml',

        # 6. Portal Frontend
        'views/portal_templates.xml',
        'views/portal_service_form.xml',
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





















