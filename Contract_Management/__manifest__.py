{
    "name": "Contract Management",
    "version": "1.0",
    "author": "Sufalam Technologies",
    "depends": ["documents", "web"],
    "category": "Documents",
    "summary": "Show AI popup when user uploads a document",
    "assets": {
        "web.assets_backend": [
            "Contract_Management/static/src/js/documents_ai_popup_beautiful.js",
            "Contract_Management/static/src/xml/documents_upload_contract.xml",
        ],  
    },
    "license": "LGPL-3",
    'website': 'https://www.sufalamtech.com',
    'images': [
         'static/description/banner.jpg',
    ],

    "data": [
        "data/contract_tag.xml",
        "security/ir.model.access.csv",
        "views/documents_ai_popup.xml",
        "views/registration_views.xml",
        'views/contract_management_menu.xml',
        'views/documents_contract_menu.xml',
        'data/contract_reminder_cron.xml',
    ],

    'post_init_hook': 'post_init_contract_module',
    'uninstall_hook': 'unregister_contract_module',
    # 'reinstall_hook': 'reinstall_contract_module',
    "installable": True,
    "application": False,
}
