# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from datetime import timedelta

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc, create_date desc'

    sequence = fields.Char(string='Consecutivo', copy=False, readonly=True, default='Nuevo')

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True,
                                 domain=[('is_company','=',True)], tracking=True)
    contact_id = fields.Many2one('res.partner', string='Persona solicitante', required=True,
                                 domain="[('parent_id','=',partner_id)]", tracking=True)

    carrier_id = fields.Many2one('custodia.carrier', string='Carrier', required=True, tracking=True)
    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', required=True, tracking=True)
    ruta_tipo = fields.Selection([('local','Local'), ('foraneo','Foráneo')],
                                 string='Tipo de ruta', related='ruta_id.tipo', store=True)

    start_datetime = fields.Datetime(string='Inicio del servicio', required=True, tracking=True)
    nivel_seguridad = fields.Selection([
        ('1','Nivel 1'),
        ('2','Nivel 2'),
        ('3','Nivel 3'),
        ('4','Nivel 4'),
        ('4x','Excepción + Nivel 4'),
    ], string='Nivel de seguridad', required=True, tracking=True)
    load_id = fields.Char(string='Load ID', required=True, index=True, tracking=True)

    tipo_unidad = fields.Char(string='Tipo de unidad', required=True)
    placas = fields.Char(string='Placas', required=True)
    operador1_nombre = fields.Char(string='Nombre del operador 1', required=True)
    operador1_licencia = fields.Char(string='Licencia del operador 1', required=True)
    transporte = fields.Char(string='Transporte', required=True)
    operador2_nombre = fields.Char(string='Nombre del operador 2')
    operador2_licencia = fields.Char(string='Licencia del operador 2')
    tel_monitoreo_1 = fields.Char(string='Teléfono central de monitoreo 1', required=True)
    tel_monitoreo_2 = fields.Char(string='Teléfono central de monitoreo 2')
    comentarios_cliente = fields.Text(string='Comentarios del cliente')

    state = fields.Selection([
        ('solicitado','Solicitado'),
        ('asignado','Asignado'),
        ('aprobado','Aprobado'),
        ('en_ejecucion','En ejecución'),
        ('finalizado','Finalizado'),
        ('cancelado','Cancelado'),
    ], string='Estado', default='solicitado', tracking=True, index=True)

    planner_id = fields.Many2one('res.users', string='Planeador', tracking=True)

    # One2many hacia el modelo hijo correcto
    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')

    # Smart buttons
    purchase_ids = fields.One2many('purchase.order', 'custodia_service_id', string='Órdenes de compra')
    account_move_ids = fields.One2many('account.move', 'custodia_service_id', string='Facturas')
    planning_slot_ids = fields.One2many('planning.slot', 'custodia_service_id', string='Planeación')

    purchase_count = fields.Integer(compute='_compute_counts')
    invoice_count = fields.Integer(compute='_compute_counts')
    planning_count = fields.Integer(compute='_compute_counts')

    @api.depends('purchase_ids','account_move_ids','planning_slot_ids')
    def _compute_counts(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_ids)
            rec.invoice_count = len(rec.account_move_ids)
            rec.planning_count = len(rec.planning_slot_ids)

    # Métodos de estado
    def action_asignar(self): self.write({'state':'asignado'})
    def action_aprobar(self): self.write({'state':'aprobado'})
    def action_iniciar(self): self.write({'state':'en_ejecucion'})
    def action_finalizar(self): self.write({'state':'finalizado'})
    def action_cancelar(self): self.write({'state':'cancelado'})

    # Stub para botón "Generar Asignaciones"
    def action_generar_asignaciones_por_nivel(self):
        for rec in self:
            rec.message_post(body=f'Asignaciones generadas automáticamente para nivel {rec.nivel_seguridad}.')
        return True
