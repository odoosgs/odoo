# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaRutaMaestra(models.Model):
    _name = 'custodia.ruta.maestra'  # <--- Este nombre DEBE ser idéntico al error
    _description = 'Ruta Maestra'
    
    name = fields.Char(string="Nombre de Ruta", required=True)

class CustodiaPuntoOperativo(models.Model):
    _name = 'custodia.punto.operativo'
    _description = 'Puntos Operativos (Bodegas del Excel)'
    _order = 'sequence, id' # Ordenar por secuencia

    name = fields.Char(string="Nombre del Punto", required=True)
    latitude = fields.Float(string="Latitud")
    longitude = fields.Float(string="Longitud")
    sequence = fields.Integer(string="Secuencia", default=10) # <--- AGREGAR ESTA LÍNEA
