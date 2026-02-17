# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustodiaPortal(CustomerPortal):

    # ---------------------------------------------------------
    # CONTADOR EN HOME DEL PORTAL
    # ---------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'services_count' in counters:
            user = request.env.user
            company = user.partner_id.commercial_partner_id

            values['services_count'] = request.env[
                'custodia.service'
            ].sudo().search_count([
                ('partner_id', '=', company.id)
            ])

        return values

    # ---------------------------------------------------------
    # LISTADO DE SERVICIOS (auth=user)
    # ---------------------------------------------------------
    @http.route(['/mis-servicios'], type='http', auth='user', website=True)
    def portal_services(self, **kwargs):
        user = request.env.user
        company = user.partner_id.commercial_partner_id

        services = request.env['custodia.service'].sudo().search(
            [('partner_id', '=', company.id)],
            order='create_date desc'
        )

        values = {
            'services': services,
            'cliente': company,
        }

        return request.render(
            'custodia_logistica.portal_service_list',
            values
        )

    # ---------------------------------------------------------
    # DETALLE DEL SERVICIO (auth=public + token)
    # ---------------------------------------------------------
    @http.route(['/mis-servicios/<int:service_id>'], 
                type='http', auth='public', website=True)
    def portal_service_detail(self, service_id=None, access_token=None, **kwargs):

        service = request.env['custodia.service'].sudo().browse(service_id)

        # 🔐 Validación obligatoria para que funcione el chatter
        self._document_check_access(
            'custodia.service',
            service_id,
            access_token
        )

        values = {
            'service': service,
            'cliente': service.partner_id,
            'token': access_token,
        }

        return request.render(
            'custodia_logistica.portal_service_detail',
            values
        )

    # ---------------------------------------------------------
    # FORMULARIO NUEVA SOLICITUD
    # ---------------------------------------------------------
    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):

        user = request.env.user
        company = user.partner_id.commercial_partner_id

        carriers = request.env['custodia.carrier'].sudo().search([])
        rutas = request.env['custodia.ruta'].sudo().search([])
        contacts = request.env['res.partner'].sudo().search([
            ('parent_id', '=', company.id)
        ])

        values = {
            'carriers': carriers,
            'rutas': rutas,
            'contacts': contacts,
            'cliente': company,
        }

        return request.render(
            'custodia_logistica.portal_service_form',
            values
        )

    # ---------------------------------------------------------
    # SUBMIT NUEVA SOLICITUD
    # ---------------------------------------------------------
    @http.route(['/solicitar-servicio/submit'], 
                type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):

        company = request.env.user.partner_id.commercial_partner_id

        try:
            # Conversión fecha/hora HTML5
            start_dt = False
            if post.get('start_datetime'):
                try:
                    start_dt = datetime.strptime(
                        post['start_datetime'],
                        "%Y-%m-%dT%H:%M"
                    )
                except Exception:
                    start_dt = fields.Datetime.from_string(
                        post['start_datetime']
                    )

            vals = {
                'partner_id': company.id,
                'contact_id': int(post['contact_id']),
                'carrier_id': int(post['carrier_id']),
                'ruta_id': int(post['ruta_id']),
                'start_datetime': start_dt,
                'nivel_seguridad': post['nivel_seguridad'],
                'load_id': post['load_id'],
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

            # 🔁 Redirigimos con token para que el chatter funcione
            return request.redirect(
                '/mis-servicios/%s?access_token=%s' % (
                    service.id,
                    service.access_token
                )
            )

        except Exception as e:

            carriers = request.env['custodia.carrier'].sudo().search([])
            rutas = request.env['custodia.ruta'].sudo().search([])
            contacts = request.env['res.partner'].sudo().search([
                ('parent_id', '=', company.id)
            ])

            return request.render(
                'custodia_logistica.portal_service_form',
                {
                    'carriers': carriers,
                    'rutas': rutas,
                    'contacts': contacts,
                    'cliente': company,
                    'error': str(e),
                }
            )
