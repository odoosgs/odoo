# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustodiaCarrier(models.Model):
    _name = 'custodia.carrier'
    _description = 'Carrier de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Para chatter y notas

    name = fields.Char(string='Nombre del Carrier', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True)
    
    # Relación opcional con res.partner para aprovechar la libreta de direcciones de Odoo
    partner_id = fields.Many2one('res.partner', string='Contacto Asociado', help="Vincula este carrier con un contacto del sistema.")
    
    rfc = fields.Char(string='RFC', tracking=True)
    telefono = fields.Char(string='Teléfono de Contacto')
    email = fields.Char(string='Correo Electrónico')
    
    # Clasificación o Tipo de Carrier
    tipo_servicio = fields.Selection([
        ('terrestre', 'Terrestre'),
        ('aereo', 'Aéreo'),
        ('maritimo', 'Marítimo'),
        ('ferreo', 'Férreo')
    ], string='Tipo de Servicio', default='terrestre')

    notas = fields.Text(string='Notas Internas')