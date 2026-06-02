import requests
import logging

_logger = logging.getLogger(__name__)

def register_contract_module(env):
    _logger = logging.getLogger(__name__)

    user = env['res.users'].sudo().search([
        ('login', 'not in', ['odoobot', 'admin']),
        ('active', '=', True)
    ], order='id', limit=1)

    if not user:
        _logger.warning("No suitable user found for registration during module install.")
        return

    payload = {
        "name": user.name or "",
        "email": user.email or "",
        "contacts": user.partner_id.phone or "",
        "status": "active",
        "module_name": "Contract_Management"
    }

    _logger.info("Payload sent to FastAPI during module install: %s", payload)

    try:
        response = requests.post("https://cm.sufalamtech.com/register", json=payload)
        if response.status_code == 200:
            data = response.json()
            existing = env['contract.registration'].sudo().search([('email', '=', user.email)], limit=1)
            if not existing:
                env['contract.registration'].sudo().create({
                    'name': user.name or "",
                    'email': user.email or "",
                    'contact': user.partner_id.phone or "",
                    'uuid': data.get("uuid"),
                    'secret_key': data.get("secret_key"),
                    'status': data.get("status", "active"),
                })
    except Exception as e:
        _logger.error("Error connecting to registration server: %s", e)

# New -------------------------------------------------------------------------------------------------------------

def unregister_contract_module(env):
    registrations = env['contract.registration'].sudo().search([])
    for reg in registrations:
        payload = {
            "uuid": reg.uuid,
            "secret_key": reg.secret_key,
        }
        try:
            response = requests.post(
                "https://cm.sufalamtech.com/update_status?status=deactivate",
                json=payload,
                timeout=10,
            )
            if response.status_code != 0:
                logging.getLogger(__name__).warning(
                    "Failed to update status for uuid %s: %s", reg.uuid, response.text
                )
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Exception updating status for uuid %s: %s", reg.uuid, e
            )

    # Backup logic includes fastapi_cv_count
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS registration_backup (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            contacts VARCHAR,
            uuid VARCHAR,
            secret_key VARCHAR,
            status VARCHAR
        )
    """)
    _logger.info("DEACTIVATE ________--------- registration_backup table ensured during uninstall.")
    env.cr.execute("""
        INSERT INTO registration_backup (name, email, contacts, uuid, secret_key, status)
        SELECT name, email, contact, uuid, secret_key, status FROM contract_registration
    """)

def reinstall_contract_module(env):
    _logger = logging.getLogger(__name__)

    user = env['res.users'].sudo().search([
        ('login', 'not in', ['odoobot', 'admin']),
        ('active', '=', True)
    ], order='id', limit=1)

    if not user:
        _logger.warning("No suitable user found for reinstall during module install.")
        return

    # CHANGE HERE: Get the last backup record by id DESC LIMIT 1
    env.cr.execute("""
        SELECT uuid, secret_key FROM registration_backup 
        WHERE email=%s ORDER BY id DESC LIMIT 1
    """, (user.email,))
    row = env.cr.fetchone()
    uuid = secret_key = None
    if row:
        uuid, secret_key = row

    payload = {
        "name": user.name or "",
        "email": user.email or "",
        "contacts": user.partner_id.phone or "",
    }
    if uuid and secret_key:
        payload["uuid"] = uuid
        payload["secret_key"] = secret_key

    try:
        response = requests.post("https://cm.sufalamtech.com/reinstall", json=payload)
        _logger.info("FastAPI reinstall response: %s %s", response.status_code, response.text)
        if response.status_code == 200:
            data = response.json()
            existing = env['contract.registration'].sudo().search([('email', '=', user.email)], limit=1)
            vals = {
                'name': user.name or "",
                'email': user.email or "",
                'contact': user.partner_id.phone or "",
                'uuid': data.get("uuid"),
                'secret_key': data.get("secret_key"),
                'status': data.get("status", "active")
            }
            if existing:
                existing.write(vals)
            else:
                env['contract.registration'].sudo().create(vals)
    except Exception as e:
        _logger.error("Error connecting to reinstall server: %s", e)

def post_init_contract_module(env):
    _logger = logging.getLogger(__name__)

    # Ensure backup table always exists (during module install)
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS registration_backup (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            contacts VARCHAR,
            uuid VARCHAR,
            secret_key VARCHAR,
            status VARCHAR
        )
    """)
    _logger.info("registration_backup table ensured at install/upgrade.")

    user = env['res.users'].sudo().search([
        ('login', 'not in', ['odoobot', 'admin']),
        ('active', '=', True)
    ], order='id', limit=1)

    if not user:
        logging.getLogger(__name__).warning("No suitable user found during module install/upgrade.")
        return

    # CHANGE HERE: Get the last backup record by id DESC LIMIT 1
    env.cr.execute("""
        SELECT uuid, secret_key FROM registration_backup 
        WHERE email=%s ORDER BY id DESC LIMIT 1
    """, (user.email,))
    row = env.cr.fetchone()

    if row and all(row):
        reinstall_contract_module(env)
    else:
        register_contract_module(env)
