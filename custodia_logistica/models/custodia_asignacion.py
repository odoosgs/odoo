# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaAsignacion(models.Model):
    _name = 'custodia.asignacion'
    _description = 'Asignación de Recursos de Custodia'
    _inherit = ['mail.thread']

    # Relación con el servicio
    service_id = fields.Many2one(
        'custodia.service',
        string='Servicio',
        required=True,
        ondelete='cascade'
    )

    # Contexto del nivel (informativo)
    nivel_seguridad = fields.Selection(
        related='service_id.nivel_seguridad',
        store=True
    )

    # Recursos asignados (tablas relacionales únicas por campo)
    employee_ids = fields.Many2many(
        'hr.employee',
        'custodia_asignacion_employee_rel',  # tabla M2M única
        'asignacion_id', 'employee_id',
        string='Personal asignado'
    )

    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        'custodia_asignacion_vehicle_rel',  # tabla M2M única
        'asignacion_id', 'vehicle_id',
        string='Vehículos'
    )

    candado_ids = fields.Many2many(
        'product.product',
        'custodia_asignacion_candado_rel',  # tabla M2M única
        'asignacion_id', 'product_id',
        string='Candados',
        domain=[('type', '=', 'product')]
    )

    radio_ids = fields.Many2many(
        'product.product',
        'custodia_asignacion_radio_rel',  # tabla M2M única
        'asignacion_id', 'product_id',
        string='Radios',
        domain=[('type', '=', 'product')]
    )

    # Notas
    notes = fields.Text(string='Notas de asignación')
