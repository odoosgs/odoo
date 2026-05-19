import base64
import io
import re
from datetime import date as pydate

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None


class SgsExpenseDocument(models.Model):
    _name = 'sgs.expense.document'
    _description = 'Documento de gasto SGS'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(default='Nuevo', copy=False, readonly=True, tracking=True)
    custodian_id = fields.Many2one('sgs.custodian', required=True, ondelete='cascade', tracking=True)
    company_id = fields.Many2one(related='custodian_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='custodian_id.currency_id', readonly=True)

    document_type = fields.Selection([
        ('toll', 'Caseta'),
        ('lodging', 'Hospedaje'),
        ('food', 'Alimentos'),
        ('misc', 'Varios'),
        ('invoice', 'Factura')
    ], default='toll', required=True, tracking=True)

    date = fields.Date(default=fields.Date.context_today, tracking=True)
    amount = fields.Monetary(currency_field='currency_id', tracking=True)
    vendor = fields.Char(tracking=True)
    rfc = fields.Char(tracking=True)
    concept = fields.Char(tracking=True)

    ocr_text = fields.Text(readonly=True)
    ocr_state = fields.Selection([
        ('draft', 'Borrador'),
        ('processed', 'Procesado'),
        ('confirmed', 'Confirmado'),
        ('failed', 'Falló')
    ], default='draft', tracking=True)

    image = fields.Binary(required=True)
    image_filename = fields.Char()

    service_id = fields.Many2one('sgs.route.service', ondelete='set null')
    toll_line_id = fields.Many2one('sgs.toll.line', ondelete='set null')
    fiscal_receipt_id = fields.Many2one('sgs.fiscal.receipt', ondelete='set null')

    line_ids = fields.One2many('sgs.expense.document.line', 'document_id')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if rec.name == 'Nuevo':
                rec.name = 'DOC/%s/%s' % (rec.custodian_id.employee_number or rec.custodian_id.id, rec.id)
        return res

    def action_process_ocr(self):
        for rec in self:
            rec.ocr_text = False
            rec.ocr_state = 'failed'
            if not rec.image:
                continue
            text = rec._run_ocr(rec.image)
            rec.ocr_text = text or ''
            vals = rec._extract_fields(text or '')
            if vals.get('date') and not rec.date:
                rec.date = vals['date']
            if vals.get('amount') and not rec.amount:
                rec.amount = vals['amount']
            if vals.get('vendor') and not rec.vendor:
                rec.vendor = vals['vendor']
            if vals.get('rfc') and not rec.rfc:
                rec.rfc = vals['rfc']
            if vals.get('concept') and not rec.concept:
                rec.concept = vals['concept']
            rec.ocr_state = 'processed' if text else 'failed'
        return True

    def action_confirm(self):
        for rec in self:
            if not rec.amount:
                raise ValidationError(_('Debes capturar o detectar el monto antes de confirmar.'))

            if rec.document_type == 'invoice':
                fiscal = self.env['sgs.fiscal.receipt'].sudo().create({
                    'custodian_id': rec.custodian_id.id,
                    'date': rec.date or fields.Date.context_today(rec),
                    'amount': rec.amount,
                    'description': rec.concept or _('Comprobante fiscal'),
                    'provider': rec.vendor,
                    'provider_vat': rec.rfc,
                    'image': rec.image,
                    'image_filename': rec.image_filename,
                })
                rec.fiscal_receipt_id = fiscal.id
            else:
                service = self.env['sgs.route.service'].sudo().create({
                    'custodian_id': rec.custodian_id.id,
                    'date': rec.date or fields.Date.context_today(rec),
                    'comments': rec.concept or rec.vendor or _('Comprobante capturado por portal'),
                    'status': 'pending',
                })
                line = self.env['sgs.toll.line'].sudo().create({
                    'service_id': service.id,
                    'name': rec.vendor or rec.concept or _('Gasto'),
                    'amount': rec.amount,
                    'image': rec.image,
                    'image_filename': rec.image_filename,
                })
                rec.service_id = service.id
                rec.toll_line_id = line.id

            rec.ocr_state = 'confirmed'
        return True

    def _run_ocr(self, binary_image):
        if not pytesseract or not Image:
            return ''
        data = base64.b64decode(binary_image)
        img = Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(img, lang='spa+eng')

    def _extract_fields(self, text):
        vals = {}
        txt = (text or '').upper()

        amount_match = re.search(r'(?<!\d)(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})|\d+(?:[.,]\d{2}))(?!\d)', txt)
        if amount_match:
            raw = amount_match.group(1).replace(',', '')
            try:
                vals['amount'] = float(raw)
            except Exception:
                pass

        rfc_match = re.search(r'([A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3})', txt)
        if rfc_match:
            vals['rfc'] = rfc_match.group(1)

        date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{2,4})', txt)
        if date_match:
            ds = date_match.group(1).replace('-', '/')
            parts = ds.split('/')
            try:
                year = int('20' + parts[2]) if len(parts[2]) == 2 else int(parts[2])
                vals['date'] = pydate(year, int(parts[1]), int(parts[0]))
            except Exception:
                pass

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            vals['vendor'] = lines[0][:120]
            vals['concept'] = lines[1][:120] if len(lines) > 1 else lines[0][:120]
        return vals


class SgsExpenseDocumentLine(models.Model):
    _name = 'sgs.expense.document.line'
    _description = 'Línea OCR SGS'

    document_id = fields.Many2one('sgs.expense.document', required=True, ondelete='cascade')
    label = fields.Char(required=True)
    value = fields.Char()
    confidence = fields.Float()
