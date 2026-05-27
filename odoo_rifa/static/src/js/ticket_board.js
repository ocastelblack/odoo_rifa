/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { TicketModal } from "./ticket_modal";
import { WinnerModal } from "./winner_modal";

class TicketBoard extends Component {

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.action = useService("action");

        const ctx = this.props.action.context || {};

        this.isBienestar = ctx.is_bienestar || false;

        this.state = useState({
            tickets: [],
            selected: [],
            page: 1,
            limit: 50,
            total: 0,
            rifa: null,
            pageOptions: [],
        });

        onWillStart(async () => {
            await this.loadTickets();
        });
    }

    async loadTickets() {

        const ctx = this.props.action.context || {};
        const rifa_id = ctx.rifa_id;

        // RIFA
        const rifa = await this.orm.read(
            "rifa.rifa",
            [rifa_id],
            [
                "id",
                "name",
                "premio_nombre",
                "fecha_rifa",
                "state",
                "can_play",
            ]
        );

        this.state.rifa = rifa[0];

        // TICKETS
        const offset = (this.state.page - 1) * this.state.limit;

        const result = await this.orm.searchRead(
            "rifa.ticket",
            [["rifa_id", "=", rifa_id]],
            [
                "id",
                "numero",
                "state",
                "partner_id",
                "payment_method",
                "comprobante",
            ],
            {
                offset: offset,
                limit: this.state.limit,
            }
        );

        this.state.tickets = result;

        this.state.total = await this.orm.searchCount(
            "rifa.ticket",
            [["rifa_id", "=", rifa_id]]
        );

        // opciones dinámicas
        const options = [];

        for (let i = 50; i <= this.state.total; i += 50) {
            options.push(i);
        }

        // agregar total exacto si no coincide
        if (
            this.state.total > 0 &&
            !options.includes(this.state.total)
        ) {
            options.push(this.state.total);
        }

        this.state.pageOptions = options;
    }

    nextPage() {
        if (this.state.page * this.state.limit < this.state.total) {
            this.state.page++;
            this.loadTickets();
        }
    }

    prevPage() {
        if (this.state.page > 1) {
            this.state.page--;
            this.loadTickets();
        }
    }

    openTicket(ticket) {

        // bloquear interacción si terminó
        if (this.state.rifa?.state === "done") {
            return;
        }

        console.log("CLICK TICKET", ticket);

        this.dialog.add(TicketModal, {
            ticket: ticket,
            isBienestar: this.isBienestar,

            onSave: async (data) => {
                await this.orm.write("rifa.ticket", [ticket.id], data);
                await this.loadTickets();
            },

            onValidate: async () => {
                await this.orm.call(
                    "rifa.ticket",
                    "action_validate",
                    [[ticket.id]]
                );

                await this.loadTickets();
            }
        });
    }

    getColor(ticket) {
        if (ticket.state === 'paid') return '#28a745';
        if (ticket.state === 'pending') return '#ffc107';
        if (ticket.state === 'reserved') return '#dc3545';
        if (this.state.selected.includes(ticket.id)) return '#007bff';
        return '#ffffff';
    }

    goBack() {
        this.action.doAction("odoo_rifa.action_rifas");
    }

    //paginador
    async changeLimit(ev) {
        this.state.limit = parseInt(ev.target.value);
        this.state.page = 1;
        await this.loadTickets();
    }

    async generateImage() {

        const board = document.getElementById("rifa-export");

        if (!board) {
            return;
        }

        const canvas = await html2canvas(board, {
            backgroundColor: "#ffffff",
            scale: 3,
        });

        const link = document.createElement("a");

        link.download = `rifa_${this.state.rifa.name}.png`;

        link.href = canvas.toDataURL("image/png");

        link.click();
    }

    async playRaffle() {

        if (this.state.rifa?.state === "done") {
            return;
        }

        // traer TODOS los tickets
        const allTickets = await this.orm.searchRead(
            "rifa.ticket",
            [["rifa_id", "=", this.state.rifa.id]],
            [
                "id",
                "numero",
                "state",
                "partner_id",
            ]
        );

        // animación fake
        let counter = 0;

        const interval = setInterval(() => {

            const random =
                allTickets[
                Math.floor(Math.random() * allTickets.length)
                ];

            // si está visible en pantalla lo ilumina
            const visible = this.state.tickets.find(
                t => t.id === random.id
            );

            if (visible) {
                this.state.selected = [visible.id];
            }

            counter++;

            if (counter > 30) {
                clearInterval(interval);
            }

        }, 100);

        // esperar animación
        await new Promise(resolve => setTimeout(resolve, 4000));

        // sorteo REAL backend
        const result = await this.orm.call(
            "rifa.rifa",
            "action_play_raffle",
            [[this.state.rifa.id]]
        );

        // buscar ganador visible
        const winnerVisible = this.state.tickets.find(
            t => t.numero === result.ticket
        );

        if (winnerVisible) {
            this.state.selected = [winnerVisible.id];
        }

        // modal
        this.dialog.add(WinnerModal, {
            result: result,
        });

        // bloquear sistema
        this.state.rifa.state = "done";

        await this.loadTickets();
    }
}

TicketBoard.template = "odoo_rifa.TicketBoard";

registry.category("actions").add("rifa_ticket_board", TicketBoard);