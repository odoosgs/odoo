# -*- coding: utf-8 -*-
def migrate(cr, version):
    # Este script crea las columnas en SQL antes de que Odoo intente cargar los modelos
    columns = [
        ('initial_fund', 'numeric DEFAULT 0.0'),
        ('portal_token', 'varchar'),
        ('employee_token', 'varchar'), # Lo añadimos porque aparece en tu log de error
    ]
    for col, col_type in columns:
        cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='hr_employee' AND column_name=%s", (col,))
        if not cr.fetchone():
            cr.execute(f"ALTER TABLE hr_employee ADD COLUMN {col} {col_type}")
