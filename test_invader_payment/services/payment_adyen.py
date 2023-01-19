# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (https://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServiceAdyen(Component):
    _name = "test.payment.service.adyen"
    _inherit = "payment.service.adyen"
    _collection = "res.partner"
