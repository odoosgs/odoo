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
    # FILTRADO DE NODOS (CASCADA) - TYPE HTTP PARA FETCH
    # =========================================================
    @http.route('/get_nodos_by_maestra/<int:maestra_id>', type='http', auth='user', website=True, csrf=False)
    def get_nodos_by_maestra(self, maestra_id, **kwargs):
        rutas = request.env['custodia.ruta'].sudo().search([
            ('ruta_maestra_id', '=', maestra_id)
        ])
        
        origenes = []
        destinos = []
        seen_orig = set()
        seen_dest = set()

        for r in rutas:
            if r.nodo_origen_id and r.nodo_origen_id.id not in seen_orig:
                origenes.append({'id': r.nodo_origen_id.id, 'name': r.nodo_origen_id.name})
                seen_orig.add(r.nodo_origen_id.id)
            if r.nodo_destino_id and r.nodo_destino_id.id not in seen_dest:
                destinos.append({'id': r.nodo_destino_id.id, 'name': r.nodo_destino_id.name})
                seen_dest.add(r.nodo_destino_id.id)

        data = {
            'origenes': sorted(origenes, key=lambda x: x['name']),
            'destinos': sorted(destinos, key=lambda x: x['name'])
        }
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )

    # =========================================================
    # SUBMIT NUEVA SOLICITUD (MODO ALERTA / PROGRAMACIÓN)
    # =========================================================
    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        try:
            # 1. Validación de fecha (Campo mandatorio)
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(post['start_datetime'], "%Y-%m-%dT%H:%M")
            else:
                raise Exception("La fecha de inicio es obligatoria para programar el servicio.")

            # 2. Función interna de limpieza y verificación de IDs
            def clean_id(field_name, model_name):
                val = post.get(field_name)
                if not val:
                    return False
                try:
                    val_id = int(val)
                    if val_id <= 0:
                        return False
                    # Verificamos que el ID exista realmente en la tabla correspondiente
                    exists = request.env[model_name].sudo().browse(val_id).exists()
                    return val_id if exists else False
                except:
                    return False

            # Limpieza de los campos relacionales enviando el modelo correcto
            maestra_id = clean_id('ruta_maestra_id', 'custodia.ruta.maestra')
            origen_id = clean_id('nodo_origen_id', 'custodia.ruta.nodo')
            destino_id = clean_id('nodo_destino_id', 'custodia.ruta.nodo')
            carrier_id = clean_id('carrier_id', 'custodia.carrier')
            contact_id = clean_id('contact_id', 'res.partner')

            # 3. Buscar variante de ruta (Opcional para alertas)
            # --- BUSQUEDA DE LA VARIANTE ESPECIFICA PARA EL MAPA ---
            ruta_id = False
            if maestra_id and origen_id and destino_id:
                # Buscamos solo por la combinación geográfica
                ruta_variante = request.env['custodia.ruta'].sudo().search([
                    ('ruta_maestra_id', '=', maestra_id),
                    ('nodo_origen_id', '=', origen_id),
                    ('nodo_destino_id', '=', destino_id)
                ], limit=1)
                
                if ruta_variante:
                    ruta_id = ruta_variante.id
                else:
                    # Opcional: log para debug en Odoo.sh
                    _logger.info("No se encontro variante para M:%s O:%s D:%s", maestra_id, origen_id, destino_id)

            # --- PREPARAR VALORES (Se incluyen TODOS los campos del formulario) ---
            vals = {
                'partner_id': partner.id,
                'contact_id': contact_id,
                'start_datetime': start_dt,
                'state': 'solicitado',
                'ruta_maestra_id': maestra_id,
                'nodo_origen_id': origen_id,
                'nodo_destino_id': destino_id,
                'ruta_id': ruta_id,  # Este es el campo "llave" para el mapa
                'carrier_id': carrier_id,
                'nivel_seguridad': post.get('nivel_seguridad'),
                'load_id': post.get('load_id') or "PENDIENTE",
                'tipo_unidad': post.get('tipo_unidad'),
                'placas': post.get('placas'),
                'transporte': post.get('transporte'),
                'operador1_nombre': post.get('operador1_nombre'),
                'tel_monitoreo_1': post.get('tel_monitoreo_1'),
            }
            
            service = request.env['custodia.service'].sudo().create(vals)
            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        except Exception as e:
            # En caso de error, no consultamos la BD para evitar problemas de transacción
            return request.render('custodia_logistica.portal_service_form', {
                'error': f"Error al procesar la solicitud: {str(e)}",
                'cliente': partner,
                # Cargamos listas mínimas solo si la transacción lo permite
                'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            })

    # =========================================================
    # ACCIONES DEL CUSTODIO E INCIDENCIAS (Mantener tus funciones)
    # =========================================================
    @http.route('/custodia/service/<int:service_id>/incidencia', type='json', auth='user', methods=['POST'], website=True)
    def custodia_reportar_incidencia(self, service_id, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        mensaje = kwargs.get('mensaje')
        if not service.exists() or not mensaje:
            return {'status': 'error', 'message': 'Datos incompletos'}
        service.message_post(body=f"⚠️ <b>INCIDENCIA REPORTADA:</b><br/>{mensaje}")
        return {'status': 'success'}

    @http.route(['/mis-servicios/<int:service_id>/tracking'], type='http', auth='public', website=True, csrf=False)
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except:
            return request.make_response(json.dumps({'error': 'Acceso denegado'}), headers=[('Content-Type', 'application/json')])
        
        lat = service.current_lat or service.ruta_id.origin_latitude
        lng = service.current_lng or service.ruta_id.origin_longitude
        data = {'lat': lat, 'lng': lng, 'last_update': str(service.last_update), 'state': service.state}
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/custodia/service/<int:service_id>/<string:action>', type='json', auth='user', methods=['POST'], website=True)
    def custodia_action(self, service_id, action, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        if not service.exists():
            return {'status': 'error', 'message': 'Servicio no encontrado.'}
        
        now = fields.Datetime.now()
        try:
            if action == 'llegada':
                service.write({'hora_llegada': now})
                service.message_post(body=f"✅ <b>Llegada de Custodio</b>")
            elif action == 'iniciar':
                service.write({'hora_inicio_real': now, 'state': 'en_ejecucion'})
                service.message_post(body=f"🚀 <b>Servicio Iniciado</b>")
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
        })
