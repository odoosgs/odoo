# -*- coding: utf-8 -*-
import json
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError

class CustodiaPortal(CustomerPortal):

    # =========================================================
    # CONTADOR EN HOME DEL PORTAL
    # =========================================================
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'services_count' in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            values['services_count'] = request.env['custodia.service'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        return values

    # =========================================================
    # ENDPOINT PARA COORDENADAS (Necesario para route_map.js)
    # =========================================================
    @http.route(['/custodia/ruta/<int:ruta_id>/coordinates'], type='json', auth='public', website=True)
    def get_ruta_coordinates(self, ruta_id, **kwargs):
        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)
        if not ruta.exists():
            return []
        return ruta.get_route_coordinates()

    # NOTA: Asegúrate de que el template 'portal_service_form' 
    # exista en tus archivos XML. Si no existe, el 404 persistirá.

    # =========================================================
    # LISTADO DE SERVICIOS
    # =========================================================
    @http.route(['/mis-servicios'], type='http', auth='user', website=True)
    def portal_services(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        services = request.env['custodia.service'].sudo().search(
            [('partner_id', '=', partner.id)],
            order='create_date desc'
        )
        return request.render('custodia_logistica.portal_service_list', {
            'services': services,
            'cliente': partner,
            'page_name': 'services',
        })

    # =========================================================
    # DETALLE DEL SERVICIO
    # =========================================================
    @http.route(['/mis-servicios/<int:service_id>'], type='http', auth='public', website=True)
    def portal_service_detail(self, service_id, access_token=None, **kwargs):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except AccessError:
            return request.redirect('/mis-servicios')

        return request.render('custodia_logistica.portal_service_detail', {
            'service': service,
            'cliente': service.partner_id,
            'token': service.access_token,
            'page_name': 'service_detail',
        })

    # =========================================================
    # ENDPOINT JSON TRACKING (Sincronizado con route_map.js)
    # =========================================================
    @http.route(['/mis-servicios/<int:service_id>/tracking'], type='http', auth='public', website=True, csrf=False)
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):
        try:
            # Verificamos acceso mediante token o sesión
            service = self._document_check_access('custodia.service', service_id, access_token)
        except Exception:
            return request.make_response(
                json.dumps({'error': 'Acceso no autorizado'}),
                headers=[('Content-Type', 'application/json')]
            )

        data = {
            'lat': service.current_lat or 0.0,
            'lng': service.current_lng or 0.0,
            'last_update': str(service.last_update) if service.last_update else False,
            'state': service.state,
        }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    # =========================================================
    # FORMULARIO NUEVA SOLICITUD
    # =========================================================
    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'rutas': request.env['custodia.ruta'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
        })

    # =========================================================
    # SUBMIT NUEVA SOLICITUD (Corregido para nivel_seguridad)
    # =========================================================
    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        try:
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(post['start_datetime'], "%Y-%m-%dT%H:%M")

            vals = {
                'partner_id': partner.id,
                'contact_id': int(post.get('contact_id')) if post.get('contact_id') else False,
                'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
                'ruta_id': int(post.get('ruta_id')) if post.get('ruta_id') else False,
                'start_datetime': start_dt,
                'nivel_seguridad': post.get('nivel_seguridad'), # Dato obligatorio
                'load_id': post.get('load_id'),
                'tipo_unidad': post.get('tipo_unidad'),
                'placas': post.get('placas'),
                'transporte': post.get('transporte'),
                'operador1_nombre': post.get('operador1_nombre'),
                'tel_monitoreo_1': post.get('tel_monitoreo_1'),
                'state': 'solicitado',
            }

            service = request.env['custodia.service'].sudo().create(vals)
            service._portal_ensure_token()

            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        except Exception as e:
            return request.render('custodia_logistica.portal_service_form', {
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'rutas': request.env['custodia.ruta'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
                'cliente': partner,
                'error': str(e),
            })

    # =========================================================
    # ACCIONES DEL CUSTODIO
    # =========================================================
    @http.route('/custodia/service/<int:service_id>/<string:action>', type='json', auth='user')
    def custodia_action(self, service_id, action):
        service = request.env['custodia.service'].sudo().browse(service_id)
        # Verificación de propiedad básica
        if service.partner_id.id != request.env.user.partner_id.commercial_partner_id.id:
            return False
        
        if action == 'iniciar':
            service.write({'state': 'iniciado', 'real_start_datetime': fields.Datetime.now()})
        elif action == 'en_ruta':
            service.write({'state': 'en_ruta'})
        elif action == 'llegada':
            service.write({'state': 'llegada', 'arrival_datetime': fields.Datetime.now()})
        return True
