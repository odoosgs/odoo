{
    "name": "CFDI MX – Fix Company Name (Odoo 19)",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localization",
    "summary": "Corrige el nombre fiscal de la empresa en el PDF CFDI México",
    "description": """
En Odoo 19, el PDF CFDI puede mostrar el nombre del dueño (Persona Física)
en lugar del nombre fiscal real de la empresa.

Este módulo fuerza el uso de company.partner_id.name en el reporte CFDI.
""",
    "author": "Custom / SGS",
    "license": "LGPL-3",
    "depends": [
        "account",
        "l10n_mx_edi",
    ],
    "data": [
        "views/report_invoice_document.xml",
    ],
    "installable": True,
    "application": False,
}
