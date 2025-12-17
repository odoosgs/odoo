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
    'author': "Grupo Brame",
    'website': "https://www.grupobrame.com",
    'category': 'Services',
    'license': 'LGPL-3',
    
    # Dependencias base
    'depends': ['base', 'contacts', 'mail'],

    # Orden de carga: seguridad → vistas → menús
    'data': [
        'security/ir.model.access.csv',
        'views/custodia_carrier_views.xml',  # Define action_custodia_carrier
        'views/custodia_ruta_views.xml',     # Define action_custodia_ruta
        'views/custodia_menus.xml',          # Usa las acciones anteriores
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
