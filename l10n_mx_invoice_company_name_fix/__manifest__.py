{
    "name": "CFDI MX – Fix Company Name (Odoo 19)",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localization",
    "summary": "Corrige el nombre fiscal del emisor en PDF CFDI México",
    "author": "Custom / SGS",
    "license": "LGPL-3",
    "depends": [
        "web",
        "account",
        "l10n_mx_edi",
    ],
    "data": [
        "views/report_external_layout.xml",
    ],
    "installable": True,
}
