# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaRutaMaestra(models.Model):
    _name = 'custodia.ruta.maestra'  # <--- Este nombre DEBE ser idéntico al error
    _description = 'Ruta Maestra'
    
    name = fields.Char(string="Nombre de Ruta", required=True)

class CustodiaPuntoOperativo(models.Model):
    _name = 'custodia.punto.operativo' # <--- Cambio de nombre técnico
    _description = 'Puntos Operativos (Bodegas del Excel)'
    
    name = fields.Char(string="Nombre del Punto", required=True)
    latitude = fields.Float(string="Latitud")
    longitude = fields.Float(string="Longitud")
