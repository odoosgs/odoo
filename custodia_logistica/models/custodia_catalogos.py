# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaRutaMaestra(models.Model):
    _name = 'custodia.ruta.maestra'
    _description = 'Ruta Maestra (Agrupador del Excel)'
    
    name = fields.Char(string="Nombre de Ruta", required=True)

class CustodiaRutaNodo(models.Model):
    _name = 'custodia.ruta.nodo'
    _description = 'Nodos de Carga/Descarga (Bodegas)'
    
    name = fields.Char(string="Nombre del Punto", required=True)
    latitude = fields.Float(string="Latitud")
    longitude = fields.Float(string="Longitud")
