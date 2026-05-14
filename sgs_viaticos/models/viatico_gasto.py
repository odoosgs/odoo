from odoo import models, fields, api

class SGSViaticoGasto(models.Model):
    _name = 'sgs.viatico.gasto'
    _description = 'Gasto Reportado por Custodio'
    _inherit = ['mail.thread']

    name = fields.Char(string="Concepto", required=True)
    employee_id = fields.Many2one('hr.employee', string="Custodio", required=True)
    amount = fields.Float(string="Monto del Gasto", required=True)
    date = fields.Date(string="Fecha", default=fields.Date.context_today)
    category = fields.Selection([
        ('alimentacion', 'Alimentación'),
        ('combustible', 'Combustible'),
        ('peaje', 'Peaje'),
        ('hospedaje', 'Hospedaje'),
        ('otros', 'Otros')
    ], string="Categoría", default='otros')
    receipt_image = fields.Binary(string="Evidencia/Ticket")
    state = fields.Selection([
        ('reported', 'Reportado'),
        ('approved', 'Aprobado'),
        ('refused', 'Rechazado')
    ], default='reported', tracking=True)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_refuse(self):
        self.write({'state': 'refused'})
