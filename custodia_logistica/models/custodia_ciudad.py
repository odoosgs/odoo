from odoo import models, fields

class CustodiaCiudad(models.Model):
    _name = 'custodia.ciudad'
    _description = 'Ciudades Operativas'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'La ciudad ya existe.')
    ]
