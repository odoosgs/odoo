# -*- coding: utf-8 -*-
import json
from datetime import datetime

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError
from odoo.http import request


class CustodiaPortal(CustomerPortal):

    def _extract_lat_lng(self, record, lat_names=None, lng_names=None):
        if not record:
            return None
        lat_names = lat_names or ['latitude', 'lat', 'origin_latitude', 'destination_latitude']
        lng_names = lng_names or ['longitude', 'lng', 'lon', 'origin_longitude', 'destination_longitude']
        lat = False
        lng = False
        for name in lat_names:
            if hasattr(record, name):
                lat = getattr(record, name)
                if lat not in (False, None, ''):
                    break
        for name in lng_names:
            if hasattr(record, name):
                lng = getattr(record, name)
                if lng not in (False, None, ''):
                    break
        if lat in (False, None, '') or lng in (False, None, ''):
            return None
        return {'lat': lat, 'lng': lng}

    def _extract_point_from_text(self, value, label=None):
        if not value or ',' not in str(value):
            return None
        try:
            parts = [p.strip() for p in str(value).split(',')]
            if len(parts) < 2:
                return None
            return {'lat': float(parts[0]), 'lng': float(parts[1]), 'label': label}
        except Exception:
            return None

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'services_count' in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            values['services_count'] = request.env['custodia.service'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        return values

    @http.route(['/custodia/ruta/<int:ruta_id>/coordinates'], type='json', auth='public', website=True)
    def get_ruta_coordinates(self, ruta_id, **kwargs):
        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)
        if not ruta.exists():
            return []

        coords = ruta.get_route_coordinates() if hasattr(ruta, 'get_route_coordinates') else []
        if coords and len(coords) >= 2:
            return coords

        fallback = []

        direct_origin = self._extract_lat_lng(
            ruta,
            lat_names=['origin_latitude', 'latitude', 'lat'],
            lng_names=['origin_longitude', 'longitude', 'lng', 'lon'],
        )
        direct_dest = self._extract_lat_lng(
            ruta,
            lat_names=['destination_latitude', 'dest_latitude', 'latitude_destino'],
            lng_names=['destination_longitude', 'dest_longitude', 'longitude_destino'],
        )
        node_origin = self._extract_lat_lng(getattr(ruta, 'nodo_origen_id', False))
        node_dest = self._extract_lat_lng(getattr(ruta, 'nodo_destino_id', False))
        text_origin = self._extract_point_from_text(getattr(ruta, 'start_coords', False), 'Origen')
        text_dest = self._extract_point_from_text(getattr(ruta, 'end_coords', False), 'Destino')

        for point, label in [
            (direct_origin, 'Origen'),
            (node_origin, 'Origen'),
            (text_origin, 'Origen'),
            (direct_dest, 'Destino'),
            (node_dest, 'Destino'),
            (text_dest, 'Destino'),
        ]:
            if point:
                point.setdefault('label', label)
                exists = any(abs(p['lat'] - point['lat']) < 1e-9 and abs(p['lng'] - point['lng']) < 1e-9 for p in fallback)
                if not exists:
                    fallback.append(point)

        return fallback

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
            'can_convert_alert': service.request_type == 'alerta',
        })

    @http.route('/custodia/service/<int:service_id>/incidencia', type='json', auth='user', methods=['POST'], website=True)
    def custodia_reportar_incidencia(self, service_id, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        mensaje = kwargs.get('mensaje')

        if not service.exists() or not mensaje:
            return {'status': 'error', 'message': 'Datos incompletos'}

        service.message_post(
            body=f"⚠️ <b>INCIDENCIA REPORTADA:</b><br/>{mensaje}",
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        return {'status': 'success'}


    @http.route(['/mis-servicios/<int:service_id>/convertir'], type='http', auth='user', website=True)
    def portal_convert_alert(self, service_id, access_token=None, **kwargs):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except Exception:
            return request.redirect('/mis-servicios')

        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id != partner and not request.env.user.has_group('base.group_user'):
            return request.redirect('/mis-servicios')

        if service.request_type == 'alerta':
            service.action_convert_to_service()
            service.message_post(body='Alerta convertida a solicitud desde portal por el cliente.')

        return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')


    @http.route(['/mis-servicios/<int:service_id>/editar'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_edit_service(self, service_id, access_token=None, **post):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except Exception:
            return request.redirect('/mis-servicios')

        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id != partner and not request.env.user.has_group('base.group_user'):
            return request.redirect('/mis-servicios')

        if request.httprequest.method == 'POST':
            vals = {
                'contact_id': int(post.get('contact_id')) if post.get('contact_id') else service.contact_id.id,
                'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
                'start_datetime': datetime.strptime(post.get('start_datetime'), '%Y-%m-%dT%H:%M') if post.get('start_datetime') else service.start_datetime,
                'nivel_seguridad': post.get('nivel_seguridad') or False,
                'load_id': post.get('load_id') or False,
                'tipo_unidad': post.get('tipo_unidad') or False,
                'placas': post.get('placas') or False,
                'transporte': post.get('transporte') or False,
                'operador1_nombre': post.get('operador1_nombre') or False,
                'tel_monitoreo_1': post.get('tel_monitoreo_1') or False,
            }
            service.sudo().write(vals)
            service.message_post(body='Datos actualizados por cliente desde portal.')
            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        return request.render('custodia_logistica.portal_service_edit', {
            'service': service,
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
            'page_name': 'service_edit',
        })

    @http.route(['/mis-servicios/<int:service_id>/tracking'], type='http', auth='public', website=True, csrf=False)
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except Exception:
            return request.make_response(
                json.dumps({'error': 'Acceso denegado'}),
                headers=[('Content-Type', 'application/json')]
            )

        lat = service.current_lat or service.ruta_id.origin_latitude
        lng = service.current_lng or service.ruta_id.origin_longitude

        data = {
            'lat': lat,
            'lng': lng,
            'last_update': str(service.last_update) if service.last_update else 'Sin reportes',
            'state': service.state,
        }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/get_nodos_by_maestra/<int:maestra_id>', type='http', auth='user', website=True, csrf=False)
    def get_nodos_by_maestra(self, maestra_id, **kwargs):
        rutas = request.env['custodia.ruta'].sudo().search([
            ('ruta_maestra_id', '=', maestra_id)
        ])

        origenes = []
        destinos = []
        seen_orig = set()
        seen_dest = set()

        for ruta in rutas:
            if ruta.nodo_origen_id and ruta.nodo_origen_id.id not in seen_orig:
                origenes.append({'id': ruta.nodo_origen_id.id, 'name': ruta.nodo_origen_id.name})
                seen_orig.add(ruta.nodo_origen_id.id)
            if ruta.nodo_destino_id and ruta.nodo_destino_id.id not in seen_dest:
                destinos.append({'id': ruta.nodo_destino_id.id, 'name': ruta.nodo_destino_id.name})
                seen_dest.add(ruta.nodo_destino_id.id)

        data = {
            'origenes': sorted(origenes, key=lambda x: x['name']),
            'destinos': sorted(destinos, key=lambda x: x['name']),
        }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
        })

    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        try:
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(post['start_datetime'], '%Y-%m-%dT%H:%M')

            contact_id = int(post.get('contact_id')) if post.get('contact_id') else False
            if not contact_id or not start_dt:
                raise ValueError('Debe capturar contacto solicitante y fecha programada.')

            maestra_id = int(post.get('ruta_maestra_id', 0))
            origen_id = int(post.get('nodo_origen_id', 0))
            destino_id = int(post.get('nodo_destino_id', 0))

            ruta_variante = request.env['custodia.ruta'].sudo().search([
                ('ruta_maestra_id', '=', maestra_id),
                ('nodo_origen_id', '=', origen_id),
                ('nodo_destino_id', '=', destino_id),
            ], limit=1) if (maestra_id and origen_id and destino_id) else request.env['custodia.ruta']

            vals = {
                'partner_id': partner.id,
                'contact_id': contact_id,
                'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
                'ruta_id': ruta_variante.id if ruta_variante else False,
                'start_datetime': start_dt,
                'nivel_seguridad': post.get('nivel_seguridad') or False,
                'load_id': post.get('load_id') or False,
                'tipo_unidad': post.get('tipo_unidad'),
                'placas': post.get('placas'),
                'transporte': post.get('transporte'),
                'operador1_nombre': post.get('operador1_nombre'),
                'tel_monitoreo_1': post.get('tel_monitoreo_1'),
            }

            # Portal crea ALERTA por defecto para captura anticipada.
            # Solo se crea servicio directo cuando el formulario lo envía explícitamente.
            create_as_service = str(post.get('create_as_service', '')).lower() in ('1', 'true', 'on', 'yes')
            if create_as_service:
                required_for_service = all([
                    vals.get('carrier_id'),
                    vals.get('ruta_id'),
                    vals.get('nivel_seguridad'),
                    vals.get('load_id'),
                ])
                vals['request_type'] = 'servicio' if required_for_service else 'alerta'
                vals['state'] = 'solicitado' if required_for_service else 'alerta'
            else:
                vals['request_type'] = 'alerta'
                vals['state'] = 'alerta'

            service = request.env['custodia.service'].sudo().create(vals)
            service._portal_ensure_token()

            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        except Exception as err:
            return request.render('custodia_logistica.portal_service_form', {
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
                'cliente': partner,
                'error': str(err),
            })

    @http.route('/custodia/service/<int:service_id>/<string:action>', type='json', auth='user', methods=['POST'], website=True)
    def custodia_action(self, service_id, action, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        if not service.exists():
            return {'status': 'error', 'message': 'Servicio no encontrado.'}

        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id != partner and not request.env.user.has_group('base.group_user'):
            return {'status': 'error', 'message': 'No tiene permisos para realizar esta acción.'}

        now = fields.Datetime.now()
        try:
            if action == 'llegada':
                if service.hora_llegada:
                    return {'status': 'error', 'message': 'La llegada ya ha sido registrada anteriormente.'}
                service.write({'hora_llegada': now})
                service.message_post(
                    body=f"✅ <b>Llegada de Custodio:</b> Registrada el {fields.Datetime.to_string(now)}.",
                    subtype_xmlid='mail.mt_note'
                )
            elif action == 'iniciar':
                if service.state in ['en_ejecucion', 'finalizado']:
                    return {'status': 'error', 'message': 'El servicio ya se encuentra en ejecución o ha finalizado.'}
                service.write({'hora_inicio_real': now, 'state': 'en_ejecucion'})
                service.message_post(
                    body=f"🚀 <b>Servicio Iniciado:</b> Ejecución comenzada el {fields.Datetime.to_string(now)}.",
                    subtype_xmlid='mail.mt_note'
                )
            else:
                return {'status': 'error', 'message': 'Acción no reconocida.'}

            return {'status': 'success', 'message': 'Registro actualizado correctamente'}
        except Exception as err:
            return {'status': 'error', 'message': str(err)}
