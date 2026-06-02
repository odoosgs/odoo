from odoo import models, fields, api

class ContractRegistrationBackup(models.Model):
    _name = 'contract.registration.backup'
    _description = 'Contract Registration Backup'

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email", required=True)
    contact = fields.Char(string="Contact")
    uuid = fields.Char(string="UUID", readonly=True)
    secret_key = fields.Char(string="Secret Key")
    status = fields.Selection([('active', 'Active'), ('deactivate', 'Deactivated')],
                              string="Status", readonly=True)