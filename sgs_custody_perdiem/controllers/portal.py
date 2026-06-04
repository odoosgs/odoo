# -*- coding: utf-8 -*-
import base64
from odoo import http, fields, _
from odoo.http import request
from werkzeug.exceptions import NotFound

class SgsPortal(http.Controller ):

    def _get_custodian(self, token):
        # Buscamos en hr.employee usando el nuevo campo portal_token
        custodian = request.env['hr.employee'].sudo().search([('portal_token', '=', token), ('active', '=', True)], limit=1)
        if not custodian:
            raise NotFound()
        return custodian

    @http.route(['/sgs/custodio/<string:token>'], type='http', auth="public", website=True )
    def custodian_home(self, token, **kw):
        custodian = self._get_custodian(token)
        # Usamos los modelos estándar de Odoo para las listas desplegables
        clients = request.env['res.partner'].sudo().search([('is_company', '=', True)])
        vehicles = request.env['fleet.vehicle'].sudo().search([])
        companions = request.env['hr.employee'].sudo().search([('id', '!=', custodian.id)])
        
        values = {
            'custodian': custodian,
            'clients': clients,
            'vehicles': vehicles,
            'companions': companions,
            'token': token,
            'ok': kw.get('ok'),
        }
        return request.render("sgs_custody_perdiem.portal_custodian_home", values)

    @http.route(['/sgs/custodio/<string:token>/servicio'], type='http', auth='public', methods=['POST'], website=True, csrf=True, sitemap=False )
    def submit_service(self, token, **post):
        custodian = self._get_custodian(token)
        
        # REFACTORIZACIÓN: Usar res.partner y fleet.vehicle
        client_id = int(post.get('client_id')) if post.get('client_id') else False
        vehicle_id = int(post.get('vehicle_id')) if post.get('vehicle_id') else False
        companion_id = int(post.get('companion_id')) if post.get('companion_id') else False

        vals = {
            'custodian_id': custodian.id,
            'date': post.get('date') or fields.Date.today(),
            'client_id': client_id,
            'vehicle_id': vehicle_id,
            'companion_id': companion_id,
            'origin': post.get('origin'),
            'destination': post.get('destination'),
            'comments': post.get('comments'),
            'amount_perdiem': float(post.get('amount_perdiem') or 0),
            'amount_fuel': float(post.get('amount_fuel') or 0),
            'amount_lodging': float(post.get('amount_lodging') or 0),
            'amount_misc': float(post.get('amount_misc') or 0),
            'misc_detail': post.get('misc_detail'),
            'status': 'pending',
        }

        # Manejo de evidencia principal
        upload = request.httprequest.files.get('evidence' )
        if upload and upload.filename:
            vals['evidence_filename'] = upload.filename
            vals['evidence_image'] = base64.b64encode(upload.read())

        # Crear el servicio
        service = request.env['sgs.route.service'].sudo().create(vals)

        # Manejo de casetas (Tolls)
        toll_names = request.httprequest.form.getlist('toll_name[]' )
        toll_amounts = request.httprequest.form.getlist('toll_amount[]' )
        toll_files = request.httprequest.files.getlist('toll_image[]' )

        for idx, name in enumerate(toll_names):
            amount = float(toll_amounts[idx] or 0) if idx < len(toll_amounts) else 0
            if not name and not amount:
                continue
            
            line_vals = {
                'service_id': service.id, 
                'name': name or 'Caseta', 
                'amount': amount
            }
            
            if idx < len(toll_files) and toll_files[idx] and toll_files[idx].filename:
                line_vals['image_filename'] = toll_files[idx].filename
                line_vals['image'] = base64.b64encode(toll_files[idx].read())
            
            request.env['sgs.toll.line'].sudo().create(line_vals)

        return request.redirect('/sgs/custodio/%s?ok=servicio' % token)
