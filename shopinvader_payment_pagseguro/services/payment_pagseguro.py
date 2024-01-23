#  Copyright 2022 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentServicePagseguroShopinvader(Component):
    """Expose Pagseguro payment service under /shopinvader endpoint"""

    _name = "payment.service.pagseguro.shopinvader"
    _inherit = ["payment.service.pagseguro", "base.shopinvader.service"]
    _usage = "payment_pagseguro"
    _collection = "shopinvader.backend"
