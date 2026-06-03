# -*- coding: utf-8 -*-
import base64
import secrets
import re
from datetime import datetime, timedelta, time
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# Importar pdfminer.six para extracción de texto de PDF
try:
    from pdfminer.high_level import extract_text
    from io import BytesIO
except ImportError:
    extract_text = None
    BytesIO = None
    # Considerar añadir una advertencia o error si pdfminer no está instalado

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Añadimos los campos necesarios a hr.employee
    #initial_fund = fields.Monetary('Fondo inicial', currency_field='currency_id', default=0.0, tracking=True)
    #portal_token = fields.Char('Token portal', copy=False, index=True, readonly=True, default=lambda self: secrets.token_urlsafe(24))
    #portal_url = fields.Char('Enlace portal', compute='_compute_portal_url')
    #whatsapp_url = fields.Char('Enlace WhatsApp', compute='_compute_portal_url')
    #portal_qr_code = fields.Binary('Código QR Portal', compute='_compute_portal_qr_code')
    
    #deposit_ids = fields.One2many('sgs.perdiem.deposit', 'custodian_id', string='Depósitos')
    #service_ids = fields.One2many('sgs.route.service', 'custodian_id', string='Servicios')
    #fiscal_receipt_ids = fields.One2many('sgs.fiscal.receipt', 'custodian_id', string='Comprobantes fiscales')
    
    #total_deposits = fields.Monetary('Total depositado', compute='_compute_amounts', currency_field='currency_id')
    #total_expenses = fields.Monetary('Total gastos', compute='_compute_amounts', currency_field='currency_id')
    #total_fiscal = fields.Monetary('Total fiscal comprobado', compute='_compute_amounts', currency_field='currency_id')
    #balance = fields.Monetary('Saldo', compute='_compute_amounts', currency_field='currency_id')
    
    #pending_service_count = fields.Integer('Servicios pendientes', compute='_compute_amounts')
    #late_service_count = fields.Integer('Servicios fuera de 12h', compute='_compute_amounts')
    
    compliance_state = fields.Selection([
        ('blue', 'Sin gastos'),
        ('green', 'Al día'),
        ('yellow', 'Pendiente'),
        ('red', 'Atrasado / Rechazado'),
    ], string='Semáforo', compute='_compute_amounts')

    @api.depends('portal_token', 'mobile_phone')
    def _compute_portal_url(self):
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for rec in self:
            rec.portal_url = f'{base}/sgs/custodio/{rec.portal_token}' if rec.portal_token else ''
            phone = ''.join(ch for ch in (rec.mobile_phone or '') if ch.isdigit())
            if phone and rec.portal_url:
                if len(phone) == 10: phone = '52' + phone
                msg = f'Hola {rec.name.split()[0] if rec.name else ""}, este es tu enlace de viáticos SGS: {rec.portal_url}'
                rec.whatsapp_url = 'https://wa.me/%s?text=%s' % (phone, msg.replace(' ', '%20' ))
            else:
                rec.whatsapp_url = ''

    @api.depends('portal_url')
    def _compute_portal_qr_code(self):
        try:
            import qrcode
            from io import BytesIO
        except ImportError:
            qrcode = None
        for rec in self:
            if qrcode and rec.portal_url:
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(rec.portal_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                temp = BytesIO()
                img.save(temp, format="PNG")
                rec.portal_qr_code = base64.b64encode(temp.getvalue())
            else:
                rec.portal_qr_code = False

    @api.depends('initial_fund', 'deposit_ids.amount', 'service_ids.amount_total', 'service_ids.status', 'fiscal_receipt_ids.amount')
    def _compute_amounts(self):
        for rec in self:
            deposits = sum(rec.deposit_ids.mapped('amount'))
            expenses = sum(rec.service_ids.filtered(lambda s: s.status != 'rejected').mapped('amount_total'))
            fiscal = sum(rec.fiscal_receipt_ids.mapped('amount'))
            rec.total_deposits = deposits
            rec.total_expenses = expenses
            rec.total_fiscal = fiscal
            rec.balance = rec.initial_fund + deposits - expenses
            rec.pending_service_count = len(rec.service_ids.filtered(lambda s: s.status == 'pending'))
            rec.late_service_count = len(rec.service_ids.filtered(lambda s: s.is_late and s.status != 'approved'))
            if not rec.service_ids: rec.compliance_state = 'blue'
            elif rec.late_service_count: rec.compliance_state = 'red'
            elif rec.pending_service_count: rec.compliance_state = 'yellow'
            else: rec.compliance_state = 'green'

    def action_regenerate_portal_token(self):
        for rec in self: rec.portal_token = secrets.token_urlsafe(24)
        return True

    def action_open_portal(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.portal_url, 'target': 'new'}

class SgsPerdiemDeposit(models.Model):
    _name = 'sgs.perdiem.deposit'
    _description = 'Depósito de viáticos SGS'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    name = fields.Char('Referencia', compute='_compute_name', store=True)
    custodian_id = fields.Many2one('hr.employee', string='Custodio', required=True, ondelete='cascade', tracking=True)
    company_id = fields.Many2one(related='custodian_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='custodian_id.currency_id', readonly=True)
    date = fields.Date('Fecha de depósito', required=True, default=fields.Date.context_today, tracking=True)
    month = fields.Char('Mes', compute='_compute_month', store=True)
    week = fields.Char('Semana / período')
    concept = fields.Char('Concepto', default='Depósito semanal viáticos')
    amount = fields.Monetary('Monto', currency_field='currency_id', required=True, tracking=True)
    batch_id = fields.Many2one('sgs.deposit.batch', string='Lote de Carga', ondelete='set null')

    @api.depends('custodian_id', 'date', 'amount')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s · %s · $%0.2f' % (rec.custodian_id.name or 'Custodio', rec.date or '', rec.amount or 0.0)

    @api.depends('date')
    def _compute_month(self):
        months = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
        for rec in self:
            rec.month = months[rec.date.month - 1] if rec.date else ''

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('El monto del depósito debe ser mayor a cero.'))

class SgsRouteService(models.Model):
    _name = 'sgs.route.service'
    _description = 'Servicio de custodia y gasto SGS'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date desc, id desc'
    name = fields.Char('Folio', default='Nuevo', copy=False, readonly=True, tracking=True)
    custodian_id = fields.Many2one('hr.employee', string='Custodio', required=True, ondelete='cascade', tracking=True)
    company_id = fields.Many2one(related='custodian_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='custodian_id.currency_id', readonly=True)
    date = fields.Date('Fecha del servicio', required=True, default=fields.Date.context_today, tracking=True)
    submit_datetime = fields.Datetime('Fecha/hora de captura', default=fields.Datetime.now, readonly=True)
    client_id = fields.Many2one('res.partner', string='Cliente')
    origin = fields.Char('Origen')
    destination = fields.Char('Destino')
    companion_id = fields.Many2one('hr.employee', string='Compañero / segundo custodio')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo')
    vehicle_snapshot = fields.Char('Vehículo usado')
    plate_snapshot = fields.Char('Placas')
    comments = fields.Text('Comentarios / aclaraciones')
    amount_perdiem = fields.Monetary('Viáticos', currency_field='currency_id', default=0.0)
    amount_fuel = fields.Monetary('Gasolina', currency_field='currency_id', default=0.0)
    amount_lodging = fields.Monetary('Hospedaje', currency_field='currency_id', default=0.0)
    amount_misc = fields.Monetary('Gastos varios', currency_field='currency_id', default=0.0)
    misc_detail = fields.Char('Especificación gastos varios')
    toll_line_ids = fields.One2many('sgs.toll.line', 'service_id', string='Casetas')
    amount_tolls = fields.Monetary('Casetas', compute='_compute_total', currency_field='currency_id', store=True)
    amount_total = fields.Monetary('Total servicio', compute='_compute_total', currency_field='currency_id', store=True)
    evidence_image = fields.Binary('Evidencia general')
    evidence_filename = fields.Char('Nombre archivo evidencia')
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Autorizado'),
        ('rejected', 'Rechazado'),
    ], default='pending', required=True, tracking=True)
    validation_note = fields.Text('Observación de validación')
    is_late = fields.Boolean('Fuera de 12h', compute='_compute_is_late', store=True)

    @api.depends('amount_perdiem', 'amount_fuel', 'amount_lodging', 'amount_misc', 'toll_line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.amount_tolls = sum(rec.toll_line_ids.mapped('amount'))
            rec.amount_total = rec.amount_perdiem + rec.amount_fuel + rec.amount_lodging + rec.amount_misc + rec.amount_tolls

    @api.depends('date', 'submit_datetime')
    def _compute_is_late(self):
        for rec in self:
            if rec.date and rec.submit_datetime:
                deadline = datetime.combine(rec.date, time.min) + timedelta(hours=36)
                rec.is_late = rec.submit_datetime > deadline
            else:
                rec.is_late = False

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.vehicle_snapshot = rec.vehicle_id.name
                rec.plate_snapshot = rec.vehicle_id.license_plate

    @api.constrains('amount_misc', 'misc_detail')
    def _check_amounts(self):
        for rec in self:
            if rec.amount_misc > 0 and not rec.misc_detail:
                raise ValidationError(_('Debes especificar el detalle de gastos varios.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                cust = self.env['hr.employee'].browse(vals.get('custodian_id'))
                seq = self.env['ir.sequence'].next_by_code('sgs.route.service') or '0001'
                emp = cust.employee_number or str(cust.id or '')
                vals['name'] = 'F-%s-%s' % (emp, seq)
            if vals.get('vehicle_id') and not vals.get('vehicle_snapshot'):
                veh = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
                vals['vehicle_snapshot'] = veh.name
                vals['plate_snapshot'] = veh.license_plate
        return super().create(vals_list)

    def action_approve(self):
        self.write({'status': 'approved'})

    def action_reject(self):
        self.write({'status': 'rejected'})

    def action_pending(self):
        self.write({'status': 'pending'})

class SgsTollLine(models.Model):
    _name = 'sgs.toll.line'
    _description = 'Caseta de servicio SGS'
    _order = 'id'
    service_id = fields.Many2one('sgs.route.service', string='Servicio', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='service_id.currency_id', readonly=True)
    name = fields.Char('Caseta / peaje', required=True)
    amount = fields.Monetary('Monto', currency_field='currency_id', required=True)
    image = fields.Binary('Foto de comprobante')
    image_filename = fields.Char('Archivo')

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('El monto de la caseta debe ser mayor a cero.'))

class SgsFiscalReceipt(models.Model):
    _name = 'sgs.fiscal.receipt'
    _description = 'Comprobante fiscal SGS'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    name = fields.Char('Referencia', compute='_compute_name', store=True)
    custodian_id = fields.Many2one('hr.employee', string='Custodio', required=True, ondelete='cascade', tracking=True)
    company_id = fields.Many2one(related='custodian_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='custodian_id.currency_id', readonly=True)
    date = fields.Date('Fecha factura', required=True, default=fields.Date.context_today)
    amount = fields.Monetary('Monto', currency_field='currency_id', required=True, tracking=True)
    description = fields.Char('Concepto / descripción', required=True)
    provider = fields.Char('Proveedor / razón social')
    provider_vat = fields.Char('RFC proveedor')
    image = fields.Binary('Foto factura')
    image_filename = fields.Char('Archivo')
    # Campos OCR
    ocr_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('success', 'Exitoso'),
        ('failed', 'Fallido')
    ], string='Estado OCR', default='pending', tracking=True)
    ocr_raw_data = fields.Text('Datos crudos OCR')
    ocr_error_message = fields.Text('Error OCR')
    is_fiscal = fields.Boolean('Es comprobante fiscal', default=False)
    rfc_emitter = fields.Char('RFC Emisor (OCR)')
    emitter_name = fields.Char('Nombre Emisor (OCR)')
    ocr_date = fields.Date('Fecha (OCR)')
    ocr_amount = fields.Monetary('Monto (OCR)', currency_field='currency_id')

    @api.depends('custodian_id', 'date', 'description')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s · %s · %s' % (rec.custodian_id.name or 'Custodio', rec.date or '', rec.description or 'Factura')

    @api.constrains('amount', 'ocr_status')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0 and rec.ocr_status == 'success':
                raise ValidationError(_('El monto del comprobante fiscal debe ser mayor a cero.'))


class SgsDepositBatch(models.Model):
    _name = 'sgs.deposit.batch'
    _description = 'Lote de Carga de Depósitos'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char('Nombre del Lote', required=True, default=lambda self: _('Nuevo Lote de Depósitos'))
    date = fields.Date('Fecha de Carga', default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', string='Cargado por', default=lambda self: self.env.user, required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'Procesando'),
        ('processed', 'Procesado'),
        ('validated', 'Validado'),
        ('error', 'Con Errores'),
    ], string='Estado', default='draft', tracking=True)
    deposit_file_ids = fields.One2many('sgs.deposit.file', 'batch_id', string='Archivos de Depósito')
    total_files = fields.Integer('Total Archivos', compute='_compute_totals')
    processed_files = fields.Integer('Archivos Procesados', compute='_compute_totals')
    error_files = fields.Integer('Archivos con Error', compute='_compute_totals')
    total_amount = fields.Monetary('Monto Total', compute='_compute_totals', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

    @api.depends('deposit_file_ids.status', 'deposit_file_ids.extracted_amount')
    def _compute_totals(self):
        for rec in self:
            rec.total_files = len(rec.deposit_file_ids)
            rec.processed_files = len(rec.deposit_file_ids.filtered(lambda f: f.status in ('processed', 'validated')))
            rec.error_files = len(rec.deposit_file_ids.filtered(lambda f: f.status == 'error'))
            rec.total_amount = sum(rec.deposit_file_ids.filtered(lambda f: f.status in ('processed', 'validated')).mapped('extracted_amount'))

    def action_process_batch(self):
        self.ensure_one()
        self.write({'state': 'processing'})
        for deposit_file in self.deposit_file_ids.filtered(lambda f: f.status == 'pending'):
            deposit_file.action_extract_data()
        self.action_update_batch_state()

    def action_update_batch_state(self):
        self.ensure_one()
        if all(f.status in ('processed', 'validated', 'error') for f in self.deposit_file_ids):
            if any(f.status == 'error' for f in self.deposit_file_ids):
                self.write({'state': 'error'})
            elif all(f.status in ('processed', 'validated') for f in self.deposit_file_ids):
                self.write({'state': 'processed'})
        else:
            self.write({'state': 'draft'})

    def action_validate_batch(self):
        self.ensure_one()
        for deposit_file in self.deposit_file_ids.filtered(lambda f: f.status == 'processed'):
            deposit_file.action_create_deposit()
        self.write({'state': 'validated'})


class SgsDepositFile(models.Model):
    _name = 'sgs.deposit.file'
    _description = 'Archivo de Depósito para Carga Masiva'
    _order = 'create_date desc'

    batch_id = fields.Many2one('sgs.deposit.batch', string='Lote de Carga', required=True, ondelete='cascade')
    name = fields.Char('Nombre del Archivo', required=True)
    file_content = fields.Binary('Archivo PDF', required=True, attachment=True)
    file_mimetype = fields.Char('Tipo de Archivo', compute='_compute_file_mimetype', store=True)
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('processed', 'Procesado'),
        ('validated', 'Validado'),
        ('error', 'Error'),
    ], string='Estado', default='pending', tracking=True)
    error_message = fields.Text('Mensaje de Error')

    extracted_rfc = fields.Char('RFC Extraído')
    extracted_name = fields.Char('Nombre Extraído')
    extracted_amount = fields.Monetary('Monto Extraído', currency_field='currency_id')
    extracted_date = fields.Date('Fecha Extraída')
    extracted_reference = fields.Char('Referencia Extraída')
    
    currency_id = fields.Many2one('res.currency', related='batch_id.currency_id', readonly=True)
    company_id = fields.Many2one(related='batch_id.company_id', readonly=True)

    employee_id = fields.Many2one('hr.employee', string='Custodio Identificado', ondelete='set null')
    deposit_id = fields.Many2one('sgs.perdiem.deposit', string='Depósito Creado', ondelete='set null')

    @api.depends('file_content')
    def _compute_file_mimetype(self):
        for rec in self:
            if rec.file_content:
                rec.file_mimetype = 'application/pdf' # Asumimos PDF por ahora
            else:
                rec.file_mimetype = False

    def action_extract_data(self):
        self.ensure_one()
        if not extract_text or not BytesIO:
            self.write({'status': 'error', 'error_message': 'Librería pdfminer.six no instalada o BytesIO no disponible.'})
            return

        self.write({'status': 'processing', 'error_message': False})
        try:
            pdf_content = base64.b64decode(self.file_content)
            text = extract_text(BytesIO(pdf_content))
            
            # Lógica de extracción basada en el desglose del usuario
            rfc_beneficiario = re.search(r'RFC Beneficiario\s*([A-Z0-9]+)', text)
            nombre_beneficiario = re.search(r'Nombre del Beneficiario\s*(.+)', text)
            importe_transferir = re.search(r'Importe a Transferir\s*\$([0-9,.]+)', text)
            fecha_aplicacion = re.search(r'Fecha Aplicación\s*([0-9/]+)', text)
            referencia_numerica = re.search(r'Referencia numérica\s*([0-9]+)', text)

            extracted_data = {
                'extracted_rfc': rfc_beneficiario.group(1) if rfc_beneficiario else False,
                'extracted_name': nombre_beneficiario.group(1).strip() if nombre_beneficiario else False,
                'extracted_amount': float(importe_transferir.group(1).replace(',', '')) if importe_transferir else 0.0,
                'extracted_date': datetime.strptime(fecha_aplicacion.group(1), '%d/%m/%Y').date() if fecha_aplicacion else False,
                'extracted_reference': referencia_numerica.group(1) if referencia_numerica else False,
            }

            # Identificar al empleado (custodio)
            employee = False
            if extracted_data['extracted_rfc']:
                employee = self.env['hr.employee'].search([('rfc', '=', extracted_data['extracted_rfc'])], limit=1)
            if not employee and extracted_data['extracted_name']:
                employee = self.env['hr.employee'].search([('name', 'ilike', extracted_data['extracted_name'])], limit=1)
            
            if employee:
                extracted_data['employee_id'] = employee.id
                extracted_data['status'] = 'processed'
            else:
                extracted_data['status'] = 'error'
                extracted_data['error_message'] = 'No se pudo identificar al custodio por RFC o nombre.'

            self.write(extracted_data)

        except Exception as e:
            self.write({'status': 'error', 'error_message': str(e)})
        finally:
            self.batch_id.action_update_batch_state()

    def action_create_deposit(self):
        self.ensure_one()
        if self.status == 'processed' and self.employee_id and self.extracted_amount > 0 and self.extracted_date:
            deposit = self.env['sgs.perdiem.deposit'].create({
                'custodian_id': self.employee_id.id,
                'date': self.extracted_date,
                'amount': self.extracted_amount,
                'concept': f'Depósito masivo - Ref: {self.extracted_reference or self.name}',
                'batch_id': self.batch_id.id,
            })
            self.write({'deposit_id': deposit.id, 'status': 'validated'})
        else:
            self.write({'status': 'error', 'error_message': 'Datos insuficientes o estado incorrecto para crear depósito.'})

