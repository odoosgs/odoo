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
        'mail',      
        'fleet',     
        'hr',        
        'account',   
        'project',   
    ],
    'data': [
        # 1. Seguridad
        'security/custody_security.xml',        
        'security/ir.model.access.csv',         
        
        # 2. Datos (Secuencia)
        'data/custody_service_sequence.xml',     # <-- ¡NUEVO! Secuencia para el folio CS-XXXX
        
        # 3. Vistas y Menús
        'views/custody_carrier_views.xml',
        'views/custody_service_views.xml',      # <-- ¡NUEVO! Vistas y Acción de Servicio
        'views/custody_menus.xml', 
        
        # Nota: menus.xml siempre debe cargarse después de las acciones (views) que referencia.
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
