# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.component.core import Component


class PaymentServiceBankTransferShopinvader(Component):

    # expose bank transfer payment service under /shopinvader

    _name = "payment.service.bank_transfer.shopinvader"
    _inherit = ["payment.service.bank_transfer", "base.shopinvader.service"]
    _usage = "payment_bank_transfer"
    _collection = "shopinvader.backend"
