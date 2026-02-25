# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
from datetime import datetime
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

            values['services_count'] = request.env[
                'custodia.service'
            ].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])

        return values

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

        return request.render(
            'custodia_logistica.portal_service_list',
            {
                'services': services,
                'cliente': partner,
                'page_name': 'services',
            }
        )

    # =========================================================
    # DETALLE DEL SERVICIO
    # =========================================================
    @http.route(
        ['/mis-servicios/<int:service_id>'],
        type='http',
        auth='public',
        website=True
    )
    def portal_service_detail(self, service_id, access_token=None, **kwargs):

        try:
            service = self._document_check_access(
                'custodia.service',
                service_id,
                access_token
            )
        except AccessError:
            return request.redirect('/mis-servicios')

        return request.render(
            'custodia_logistica.portal_service_detail',
            {
                'service': service,
                'cliente': service.partner_id,
                'token': service.access_token,
                'page_name': 'service_detail',
            }
        )

    # =========================================================
    # VISTA TRACKING MAPA
    # =========================================================
    @http.route(
        ['/mis-servicios/<int:service_id>/tracking-view'],
        type='http',
        auth='public',
        website=True
    )
    def portal_service_tracking_view(self, service_id, access_token=None, **kwargs):

        try:
            service = self._document_check_access(
                'custodia.service',
                service_id,
                access_token
            )
        except AccessError:
            return request.redirect('/mis-servicios')

        return request.render(
            'custodia_logistica.portal_service_tracking',
            {
                'service': service,
                'token': service.access_token,
            }
        )

    # =========================================================
    # ENDPOINT JSON TRACKING EN VIVO
    # =========================================================
    @http.route(
        ['/mis-servicios/<int:service_id>/tracking'],
        type='json',
        auth='public'
    )
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):

        try:
            service = self._document_check_access(
                'custodia.service',
                service_id,
                access_token
            )
        except AccessError:
            return {'error': 'Acceso no autorizado'}

        return {
            'lat': service.current_lat or 0.0,
            'lng': service.current_lng or 0.0,
            'last_update': service.last_update,
            'state': service.state,
        }

    # =========================================================
    # FORMULARIO NUEVA SOLICITUD
    # =========================================================
    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):

        partner = request.env.user.partner_id.commercial_partner_id

        return request.render(
            'custodia_logistica.portal_service_form',
            {
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'rutas': request.env['custodia.ruta'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([
                    ('parent_id', '=', partner.id)
                ]),
                'cliente': partner,
            }
        )

    # =========================================================
    # CAMBIOS DE ESTADO (VALIDANDO PROPIEDAD)
    # =========================================================
    def _check_service_owner(self, service):
        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id.id != partner.id:
            raise AccessError("No autorizado")

    @http.route('/custodia/service/<int:service_id>/en_ruta', type='json', auth='user')
    def marcar_en_ruta(self, service_id):
        service = request.env['custodia.service'].sudo().browse(service_id)
        self._check_service_owner(service)
        service.write({'state': 'en_ruta'})
        return True

    @http.route('/custodia/service/<int:service_id>/llegada', type='json', auth='user')
    def marcar_llegada(self, service_id):
        service = request.env['custodia.service'].sudo().browse(service_id)
        self._check_service_owner(service)
        service.write({
            'arrival_datetime': fields.Datetime.now(),
            'state': 'llegada'
        })
        return True

    @http.route('/custodia/service/<int:service_id>/iniciar', type='json', auth='user')
    def iniciar_servicio(self, service_id):
        service = request.env['custodia.service'].sudo().browse(service_id)
        self._check_service_owner(service)
        service.write({
            'real_start_datetime': fields.Datetime.now(),
            'state': 'iniciado'
        })
        return True

    # =========================================================
    # COORDENADAS DE RUTA
    # =========================================================
    @http.route(
        ['/custodia/ruta/<int:ruta_id>/coordinates'],
        type='json',
        auth='public'
    )
    def get_ruta_coordinates(self, ruta_id, **kwargs):

        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)

        if not ruta.exists():
            return []

        coords = []

        if hasattr(ruta, 'punto_ids') and ruta.punto_ids:
            for punto in ruta.punto_ids:
                if punto.lat and punto.lng:
                    coords.append({
                        'lat': punto.lat,
                        'lng': punto.lng,
                    })

        if not coords and ruta.start_coords and ruta.end_coords:
            try:
                start_lat, start_lng = map(float, ruta.start_coords.split(','))
                end_lat, end_lng = map(float, ruta.end_coords.split(','))
                coords = [
                    {'lat': start_lat, 'lng': start_lng},
                    {'lat': end_lat, 'lng': end_lng},
                ]
            except Exception:
                pass

        return coords

    # =========================================================
    # SUBMIT NUEVA SOLICITUD
    # =========================================================
    @http.route(
        ['/solicitar-servicio/submit'],
        type='http',
        auth='user',
        website=True,
        csrf=True
    )
    def solicitar_submit(self, **post):

        partner = request.env.user.partner_id.commercial_partner_id

        try:
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(
                    post['start_datetime'],
                    "%Y-%m-%dT%H:%M"
                )

            vals = {
                'partner_id': partner.id,
                'contact_id': int(post.get('contact_id')) if post.get('contact_id') else False,
                'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
                'ruta_id': int(post.get('ruta_id')) if post.get('ruta_id') else False,
                'start_datetime': start_dt,
                'nivel_seguridad': post.get('nivel_seguridad'),
                'load_id': post.get('load_id'),
                'tipo_unidad': post.get('tipo_unidad'),
                'placas': post.get('placas'),
                'transporte': post.get('transporte'),
                'operador1_nombre': post.get('operador1_nombre'),
                'operador1_licencia': post.get('operador1_licencia'),
                'operador2_nombre': post.get('operador2_nombre') or False,
                'operador2_licencia': post.get('operador2_licencia') or False,
                'tel_monitoreo_1': post.get('tel_monitoreo_1'),
                'tel_monitoreo_2': post.get('tel_monitoreo_2') or False,
                'comentarios_cliente': post.get('comentarios_cliente') or False,
                'start_coords': post.get('start_coords'),
                'end_coords': post.get('end_coords'),
                'state': 'solicitado',
            }

            service = request.env['custodia.service'].sudo().create(vals)
            service._portal_ensure_token()

            return request.redirect(
                f'/mis-servicios/{service.id}?access_token={service.access_token}'
            )

        except Exception as e:

            return request.render(
                'custodia_logistica.portal_service_form',
                {
                    'carriers': request.env['custodia.carrier'].sudo().search([]),
                    'rutas': request.env['custodia.ruta'].sudo().search([]),
                    'contacts': request.env['res.partner'].sudo().search([
                        ('parent_id', '=', partner.id)
                    ]),
                    'cliente': partner,
                    'error': str(e),
                }
            )
