from odoo import models, fields, api

class AiPopupWizard(models.TransientModel):
    _name = "ai.popup.wizard"
    _description = "AI Popup Wizard"

    def action_yes(self):
        # Here you can trigger AI logic (like calling OpenAI or any custom code)
        # Example: log message
        self.env.user.notify_info("AI processing will start for your document.")
        return {'type': 'ir.actions.act_window_close'}
