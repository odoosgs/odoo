# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class CustodiaPortal(http.Controller):

    @http.route(['/mis-servicios', '/mis-servicios/<int:service_id>'], type='http', auth='user', website=True)
    def portal_services(self, service_id=None, **kwargs):
        user = request.env.user
        company = user.partner_id.commercial_partner_id
        services = request.env['custodia.service'].sudo().search([('partner_id','=',company.id)], order='create_date desc')
        if service_id:
            service = request.env['custodia.service'].sudo().browse(service_id)
            return request.render('custodia_logistica.portal_service_detail', {'service': service, 'cliente': company})
        return request.render('custodia_logistica.portal_service_list', {'services': services, 'cliente': company})

    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        user = request.env.user
        company = user.partner_id.commercial_partner_id
        carriers = request.env['custodia.carrier'].sudo().search([])
        rutas = request.env['custodia.ruta'].sudo().search([])
        contacts = request.env['res.partner'].sudo().search([('parent_id','=',company.id)])
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': carriers, 'rutas': rutas, 'contacts': contacts, 'cliente': company,
        })

    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        company = request.env.user.partner_id.commercial_partner_id
        vals = {
            'partner_id': company.id,
            'contact_id': int(post['contact_id']),
            'carrier_id': int(post['carrier_id']),
            'ruta_id': int(post['ruta_id']),
            'start_datetime': post['start_datetime'],
            'nivel_seguridad': post['nivel_seguridad'],
            'load_id': post['load_id'],
            'tipo_unidad': post['tipo_unidad'],
            'placas': post['placas'],
            'operador1_nombre': post['operador1_nombre'],
            'operador1_licencia': post['operador1_licencia'],
            'transporte': post['transporte'],
            'operador2_nombre': post.get('operador2_nombre') or False,
            'operador2_licencia': post.get('operador2_licencia') or False,
            'tel_monitoreo_1': post['tel_monitoreo_1'],
            'tel_monitoreo_2': post.get('tel_monitoreo_2') or False,
            'comentarios_cliente': post.get('comentarios_cliente') or False,
        }
        service = request.env['custodia.service'].sudo().create(vals)
        return request.redirect('/mis-servicios/%s' % service.id)
