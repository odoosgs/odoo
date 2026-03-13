# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'start_datetime desc, id desc'

    name = fields.Char(string='Folio del Servicio', required=True, copy=False, default='Nuevo', tracking=True)

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    contact_id = fields.Many2one('res.partner', string='Persona solicitante', required=True, tracking=True)

    planner_id = fields.Many2one('res.users', string='Planeador', tracking=True)

    carrier_id = fields.Many2one('custodia.carrier', string='Carrier', tracking=True)
    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', tracking=True)

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

    hora_llegada = fields.Datetime(string='Hora de llegada custodio', tracking=True)
    hora_inicio_real = fields.Datetime(string='Hora de inicio real', tracking=True)

    tipo_unidad = fields.Char(string='Tipo de unidad', tracking=True)
    placas = fields.Char(string='Placas', tracking=True)
    transporte = fields.Char(string='Transporte', tracking=True)
    operador1_nombre = fields.Char(string='Operador 1', tracking=True)
    tel_monitoreo_1 = fields.Char(string='Teléfono Monitoreo 1', tracking=True)

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
            if rec.request_type == 'alerta' or rec.state == 'alerta':
                rec.calendar_color = color_map['alerta']
            else:
                rec.calendar_color = color_map.get(rec.state, 1)

    @api.constrains('request_type', 'start_datetime')
    def _check_alerta_lead_time(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.request_type == 'alerta' and rec.start_datetime:
                if rec.start_datetime <= now + timedelta(hours=24):
                    raise ValidationError(_(
                        'La alerta debe programarse con al menos 24 horas de anticipación. '
                        'Para servicios urgentes, capture directamente el servicio completo.'
                    ))

    @api.constrains('request_type', 'carrier_id', 'ruta_id', 'nivel_seguridad', 'load_id', 'contact_id', 'start_datetime')
    def _check_required_for_service(self):
        for rec in self:
            if rec.request_type != 'servicio':
                continue
            missing = []
            if not rec.contact_id:
                missing.append(_('Contacto solicitante'))
            if not rec.start_datetime:
                missing.append(_('Fecha programada'))
            if not rec.carrier_id:
                missing.append(_('Carrier'))
            if not rec.ruta_id:
                missing.append(_('Ruta'))
            if not rec.nivel_seguridad:
                missing.append(_('Nivel de seguridad'))
            if not rec.load_id:
                missing.append(_('Load ID'))
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
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = seq.next_by_code('custodia.service') or 'Nuevo'
            if not vals.get('state'):
                vals['state'] = 'alerta' if vals.get('request_type', 'alerta') == 'alerta' else 'solicitado'
        return super().create(vals_list)

    def action_convert_to_service(self):
        for rec in self:
            rec.write({
                'request_type': 'servicio',
                'state': 'solicitado',
            })
            rec.message_post(body=_('Alerta convertida a servicio por %s.') % self.env.user.display_name)

    def action_aprobar(self):
        self.write({'state': 'aprobado'})

    def action_asignar(self):
        self.write({'state': 'asignado'})

    def action_ejecutar(self):
        self.write({'state': 'en_ejecucion'})

    def action_finalizar(self):
        self.write({'state': 'finalizado'})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})
