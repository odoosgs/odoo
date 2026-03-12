# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'sequence desc, create_date desc'

    # =========================
    # CAMPOS DE UBICACIÓN LIVE
    # =========================
    current_lat = fields.Float(string="Latitud Actual", tracking=True)
    current_lng = fields.Float(string="Longitud Actual", tracking=True)
    last_update = fields.Datetime(string="Última Actualización", tracking=True)

    # =========================
    # IDENTIFICADORES
    # =========================
    name = fields.Char(
        string='Folio del Servicio',
        required=True,
        copy=False,
        index=True,
        default='Nuevo'
    )

    sequence = fields.Char(
        string='Consecutivo',
        copy=False,
        readonly=True,
        default='Nuevo'
    )

    # =========================
    # RELACIONES
    # =========================
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

    # Se quita required=True para permitir el modo Alerta
    carrier_id = fields.Many2one(
        'custodia.carrier',
        string='Carrier',
        tracking=True
    )

    # Se quita required=True para permitir el modo Alerta
    ruta_id = fields.Many2one(
        'custodia.ruta',
        string='Ruta',
        tracking=True
    )

    planner_id = fields.Many2one(
        'res.users',
        string='Planeador',
        tracking=True
    )

    # === CAMPOS PARA SELECCIÓN EN CASCADA ===
    ruta_maestra_id = fields.Many2one(
        'custodia.ruta.maestra', 
        string='Ruta Principal (Origen - Destino)',
        tracking=True
    )
    
    nodo_origen_id = fields.Many2one(
        'custodia.ruta.nodo', 
        string='Punto de Salida Específico',
        tracking=True
    )
    
    nodo_destino_id = fields.Many2one(
        'custodia.ruta.nodo', 
        string='Punto de Llegada Específico',
        tracking=True
    )

    ruta_tipo = fields.Selection(
        related='ruta_id.tipo',
        string='Tipo de ruta',
        store=True,
        readonly=True
    )

    # =========================
    # DATOS OPERATIVOS
    # =========================
    start_datetime = fields.Datetime(
        string='Inicio del servicio',
        required=True,
        tracking=True
    )

    # Se quita required=True para permitir el modo Alerta
    nivel_seguridad = fields.Selection(
        [
            ('1', 'Nivel 1'),
            ('2', 'Nivel 2'),
            ('3', 'Nivel 3'),
            ('4', 'Nivel 4'),
            ('4x', 'Excepción + Nivel 4'),
        ],
        string='Nivel de seguridad',
        tracking=True
    )

    # Se quita required=True para permitir el modo Alerta
    load_id = fields.Char(
        string='Load ID',
        index=True,
        tracking=True,
        copy=False
    )

    tipo_unidad = fields.Char(string='Tipo de unidad', tracking=True)
    placas = fields.Char(string='Placas', tracking=True)
    transporte = fields.Char(string='No. Económico U.', tracking=True)

    operador1_nombre = fields.Char(string='Operador 1', tracking=True)
    operador1_licencia = fields.Char(string='Licencia Operador 1', tracking=True)
    tel_monitoreo_1 = fields.Char(string='Teléfono Monitoreo 1', tracking=True)

    comentarios_cliente = fields.Text(string='Comentarios del Cliente', tracking=True)

    # =========================
    # RESTRICCIONES Y VALIDACIONES
    # =========================
    _sql_constraints = [
        ('load_id_unique', 'unique(load_id)', '¡El Load ID ya existe! Este número debe ser único por servicio.')
    ]

    @api.constrains('start_datetime')
    def _check_anticipacion(self):
        for record in self:
            if record.start_datetime and record.state == 'solicitado':
                # Validar 24 horas de anticipación para alertas nuevas
                now = fields.Datetime.now()
                if record.start_datetime < now + timedelta(hours=24):
                    # Aquí puedes decidir si bloqueas (ValidationError) o solo avisas.
                    # Por tu requerimiento de "restricción", lanzamos el error:
                    raise ValidationError(_("Las alertas deben programarse con al menos 24 horas de anticipación."))

    @api.onchange('load_id')
    def _onchange_load_id(self):
        if self.load_id:
            existente = self.search([('load_id', '=', self.load_id), ('id', '!=', self._origin.id)], limit=1)
            if existente:
                return {
                    'warning': {
                        'title': "Load ID Duplicado",
                        'message': f"Este ID ya fue capturado en el servicio {existente.name} por {existente.contact_id.name}."
                    }
                }

    # =========================
    # RELACIONES HIJAS
    # =========================
    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')
    tracking_ids = fields.One2many('custodia.service.tracking', 'service_id', string='Historial de Ubicaciones')

    # =========================
    # ESTADO
    # =========================
    state = fields.Selection(
        [
            ('solicitado', 'Alerta (Solicitado)'),
            ('aprobado', 'Confirmado (Aprobado)'),
            ('asignado', 'Asignado'),
            ('en_ejecucion', 'En ejecución'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='solicitado',
        tracking=True,
        index=True
    )

    # =========================
    # CONTROL DE TIEMPOS
    # =========================
    hora_llegada = fields.Datetime(string='Hora de llegada custodio', tracking=True)
    hora_inicio_real = fields.Datetime(string='Hora de inicio real', tracking=True)
    
    diff_llegada_min = fields.Integer(string='Diferencia llegada (min)', compute='_compute_diferencias')
    diff_inicio_min = fields.Integer(string='Diferencia inicio (min)', compute='_compute_diferencias')

    @api.depends('start_datetime', 'hora_llegada', 'hora_inicio_real')
    def _compute_diferencias(self):
        for record in self:
            diff_llegada = 0
            diff_inicio = 0
            if record.start_datetime:
                if record.hora_llegada:
                    diff_llegada = int((record.hora_llegada - record.start_datetime).total_seconds() / 60)
                if record.hora_inicio_real:
                    diff_inicio = int((record.hora_inicio_real - record.start_datetime).total_seconds() / 60)
            record.diff_llegada_min = diff_llegada
            record.diff_inicio_min = diff_inicio

    # =========================
    # MÉTODOS DE ACCIÓN
    # =========================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sequence', 'Nuevo') == 'Nuevo':
                vals['sequence'] = self.env['ir.sequence'].next_by_code('custodia.service') or 'Nuevo'
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = vals['sequence']
        return super().create(vals_list)

    def action_aprobar(self):
        """Valida campos obligatorios antes de fincar el servicio"""
        for record in self:
            if not record.ruta_id or not record.carrier_id or not record.load_id or not record.nivel_seguridad:
                raise ValidationError(_("Faltan datos para confirmar el servicio (Ruta, Carrier, Load ID y Nivel de Seguridad son obligatorios en este estado)."))
        self.write({'state': 'aprobado'})

    def action_asignar(self): self.write({'state': 'asignado'})
    def action_ejecutar(self): self.write({'state': 'en_ejecucion'})
    def action_finalizar(self): self.write({'state': 'finalizado'})
    def action_cancelar(self): self.write({'state': 'cancelado'})

    def update_live_location(self, lat, lng):
        self.ensure_one()
        now = fields.Datetime.now()
        self.write({'current_lat': lat, 'current_lng': lng, 'last_update': now})
        self.env['custodia.service.tracking'].create({
            'service_id': self.id,
            'latitude': lat,
            'longitude': lng,
            'timestamp': now
        })
        return True
