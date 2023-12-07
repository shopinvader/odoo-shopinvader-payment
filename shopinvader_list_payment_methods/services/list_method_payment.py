#  Copyright 2023 KMEE
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PaymentListMethodShopinvader(Component):
    """Expose list of payment methods on service under /shopinvader endpoint"""

    _name = "payment.service.list.shopinvader"
    _inherit = ["payment.service.list", "base.shopinvader.service"]
    _usage = "payment_list_method"
    _collection = "shopinvader.backend"
