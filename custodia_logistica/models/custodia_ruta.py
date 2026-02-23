# -*- coding: utf-8 -*-
from odoo import models, fields


class CustodiaRuta(models.Model):
    _name = 'custodia.ruta'
    _description = 'Ruta Comercial de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nombre de la Ruta',
        required=True,
        tracking=True,
        help="Ejemplo: GDL - Ciudad Juárez"
    )

    tipo = fields.Selection(
        [('local', 'Local'), ('foraneo', 'Foráneo')],
        string='Tipo de ruta',
        required=True,
        default='local',
        tracking=True
    )

    # =========================
    # INFORMACIÓN DEL TRAYECTO
    # =========================
    origen = fields.Char(
        string='Origen',
        tracking=True
    )

    destino = fields.Char(
        string='Destino',
        tracking=True
    )

    distancia_km = fields.Float(
        string='Distancia (km)',
        tracking=True
    )

    tiempo_estimado = fields.Float(
        string='Tiempo Estimado (horas)',
        tracking=True,
        help="Tiempo estimado en horas"
    )

    origin_latitude = fields.Float(
        string='Latitud Origen',
        digits=(10, 6)
    )

    origin_longitude = fields.Float(
        string='Longitud Origen',
        digits=(10, 6)
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
        'custodia.ruta.nodo',
        'ruta_id',
        string='Nodos Intermedios'
    )


    # =========================
    # COSTOS
    # =========================
    tiene_peajes = fields.Boolean(
        string='Incluye Casetas/Peajes',
        default=False
    )

    costo_peaje_estimado = fields.Monetary(
        string='Costo Estimado Peajes',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )

    # =========================
    # OTROS
    # =========================
    descripcion = fields.Text(
        string='Descripción / Detalles de la Ruta'
    )

    active = fields.Boolean(
        string='Activa',
        default=True
    )

