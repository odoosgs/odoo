# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaAsignacion(models.Model):
    _name = 'custodia.asignacion'
    _description = 'Asignación de Recursos de Custodia'
    _inherit = ['mail.thread']

    service_id = fields.Many2one('custodia.service', string='Servicio', required=True, ondelete='cascade')
    nivel_seguridad = fields.Selection(related='service_id.nivel_seguridad', store=True)

    employee_ids = fields.Many2many('hr.employee', string='Personal asignado')
    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehículos')
    candado_ids = fields.Many2many('product.product', string='Candados', domain=[('type','=','product')])
    radio_ids = fields.Many2many('product.product', string='Radios', domain=[('type','=','product')])

    notes = fields.Text(string='Notas de asignación')
