# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SGSPerdiemImportBatch(models.Model):
    _name = 'sgs.perdiem.import.batch'
    _description = 'Lote de Dispersión Banorte'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        tracking=True,
        default=lambda self: _('Nueva Dispersión')
    )

    deposit_date = fields.Date(
        string='Fecha de Depósito',
        required=True,
        tracking=True
    )

    source_file = fields.Binary(
        string='PDF Banorte',
        attachment=True
    )

    source_filename = fields.Char(
        string='Nombre Archivo'
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processed', 'Procesado'),
        ('done', 'Aplicado'),
        ('error', 'Error')
    ], default='draft', tracking=True)

    line_ids = fields.One2many(
        'sgs.perdiem.import.line',
        'batch_id',
        string='Detalle'
    )

    total_amount = fields.Monetary(
        string='Monto Total',
        compute='_compute_totals',
        store=True
    )

    total_lines = fields.Integer(
        string='Registros',
        compute='_compute_totals',
        store=True
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True
    )

    currency_id = fields.Many2one(
        related='company_id.currency_id'
    )

    @api.depends('line_ids.amount')
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.total_amount = sum(rec.line_ids.mapped('amount'))

    def action_apply_deposits(self):

        deposit_model = self.env['sgs.perdiem.deposit']

        for batch in self:

            for line in batch.line_ids.filtered(
                lambda l: l.status == 'ok'
            ):

                deposit_model.create({
                    'custodian_id': line.employee_id.id,
                    'date': batch.deposit_date,
                    'concept': 'Dispersión Banorte',
                    'amount': line.amount,
                    'import_batch_id': batch.id,
                })

            batch.state = 'done'

class SGSPerdiemImportLine(models.Model):
    _name = 'sgs.perdiem.import.line'
    _description = 'Detalle Dispersión Banorte'
    _order = 'id'

    batch_id = fields.Many2one(
        'sgs.perdiem.import.batch',
        required=True,
        ondelete='cascade'
    )

    rfc = fields.Char(
        string='RFC'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Custodio'
    )

    registration_number = fields.Char(
        related='employee_id.registration_number',
        string='ID Empleado'
    )

    amount = fields.Monetary(
        string='Monto'
    )

    notes = fields.Char(
        string='Observaciones'
    )

    status = fields.Selection([
        ('ok', 'Correcto'),
        ('warning', 'Advertencia'),
        ('error', 'Error')
    ], default='ok')

    company_id = fields.Many2one(
        related='batch_id.company_id'
    )

    currency_id = fields.Many2one(
        related='batch_id.currency_id'
    )

    @api.onchange('rfc')
    def _onchange_rfc(self):

        if not self.rfc:
            return

        employee = self.env['hr.employee'].search([
            ('l10n_mx_rfc', '=', self.rfc.upper().strip())
        ], limit=1)

        self.employee_id = employee.id if employee else False

        if not employee:
            self.status = 'error'
            self.notes = _('RFC no encontrado')
