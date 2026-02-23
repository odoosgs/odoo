# -*- coding: utf-8 -*-
from odoo import models, fields


class CustodiaRutaNodo(models.Model):
    _name = 'custodia.ruta.nodo'
    _description = 'Nodo Intermedio de Ruta'
    _order = 'sequence, id'

    ruta_id = fields.Many2one(
        'custodia.ruta',
        string='Ruta',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    name = fields.Char(
        string='Nombre del Nodo',
        required=True
    )

    latitude = fields.Float(
        string='Latitud',
        digits=(10, 6),
        required=True
    )

    longitude = fields.Float(
        string='Longitud',
        digits=(10, 6),
        required=True
    )
