{
    'name': "Servicios de Custodia",
    'summary': "Gestión de Servicios de Custodia y Transporte Vehicular (México)",
    'description': """
        Módulo para la gestión integral de servicios de custodia vehicular.
        Incluye el manejo de Carriers (Transportistas externos), Servicios de Custodia, 
        asignación de rutas, medidas de seguridad y reportes específicos para logística 3PL.
    """,
    'author': "Gemini Odoo Developer",
    'website': "http://www.ejemplo.com",
    'category': 'Operations/Logistics',
    'version': '19.0.1.0.0',
    'depends': [
        'base',      # Core de Odoo para modelos básicos y partners
        'mail',      # Para el tracking de mensajes y actividades
        'fleet',     # Para futura integración de vehículos de custodia propios
        'hr',        # Para integrar con empleados (custodios)
        'account',   # Para la integración contable de servicios
        'project',   # Para la planeación y gestión de los servicios como proyectos
    ],
    'data': [
        # 1. Seguridad y Definición de Modelos (Orden de Carga CORRECTO y con COMAS)
        'security/custody_security.xml',        # Define grupos (cargado primero)
        'security/custody_models.xml',          # Declara ir.model para 'custody.carrier'
        'security/ir.model.access.csv',         # Usa el ID del modelo para permisos
        
        # 2. Vistas de Menú
        'views/custody_menus.xml', 
        
        # 3. Vistas del Catálogo de Carriers
        'views/custody_carrier_views.xml',
        
        # Datos iniciales (si son necesarios)
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
