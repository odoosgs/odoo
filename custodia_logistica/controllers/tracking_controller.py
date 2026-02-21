# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class CustodiaTrackingController(http.Controller):

    @http.route(
        '/api/custodia/update_location',
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def update_location(self, **kwargs):
        """
        Endpoint para actualizar ubicación en tiempo real.
        Espera JSON:
        {
            "service_id": 1,
            "lat": 19.4326,
            "lng": -99.1332
        }
        """

        try:
            service_id = kwargs.get('service_id')
            lat = kwargs.get('lat')
            lng = kwargs.get('lng')

            if not service_id or lat is None or lng is None:
                return {
                    "success": False,
                    "error": "Faltan parámetros obligatorios"
                }

            service = request.env['custodia.service'].sudo().browse(service_id)

            if not service.exists():
                return {
                    "success": False,
                    "error": "Servicio no encontrado"
                }

            service.update_live_location(lat, lng)

            return {
                "success": True,
                "message": "Ubicación actualizada correctamente"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
