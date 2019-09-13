# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AcquirerPaypal(models.Model):
    _inherit = "payment.acquirer"

    paypal_client_id = fields.Char()
    paypal_secret = fields.Char()
