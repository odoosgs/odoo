from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    # Kit Vehicular / Equipamiento de Seguridad
    kit_asset_id = fields.Char(string="ID Activo Kit", help="Ejemplo: AGI-SGS-001")
    gps_vehicular = fields.Char(string="GPS Vehicular", help="Ejemplo: VHG-SGS-001")
    gps_vehicular_imei = fields.Char(string="IMEI GPS Vehicular")
    
    dashcam_vehicular = fields.Char(string="Dash Cam Vehicular", help="Ejemplo: CAM-SGS-001")
    dashcam_imei = fields.Char(string="IMEI Dash Cam")
    
    gps_portatil = fields.Char(string="GPS Portátil", help="Ejemplo: GPS-SGS-001")
    gps_portatil_serial = fields.Char(string="No. Serie GPS Portátil")
    gps_portatil_sim = fields.Char(string="SIM (Telcel)")
    gps_portatil_imei = fields.Char(string="IMEI GPS Portátil")
    
    candado_digital = fields.Char(string="Candado Digital", help="Ejemplo: CDI-SGS-001")
    candado_mecanico = fields.Char(string="Candado Mecánico", help="Ejemplo: CME-SGS-001")
    radio_portatil = fields.Char(string="Radio Portátil", help="Ejemplo: RAD-SGS-001")
    
    kit_observaciones = fields.Text(string="Observaciones del Kit")
