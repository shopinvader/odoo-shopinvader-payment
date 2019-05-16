# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopinvaderDonationService(Component):
    _inherit = ["shopinvader.invoice.service", "payment.service.adyen"]
    _name = "shopinvader.invoice.service"
