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
    'category': 'Logistics',
    'license': 'LGPL-3',
    
    # Dependencias base.
    # 'base' y 'contacts' son esenciales. 'mail' se añade porque usamos mail.thread en los modelos.
    'depends': ['base', 'contacts', 'mail'],

    # Carga de datos (Vistas, Seguridad, Datos)
    # --- IMPORTANTE: EL ORDEN ES CRÍTICO ---
    # 1. Seguridad: Siempre primero para definir accesos.
    # 2. Vistas de Modelos: Definen las acciones (ir.actions.act_window).
    # 3. Menús: Usan las acciones definidas anteriormente.
    'data': [
        'security/ir.model.access.csv',
        'views/custodia_carrier_views.xml', # Define action_custodia_carrier
        'views/custodia_ruta_views.xml',    # Define action_custodia_ruta
        'views/custodia_menus.xml',         # Usa las acciones anteriores
    ],

    # Archivos estáticos (Iconos, CSS, JS)
    'assets': {
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
