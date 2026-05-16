{
    "name": "Raffle Management",
    "version": "19.0.0.1",
    "summary": """Module for managing raffles in Odoo, creating contacts if they do not exist, managing products directly from the inventory, controlling ticket payments,
                playing games directly from Odoo, to generate well-being in the company.
    """,
    "author": "Oscar Danilo Castelblanco Amaya",
    "category": "Sales",
    "price": 30,
    "currency": "EUR",
    "depends": ["base", "contacts"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/rifa_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoo_rifa/static/lib/html2canvas.min.js",
            "odoo_rifa/static/src/js/ticket_board.js",
            "odoo_rifa/static/src/js/ticket_modal.js",
            "odoo_rifa/static/src/xml/ticket_board.xml",
            "odoo_rifa/static/src/xml/ticket_modal.xml",
            "odoo_rifa/static/src/js/winner_modal.js",
            "odoo_rifa/static/src/xml/winner_modal.xml",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
