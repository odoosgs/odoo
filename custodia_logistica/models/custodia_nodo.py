from odoo import models, fields

class CustodiaNodo(models.Model):
    _name = 'custodia.nodo'
    _description = 'Nodos Operativos'

    name = fields.Char(required=True)
    ciudad_id = fields.Many2one(
        'custodia.ciudad',
        required=True,
        ondelete='restrict'
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('nodo_unique', 'unique(name, ciudad_id)',
         'El nodo ya existe en esta ciudad.')
    ]
