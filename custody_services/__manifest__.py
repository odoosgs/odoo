{
    'name': "Servicios de Custodia",
    'summary': "Gestión de Servicios de Custodia y Transporte Vehicular (México)",
    'description': """
        Módulo para la gestión integral de servicios de custodia vehicular.
        Incluye el manejo de Carriers (Transportistas externos), Servicios de Custodia, 
        asignación de rutas, medidas de seguridad y reportes específicos para logística 3PL.
    """,
    'author': "Luis Garcia, asistido por Gemini IA Odoo Developer",
    'website': "http://www.xentinell.com",
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
        # Seguridad y Accesos
        'security/custody_security.xml',
        'security/ir.model.access.csv',
        
        # Vistas de Menú (para crear toda la estructura de navegación)
        'views/custody_menus.xml', 
        
        # Vistas del Catálogo de Carriers
        'views/custody_carrier_views.xml',
        
        # Datos iniciales (si son necesarios)
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}