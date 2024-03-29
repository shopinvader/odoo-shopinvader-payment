# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ShopinvaderPayment(models.Model):
    _name = "shopinvader.payment"
    _description = "Shopinvader Payment"
    _order = "sequence"

    acquirer_id = fields.Many2one(
        "payment.acquirer", required=True, ondelete="restrict"
    )
    sequence = fields.Integer()
    backend_id = fields.Many2one(
        "shopinvader.backend", "Backend", required=True, ondelete="cascade"
    )
    notification = fields.Selection(
        [
            ("cart_confirmation", "Cart Validation"),
            ("sale_confirmation", "Sale Confirmation"),
            (
                "cart_confirmation_and_sale_confirmation",
                "Cart and Sale Confirmation",
            ),
        ]
    )
    manual = fields.Boolean()
    code = fields.Char()
    description = fields.Html()
    show_description_after_validation = fields.Boolean()
