from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    registration_number = fields.Char(string="ID Empleado", copy=False, tracking=True)
    # Definimos el campo para que Odoo lo reconozca
    contract_date_start = fields.Date(string="Fecha de Contrato (Importada)")

    def action_generate_numbers_by_seniority(self):
        employees = self.search([])
        
        if not employees:
            raise UserError("No hay empleados en el sistema.")

        # Reiniciar secuencia a 1
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.employee.number')], limit=1)
        if sequence:
            sequence.write({'number_next_actual': 1})

        # Función de ordenamiento con conversión de tipos para evitar el TypeError
        def get_cleaning_date(emp):
            # Si tiene fecha importada, esa es la prioridad
            if emp.contract_date_start:
                return fields.Date.to_date(emp.contract_date_start)
            # Si no, usamos la fecha de creación convertida a solo fecha (Date)
            return fields.Datetime.to_date(emp.create_date)

        # Ahora sí, la comparación es entre Date y Date
        sorted_employees = sorted(employees, key=get_cleaning_date)

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
                'message': '¡Numeración corregida por antigüedad real!',
                'type': 'rainbow_man',
            }
        }
