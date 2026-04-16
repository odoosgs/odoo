from odoo import models, fields

class Custodia(models.Model):
    _name = 'custodia.orden'
    _description = 'Plantilla de Custodia'

    name = fields.Char(string="Folio", required=True, copy=False, readonly=True, default='Nuevo')
    linea_transporte = fields.Char(string="Línea de Transporte")
    nombre_operador = fields.Char(string="Nombre del Operador")
    placas_tractor = fields.Char(string="Placas Tractor")
    placas_caja = fields.Char(string="Placas Caja / Contenedor")
    eco = fields.Char(string="ECO")
    cliente_id = fields.Many2one('res.partner', string="Cliente")
    
    # Datos de la unidad de custodia
    custodio_cargo = fields.Char(string="Custodio a Cargo")
    marca_unidad = fields.Char(string="Marca")
    color_unidad = fields.Char(string="Color")
    placas_unidad = fields.Char(string="Placas")
    origen = fields.Char(string="Origen")
    destino = fields.Char(string="Destino")

    # El "Detalle" (Muchos a Muchos / Uno a Muchos)
    bitacora_ids = fields.One2many('custodia.bitacora', 'custodia_id', string="Líneas de Bitácora")

class CustodiaBitacora(models.Model):
    _name = 'custodia.bitacora'
    _description = 'Detalle de Bitácora de Custodia'

    custodia_id = fields.Many2one('custodia.orden', string="Referencia de Custodia")
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today)
    hora = fields.Float(string="Hora", widget='float_time')
    gps = fields.Boolean(string="GPS")
    tipo_reporte = fields.Selection([
        ('whatsapp', 'WhatsApp'),
        ('llamada', 'Llamada')
    ], string="What/Llamada")
    ubicacion = fields.Text(string="Ubicación")
    comentarios = fields.Char(string="Comentarios", default="SIN NOVEDAD")
