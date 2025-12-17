{
    'name': "Gestión de Servicios de Custodia",
    'version': '1.0',
    'summary': "Gestión integral de servicios de custodia, carriers y rutas.",
    'description': """
        Módulo para la administración de servicios de custodia logística.
        
        Funcionalidades Principales:
        - Gestión de Carriers (Transportistas)
        - Gestión de Rutas y Tramos
        - Integración futura con APIs (SCT, Casetas)
        - Control de Servicios de Custodia
    """,
    'author': "sgs seguridad",
    'website': "https://www.grupobrame.com",
    'category': 'Logistics',
    'license': 'LGPL-3',
    
    # Dependencias base.
    # 'base' es esencial. 'contacts' puede ser útil si los carriers son partners.
    'depends': ['base', 'contacts'],

    # Carga de datos (Vistas, Seguridad, Datos)
    'data': [
        'security/ir.model.access.csv',
        'views/custodia_menus.xml',
        'views/custodia_carrier_views.xml',
        'views/custodia_ruta_views.xml',
    ],

    # Archivos estáticos (Iconos, CSS, JS)
    'assets': {
        # En Odoo 19+ la estructura de assets puede variar, pero esta es la estándar actual.
        # El icono del módulo se busca automáticamente en static/description/icon.png
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}