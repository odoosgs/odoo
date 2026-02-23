# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaRoute(models.Model):
    _name = 'custodia.route'
    _description = 'Ruta Operativa de Custodia'
    _order = 'name'

    name = fields.Char(
        string='Nombre de la Ruta',
        required=True
    )

    origin_city = fields.Char(
        string='Ciudad Origen'
    )

    origin_latitude = fields.Float(
        string='Latitud Origen',
        digits=(10, 6)
    )

    origin_longitude = fields.Float(
        string='Longitud Origen',
        digits=(10, 6)
    )

    destination_city = fields.Char(
        string='Ciudad Destino'
    )

    destination_latitude = fields.Float(
        string='Latitud Destino',
        digits=(10, 6)
    )

    destination_longitude = fields.Float(
        string='Longitud Destino',
        digits=(10, 6)
    )

    node_ids = fields.One2many(
        'custodia.route.node',
        'route_id',
        string='Nodos Intermedios'
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )
