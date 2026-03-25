from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    registration_number = fields.Char(string="ID Empleado", copy=False, tracking=True)
    # Aseguramos que el campo del Excel sea reconocido por el modelo si no lo estaba
    contract_date_start = fields.Date(string="Fecha de Contrato (Importada)")

    def action_generate_numbers_by_seniority(self):
        # 1. Buscamos a todos los empleados
        employees = self.search([])
        
        if not employees:
            raise UserError("No hay empleados en el sistema.")

        # 2. Reiniciamos la secuencia a 1 para corregir los números mal asignados
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.employee.number')], limit=1)
        if sequence:
            sequence.write({'number_next_actual': 1})

        # 3. Ordenamos por tu campo específico del Excel
        # Si el campo está vacío en algún empleado, usamos la fecha de creación como plan C
        sorted_employees = sorted(
            employees, 
            key=lambda e: e.contract_date_start if e.contract_date_start else e.create_date
        )

        # 4. Asignación masiva (Sobreescribe los EMP00024, EMP00025, etc.)
        for emp in sorted_employees:
            new_seq = self.env['ir.sequence'].next_by_code('hr.employee.number')
            numeric_pin = ''.join(filter(str.isdigit, new_seq))
            
            emp.write({
                'registration_number': new_seq,
                'pin': numeric_pin
            })
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': '¡Éxito! Numeración corregida por fecha de contrato real.',
                'type': 'rainbow_man',
            }
        }
