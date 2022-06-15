# Copyright 2021 Camptocamp SA (https://www.camptocamp.com).
# @author Iván Todorovich <ivan.todorovich@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShopinvaderPayment(models.Model):
    _inherit = "shopinvader.payment"

    domain = fields.Char(
        string="Condition",
        help="Propose this payment method only if the sale order satisfies this domain",
        default="[]",
    )
