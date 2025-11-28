# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CustodyCarrier(models.Model):
    _name = 'x_custody.carrier'
    _description = 'Catálogo de Transportistas Externos (Carriers)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # --- Información Básica y Contacto (Similar a res.partner) ---
    name = fields.Char(string='Nombre del Carrier o Razón Social', required=True, tracking=True)
    carrier_type = fields.Selection([
        ('company', 'Compañía de Transporte'),
        ('independent', 'Transportista Independiente'),
    ], string='Tipo de Carrier', required=True, default='company', tracking=True)
    
    # --- Datos Fiscales y Legales (Críticos en México) ---
    vat = fields.Char(string='RFC / ID Fiscal', help="Registro Federal de Contribuyentes para México o equivalente.", copy=False, tracking=True)
    is_active = fields.Boolean(string='Activo', default=True, help="Indica si este Carrier está disponible para nuevos servicios.")
    
    # --- Contacto y Dirección ---
    street = fields.Char(string='Calle')
    street2 = fields.Char(string='Colonia')
    zip = fields.Char(string='C.P.')
    city = fields.Char(string='Ciudad')
    state_id = fields.Many2one('res.country.state', string='Estado', domain="[('country_id.code', '=', 'MX')]") # Filtrado para estados de México
    country_id = fields.Many2one('res.country', string='País', default=lambda self: self.env.ref('base.mx')) # Default a México
    phone = fields.Char(string='Teléfono Principal')
    email = fields.Char(string='Correo Electrónico')

    # --- Compliance y Documentación (Sugerencias del Consultor) ---
    insurance_policy = fields.Char(string='No. Póliza de Seguro de Carga')
    insurance_expiry_date = fields.Date(string='Vigencia del Seguro')
    
    contact_name = fields.Char(string='Contacto Operativo')
    contact_phone = fields.Char(string='Teléfono Contacto')
    
    # --- Relaciones (Futuras) ---
    # service_ids = fields.One2many('custody.service', 'carrier_id', string='Servicios Realizados')
    
    @api.onchange('country_id')
    def _onchange_country_id(self):
        # Limpia el campo de estado si el país cambia y ya no es México
        if self.country_id and self.country_id != self.env.ref('base.mx'):
            self.state_id = False
            
    # Restricción para asegurar que el RFC/VAT es único (si aplica)
    _sql_constraints = [
        ('vat_unique', 'unique(vat)', '¡El RFC/ID Fiscal ya existe en el sistema!'),

    ]
