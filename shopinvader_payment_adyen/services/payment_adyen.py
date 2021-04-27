# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PaymentServiceAdyenShopinvader(Component):

    # expose Adyen payment service under /shopinvader

    _name = "payment.service.adyen.shopinvader"
    _inherit = ["payment.service.adyen", "base.shopinvader.service"]
    _usage = "payment_adyen"
    _collection = "shopinvader.backend"
