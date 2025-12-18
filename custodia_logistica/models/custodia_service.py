# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from datetime import timedelta

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc, create_date desc'

    # Identificación
    sequence = fields.Char(string='Consecutivo', copy=False, readonly=True, default='Nuevo')

    # Cliente y contacto
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True,
                                 domain=[('is_company','=',True)], tracking=True)
    contact_id = fields.Many2one('res.partner', string='Persona solicitante', required=True,
                                 domain="[('parent_id','=',partner_id)]", tracking=True)

    # Catálogos
    carrier_id = fields.Many2one('custodia.carrier', string='Carrier', required=True, tracking=True)
    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', required=True, tracking=True)
    ruta_tipo = fields.Selection([('local','Local'), ('foraneo','Foráneo')],
                                 string='Tipo de ruta', related='ruta_id.tipo', store=True)

    # Parámetros del servicio
    start_datetime = fields.Datetime(string='Inicio del servicio', required=True, tracking=True)
    nivel_seguridad = fields.Selection([
        ('1','Nivel 1'),
        ('2','Nivel 2'),
        ('3','Nivel 3'),
        ('4','Nivel 4'),
        ('4x','Excepción + Nivel 4'),
    ], string='Nivel de seguridad', required=True, tracking=True)
    load_id = fields.Char(string='Load ID', required=True, index=True, tracking=True)

    # Datos Carrier
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

    # Estado
    state = fields.Selection([
        ('solicitado','Solicitado'),
        ('asignado','Asignado'),
        ('aprobado','Aprobado'),
        ('en_ejecucion','En ejecución'),
        ('finalizado','Finalizado'),
        ('cancelado','Cancelado'),
    ], string='Estado', default='solicitado', tracking=True, index=True)

    # Gestión interna
    planner_id = fields.Many2one('res.users', string='Planeador', tracking=True)
    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')

    # Documentos externos
    purchase_ids = fields.One2many('purchase.order', 'custodia_service_id', string='Órdenes de compra')
    account_move_ids = fields.One2many('account.move', 'custodia_service_id', string='Facturas')
    planning_slot_ids = fields.One2many('planning.slot', 'custodia_service_id', string='Planeación')

    # Contadores para smart buttons
    purchase_count = fields.Integer(string='Órdenes de compra', compute='_compute_counts')
    invoice_count = fields.Integer(string='Facturas', compute='_compute_counts')
    planning_count = fields.Integer(string='Planeaciones', compute='_compute_counts')

    @api.depends('purchase_ids', 'account_move_ids', 'planning_slot_ids')
    def _compute_counts(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_ids)
            rec.invoice_count = len(rec.account_move_ids)
            rec.planning_count = len(rec.planning_slot_ids)

    # Validación de tiempo mínimo según ruta
    @api.constrains('start_datetime', 'ruta_tipo')
    def _check_lead_time(self):
        for rec in self:
            if not rec.start_datetime or not rec.ruta_tipo:
                continue
            required_hours = 6 if rec.ruta_tipo == 'local' else 19
            delta = rec.start_datetime - fields.Datetime.now()
            if delta < timedelta(hours=required_hours):
                raise exceptions.ValidationError(
                    f'La solicitud debe realizarse con al menos {required_hours} horas de anticipación para rutas {rec.ruta_tipo}.'
                )

    # Secuencia y notificación al crear
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'Nuevo') == 'Nuevo':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('custodia.service') or 'CS-000000'
        rec = super().create(vals)
        rec._notify_new_service()
        return rec

    def _notify_new_service(self):
        subject = f'Nuevo servicio de custodia: {self.sequence}'
        body = f'Cliente: {self.partner_id.display_name}<br/>Ruta: {self.ruta_id.name}<br/>Inicio: {self.start_datetime}<br/>Nivel: {self.nivel_seguridad}'
        self.message_post(body=body, subject=subject, message_type='notification', subtype_xmlid='mail.mt_comment')

    # Acciones de estado
    def action_asignar(self):
        for rec in self:
            rec.state = 'asignado'
        return True

    def action_aprobar(self):
        for rec in self:
            rec.state = 'aprobado'
        return True

    def action_iniciar(self):
        for rec in self:
            rec.state = 'en_ejecucion'
        return True

    def action_finalizar(self):
        for rec in self:
            rec.state = 'finalizado'
        return True

    def action_cancelar(self):
        for rec in self:
            rec.state = 'cancelado'
        return True

    # Stub para botón "Generar Asignaciones"
    def action_generar_asignaciones_por_nivel(self):
        for rec in self:
            rec.message_post(body=f'Asignaciones generadas automáticamente para nivel {rec.nivel_seguridad}.')
        return True

    # Smart button actions
    def action_view_purchases(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Órdenes de compra',
            'res_model': 'purchase.order',
            'domain': [('custodia_service_id','=',self.id)],
            'view_mode': 'list,form',
        }

    def action_view_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facturas',
            'res_model': 'account.move',
            'domain': [('custodia_service_id','=',self.id)],
            'view_mode': 'list,form',
        }

    def action_view_planning(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Planeaciones',
            'res_model': 'planning.slot',
            'domain': [('custodia_service_id','=',self.id)],
            'view_mode': 'list,form',
        }
