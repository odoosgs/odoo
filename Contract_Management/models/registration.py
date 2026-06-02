from odoo import models, fields, api
import requests

class ContractRegistration(models.Model):
    _name = 'contract.registration'
    _description = 'Contract Module Registration'

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email", required=True)
    contact = fields.Char(string="Contact")
    uuid = fields.Char(string="UUID", readonly=True)
    secret_key = fields.Char(string="Secret Key")
    status = fields.Selection([('active', 'Active'), ('deactivate', 'Deactivated')], string="Status", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(ContractRegistration, self).default_get(fields_list)
        user = self.env.user
        res.update({
            'name': user.name or '',
            'email': user.email or '',
            'contact': user.partner_id.phone or '',
        })
        return res

    def action_regenerate_uuid(self):
        for rec in self:
            payload = {
                "uuid": rec.uuid,
                "secret_key": rec.secret_key
            }
            try:
                response = requests.post("https://cm.sufalamtech.com/regenerate", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    rec.uuid = data.get("new_uuid")
                    if data.get("status"):
                        rec.status = data.get("status")
                else:
                    raise Exception(response.text)
            except Exception as e:
                raise models.ValidationError(f"Failed to regenerate UUID: {e}")

    def action_update_status(self, status):
        for rec in self:
            payload = {
                "uuid": rec.uuid,
                "secret_key": rec.secret_key
            }
            try:
                response = requests.post(f"https://cm.sufalamtech.com/update_status?status={status}", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    rec.status = data.get("status")
                else:
                    raise Exception(response.text)
            except Exception as e:
                raise models.ValidationError(f"Failed to update status: {e}")
