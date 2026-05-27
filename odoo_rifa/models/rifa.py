from odoo import models, fields, api
from odoo.exceptions import ValidationError
import random


class Rifa(models.Model):
    _name = "rifa.rifa"
    _description = "Rifa"

    name = fields.Char(string="Nombre de la Rifa", required=True)

    premio_nombre = fields.Char(string="Premio", required=True)

    premio_imagen = fields.Binary(string="Imagen del Premio")

    cantidad_boletas = fields.Integer(string="Cantidad de Boletas", required=True)

    precio_boleta = fields.Float(string="Precio por Boleta")

    fecha_rifa = fields.Datetime(string="Fecha y Hora del Sorteo")

    porcentaje_disponible = fields.Float(
        string="Disponibilidad (%)", compute="_compute_disponibilidad"
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("open", "En Curso"),
            ("done", "Finalizada"),
        ],
        default="draft",
    )

    is_locked = fields.Boolean(compute="_compute_is_locked")

    can_play = fields.Boolean(compute="_compute_can_play")

    # relacion con tickets
    ticket_ids = fields.One2many("rifa.ticket", "rifa_id")

    has_tickets = fields.Boolean(compute="_compute_has_tickets")

    def _compute_has_tickets(self):
        for rec in self:
            rec.has_tickets = bool(rec.ticket_ids)

    @api.depends("ticket_ids.state", "fecha_rifa")
    def _compute_is_locked(self):

        for rec in self:

            vendidos = rec.ticket_ids.filtered(
                lambda t: t.state in ["pending", "paid", "reserved"]
            )

            # si ya vendieron una boleta
            if vendidos:
                rec.is_locked = True
            else:
                rec.is_locked = False

    @api.depends("fecha_rifa", "state")
    def _compute_can_play(self):

        now = fields.Datetime.now()

        for rec in self:

            rec.can_play = (
                rec.fecha_rifa and now >= rec.fecha_rifa and rec.state != "done"
            )

    @api.depends("ticket_ids.state")
    def _compute_disponibilidad(self):
        for rec in self:
            total = len(rec.ticket_ids)
            disponibles = len(rec.ticket_ids.filtered(lambda t: t.state == "available"))

            rec.porcentaje_disponible = (disponibles / total * 100) if total else 0

    @api.constrains("cantidad_boletas", "precio_boleta")
    def _check_numeric_values(self):
        for rec in self:
            if rec.cantidad_boletas <= 0:
                raise ValidationError("La cantidad de boletas debe ser mayor a 0.")

            if rec.precio_boleta < 0:
                raise ValidationError("El precio no puede ser negativo.")

    @api.constrains("fecha_rifa")
    def _check_fecha_rifa(self):
        for rec in self:
            if rec.fecha_rifa and rec.fecha_rifa < fields.Datetime.now():
                raise ValidationError("La fecha de la rifa no puede ser en el pasado.")

    # Generar boletas automáticamente
    def action_generar_boletas(self):
        for rec in self:
            if rec.ticket_ids:
                raise ValidationError("Las boletas ya fueron generadas.")

            tickets = []
            for i in range(1, rec.cantidad_boletas + 1):
                tickets.append(
                    {
                        "rifa_id": rec.id,
                        "numero": i,
                    }
                )

            self.env["rifa.ticket"].create(tickets)

    # eliminar rifa
    def action_delete_rifa(self):
        self.unlink()

        return {
            "type": "ir.actions.act_window",
            "name": "Rifas",
            "res_model": "rifa.rifa",
            "view_mode": "list,form",
        }

    @api.constrains("cantidad_boletas")
    def _check_boletas_update(self):
        for rec in self:
            if rec.ticket_ids:

                total_existentes = len(rec.ticket_ids)

                # no puede ser menor que las ya creadas
                if rec.cantidad_boletas < total_existentes:
                    raise ValidationError(
                        "No puedes reducir la cantidad por debajo de las boletas existentes."
                    )

                # si aumenta → crear nuevas automáticamente
                if rec.cantidad_boletas > total_existentes:
                    nuevos = []
                    for i in range(total_existentes + 1, rec.cantidad_boletas + 1):
                        nuevos.append(
                            {
                                "rifa_id": rec.id,
                                "numero": i,
                            }
                        )

                    self.env["rifa.ticket"].create(nuevos)

    def action_open_board(self):
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "rifa_ticket_board",
            "context": {
                "rifa_id": self.id,
                "is_bienestar": self.env.user.has_group(
                    "odoo_rifa.group_rifa_bienestar"
                ),
            },
        }

    def write(self, vals):
        for rec in self:

            if rec.ticket_ids:
                vendidos = len(rec.ticket_ids)

                nueva_cantidad = vals.get("cantidad_boletas", rec.cantidad_boletas)

                if nueva_cantidad < vendidos:
                    raise ValidationError(
                        "No puedes reducir por debajo de las boletas ya generadas/vendidas."
                    )

        return super().write(vals)

    # =========================
    # JUGAR RIFA
    # =========================
    def action_play_raffle(self):

        self.ensure_one()

        if self.state == "done":
            raise ValidationError("La rifa ya fue finalizada.")

        # TODAS LAS BOLETAS
        all_tickets = self.env["rifa.ticket"].search([("rifa_id", "=", self.id)])

        if not all_tickets:
            raise ValidationError("No existen boletas.")

        import random

        ticket = random.choice(all_tickets)

        winner = False

        # SOLO gana si está pagada
        if ticket.state == "paid":

            winner = {
                "numero": ticket.numero,
                "partner": ticket.partner_id.name,
            }

        # FINALIZAR RIFA
        self.state = "done"

        return {
            "winner": winner,
            "ticket": ticket.numero,
        }
