# Copyright 2019 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServicePaypalShopinvader(Component):

    # expose Paypal payment service under /shopinvader

    _name = "payment.service.paypal.shopinvader"
    _inherit = ["payment.service.paypal", "base.shopinvader.service"]
    _usage = "payment_paypal"
    _collection = "shopinvader.backend"
