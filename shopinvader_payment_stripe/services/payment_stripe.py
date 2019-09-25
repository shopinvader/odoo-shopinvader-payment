# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PaymentServiceStripShopinvader(Component):

    # expose Stripe payment service under /shopinvader

    _name = "payment.service.stripe.shopinvader"
    _inherit = ["payment.service.stripe", "base.shopinvader.service"]
    _usage = "payment_stripe"
    _collection = "shopinvader.backend"
