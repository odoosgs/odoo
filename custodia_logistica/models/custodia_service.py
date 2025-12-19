# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc, create_date desc'

    # Identificador legible
    name = fields.Char(
        string='Folio del Servicio',
        required=True,
        copy=False,
        index=True,
        default='Nuevo'
    )

    # Consecutivo interno
    sequence = fields.Char(
        string='Consecutivo',
        copy=False,
        readonly=True,
        default='Nuevo'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Persona solicitante',
        required=True,
        domain="[('parent_id','=',partner_id)]",
        tracking=True
    )

    carrier_id = fields.Many2one(
        'custodia.carrier',
        string='Carrier',
        required=True,
        tracking=True
    )
    ruta_id = fields.Many2one(
        'custodia.ruta',
        string='Ruta',
        required=True,
        tracking=True
    )
    ruta_tipo = fields.Selection(
        [('local', 'Local'), ('foraneo', 'Foráneo')],
        string='Tipo de ruta',
        related='ruta_id.tipo',
        store=True
    )

    start_datetime = fields.Datetime(
        string='Inicio del servicio',
        required=True,
        tracking=True
    )
    nivel_seguridad = fields.Selection(
        [
            ('1', 'Nivel 1'),
            ('2', 'Nivel 2'),
            ('3', 'Nivel 3'),
            ('4', 'Nivel 4'),
            ('4x', 'Excepción + Nivel 4'),
        ],
        string='Nivel de seguridad',
        required=True,
        tracking=True
    )
    load_id = fields.Char(
        string='Load ID',
        required=True,
        index=True,
        tracking=True
    )

    # Relación hijo
    asignacion_ids = fields.One2many(
        'custodia.asignacion',
        'service_id',
        string='Asignaciones'
    )

    state = fields.Selection(
        [
            ('solicitado', 'Solicitado'),
            ('asignado', 'Asignado'),
            ('aprobado', 'Aprobado'),
            ('en_ejecucion', 'En ejecución'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='solicitado',
        tracking=True,
        index=True
    )

    planner_id = fields.Many2one(
        'res.users',
        string='Planeador',
        tracking=True
    )

    # Autogenerar nombre y secuencia
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'Nuevo') == 'Nuevo':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('custodia.service') or 'Nuevo'
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = vals['sequence']
        return super(CustodiaService, self).create(vals)
