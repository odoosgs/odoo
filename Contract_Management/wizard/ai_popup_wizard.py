# contract_management/wizard/ai_popup_wizard.py
from odoo import models, _

class AiPopupWizard(models.TransientModel):
    _name = "ai.popup.wizard"
    _description = "AI Popup Wizard"

    def action_yes(self):
        """Triggered when the user clicks Yes in the popup"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("AI Assistant"),
                "message": _("AI processing will start for your document."),
                "sticky": False,
                "type": "info",
            },
        }
