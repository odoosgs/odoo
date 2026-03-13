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
        # Buscamos la ruta de forma segura (sudo para que el portal pueda leerla)
        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)
        if not ruta.exists():
            return []
        # Llamamos al método que definimos en el modelo
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
    @http.route('/custodia/service/<int:service_id>/incidencia', type='json', auth='user', methods=['POST'], website=True)
    def custodia_reportar_incidencia(self, service_id, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        mensaje = kwargs.get('mensaje')
        
        if not service.exists() or not mensaje:
            return {'status': 'error', 'message': 'Datos incompletos'}

        # Publicar en el Chatter con un formato de alerta
        service.message_post(
            body=f"⚠️ <b>INCIDENCIA REPORTADA:</b><br/>{mensaje}",
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        return {'status': 'success'}
    
    
    # =========================================================
    # ENDPOINT JSON TRACKING (Sincronizado con route_map.js)
    # =========================================================
    @http.route(['/mis-servicios/<int:service_id>/tracking'], type='http', auth='public', website=True, csrf=False)
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):
        try:
            service = self._document_check_access('custodia.service', service_id, access_token)
        except Exception:
            return request.make_response(json.dumps({'error': 'Acceso denegado'}), headers=[('Content-Type', 'application/json')])
    
        # Si no hay ubicación actual, enviamos la de origen de la ruta para que el mapa no esté en blanco
        lat = service.current_lat or service.ruta_id.origin_latitude
        lng = service.current_lng or service.ruta_id.origin_longitude
    
        data = {
            'lat': lat,
            'lng': lng,
            'last_update': str(service.last_update) if service.last_update else "Sin reportes",
            'state': service.state,
        }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    # =========================================================
    # FILTRADO DE NODOS (CASCADA)
    # =========================================================
    @http.route('/get_nodos_by_maestra/<int:maestra_id>', type='http', auth='user', website=True, csrf=False)
    def get_nodos_by_maestra(self, maestra_id, **kwargs):
        # Buscamos las variantes de ruta para esa maestra
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

        # Respuesta JSON manual para que sea compatible con fetch estándar
        data = {
            'origenes': sorted(origenes, key=lambda x: x['name']),
            'destinos': sorted(destinos, key=lambda x: x['name'])
        }
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
    # =========================================================
    # FORMULARIO NUEVA SOLICITUD
    # =========================================================
    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]), # Carga rutas maestras
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
        })

    # =========================================================
    # =========================================================
    # SUBMIT NUEVA SOLICITUD (Corregido para Rutas Relacionales)
    # =========================================================
    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        try:
            # 1. Procesar Fecha
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(post['start_datetime'], "%Y-%m-%dT%H:%M")

            # 2. BUSCAR LA VARIANTE DE RUTA (CRÍTICO)
            # Buscamos la 'custodia.ruta' que coincida con Maestra + Origen + Destino
            maestra_id = int(post.get('ruta_maestra_id', 0))
            origen_id = int(post.get('nodo_origen_id', 0))
            destino_id = int(post.get('nodo_destino_id', 0))

            ruta_variante = request.env['custodia.ruta'].sudo().search([
                ('ruta_maestra_id', '=', maestra_id),
                ('nodo_origen_id', '=', origen_id),
                ('nodo_destino_id', '=', destino_id)
            ], limit=1)

            if not ruta_variante:
                raise Exception("La combinación de ruta y puntos seleccionada no es válida.")

            # 3. Preparar Valores para el registro
            vals = {
                'partner_id': partner.id,
                'contact_id': int(post.get('contact_id')) if post.get('contact_id') else False,
                'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
                'ruta_id': ruta_variante.id, # Aquí se asigna el ID que faltaba
                'start_datetime': start_dt,
                'nivel_seguridad': post.get('nivel_seguridad'),
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
            # Si hay error, recargamos el formulario con los datos necesarios
            return request.render('custodia_logistica.portal_service_form', {
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
                'cliente': partner,
                'error': str(e),
            })
            
    # =========================================================
    # ACCIONES DEL CUSTODIO
    # =========================================================
    def custodia_action(self, service_id, action, **kwargs):
        service = request.env['custodia.service'].sudo().browse(service_id)
        if not service.exists():
            return {'status': 'error', 'message': 'Servicio no encontrado'}
     
        now = fields.Datetime.now()
        
        if action == 'llegada':
            service.write({
                'hora_llegada': now,
                'state': 'aprobado' # O el estado que desees para confirmar presencia
            })
            service.message_post(body="El custodio ha marcado su llegada al punto de origen.")
            
        elif action == 'iniciar':
            service.write({
                'hora_inicio_real': now,
                'state': 'en_ejecucion'
            })
            service.message_post(body="Servicio iniciado formalmente.")
     
        return {'status': 'success'}

    # =========================================================
    # ACCIONES DEL CUSTODIO (Versión Optimizada)
    # =========================================================
    @http.route('/custodia/service/<int:service_id>/<string:action>', type='json', auth='user', methods=['POST'], website=True)
    def custodia_action(self, service_id, action, **kwargs):
        # 1. Verificación de existencia y seguridad
        service = request.env['custodia.service'].sudo().browse(service_id)
        if not service.exists():
            return {'status': 'error', 'message': 'Servicio no encontrado.'}

        # 2. Validación de permisos (Opcional pero recomendado)
        # Asegura que solo el cliente dueño o un custodio asignado pueda disparar la acción
        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id != partner and not request.env.user.has_group('base.group_user'):
            return {'status': 'error', 'message': 'No tiene permisos para realizar esta acción.'}

        now = fields.Datetime.now()
        
        try:
            if action == 'llegada':
                # Validación: Solo permitir marcar llegada si no se ha marcado antes
                if service.hora_llegada:
                    return {'status': 'error', 'message': 'La llegada ya ha sido registrada anteriormente.'}
                
                service.write({
                    'hora_llegada': now,
                    # 'state': 'asignado' # Sugerencia: mantener asignado hasta que inicie realmente
                })
                # Trazabilidad en el Chatter
                service.message_post(
                    body=f"✅ <b>Llegada de Custodio:</b> Registrada el {fields.Datetime.to_string(now)}.",
                    subtype_xmlid="mail.mt_note"
                )
                
            elif action == 'iniciar':
                # Validación: No iniciar si ya está en ejecución o finalizado
                if service.state in ['en_ejecucion', 'finalizado']:
                    return {'status': 'error', 'message': 'El servicio ya se encuentra en ejecución o ha finalizado.'}
                
                service.write({
                    'hora_inicio_real': now,
                    'state': 'en_ejecucion'
                })
                service.message_post(
                    body=f"🚀 <b>Servicio Iniciado:</b> Ejecución comenzada el {fields.Datetime.to_string(now)}.",
                    subtype_xmlid="mail.mt_note"
                )
            
            else:
                return {'status': 'error', 'message': 'Acción no reconocida.'}

            return {
                'status': 'success',
                'message': 'Registro actualizado correctamente'
            }

        except Exception as e:
            return {'status': 'error', 'message': str(e)}
