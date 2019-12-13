# Copyright 2019 ACSONE SA/NV (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class PaymentServiceManualShopinvader(Component):

    # expose bank transfer payment service under /shopinvader

    _name = "payment.service.manual.shopinvader"
    _inherit = ["payment.service.manual", "base.shopinvader.service"]
    _usage = "payment_manual"
    _collection = "shopinvader.backend"
