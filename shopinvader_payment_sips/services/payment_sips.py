# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.component.core import Component


class PaymentServiceSipsShopinvader(Component):

    # expose SIPS payment service under /shopinvader

    _name = "payment.service.sips.shopinvader"
    _inherit = ["payment.service.sips", "base.shopinvader.service"]
    _usage = "payment_sips"
    _collection = "shopinvader.backend"
