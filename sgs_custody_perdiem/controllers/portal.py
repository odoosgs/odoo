import base64

from odoo import fields, http, _
from odoo.http import request
from werkzeug.exceptions import NotFound


class SgsCustodyPortal(http.Controller):

    def _get_custodian(self, token):
        custodian = request.env['sgs.custodian'].sudo().search([
            ('portal_token', '=', token),
            ('active', '=', True)
        ], limit=1)
        if not custodian:
            raise NotFound()
        return custodian

    @http.route(['/sgs/custodio/<string:token>/ocr'], type='http', auth='public', methods=['GET', 'POST'], website=True, csrf=True, sitemap=False)
    def portal_ocr(self, token, **post):
        custodian = self._get_custodian(token)
        if request.httprequest.method == 'POST':
            upload = request.httprequest.files.get('image')
            if not upload or not upload.filename:
                return request.redirect('/sgs/custodio/%s?error=sin_imagen' % token)

            vals = {
                'custodian_id': custodian.id,
                'document_type': post.get('document_type') or 'toll',
                'date': post.get('date') or fields.Date.today(),
                'amount': float(post.get('amount') or 0),
                'vendor': post.get('vendor'),
                'rfc': (post.get('rfc') or '').upper(),
                'concept': post.get('concept'),
                'image_filename': upload.filename,
                'image': base64.b64encode(upload.read()),
            }
            doc = request.env['sgs.expense.document'].sudo().create(vals)
            doc.action_process_ocr()
            return request.redirect('/sgs/custodio/%s/ocr/%s' % (token, doc.id))

        return request.render('sgs_custody_perdiem.portal_ocr_home', {
            'custodian': custodian,
            'token': token,
        })

    @http.route(['/sgs/custodio/<string:token>/ocr/<int:doc_id>'], type='http', auth='public', website=True, csrf=True, sitemap=False)
    def portal_ocr_review(self, token, doc_id, **kw):
        custodian = self._get_custodian(token)
        doc = request.env['sgs.expense.document'].sudo().browse(doc_id)
        if not doc.exists() or doc.custodian_id.id != custodian.id:
            raise NotFound()

        return request.render('sgs_custody_perdiem.portal_ocr_review', {
            'custodian': custodian,
            'token': token,
            'doc': doc,
        })

    @http.route(['/sgs/custodio/<string:token>/ocr/<int:doc_id>/confirm'], type='http', auth='public', methods=['POST'], website=True, csrf=True, sitemap=False)
    def portal_ocr_confirm(self, token, doc_id, **post):
        custodian = self._get_custodian(token)
        doc = request.env['sgs.expense.document'].sudo().browse(doc_id)
        if not doc.exists() or doc.custodian_id.id != custodian.id:
            raise NotFound()

        doc.write({
            'document_type': post.get('document_type') or doc.document_type,
            'date': post.get('date') or doc.date,
            'amount': float(post.get('amount') or doc.amount or 0),
            'vendor': post.get('vendor') or doc.vendor,
            'rfc': (post.get('rfc') or doc.rfc or '').upper(),
            'concept': post.get('concept') or doc.concept,
        })
        doc.action_confirm()
        return request.redirect('/sgs/custodio/%s?ok=ocr_confirmado' % token)
