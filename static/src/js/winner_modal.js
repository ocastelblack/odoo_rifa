/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class WinnerModal extends Component {

    static template = "odoo_rifa.WinnerModal";

    static components = {
        Dialog,
    };

    static props = {
        close: Function,
        result: Object,
    };
}