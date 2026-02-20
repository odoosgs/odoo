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
        [('local','Local'), ('foraneo','Foráneo')],
        string='Tipo de ruta',
        required=True,
        default='local',
        tracking=True
    )

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

    descripcion = fields.Text(
        string='Descripción / Detalles de la Ruta'
    )

    active = fields.Boolean(
        string='Activa',
        default=True
    )

    variante_ids = fields.One2many(
        'custodia.ruta.variante',
        'ruta_id',
        string='Variantes de Ruta'
    )
