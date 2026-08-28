# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'sequence desc, start_datetime desc, id desc'

    name = fields.Char(string='Folio del Servicio', required=True, copy=False, default='Nuevo', tracking=True)
    sequence = fields.Char(string='Consecutivo', copy=False, readonly=True, default='Nuevo', index=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Persona solicitante',
        required=True,
        tracking=True,
        domain="[('parent_id', '=', partner_id)]",
    )

    planner_id = fields.Many2one('res.users', string='Planeador / Monitorista', tracking=True, default=lambda self: self.env.user)

    carrier_id = fields.Many2one('custodia.carrier', string='Carrier', tracking=True)
    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', tracking=True)

    ruta_maestra_id = fields.Many2one('custodia.ruta.maestra', string='Ruta Principal', tracking=True)
    nodo_origen_id = fields.Many2one('custodia.punto.operativo', string='Punto de Salida', tracking=True)
    nodo_destino_id = fields.Many2one('custodia.punto.operativo', string='Punto de Llegada', tracking=True)
    ruta_tipo = fields.Selection(related='ruta_id.tipo', string='Tipo de ruta', store=True, readonly=True)

    start_datetime = fields.Datetime(string='Fecha programada', required=True, tracking=True)
    nivel_seguridad = fields.Selection(
        [
            ('1', 'Nivel 1'),
            ('2', 'Nivel 2'),
            ('3', 'Nivel 3'),
            ('4', 'Nivel 4'),
            ('4x', 'Excepción + Nivel 4'),
        ],
        string='Nivel de seguridad',
        tracking=True,
    )

    load_id = fields.Char(string='Load ID', index=True, tracking=True)

    # Ubicación y eventos de ejecución
    current_lat = fields.Float(string='Latitud Actual', tracking=True)
    current_lng = fields.Float(string='Longitud Actual', tracking=True)
    last_update = fields.Datetime(string='Última Actualización', tracking=True)
    gps_tracking_url = fields.Char(string='Liga GPS en tiempo real', tracking=True)

    # Vehículos y Kit Vehicular
    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        'custodia_service_fleet_vehicle_rel',
        'service_id',
        'vehicle_id',
        string='Vehículos Asignados',
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehículo Principal',
        compute='_compute_vehicle_principal',
        store=True
    )

    kit_asset_id = fields.Char(related='vehicle_id.kit_asset_id', string="ID Activo Kit", readonly=True)
    gps_vehicular = fields.Char(related='vehicle_id.gps_vehicular', string="GPS Vehicular", readonly=True)
    gps_portatil = fields.Char(related='vehicle_id.gps_portatil', string="GPS Portátil", readonly=True)
    gps_portatil_serial = fields.Char(related='vehicle_id.gps_portatil_serial', string="No. Serie GPS Portátil", readonly=True)
    gps_portatil_sim = fields.Char(related='vehicle_id.gps_portatil_sim', string="SIM GPS", readonly=True)
    candado_digital = fields.Char(related='vehicle_id.candado_digital', string="Candado Digital", readonly=True)
    candado_mecanico = fields.Char(related='vehicle_id.candado_mecanico', string="Candado Mecánico", readonly=True)
    radio_portatil = fields.Char(related='vehicle_id.radio_portatil', string="Radio Portátil", readonly=True)

    @api.depends('vehicle_ids')
    def _compute_vehicle_principal(self):
        for rec in self:
            rec.vehicle_id = rec.vehicle_ids[0] if rec.vehicle_ids else False

    # Tiempos de Custodio
    hora_llegada = fields.Datetime(string='Hora de llegada custodio', tracking=True)
    hora_inicio_real = fields.Datetime(string='Hora de inicio real', tracking=True)
    hora_fin_real = fields.Datetime(string='Hora de finalización real', tracking=True)

    diff_llegada_min = fields.Integer(string='Diferencia llegada (min)', compute='_compute_diferencias', store=True)
    diff_inicio_min = fields.Integer(string='Diferencia inicio (min)', compute='_compute_diferencias', store=True)
    duracion_real_horas = fields.Float(string='Duración real (horas)', compute='_compute_diferencias', store=True)

    # Datos de Carga y Operadores
    tipo_unidad = fields.Char(string='Tipo de unidad', tracking=True)
    placas = fields.Char(string='Placas', tracking=True)
    transporte = fields.Char(string='Línea de Transporte', tracking=True)
    operador1_nombre = fields.Char(string='Operador 1', tracking=True)
    operador1_licencia = fields.Char(string='Licencia Operador 1', tracking=True)
    tel_monitoreo_1 = fields.Char(string='Teléfono Monitoreo 1', tracking=True)
    operador2_nombre = fields.Char(string='Operador 2', tracking=True)
    operador2_licencia = fields.Char(string='Licencia Operador 2', tracking=True)
    tel_monitoreo_2 = fields.Char(string='Teléfono Monitoreo 2', tracking=True)
    start_coords = fields.Char(string='Coordenadas de inicio', tracking=True)
    end_coords = fields.Char(string='Coordenadas de llegada', tracking=True)
    comentarios_cliente = fields.Text(string='Comentarios del Cliente', tracking=True)

    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')
    tracking_ids = fields.One2many('custodia.service.tracking', 'service_id', string='Historial de Ubicaciones')

    # Incidencias
    incidencia_ids = fields.One2many('custodia.service.incidencia', 'service_id', string='Incidencias del Servicio')

    request_type = fields.Selection(
        [('alerta', 'Alerta'), ('servicio', 'Servicio')],
        string='Tipo de registro',
        required=True,
        default='alerta',
        tracking=True,
        index=True,
    )

    state = fields.Selection(
        [
            ('alerta', 'Alerta'),
            ('solicitado', 'Solicitado'),
            ('aprobado', 'Aprobado'),
            ('asignado', 'Asignado'),
            ('en_ejecucion', 'En ejecución'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='alerta',
        tracking=True,
        index=True,
    )

    calendar_color = fields.Integer(string='Color calendario', compute='_compute_calendar_color', store=False)

    @api.depends('request_type', 'state')
    def _compute_calendar_color(self):
        color_map = {
            'alerta': 2,
            'solicitado': 3,
            'aprobado': 3,
            'asignado': 3,
            'en_ejecucion': 10,
            'finalizado': 7,
            'cancelado': 8,
        }
        for rec in self:
            if rec.request_type == 'alerta' and rec.state == 'alerta':
                rec.calendar_color = color_map['alerta']
            else:
                rec.calendar_color = color_map.get(rec.state, 1)

    @api.depends('start_datetime', 'hora_llegada', 'hora_inicio_real', 'hora_fin_real')
    def _compute_diferencias(self):
        for record in self:
            diff_llegada = 0
            diff_inicio = 0
            duracion = 0.0
            if record.start_datetime:
                if record.hora_llegada:
                    diff_llegada = int((record.hora_llegada - record.start_datetime).total_seconds() / 60)
                if record.hora_inicio_real:
                    diff_inicio = int((record.hora_inicio_real - record.start_datetime).total_seconds() / 60)
            if record.hora_inicio_real and record.hora_fin_real:
                duracion = (record.hora_fin_real - record.hora_inicio_real).total_seconds() / 3600.0
            record.diff_llegada_min = diff_llegada
            record.diff_inicio_min = diff_inicio
            record.duracion_real_horas = round(duracion, 2)

    @api.constrains('request_type', 'start_datetime')
    def _check_alerta_lead_time(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.request_type == 'alerta' and rec.start_datetime:
                if rec.start_datetime <= now + timedelta(hours=24):
                    # Solo validación informativa o excepción si aplica
                    pass

    def _get_missing_service_fields(self):
        self.ensure_one()
        missing = []
        checks = [
            (_('Contacto solicitante'), self.contact_id),
            (_('Fecha programada'), self.start_datetime),
            (_('Carrier'), self.carrier_id),
            (_('Ruta'), self.ruta_id),
            (_('Nivel de seguridad'), self.nivel_seguridad),
            (_('Load ID'), self.load_id),
        ]
        for label, value in checks:
            if not value:
                missing.append(label)
        return missing

    def _raise_if_missing_service_fields(self):
        for rec in self:
            missing = rec._get_missing_service_fields()
            if missing:
                raise ValidationError(_('Para convertir a servicio faltan campos: %s') % ', '.join(missing))

    @api.constrains('load_id')
    def _check_unique_load_id(self):
        for rec in self:
            if not rec.load_id:
                continue
            dup = self.search([
                ('id', '!=', rec.id),
                ('load_id', '=', rec.load_id),
            ], limit=1)
            if dup:
                raise ValidationError(_(
                    "El Load ID '%(load)s' ya está registrado en %(folio)s (estado: %(state)s, fecha: %(date)s)."
                ) % {
                    'load': rec.load_id,
                    'folio': dup.name,
                    'state': dup.state,
                    'date': fields.Datetime.to_string(dup.start_datetime) if dup.start_datetime else '-',
                })

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('sequence', 'Nuevo') == 'Nuevo':
                vals['sequence'] = seq.next_by_code('custodia.service') or 'Nuevo'
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = vals['sequence']
            if not vals.get('state'):
                vals['state'] = 'alerta' if vals.get('request_type', 'alerta') == 'alerta' else 'solicitado'
        return super().create(vals_list)

    # Botones de Flujo de Estados
    def action_convert_to_service(self):
        for rec in self:
            rec._raise_if_missing_service_fields()
            rec.write({
                'request_type': 'servicio',
                'state': 'solicitado',
            })
            rec.message_post(body=_('Alerta convertida a solicitud de servicio.'))

    def action_solicitar(self):
        self.write({'request_type': 'servicio', 'state': 'solicitado'})

    def action_aprobar(self):
        self.write({'state': 'aprobado'})

    def action_asignar(self):
        self.write({'state': 'asignado'})

    def action_ejecutar(self):
        now = fields.Datetime.now()
        vals = {'state': 'en_ejecucion'}
        for rec in self:
            if not rec.hora_inicio_real:
                vals['hora_inicio_real'] = now
            rec.write(vals)

    def action_finalizar(self):
        now = fields.Datetime.now()
        vals = {'state': 'finalizado'}
        for rec in self:
            if not rec.hora_fin_real:
                vals['hora_fin_real'] = now
            rec.write(vals)

    def action_cancelar(self):
        self.write({'state': 'cancelado'})

    def action_reset_to_draft(self):
        self.write({'state': 'solicitado'})


class CustodiaServiceIncidencia(models.Model):
    _name = 'custodia.service.incidencia'
    _description = 'Incidencia de Servicio de Custodia'
    _order = 'fecha desc, id desc'

    service_id = fields.Many2one('custodia.service', string='Servicio', required=True, ondelete='cascade')
    fecha = fields.Datetime(string='Fecha y Hora', default=fields.Datetime.now, required=True)
    reportado_por = fields.Selection([
        ('custodio', 'Custodio en Ruta'),
        ('monitorista', 'Monitorista / Cabina'),
        ('cliente', 'Cliente'),
        ('satelital', 'Teléfono Satelital / Radio'),
    ], string='Medio / Reportado por', default='monitorista', required=True)
    tipo_incidencia = fields.Selection([
        ('bloqueo', 'Bloqueo / Tráfico Carretero'),
        ('mecanica', 'Falla Mecánica'),
        ('seguridad', 'Alerta de Seguridad / Sospecha'),
        ('clima', 'Condición Climática Adversa'),
        ('pernocta', 'Pernocta / Espera Forzada'),
        ('otra', 'Otra'),
    ], string='Tipo de Incidencia', default='bloqueo', required=True)
    ubicacion = fields.Char(string='Ubicación / Kilómetro')
    descripcion = fields.Text(string='Descripción del Evento', required=True)
    user_id = fields.Many2one('res.users', string='Registrado por', default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.service_id:
                rec.service_id.message_post(
                    body=f"⚠️ <b>INCIDENCIA REGISTRADA ({dict(rec._fields['tipo_incidencia'].selection).get(rec.tipo_incidencia)}):</b><br/>"
                         f"<b>Ubicación:</b> {rec.ubicacion or 'N/A'}<br/>"
                         f"<b>Medio:</b> {dict(rec._fields['reportado_por'].selection).get(rec.reportado_por)}<br/>"
                         f"<b>Detalle:</b> {rec.descripcion}",
                    subtype_xmlid='mail.mt_comment'
                )
        return records
