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
        # 1. Seguridad
        'security/custody_security.xml',        # Define grupos
        # *** SE REMUEVE EL ARCHIVO 'custody_models.xml' AQUÍ PARA EVITAR EL ERROR DE DUPLICIDAD. ***
        'security/ir.model.access.csv',         # Permisos (usa el modelo creado por Python)
        
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
