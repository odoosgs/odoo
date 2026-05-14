from odoo import http
from odoo.http import request
import base64

class SGSPortalViaticos(http.Controller):

    @http.route(['/my/viaticos'], type='http', auth="user", website=True)
    def portal_my_viaticos(self, **kw):
        employee = request.env.user.employee_id
        if not employee:
            return request.render("sgs_viaticos.sgs_no_employee_error")

        # Cálculo de Saldo (Entregas - Gastos Aprobados)
        entregas = sum(request.env['sgs.viatico.entrega'].search([
            ('employee_id', '=', employee.id), ('state', '=', 'done')]).mapped('amount'))
        gastos = sum(request.env['sgs.viatico.gasto'].search([
            ('employee_id', '=', employee.id), ('state', '!=', 'refused')]).mapped('amount'))
        
        saldo = entregas - gastos
        gastos_list = request.env['sgs.viatico.gasto'].search([('employee_id', '=', employee.id)], order="date desc")

        return request.render("sgs_viaticos.sgs_portal_layout", {
            'employee': employee,
            'saldo_actual': saldo,
            'gastos': gastos_list,
            'page_name': 'viaticos_sgs',
        })

    @http.route(['/my/viaticos/save'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def save_gasto(self, **post):
        employee = request.env.user.employee_id
        vals = {
            'name': post.get('name'),
            'amount': float(post.get('amount') or 0.0),
            'category': post.get('category'),
            'employee_id': employee.id,
            'date': post.get('date'),
        }
        if post.get('receipt_image'):
            vals['receipt_image'] = base64.b64encode(post.get('receipt_image').read())
            
        request.env['sgs.viatico.gasto'].sudo().create(vals)
        return request.redirect('/my/viaticos')
