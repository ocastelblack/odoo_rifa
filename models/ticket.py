from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class RifaTicket(models.Model):
    _name = 'rifa.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Boleta de Rifa'
    _order = 'numero asc'

    rifa_id = fields.Many2one('rifa.rifa', required=True, ondelete='cascade')

    numero = fields.Integer(string='Número', required=True)

    partner_id = fields.Many2one('res.partner', string='Cliente')

    state = fields.Selection([
        ('available', 'Disponible'),
        ('pending', 'Pendiente Validación'),
        ('reserved', 'Reservado'),
        ('paid', 'Pagado'),
    ], default='available')

    payment_method = fields.Selection([
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
        ('other', 'Otro'),
    ], string='Medio de Pago')

    comprobante = fields.Binary(string='Comprobante')

    _sql_constraints = [
        ('unique_ticket', 'unique(rifa_id, numero)', 'Número de boleta duplicado!')
    ]

    display_name = fields.Char(compute="_compute_display_name")

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.partner_id and record.state == 'pending':

            bienestar_group = self.env.ref(
                'odoo_rifa.group_rifa_bienestar'
            )

            users = bienestar_group.user_ids

            for user in users:
                record.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=user.id,
                    note=f"Validar pago de boleta #{record.numero}"
                )

        return record

    @api.depends('numero')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.numero:03d}"

    def action_validate(self):
        for rec in self:

            if rec.state != 'pending':
                continue

            if rec.payment_method in ['transfer', 'other'] and not rec.comprobante:
                raise ValidationError("Debe adjuntar comprobante para validar el pago.")

            rec.state = 'paid'

            rec.partner_id.activity_schedule(
                'mail.mail_activity_data_meeting',
                summary="Participación en rifa",
                note=f"Boleta #{rec.numero} validada",
                date_deadline=fields.Date.today()
            )

            # marcar actividad como hecha
            rec.activity_unlink(['mail.mail_activity_data_todo'])

            # crear log
            rec.message_post(body="Pago validado correctamente.")

    def action_reject(self):

        for rec in self:

            if rec.state != 'pending':
                continue

            rec.write({
                'partner_id': False,
                'payment_method': False,
                'comprobante': False,
                'state': 'available',
            })

            # eliminar actividades
            rec.activity_unlink(['mail.mail_activity_data_todo'])

            # log
            rec.message_post(
                body=f"Pago rechazado. Boleta #{rec.numero} liberada nuevamente."
            )

    def write(self, vals):
        res = super().write(vals)

        for rec in self:

            if vals.get('state') == 'pending':

                # pasar rifa a en curso
                if rec.rifa_id.state == 'draft':
                    rec.rifa_id.state = 'open'

                group = self.env.ref(
                    'odoo_rifa.group_rifa_bienestar'
                )

                users = group.user_ids

                for user in users:

                    rec.message_post(
                        body=f"Boleta {rec.numero} pendiente de validación",
                        partner_ids=[user.partner_id.id]
                    )

        return res

    def create_activity(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        group = self.env.ref('odoo_rifa.group_rifa_bienestar')

        for user in group.users:
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get_id('rifa.ticket'),
                'res_id': self.id,
                'user_id': user.id,
                'activity_type_id': activity_type.id,
                'summary': 'Validar pago de boleta',
                'date_deadline': fields.Date.today(),
            })