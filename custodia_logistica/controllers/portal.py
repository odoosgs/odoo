# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime

class CustodiaPortal(http.Controller):

    @http.route(['/mis-servicios', '/mis-servicios/<int:service_id>'], type='http', auth='user', website=True)
    def portal_services(self, service_id=None, **kwargs):
        user = request.env.user
        company = user.partner_id.commercial_partner_id
        services = request.env['custodia.service'].sudo().search(
            [('partner_id', '=', company.id)], order='create_date desc'
        )
        if service_id:
            service = request.env['custodia.service'].sudo().browse(service_id)
            return request.render(
                'custodia_logistica.portal_service_detail',
                {'service': service, 'cliente': company}
            )
        return request.render(
            'custodia_logistica.portal_service_list',
            {'services': services, 'cliente': company}
        )

    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        user = request.env.user
        company = user.partner_id.commercial_partner_id
        carriers = request.env['custodia.carrier'].sudo().search([])
        rutas = request.env['custodia.ruta'].sudo().search([])
        contacts = request.env['res.partner'].sudo().search([('parent_id', '=', company.id)])
        return request.render(
            'custodia_logistica.portal_service_form',
            {
                'carriers': carriers,
                'rutas': rutas,
                'contacts': contacts,
                'cliente': company,
            }
        )

    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        company = request.env.user.partner_id.commercial_partner_id
        try:
            # Convertir fecha/hora del input HTML5 (ejemplo: 2026-01-29T14:51)
            start_dt = False
            if post.get('start_datetime'):
                try:
                    start_dt = datetime.strptime(post['start_datetime'], "%Y-%m-%dT%H:%M")
                except Exception:
                    # fallback: usar el parser de Odoo
                    start_dt = fields.Datetime.from_string(post['start_datetime'])

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
            return request.redirect('/mis-servicios/%s' % service.id)

        except Exception as e:
            # Si hay error, re-renderizamos el formulario con mensaje
            carriers = request.env['custodia.carrier'].sudo().search([])
            rutas = request.env['custodia.ruta'].sudo().search([])
            contacts = request.env['res.partner'].sudo().search([('parent_id', '=', company.id)])
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
