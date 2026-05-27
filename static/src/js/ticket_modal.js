/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class TicketModal extends Component {

    static template = "odoo_rifa.TicketModal";

    static components = {
        Dialog,
    };

    static props = {
        close: Function,
        ticket: Object,
        isBienestar: Boolean,
        onSave: Function,
        onValidate: Function,
    };

    setup() {

        this.orm = useService("orm");

        const ticket = this.props.ticket;

        this.state = useState({

            partner_id: ticket.partner_id ? ticket.partner_id[0] : null,

            partner_name: ticket.partner_id ? ticket.partner_id[1] : "",

            partner_results: [],

            payment_method: ticket.payment_method || "cash",

            comprobante: ticket.comprobante || null,

            state: ticket.state,

        });

        this.searchTimeout = null;
    }

    onSearchPartner(ev) {
        const value = ev.target.value;
        this.state.partner_name = value;

        clearTimeout(this.searchTimeout);

        this.searchTimeout = setTimeout(async () => {

            if (!value) {
                this.state.partner_results = [];
                return;
            }

            const results = await this.orm.searchRead(
                "res.partner",
                [["name", "ilike", value]],
                ["name"],
                { limit: 5 }
            );

            this.state.partner_results = results;

        }, 300);
    }

    selectPartner(p) {
        this.state.partner_id = p.id;
        this.state.partner_name = p.name;
        this.state.partner_results = [];
    }

    onFileChange(ev) {

        const file = ev.target.files?.[0];

        if (!file) {
            return;
        }

        const reader = new FileReader();

        reader.onload = () => {
            this.state.comprobante = reader.result.split(",")[1];
        };

        reader.readAsDataURL(file);
    }

    async save() {

        if (!this.state.partner_id) {
            alert("Debe seleccionar un cliente");
            return;
        }

        const data = {
            partner_id: this.state.partner_id,
            payment_method: this.state.payment_method,
            comprobante: this.state.comprobante,
            state: "pending",
        };

        await this.props.onSave(data);

        this.props.close();
    }

    async validate() {

        await this.props.onValidate();

        this.props.close();
    }

    async reject() {

        await this.orm.call(
            "rifa.ticket",
            "action_reject",
            [[this.props.ticket.id]]
        );

        this.props.close();

        location.reload();
    }

    async createPartner() {

        if (!this.state.partner_name) {
            alert("Escribe un nombre");
            return;
        }

        const newName = this.state.partner_name;

        const partnerId = await this.orm.create(
            "res.partner",
            [{
                name: newName,
            }]
        );

        this.state.partner_id = partnerId;

        this.state.partner_name = newName;

        this.state.partner_results = [];
    }
}