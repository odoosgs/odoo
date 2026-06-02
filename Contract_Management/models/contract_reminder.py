from odoo import api, fields, models
from datetime import date, timedelta

class ContractReminder(models.Model):
    _name = 'contract.reminder'
    _description = 'Contract Reminder'
    _order = 'end_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    
    name = fields.Char(string='Name', compute='_compute_name', store=True, tracking=True)
    document_id = fields.Many2one('documents.document', string='Document', ondelete='set null', index=True, tracking=True)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    reminder1_days = fields.Integer(string='Days Ago Reminder 1', tracking=True)
    reminder2_days = fields.Integer(string='Days Ago Reminder 2', tracking=True)

    # Email configuration
    email_to = fields.Char(string='To', help='Comma-separated recipient addresses')
    email_cc = fields.Char(string='CC', help='Comma-separated CC addresses')

    user_id = fields.Many2one('res.users', string="Assigned To", default=lambda self: self.env.user)

    # De-duplication markers to avoid re-sending within the same day when cron runs frequently
    sent_end_on = fields.Date(string='End Notice Sent On', tracking=True)
    sent_reminder1_on = fields.Date(string='Reminder 1 Sent On', tracking=True)
    sent_reminder2_on = fields.Date(string='Reminder 2 Sent On', tracking=True)

    @api.depends('document_id', 'end_date')
    def _compute_name(self):
        for rec in self:
            base = rec.document_id.display_name if rec.document_id else 'Reminder'
            if rec.end_date:
                rec.name = f"{base} - {rec.end_date}"
            else:
                rec.name = base

    # Utility: split To recipients into internal users and external emails
    def _split_internal_external(self):
        self.ensure_one()
        raw = (self.email_to or '')
        emails = [e.strip() for e in raw.replace(';', ',').split(',') if e and e.strip()]
        if not emails:
            return [], []
        # Match res.users by login (case-insensitive)
        users = self.env['res.users'].sudo().search([('login', 'in', [e.lower() for e in emails]), ('active', '=', True)])
        internal_logins = set(u.login.lower() for u in users)
        internal_users = users
        external_emails = [e for e in emails if e.lower() not in internal_logins]
        return internal_users, external_emails

    # Create activities for internal recipients on the related document (no emails)
    def _create_internal_activities(self, summary, note, deadline):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for rec in self:
            internal_users, _ = rec._split_internal_external()
            if not internal_users:
                continue
            doc = rec.document_id
            if not doc:
                continue
            res_model_id = self.env['ir.model']._get_id('documents.document')
            for user in internal_users:
                # Avoid duplicate activities for same day/user/summary
                existing = self.env['mail.activity'].sudo().search_count([
                    ('res_model_id', '=', res_model_id),
                    ('res_id', '=', doc.id),
                    ('user_id', '=', user.id),
                    ('summary', '=', summary),
                    ('date_deadline', '=', deadline),
                    ('activity_type_id', '=', activity_type.id),
                ])
                if existing:
                    continue
                self.env['mail.activity'].with_context(mail_notify_noemail=True).sudo().create({
                    'activity_type_id': activity_type.id,
                    'res_model_id': res_model_id,
                    'res_id': doc.id,
                    'user_id': user.id,
                    'summary': summary,
                    'note': note,
                    'date_deadline': deadline,
                })

    # Cron method
    @api.model
    def _cron_check_reminders(self):
        # Use context-aware today for proper tz handling
        today = fields.Date.context_today(self)
        reminders = self.sudo().search([])
        for rec in reminders:
            if not rec.end_date:
                continue

            reminder1_date = rec.end_date - timedelta(days=rec.reminder1_days or 0)
            reminder2_date = rec.end_date - timedelta(days=rec.reminder2_days or 0)

            # End date (send once per day)
            if rec.end_date == today and rec.sent_end_on != today:
                # Build context strings
                summary = "Contract End Today"
                note = f"Contract: {rec.name}"
                # Internal -> activities, External -> email
                internal_users, external_emails = rec._split_internal_external()
                if internal_users:
                    rec._create_internal_activities(summary, note, rec.end_date)
                    # Bell notification to assignee remains via _send_notification
                rec._send_notification(summary)
                if external_emails:
                    rec._send_email_notification(kind='end', override_to=', '.join(external_emails))
                rec.sent_end_on = today

            # Reminder 1 (send once per day)
            if reminder1_date == today and rec.sent_reminder1_on != today:
                summary = f"Reminder {rec.reminder1_days} days before end date"
                note = f"Contract: {rec.name}"
                internal_users, external_emails = rec._split_internal_external()
                if internal_users:
                    rec._create_internal_activities(summary, note, rec.end_date)
                rec._send_notification(summary)
                if external_emails:
                    rec._send_email_notification(kind='reminder1', override_to=', '.join(external_emails))
                rec.sent_reminder1_on = today

            # Reminder 2 (send once per day)
            if reminder2_date == today and rec.sent_reminder2_on != today:
                summary = f"Reminder {rec.reminder2_days} days before end date"
                note = f"Contract: {rec.name}"
                internal_users, external_emails = rec._split_internal_external()
                if internal_users:
                    rec._create_internal_activities(summary, note, rec.end_date)
                rec._send_notification(summary)
                if external_emails:
                    rec._send_email_notification(kind='reminder2', override_to=', '.join(external_emails))
                rec.sent_reminder2_on = today

        return True

    def write(self, vals):
        # If scheduling changes, clear sent flags so new schedule can send again on its new dates
        schedule_fields = {'end_date', 'reminder1_days', 'reminder2_days'}
        if schedule_fields.intersection(vals.keys()):
            vals = dict(vals)  # copy to avoid mutating caller dict
            vals.setdefault('sent_end_on', False)
            vals.setdefault('sent_reminder1_on', False)
            vals.setdefault('sent_reminder2_on', False)
        return super(ContractReminder, self).write(vals)

    # Send chatter + top-right notification
    def _send_notification(self, message):
        """
        Post a chatter comment that triggers an in-app (bell) notification for the assignee,
        but suppresses email delivery. We do NOT create activities to avoid the
        "assigned to you" email.
        """
        for rec in self:
            # Target partner for bell notification (assignee or current user)
            partner_id = rec.user_id.partner_id.id if rec.user_id else self.env.user.partner_id.id
            if partner_id:
                # Ensure partner is follower (optional)
                try:
                    rec.message_subscribe(partner_ids=[partner_id])
                except Exception:
                    pass

            # Build clean, plain-text content (desktop notifications may show raw HTML)
            subject_txt = f"{rec.document_id.display_name or rec.name}"
            body_txt = f"{message} • Contract: {rec.name}"

            rec.with_context(
                mail_post_autofollow=False,
                mail_notify_noemail=True,   # suppress emails
            ).message_post(
                body=body_txt,
                subject=subject_txt,
                message_type='comment',
                subtype_xmlid="mail.mt_comment",  # comment -> inbox/bell
                partner_ids=[partner_id] if partner_id else [],
            )

        # Still avoid creating mail.activity to prevent assignment emails.

    def _send_email_notification(self, kind: str, override_to: str = None):
        """
        kind: 'reminder1' | 'reminder2' | 'end'
        Sends email to configured recipients with the document attached.
        Generates a professional subject and body based on the reminder context.
        """

        def _fmt(d):
            if not d:
                return ''
            # format as MM/DD/YYYY (human-friendly)
            return d.strftime('%m/%d/%Y')

        def _compose_subject(rec, kind):
            base = rec.document_id.display_name or rec.name or 'Contract'
            if kind == 'end':
                return f"Contract Expiry Notice – {base}"
            elif kind == 'reminder1':
                return f"Contract Reminder – {base}"
            elif kind == 'reminder2':
                return f"Second Reminder – {base}"
            return f"Contract Update – {base}"

        def _compose_body(rec, kind):
            # Compute context
            end = rec.end_date
            doc_name = rec.document_id.display_name or rec.name or 'your contract'
            company = (self.env.company.name or 'Our Company') if hasattr(self.env, 'company') else 'Our Company'
            # Lines per kind
            if kind == 'end':
                headline = "Your contract has reached its expiry date."
                details = f"The contract <b>{doc_name}</b> expired on <b>{_fmt(end)}</b>."
                cta = "If renewal is required, please reply to this email and our team will assist you promptly."
            elif kind == 'reminder1':
                reminder_date = (end - timedelta(days=rec.reminder1_days or 0)) if end else None
                remaining = rec.reminder1_days or 0
                headline = "Upcoming contract expiry reminder."
                details = (
                    f"The contract <b>{doc_name}</b> is scheduled to expire on <b>{_fmt(end)}</b>.<br/>"
                    f"This is a friendly reminder sent <b>{remaining}</b> day(s) in advance (on <b>{_fmt(reminder_date)}</b>)."
                )
                cta = "Kindly review the contract and let us know if you would like to renew or take further action."
            elif kind == 'reminder2':
                reminder_date = (end - timedelta(days=rec.reminder2_days or 0)) if end else None
                remaining = rec.reminder2_days or 0
                headline = "Final reminder: contract approaching expiry."
                details = (
                    f"The contract <b>{doc_name}</b> will expire on <b>{_fmt(end)}</b>.<br/>"
                    f"This message is sent <b>{remaining}</b> day(s) prior (on <b>{_fmt(reminder_date)}</b>)."
                )
                cta = "Please confirm whether you would like to proceed with renewal or closure."
            else:
                headline = "Contract status update."
                details = f"The contract <b>{doc_name}</b> has an upcoming deadline on <b>{_fmt(end)}</b>."
                cta = "Let us know if you need any assistance."

            # Optional To/CC echo (not exposing emails if empty)
            recipients_line = ""
            if rec.email_to:
                recipients_line = f"<p style=\"margin:8px 0 0; color:#6b7280; font-size:12px;\">This message was sent to: {rec.email_to}</p>"

            footer = (
                f"<p style=\"margin:16px 0 0; color:#6b7280; font-size:12px;\">"
                f"Regards,<br/>{company}</p>"
            )

            # Simple, clean HTML layout compatible with Odoo mail rendering
            body_html = f"""
                <div style="font-family:Segoe UI, Helvetica, Arial, sans-serif; line-height:1.6; color:#111827;">
                    <p style="margin:0 0 8px 0; font-size:14px;">Dear Recipient,</p>
                    <p style="margin:0 0 12px 0; font-size:14px;">{headline}</p>
                    <div style="margin:0 0 12px 0; font-size:14px;">{details}</div>
                    <p style="margin:0 0 12px 0; font-size:14px;">{cta}</p>
                    <p style="margin:8px 0 0; font-size:13px; color:#374151;">Document: <b>{doc_name}</b></p>
                    {recipients_line}
                    {footer}
                </div>
            """
            return body_html

        for rec in self.sudo():
            if not rec.email_to:
                continue  # no recipients configured

            subject = _compose_subject(rec, kind)
            body_html = _compose_body(rec, kind)

            # Prepare attachment (original document)
            attachment_ids = []
            if rec.document_id and rec.document_id.attachment_id:
                attachment_ids = [(4, rec.document_id.attachment_id.id)]

            mail_vals = {
                'subject': subject,
                'body_html': body_html,
                'email_to': (override_to if override_to is not None else (rec.email_to or '')),
                'email_cc': rec.email_cc or '',
                'auto_delete': True,
                'attachment_ids': attachment_ids,
            }
            mail = self.env['mail.mail'].create(mail_vals)
            try:
                mail.send()
            except Exception:
                # If immediate send fails, leave it to the mail queue cron
                pass
