<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <record id="view_sgs_import_batch_tree" model="ir.ui.view">
        <field name="name">sgs.perdiem.import.batch.tree</field>
        <field name="model">sgs.perdiem.import.batch</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="deposit_date"/>
                <field name="total_lines"/>
                <field name="total_amount"/>
                <field name="state"/>
            </list>
        </field>
    </record>

    <record id="view_sgs_import_batch_form" model="ir.ui.view">
        <field name="name">sgs.perdiem.import.batch.form</field>
        <field name="model">sgs.perdiem.import.batch</field>
        <field name="arch" type="xml">
            <form>

                <header>

                    <button
                        name="action_apply_deposits"
                        type="object"
                        string="Crear Depósitos"
                        class="btn-primary"
                        invisible="state == 'done'"/>

                    <field
                        name="state"
                        widget="statusbar"/>

                </header>

                <sheet>

                    <group>

                        <field name="name"/>

                        <field name="deposit_date"/>

                        <field
                            name="source_file"
                            filename="source_filename"/>

                        <field
                            name="source_filename"
                            invisible="1"/>

                    </group>

                    <group>

                        <field name="total_lines" readonly="1"/>

                        <field name="total_amount" readonly="1"/>

                    </group>

                    <notebook>

                        <page string="Detalle">

                            <field name="line_ids">

                                <list editable="bottom">

                                    <field name="rfc"/>

                                    <field name="employee_id"/>

                                    <field name="registration_number"/>

                                    <field name="amount"/>

                                    <field name="status"/>

                                    <field name="notes"/>

                                </list>

                            </field>

                        </page>

                    </notebook>

                </sheet>

                <chatter/>

            </form>
        </field>
    </record>

    <record id="action_sgs_import_batch"
            model="ir.actions.act_window">

        <field name="name">
            Dispersión Banorte
        </field>

        <field name="res_model">
            sgs.perdiem.import.batch
        </field>

        <field name="view_mode">
            list,form
        </field>

    </record>

</odoo>
