# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions

class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc, create_date desc'

    sequence = fields.Char(string='Consecutivo', copy=False, readonly=True, default='Nuevo')

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True,
                                 domain="[('is_company','=',True)]", tracking=True)
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
        ('4x','Excepción a Nivel 4')
    ], string='Nivel de seguridad', required=True)

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

    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')


# ------------------------------------------------------------
# MODELO HIJO: CustodiaAsignacion
# ------------------------------------------------------------
class CustodiaAsignacion(models.Model):
    _name = 'custodia.asignacion'
    _description = 'Asignación de Custodia'

    service_id = fields.Many2one('custodia.service', string='Servicio', ondelete='cascade')
    notes = fields.Text(string='Notas')
    employee_ids = fields.Many2many('hr.employee', string='Custodios')
    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehículos')
    candado_ids = fields.Many2many('custodia.candado', string='Candados')
    radio_ids = fields.Many2many('custodia.radio', string='Radios')


# ------------------------------------------------------------
# MODELOS BÁSICOS: Candado y Radio
# ------------------------------------------------------------
class CustodiaCandado(models.Model):
    _name = 'custodia.candado'
    _description = 'Candado de Custodia'

    name = fields.Char(string='Referencia', required=True)
    serial_number = fields.Char(string='Número de serie')
    active = fields.Boolean(default=True)


class CustodiaRadio(models.Model):
    _name = 'custodia.radio'
    _description = 'Radio de Custodia'

    name = fields.Char(string='Referencia', required=True)
    marca = fields.Char(string='Marca')
    modelo = fields.Char(string='Modelo')
    active = fields.Boolean(default=True)
