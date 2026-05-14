from odoo import models, fields, api

class SGSViaticoEntrega(models.Model):
    _name = 'sgs.viatico.entrega'
    _description = 'Entrega de Efectivo a Custodios'
    _inherit = ['mail.thread']

    name = fields.Char(string="Referencia", required=True, copy=False, readonly=True, default='Nuevo')
    employee_id = fields.Many2one('hr.employee', string="Custodio", required=True)
    amount = fields.Float(string="Monto Entregado", required=True)
    date = fields.Date(string="Fecha de Entrega", default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Entregado')], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('sgs.viatico.entrega') or 'Nuevo'
        return super(SGSViaticoEntrega, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'done'})
